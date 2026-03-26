import cv2
import numpy as np
import dlib
import pickle
import os
from datetime import datetime
import requests

# ----------------------------
# SEND TO BACKEND
# ----------------------------
def send_attendance(name):
    url = "http://localhost:5000/attendance"

    data = {
        "name": name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        response = requests.post(url, json=data)
        result = response.json()
        return result.get("message", "Error")
    except Exception as e:
        print(f"❌ Error sending {name}:", e)
        return "Error"

# ----------------------------
# Load dlib models
# ----------------------------
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

# ----------------------------
# Load encodings
# ----------------------------
known_encodings = []
known_names = []

encoding_folder = "encoded"

for file in os.listdir(encoding_folder):
    if file.endswith(".pkl"):
        with open(os.path.join(encoding_folder, file), "rb") as f:
            enc_list = pickle.load(f)

        if not enc_list:
            continue

        name = os.path.splitext(file)[0]
        known_encodings.extend(enc_list)
        known_names.extend([name] * len(enc_list))

print("Loaded:", list(set(known_names)))

# ----------------------------
# Load DNN face detector
# ----------------------------
net = cv2.dnn.readNetFromCaffe(
    "deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel"
)

# ----------------------------
# Initialize webcam
# ----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")

frame_count = 0
last_face_locations = []
last_face_names = []

THRESHOLD = 0.5

# 🔥 Store attendance status (Present / Already Marked)
status_dict = {}

# ----------------------------
# MAIN LOOP
# ----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_count += 1

    # Process every 3rd frame (performance boost)
    if frame_count % 3 == 0:

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        sh, sw = small_frame.shape[:2]

        # ----------------------------
        # DNN face detection
        # ----------------------------
        blob = cv2.dnn.blobFromImage(
            cv2.resize(small_frame, (300, 300)),
            1.0, (300, 300),
            (104.0, 177.0, 123.0)
        )

        net.setInput(blob)
        detections = net.forward()

        face_locations = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([sw, sh, sw, sh])
                (startX, startY, endX, endY) = box.astype("int")
                face_locations.append((startX, startY, endX, endY))

        # ----------------------------
        # Recognition
        # ----------------------------
        rgb_small = np.ascontiguousarray(small_frame[:, :, ::-1], dtype=np.uint8)
        face_names = []

        for (startX, startY, endX, endY) in face_locations:
            rect = dlib.rectangle(startX, startY, endX, endY)
            shape = shape_predictor(rgb_small, rect)
            enc = np.array(face_rec_model.compute_face_descriptor(rgb_small, shape))

            name = "Unknown"

            if known_encodings:
                distances = [np.linalg.norm(enc - k) for k in known_encodings]
                best_idx = np.argmin(distances)

                if distances[best_idx] < THRESHOLD:
                    name = known_names[best_idx]

            face_names.append(name)

        # scale back to original frame
        last_face_locations = [(x1*2, y1*2, x2*2, y2*2) for (x1, y1, x2, y2) in face_locations]
        last_face_names = face_names

        # ----------------------------
        # SEND ATTENDANCE (only once per person)
        # ----------------------------
        for name in face_names:
            if name != "Unknown":
                if name not in status_dict:
                    message = send_attendance(name)
                    status_dict[name] = message

    # ----------------------------
    # DRAW RESULTS
    # ----------------------------
    for (startX, startY, endX, endY), name in zip(last_face_locations, last_face_names):

        display_text = name
        color = (0, 0, 255)  # red for unknown

        if name in status_dict:
            if status_dict[name] == "Marked present":
                display_text = f"{name} (Present)"
                color = (0, 255, 0)  # green
            elif status_dict[name] == "Already marked today":
                display_text = f"{name} (Already Marked)"
                color = (0, 255, 255)  # yellow

        cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
        cv2.rectangle(frame, (startX, endY - 30), (endX, endY), color, cv2.FILLED)

        cv2.putText(frame, display_text, (startX + 5, endY - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imshow("Smart Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()