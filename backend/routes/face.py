from flask import Blueprint, request, jsonify
from utils.image_utils import decode_base64
from services.face_service import handle_frame

face_bp = Blueprint("face", __name__)

@face_bp.route("/process-frame", methods=["POST"])  # ← removed /api
def process_frame():
    data = request.json

    if not data or "frame" not in data:
        return jsonify({"status": "error", "message": "No frame provided"}), 400

    frame       = decode_base64(data["frame"])
    instruction = data["instruction"]
    name        = data["name"]
    timestamp   = data.get("timestamp", 0)

    result = handle_frame(name, frame, instruction, timestamp)
    return jsonify(result)

@face_bp.route("/reset/<name>", methods=["POST"])  # ← removed /api
def reset_student(name):
    from services.face_service import collected
    if name in collected:
        del collected[name]
    return jsonify({"status": "reset"})