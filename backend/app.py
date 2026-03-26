# backend/app.py
from flask import Flask
from database import init_db
from routes.attendance import attendance_bp

app = Flask(__name__)

# Register routes
app.register_blueprint(attendance_bp)

# Create tables on startup
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)