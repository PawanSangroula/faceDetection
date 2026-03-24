

import cv2
import os
import pickle
import time
import numpy as np
import face_recognition  

# -------------------- MEDIAPIPE IMPORTS --------------------
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import face_landmarker
from mediapipe.tasks.python.vision.face_landmarker import (
    FaceLandmarker,
    FaceLandmarkerOptions,
)
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode as RunningMode
import mediapipe as mp

# -------------------- CONFIG --------------------
name = input("Enter your name: ")

encodings_folder = "encodings"
if not os.path.exists(encodings_folder):
    os.makedirs(encodings_folder)

# -------------------- DNN FACE DETECTOR --------------------
modelFile = "res10_300x300_ssd_iter_140000.caffemodel"
configFile = "deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

# -------------------- MEDIA PIPE FACE LANDMARKER --------------------
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="face_landmarker.task"),
    running_mode=RunningMode.VIDEO,
    num_faces=1,
)
landmarker = FaceLandmarker.create_from_options(options)

# -------------------- INSTRUCTIONS --------------------
instructions = [
    {"text": "Look straight at the camera", "yaw": 0},
    {"text": "Turn your face slightly left", "yaw": -15},
    {"text": "Turn your face slightly right", "yaw": 15},
    {"text": "Move closer to the camera", "size": "near"},
    {"text": "Move farther from the camera", "size": "far"},
]

frames_per_instruction = 10
COUNTDOWN_SECONDS = 2

# -------------------- HELPER FUNCTIONS --------------------
def get_face_yaw(landmarks, w):
    left_eye  = landmarks[33]
    right_eye = landmarks[263]
    nose      = landmarks[1]
    eye_center_x = (left_eye.x + right_eye.x) / 2
    yaw = (nose.x - eye_center_x) * w
    return yaw

def get_face_size(landmarks, w, h):
    left_eye  = landmarks[33]
    right_eye = landmarks[263]
    eye_dist  = abs(left_eye.x - right_eye.x) * w
    return eye_dist

# -------------------- CAMERA --------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")

cv2.namedWindow("Face Capture", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Face Capture", 800, 600)
cv2.setWindowProperty("Face Capture", cv2.WND_PROP_TOPMOST, 1)

face_data = []
start_time_ms = int(time.time() * 1000)
quit_requested = False

print("Starting automatic face capture...")

# -------------------- INSTRUCTION LOOP --------------------
for instr_idx, instr in enumerate(instructions):
    print(f"\n[{instr_idx+1}/{len(instructions)}] {instr['text']}")

    # ---- Countdown loop ----
    countdown_end = time.time() + COUNTDOWN_SECONDS
    while time.time() < countdown_end:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # flip AFTER the break check

        remaining = int(countdown_end - time.time()) + 1
        cv2.putText(frame, instr["text"], (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        cv2.putText(frame, f"Get ready... {remaining}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
        cv2.imshow("Face Capture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            quit_requested = True
            break
    if quit_requested:
        break

    # ---- Capture loop ----
    frames_captured = 0
    while frames_captured < frames_per_instruction:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # flip added here too
        h, w = frame.shape[:2]

        timestamp_ms = int(time.time() * 1000) - start_time_ms

        # ---- DNN face detection ----
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0)
        )
        net.setInput(blob)
        detections = net.forward()

        best_confidence = 0
        best_box = None
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5 and confidence > best_confidence:
                best_confidence = confidence
                best_box = detections[0, 0, i, 3:7] * [w, h, w, h]

        instruction_done = False

        if best_box is not None:
            startX, startY, endX, endY = best_box.astype("int")
            startX, startY = max(0, startX), max(0, startY)
            endX,   endY   = min(w, endX),   min(h, endY)

            face_roi = frame[startY:endY, startX:endX]
            if face_roi.size > 0:
                rgb_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                fh, fw = rgb_face.shape[:2]

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_face
                )

                results = landmarker.detect_for_video(mp_image, timestamp_ms)

                if results.face_landmarks:
                    landmarks = results.face_landmarks[0]

                    yaw  = get_face_yaw(landmarks, fw)
                    size = get_face_size(landmarks, fw, fh)

                    if "yaw" in instr and abs(yaw - instr["yaw"]) < 15:
                        instruction_done = True
                    if "size" in instr:
                        if instr["size"] == "near" and size > 70:
                            instruction_done = True
                        if instr["size"] == "far"  and size < 50:
                            instruction_done = True

            if instruction_done:
                frames_captured += 1
                face_data.append(frame.copy())
                cv2.putText(frame, "Captured!", (w // 2 - 80, h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

        cv2.putText(frame, instr["text"], (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frames_captured}/{frames_per_instruction}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Face Capture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            quit_requested = True
            break

    if quit_requested:
        print("Quit requested — saving collected frames so far.")
        break


# -------------------- SAVE RAW FRAMES --------------------
out_path = os.path.join(encodings_folder, f"{name}.pkl")
with open(out_path, "wb") as f:
    pickle.dump(face_data, f)

print(f"Saved {len(face_data)} raw frames for '{name}' → {out_path}")

cap.release()
landmarker.close()
cv2.destroyAllWindows()