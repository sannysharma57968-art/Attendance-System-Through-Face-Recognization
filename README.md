# AI-Powered Smart Attendance System

## Setup Instructions

1.  **Install Dependencies:**
    ```bash
    pip install "dlib-19.22.99-cp310-cp310-win_amd64.whl"
    pip install -r attendance_system/requirements.txt
    ```

2.  **Run the Application:**
    Navigate to the project root and run:
    ```bash
    cd attendance_system
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *Note: We run from `attendance_system` directory so that relative paths work correctly.*

3.  **Access the Dashboard:**
    Open your browser and go to: `http://localhost:8000`

4.  **Admin Panel:**
    Go to `http://localhost:8000/admin.html` to register students and download reports.

## Project Structure
- `backend/`: Python source code (FastAPI, OpenCV logic).
- `frontend/`: HTML/CSS/JS files.
- `data/`: Stores face encodings, images, and the SQLite database.
- `PROJECT_REPORT.md`: Detailed documentation for academic submission.
