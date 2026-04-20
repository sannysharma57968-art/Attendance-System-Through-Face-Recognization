from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import cv2
import uvicorn
import os
import time
import logging

from .camera_manager import CameraManager
from .face_engine import FaceEngine
from .attendance import AttendanceManager
from .utils import draw_overlays
from .auth import (
    ADMIN_USERNAME,
    verify_password,
    create_access_token,
    get_current_user,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Attendance System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Managers
# Note: Camera source 0 is default webcam.
camera = CameraManager(source=0) 
face_engine = FaceEngine()
attendance_manager = AttendanceManager()

# Global state for last processed faces
last_face_locations = []
last_face_names = []
frame_count = 0

# Anti-flicker / Liveness state
# Dictionary to track how many consecutive frames a face has been seen: {name: count}
face_stability_counter = {}
STABILITY_THRESHOLD = 3 # Number of consecutive checks (approx 1-2 seconds) required to mark attendance

@app.on_event("startup")
async def startup_event():
    camera.start()

@app.on_event("shutdown")
async def shutdown_event():
    camera.stop()

def generate_frames():
    global frame_count, last_face_locations, last_face_names, face_stability_counter
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
                
            # Optimization: Process faces every 5 frames (adjust based on CPU)
            if frame_count % 5 == 0:
                current_locations, current_names = face_engine.process_frame(frame)
                
                # --- STABILITY LOGIC START ---
                current_detected_names = set(current_names)
                
                # Increment counter for detected faces
                for name in current_names:
                    if name == "Unknown":
                        continue
                    face_stability_counter[name] = face_stability_counter.get(name, 0) + 1
                
                # Reset counter for faces NOT detected in this frame
                # (Use a copy of keys to avoid runtime error during modification)
                for name in list(face_stability_counter.keys()):
                    if name not in current_detected_names:
                        face_stability_counter[name] = 0
                
                # Mark attendance only if threshold reached
                final_names_to_display = []
                for name in current_names:
                    if name == "Unknown":
                        final_names_to_display.append(name)
                        continue
                    
                    if face_stability_counter.get(name, 0) >= STABILITY_THRESHOLD:
                        # Mark attendance
                        attendance_manager.process_recognition(name)
                        # Add a visual indicator (e.g. asterisk or text) handled in utils, 
                        # or just rely on the name. For now, we just pass the name.
                        final_names_to_display.append(f"{name} (Marked)")
                    else:
                        # Still verifying
                        final_names_to_display.append(f"{name} (Verifying...)")
                
                last_face_locations = current_locations
                last_face_names = final_names_to_display
                # --- STABILITY LOGIC END ---
            
            frame_count += 1
            
            # Draw results on the frame
            frame = draw_overlays(frame, last_face_locations, last_face_names)
            
            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except Exception as e:
        logger.error(f"Video feed generator error: {e}")
    finally:
        logger.info("Video feed generator stopped.")

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


# --- Auth (Login) ---
class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(data: LoginRequest):
    """Authenticate admin and return JWT."""
    if data.username != ADMIN_USERNAME or not verify_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(data.username)
    return {"access_token": token, "token_type": "bearer", "username": data.username}


@app.get("/auth/check")
async def auth_check(username: str = Depends(get_current_user)):
    """Verify token and return current user. Used by frontend to check if logged in."""
    return {"authenticated": True, "username": username}


# API Endpoints (public: today's attendance only)
# Admin-only endpoints below use Depends(get_current_user)

@app.post("/register")
async def register_student(
    name: str = Form(...),
    file: UploadFile = File(...),
    _: str = Depends(get_current_user),
):
    # Save temp file
    # Ensure directory exists
    os.makedirs("data/students", exist_ok=True)
    temp_path = f"data/students/{file.filename}"
    
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
        
    success, msg = face_engine.register_student(name, temp_path)
    
    if success:
        return JSONResponse(content={"status": "success", "message": msg})
    else:
        return JSONResponse(content={"status": "error", "message": msg}, status_code=400)

@app.get("/attendance")
async def get_attendance(date: Optional[str] = Query(None, description="Date YYYY-MM-DD")):
    if date:
        return attendance_manager.get_records_for_date(date)
    return attendance_manager.get_today_records()

@app.get("/attendance/all")
async def get_all_attendance(username: str = Depends(get_current_user)):
    return attendance_manager.get_all_records()

@app.get("/export")
async def export_attendance(username: str = Depends(get_current_user)):
    path = attendance_manager.export_to_excel()
    if path and os.path.exists(path):
        return FileResponse(path, filename="attendance_report.xlsx", media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    raise HTTPException(status_code=500, detail="Export failed")

@app.get("/students")
async def list_students(username: str = Depends(get_current_user)):
    """List all registered student names."""
    return {"students": face_engine.get_registered_names()}

@app.delete("/students/{name}")
async def delete_student(name: str, username: str = Depends(get_current_user)):
    """Remove a student from face database."""
    success, msg = face_engine.remove_student(name)
    if success:
        return JSONResponse(content={"status": "success", "message": msg})
    return JSONResponse(content={"status": "error", "message": msg}, status_code=400)

# Serve Frontend
# We mount the frontend directory to root.
# Note: Ensure frontend/index.html exists.
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
