import sys
import os

# Go up from backend/services/ → backend/ → root → find vision/
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.abspath(ROOT))

import pickle
from vision.capture_logic import process_frame as vision_process

collected = {}
MAX_FRAMES = 10
ENCODINGS_DIR = os.path.join(ROOT, "vision", "encodings")

def handle_frame(name, frame, instruction, timestamp):
    if name not in collected:
        collected[name] = []

    result = vision_process(frame, instruction, timestamp)

    if result["status"] != "valid":
        return {"status": result["status"]}

    collected[name].append(result["face"])
    count = len(collected[name])

    if count >= MAX_FRAMES:
        _save_frames(name)
        collected[name] = []
        return {"status": "step_completed", "count": MAX_FRAMES}

    return {"status": "captured", "count": count}

def _save_frames(name):
    os.makedirs(ENCODINGS_DIR, exist_ok=True)
    out_path = os.path.join(ENCODINGS_DIR, f"{name}.pkl")

    existing = []
    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            existing = pickle.load(f)

    existing.extend(collected.get(name, []))

    with open(out_path, "wb") as f:
        pickle.dump(existing, f)

    print(f"[face_service] Saved {len(existing)} frames for '{name}'")