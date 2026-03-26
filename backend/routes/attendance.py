from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

# ✅ POST: Save attendance (only once per day)
@attendance_bp.route('/attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()

    student_name = data.get("name")
    marked_at = data.get("time")

    if not student_name or not marked_at:
        return jsonify({"error": "Missing data"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 🔥 Check if already marked today
    today = datetime.now().strftime("%Y-%m-%d")

    existing = cursor.execute("""
        SELECT * FROM attendance
        WHERE student_name = ?
        AND DATE(marked_at) = ?
    """, (student_name, today)).fetchone()

    if existing:
        conn.close()
        return jsonify({"message": "Already marked today"}), 200

    # ✅ Insert if not marked today
    cursor.execute(
        "INSERT INTO attendance (student_name, marked_at) VALUES (?, ?)",
        (student_name, marked_at)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Marked present"}), 201


# ✅ GET: View attendance
@attendance_bp.route('/attendance', methods=['GET'])
def get_attendance():
    conn = get_db()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT * FROM attendance
        ORDER BY marked_at DESC
    """).fetchall()

    result = [dict(row) for row in rows]

    conn.close()

    return jsonify(result)