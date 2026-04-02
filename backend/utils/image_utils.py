import base64
import numpy as np
import cv2

def decode_base64(frame_b64: str) -> np.ndarray:
    if "," in frame_b64:
        frame_b64 = frame_b64.split(",")[1]

    img_data = base64.b64decode(frame_b64)
    np_arr   = np.frombuffer(img_data, np.uint8)
    img      = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image.")

    return cv2.resize(img, (320, 240))