import uvicorn
import os
import sys

if __name__ == "__main__":
    # Get the absolute path to the 'attendance_system' directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(current_dir, "attendance_system")

    # Load .env from project root or attendance_system (for ADMIN_USERNAME, ADMIN_PASSWORD)
    try:
        from dotenv import load_dotenv
        load_dotenv(current_dir)
        load_dotenv(app_dir)
    except ImportError:
        pass  # optional: pip install python-dotenv
    
    # Change working directory to 'attendance_system' so 'backend' module is found
    os.chdir(app_dir)
    
    # Add to path just in case
    sys.path.insert(0, app_dir)
    
    print(f"Starting server from: {app_dir}")
    
    # Run Uvicorn
    # We use "backend.main:app" because inside 'attendance_system', 'backend' is a package
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
