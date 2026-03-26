import dlib
import pickle
import numpy as np
import os

raw_folder = "encodings"
encoded_folder = "encoded"

if not os.path.exists(encoded_folder):
    os.makedirs(encoded_folder)

# Load dlib models
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

for file in os.listdir(raw_folder):
    if not file.endswith(".pkl"):
        continue

    name = os.path.splitext(file)[0]
    out_path = os.path.join(encoded_folder, f"{name}.pkl")

    # 🔥 Skip if already encoded
    if os.path.exists(out_path):
        print(f"Skipping {name} (already encoded)")
        continue

    with open(os.path.join(raw_folder, file), "rb") as f:
        frames = pickle.load(f)

    print(f"\nProcessing {name} — {len(frames)} frames...")

    encodings = []
    for i, frame in enumerate(frames):
        rgb = frame[:, :, ::-1]  # BGR to RGB
        dets = detector(rgb, 1)

        if len(dets) == 0:
            print(f"  Frame {i+1}: no face found, skipping")
            continue

        shape = shape_predictor(rgb, dets[0])
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
        enc = face_rec_model.compute_face_descriptor(rgb, shape)

        encodings.append(np.array(enc))
        print(f"  Frame {i+1}: encoded OK")

    with open(out_path, "wb") as f:
        pickle.dump(encodings, f)

    print(f"Saved {len(encodings)} encodings for '{name}' → {out_path}")

print("\nAll done!")
