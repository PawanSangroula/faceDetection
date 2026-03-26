from flask import Blueprint, request, jsonify
from database import get_db
from models import save_attendance, get_all_attendance, get_attendance_by_name

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()

    if not data or "name" not in data:
        return jsonify({"success": False, "error": "name is required"}), 400

    name = data["name"].strip()
    if not name:
        return jsonify({"success": False, "error": "name cannot be empty"}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            save_attendance(cursor, name)

        return jsonify({
            "success": True,
            "message": f"Attendance marked for {name}"
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@attendance_bp.route("/attendance", methods=["GET"])
def view_attendance():
    name = request.args.get("name")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            if name:
                records = get_attendance_by_name(cursor, name)
            else:
                records = get_all_attendance(cursor)

        return jsonify({
            "success": True,
            "count": len(records),
            "records": records
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500