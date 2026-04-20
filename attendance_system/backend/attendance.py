from .database import DatabaseManager
import pandas as pd
import os
from datetime import date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttendanceManager:
    """
    Business logic for attendance.
    Bridges Face Recognition and Database.
    """
    def __init__(self):
        self.db = DatabaseManager()
    
    def process_recognition(self, name):
        """
        Processes a recognized name.
        """
        if name == "Unknown":
            return {"status": "warning", "message": "Unknown Face Detected"}
        
        success, message = self.db.mark_attendance(name)
        if success:
            return {"status": "success", "message": message, "name": name}
        else:
            # Already marked
            return {"status": "info", "message": message, "name": name}
            
    def get_today_records(self):
        return self.db.get_daily_attendance()

    def get_records_for_date(self, day_date=None):
        """Get attendance for a specific date (YYYY-MM-DD). If None, returns today."""
        return self.db.get_daily_attendance(day_date)
    
    def get_all_records(self):
        return self.db.get_all_attendance()
        
    def export_to_excel(self, output_path="data/attendance_report.xlsx"):
        """
        Exports all attendance data to an Excel file.
        """
        try:
            records = self.db.get_all_attendance()
            if not records:
                return None
            
            df = pd.DataFrame(records)
            # Reorder columns if needed
            df = df[["date", "time", "name"]]
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            df.to_excel(output_path, index=False)
            logger.info(f"Exported attendance to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None
