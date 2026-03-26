# backend/models.py
from datetime import datetime

def save_attendance(cursor, name):
    """Insert one attendance record."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO attendance (student_name, marked_at) VALUES (?, ?)",
        (name, now)
    )

def get_all_attendance(cursor):
    """Fetch all attendance records."""
    cursor.execute(
        "SELECT id, student_name, marked_at FROM attendance ORDER BY marked_at DESC"
    )
    rows = cursor.fetchall()
    return [{"id": r["id"], "name": r["student_name"], "marked_at": r["marked_at"]} for r in rows]

def get_attendance_by_name(cursor, name):
    """Fetch attendance records for a specific student."""
    cursor.execute(
        "SELECT id, student_name, marked_at FROM attendance WHERE student_name = ? ORDER BY marked_at DESC",
        (name,)
    )
    rows = cursor.fetchall()
    return [{"id": r["id"], "name": r["student_name"], "marked_at": r["marked_at"]} for r in rows]
