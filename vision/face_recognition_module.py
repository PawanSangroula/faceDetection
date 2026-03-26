import cv2
import numpy as np
import dlib
import pickle
import os
import requests

# ----------------------------
# Load dlib models
# ----------------------------
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

# ----------------------------
# Load all saved face encodings
# ----------------------------
known_encodings = []
known_names = []

encoding_folder = "encoded"
for file in os.listdir(encoding_folder):
    if file.endswith(".pkl"):
        with open(os.path.join(encoding_folder, file), "rb") as f:
            enc_list = pickle.load(f)

        if not enc_list:
            print(f"WARNING: {file} is empty, skipping.")
            continue

        name = os.path.splitext(file)[0]
        known_encodings.extend(enc_list)
        known_names.extend([name] * len(enc_list))
        print(f"Loaded {len(enc_list)} encodings for {name}")

print(f"\nTotal encodings loaded: {len(known_encodings)}")
print(f"People registered: {list(set(known_names))}\n")

# ----------------------------
# Load DNN face detector
# ----------------------------
modelFile = "res10_300x300_ssd_iter_140000.caffemodel"
configFile = "deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

# ----------------------------
# Initialize webcam
# ----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")

marked_students = set()
frame_count = 0
last_face_locations = []
last_face_names = []

THRESHOLD = 0.5
BACKEND_URL = "http://localhost:5000/attendance"

def mark_attendance(name):
    """Send attendance to Flask backend."""
    try:
        response = requests.post(BACKEND_URL, json={"name": name})
        if response.status_code == 201:
            print(f"{name} attendance marked successfully")
        else:
            print(f"Failed to mark {name}: {response.json()}")
    except Exception as e:
        print(f"Could not reach backend: {e}")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_count += 1

    if frame_count % 3 == 0:
        h, w = frame.shape[:2]

        # Shrink for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        sh, sw = small_frame.shape[:2]

        # DNN face detection
        blob = cv2.dnn.blobFromImage(cv2.resize(small_frame, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        face_locations = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([sw, sh, sw, sh])
                (startX, startY, endX, endY) = box.astype("int")
                startX, startY = max(0, startX), max(0, startY)
                endX,   endY   = min(sw, endX),  min(sh, endY)
                face_locations.append((startX, startY, endX, endY))

        face_names = []
        rgb_small = np.ascontiguousarray(small_frame[:, :, ::-1], dtype=np.uint8)

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

        # Scale locations back to full frame
        scaled_locations = [(x1*2, y1*2, x2*2, y2*2) for (x1, y1, x2, y2) in face_locations]
        last_face_locations = scaled_locations
        last_face_names = face_names

        # Mark attendance via Flask backend
        for name in face_names:
            if name != "Unknown" and name not in marked_students:
                marked_students.add(name)
                mark_attendance(name)

    # Draw boxes every frame for smooth display
    for (startX, startY, endX, endY), name in zip(last_face_locations, last_face_names):
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
        cv2.rectangle(frame, (startX, endY - 30), (endX, endY), color, cv2.FILLED)
        cv2.putText(frame, name, (startX + 5, endY - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, f"Marked: {len(marked_students)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Live Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\nSession complete. Total marked: {len(marked_students)}")
print(f"Students: {list(marked_students)}")