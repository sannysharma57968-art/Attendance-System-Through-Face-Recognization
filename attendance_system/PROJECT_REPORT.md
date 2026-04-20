# AI-Powered Smart Attendance System using Face Recognition

## 1. Abstract
This project implements a robust, real-time smart attendance system using computer vision and machine learning. Unlike traditional manual attendance methods, which are time-consuming and prone to errors, this system automates the process by recognizing faces via a camera feed. It utilizes modern web technologies (FastAPI, Vanilla JS) and efficient computer vision libraries (OpenCV, face_recognition) to deliver a seamless experience suitable for educational institutions and corporate environments.

## 2. Problem Statement
Manual attendance marking is inefficient, subject to proxy attendance, and difficult to analyze over time. Existing biometric systems (fingerprint) require physical contact, which is unhygienic and slower. There is a need for a contactless, fast, and accurate system that can operate on standard hardware without expensive GPUs.

## 3. Objectives
- To develop a real-time face recognition system for attendance.
- To eliminate proxy attendance through unique face encoding.
- To provide a user-friendly dashboard for monitoring and administration.
- To ensure the system runs efficiently on low-end CPUs (i3/i5).
- To enable data persistence and easy export of attendance records.

## 4. System Architecture & Components
The system follows a modular architecture, consisting of the following key components:

### 4.1 Backend Components (Python/FastAPI)
- **`main.py`**: The central entry point. Orchestrates the API endpoints, video streaming logic, and integrates all managers.
- **`face_engine.py`**: Encapsulates face detection and recognition logic. Handles encoding storage (pickle) and registration of new faces.
- **`camera_manager.py`**: Manages the webcam feed in a dedicated thread to ensure non-blocking performance and auto-reconnection.
- **`attendance.py`**: Business logic layer that connects the face engine results with the database.
- **`database.py`**: Manages SQLite transactions, including marking attendance and retrieving history.
- **`auth.py`**: Implements JWT-based security for the Admin Panel.

### 4.2 Frontend Components (Vanilla JS/CSS/HTML)
- **`index.html`**: The public-facing dashboard showing the live camera feed and today's attendance summary.
- **`admin.html`**: The secure administration portal for student registration, record management, and analytics.
- **`app.js`**: Contains all frontend logic, including API communication, real-time table updates, and chart rendering.
- **`style.css`**: Professional UI styling with support for responsive layouts and Dark Mode.

## 5. System Work Flow (Fork Flow)
The operation of the system follows a clear sequential flow:

1.  **Initialization**: 
    - Server starts (`run.py`), initializes the database, and loads existing face encodings.
    - Camera thread starts capturing frames in the background.
2.  **Face Detection & Recognition**:
    - The `generate_frames` loop retrieves the latest frame.
    - Every 5th frame is processed (resized to 25%) to detect faces.
    - Detected faces are compared against stored encodings using Euclidean distance.
3.  **Stability Verification**:
    - A "Stability Counter" tracks how many consecutive frames a specific face is seen.
    - If a face is verified for 3 consecutive checks, it proceeds to attendance marking.
4.  **Attendance Logging**:
    - The `AttendanceManager` checks if the student has already marked attendance for the current date.
    - If not, a new record is inserted into the SQLite database with a timestamp.
5.  **Real-Time Updates**:
    - The frontend dashboard polls the `/attendance` API every 2 seconds.
    - The UI updates dynamically to show the newly recognized student without a page refresh.

## 6. Algorithms & Logic
1.  **Face Detection**: Uses HOG + Linear SVM to find face locations.
2.  **Face Encoding**: Converts face features into a 128-dimensional vector.
3.  **Face Matching**: Calculates Euclidean distance between live face encoding and stored encodings. A match is declared if distance < 0.5 (tolerance).
4.  **Anti-Flicker / Stability Check**: To prevent false positives, the system implements a "Consecutive Frame Validation" logic. A face must be recognized consistently for 3 consecutive checks (approx. 1-2 seconds) before attendance is marked.
5.  **Optimization**: Processing is done on every 5th frame to maintain high FPS. Frames are downscaled to 25% resolution for detection speedup.

## 6. Advantages
- **Contactless**: Hygienic and fast.
- **Cost-Effective**: Runs on standard laptops/webcams; no GPU needed.
- **Anti-Duplicate**: Enforces "One Attendance Per Day" rule at the database level.
- **Robust**: Handles camera disconnections and unknown faces gracefully.
- **User-Friendly**: Professional Admin interface with Charts and Analytics.

## 7. Limitations
- Extreme lighting conditions (very dark or very bright) may affect accuracy.
- Face angles greater than 45 degrees might not be detected.
- Heavy reliance on CPU means performance may drop if too many faces (20+) are in the frame simultaneously on a low-end machine.

## 8. Future Scope
- **Liveness Detection**: Implement blink detection to prevent photo spoofing.
- **Cloud Integration**: Sync data with a central cloud server.
- **Mobile App**: Develop a companion app for students to view their attendance.
- **Notification System**: Email/SMS alerts for absence.

## 9. Viva Q&A (Preparation)
**Q: Why use FastAPI instead of Flask?**
A: FastAPI is built on Starlette and Pydantic, offering asynchronous support (ASGI) which is crucial for handling video streams without blocking the server. It is also significantly faster in execution.

**Q: How do you handle multiple faces?**
A: The `face_recognition` library returns a list of all face locations and encodings. We iterate through each detected face and compare it against our known database.

**Q: What is the underlying model?**
A: It uses dlib's pre-trained ResNet model, which achieves 99.38% accuracy on the Labeled Faces in the Wild (LFW) benchmark.

**Q: How is it optimized for CPU?**
A: We resize the video frame to 1/4th of its original size before processing. Since face recognition complexity increases with pixel count, this provides a 4x-16x speedup. We also process only every 5th frame.
