# backend/app.py
from flask import Flask
from database import init_db
from routes.attendance import attendance_bp
from routes.face import face_bp          # ← ADD THIS

app = Flask(__name__)

# Register routes
app.register_blueprint(attendance_bp)
app.register_blueprint(face_bp, url_prefix="/api")  


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)