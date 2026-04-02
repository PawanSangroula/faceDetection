"""
capture_logic.py
────────────────
Pure processing logic — no camera, no windows, no UI.

Receives a single BGR numpy frame + instruction dict + timestamp,
returns a result dict.
"""

import os
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.face_landmarker import (
    FaceLandmarker,
    FaceLandmarkerOptions,
)
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode as RunningMode,
)

# ── Resolve paths relative to THIS file so the server can be run from anywhere
_HERE = os.path.dirname(os.path.abspath(__file__))

_PROTO   = os.path.join(_HERE, "deploy.prototxt")
_MODEL   = os.path.join(_HERE, "res10_300x300_ssd_iter_140000.caffemodel")
_TASK    = os.path.join(_HERE, "face_landmarker.task")

# ── Load DNN face detector (once at import time)
net = cv2.dnn.readNetFromCaffe(_PROTO, _MODEL)

# ── Load MediaPipe face landmarker (once at import time)
_options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=_TASK),
    running_mode=RunningMode.VIDEO,
    num_faces=1,
)
landmarker = FaceLandmarker.create_from_options(_options)


# ────────────────────────────────────────────────
# Helper functions
# ────────────────────────────────────────────────

def _get_yaw(landmarks, w: int) -> float:
    """Estimate horizontal face turn from landmark positions."""
    left_eye  = landmarks[33]
    right_eye = landmarks[263]
    nose      = landmarks[1]
    eye_center_x = (left_eye.x + right_eye.x) / 2
    return (nose.x - eye_center_x) * w


def _get_size(landmarks, w: int) -> float:
    """Estimate face size (inter-eye distance in pixels)."""
    left_eye  = landmarks[33]
    right_eye = landmarks[263]
    return abs(left_eye.x - right_eye.x) * w


# ────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────

def process_frame(frame: np.ndarray, instruction: dict, timestamp: int) -> dict:
    """
    Parameters
    ----------
    frame       : BGR numpy array (already decoded from base64)
    instruction : dict with ONE of:
                    {"text": ..., "yaw": <int>}          — pose instruction
                    {"text": ..., "size": "near"|"far"}  — distance instruction
    timestamp   : milliseconds (monotonically increasing per session)

    Returns
    -------
    dict with "status" key and optionally "face" (the frame numpy array).
    """
    h, w = frame.shape[:2]

    # ── 1. DNN face detection ──────────────────────────────
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)),
        1.0, (300, 300),
        (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()

    best_conf = 0.0
    best_box  = None

    for i in range(detections.shape[2]):
        conf = float(detections[0, 0, i, 2])
        if conf > 0.5 and conf > best_conf:
            best_conf = conf
            best_box  = detections[0, 0, i, 3:7] * np.array([w, h, w, h])

    if best_box is None:
        return {"status": "no_face"}

    startX, startY, endX, endY = best_box.astype("int")
    startX, startY = max(0, startX), max(0, startY)
    endX,   endY   = min(w, endX),   min(h, endY)

    # ── 2. Crop face ROI ───────────────────────────────────
    face_roi = frame[startY:endY, startX:endX]
    if face_roi.size == 0:
        return {"status": "invalid_face"}

    rgb_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
    fh, fw   = rgb_face.shape[:2]

    # ── 3. MediaPipe landmarks ─────────────────────────────
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_face)
    results  = landmarker.detect_for_video(mp_image, timestamp)

    if not results.face_landmarks:
        return {"status": "no_landmarks"}

    landmarks = results.face_landmarks[0]
    yaw  = _get_yaw(landmarks, fw)
    size = _get_size(landmarks, fw)

    # ── 4. Validate against instruction ───────────────────
    if "yaw" in instruction:
        if abs(yaw - instruction["yaw"]) < 15:
            return {"status": "valid", "face": frame}
        return {"status": "adjust_pose"}

    if "size" in instruction:
        if instruction["size"] == "near" and size > 70:
            return {"status": "valid", "face": frame}
        if instruction["size"] == "far"  and size < 50:
            return {"status": "valid", "face": frame}
        return {"status": "adjust_distance"}

    # Fallback — accept anything
    return {"status": "valid", "face": frame}