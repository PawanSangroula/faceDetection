
# CCTV Attendance System

## Tech Stack
- Python (Flask)
- OpenCV
- Face Recognition
- React
- SQLite

## Project Structure
- backend/
- vision/
- frontend/
- database/

## How to Run
1. Activate venv
2. Run vision module
3. Run backend server
4. Run frontend


Architecture for Live CCTV

CCTV Camera (IP Camera)
        ↓
RTSP Stream
        ↓
OpenCV VideoCapture(rtsp_url)
        ↓
Frame Processing (Face Detection)
        ↓
Face Recognition
        ↓
Flask Backend (Attendance Logic)
        ↓
SQLite Database
        ↓
React Dashboard


Project structure 
attendance-system/
│
backend/
├── app.py                    <-- Main backend server (Flask/FastAPI)
├── webcam_test.py            <-- Optional webcam test script
├── face_detection.py         <-- Optional: future refactor for backend use
├── routes/                   <-- Flask API routes (attendance endpoints)
├── services/                 <-- Business logic (attendance services)
├── models/                   <-- Database models (SQLAlchemy or ORM)
├── database/                 <-- Database config / connection files
└── requirements.txt          <-- Python dependencies
│
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
│
vision/
├── camera.py                 <-- Live face data capture (enrollment)
├── face_recognition_module.py <-- Optimized live recognition + DNN + attendance
├── encodings/                 <-- Auto-created folder to save .pkl encodings
├── deploy.prototxt            <-- DNN model config file
└── res10_300x300_ssd_iter_140000.caffemodel  <-- DNN weights
│
├── database/
│   └── attendance.db
│
├── .gitignore
└── README.md



Step 1: Start with CV (Face Detection + Recognition)

Goal: Detect multiple faces and recognize students.

Output: A working Python script that prints student names or marks attendance in CSV.

Why first: Your whole system depends on this working correctly.

Step 2: Add Backend (Flask + MySQL)

Goal: Make your attendance system “server-ready.”

Process:

Create Flask API endpoints:

POST /attendance → Save attendance

GET /attendance → View attendance

Connect your Python CV script to the backend: Instead of writing CSV, send POST requests.

Save data in MySQL instead of CSV.

Why second: Once CV works, it’s easy to “plug in” backend.

Step 3: Frontend Dashboard

Goal: Show attendance in a web dashboard.

Start simple: HTML + JS to fetch from Flask API.

Later: Upgrade to React for better UI/UX.

Why last: You need API endpoints ready to fetch data.

⚡ Pro Tips

Do NOT work frontend and backend at the same time at first.
Build backend API first; frontend is just a consumer of your API.

Test CV independently before sending data to backend.
CV → Backend → Database → Frontend is your workflow.

Use CSV as a temporary “bridge”: While backend is not ready, mark attendance in CSV to test recognition.

Add Frontend incrementally:
Start with a simple table in HTML → Later style in React.




Dependencies
pip install cmake
pip install dlib
pip install face_recognition
pip install opencv_python
pip install numpy
pip install mediapipe 


