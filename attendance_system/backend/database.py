import sqlite3
from datetime import datetime, date
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Handles SQLite database operations for attendance.
    """
    def __init__(self, db_path="data/attendance.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Returns a new database connection."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        """Initializes the database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create Attendance Table
        # We enforce UNIQUE(student_name, date) to prevent duplicate attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                UNIQUE(student_name, date)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")

    def mark_attendance(self, name):
        """
        Marks attendance for a student.
        Returns: (success, message)
        """
        today_date = date.today().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M:%S")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if already marked for today
            # Note: The UNIQUE constraint would also catch this, but explicit check allows custom message
            cursor.execute("SELECT * FROM attendance WHERE student_name = ? AND date = ?", (name, today_date))
            if cursor.fetchone():
                return False, f"Attendance already marked for {name} today."
            
            cursor.execute("INSERT INTO attendance (student_name, date, time) VALUES (?, ?, ?)", 
                           (name, today_date, now_time))
            conn.commit()
            logger.info(f"Marked attendance for {name} at {now_time}")
            return True, f"Attendance marked for {name} at {now_time}"
        except sqlite3.IntegrityError:
             return False, f"Attendance already marked for {name} today."
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False, str(e)
        finally:
            conn.close()

    def get_daily_attendance(self, day_date=None):
        """Get attendance for a specific date (default: today)."""
        if day_date is None:
            day_date = date.today().strftime("%Y-%m-%d")
            
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_name, time, date FROM attendance WHERE date = ? ORDER BY time DESC", (day_date,))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts for API
        result = [{"name": r[0], "time": r[1], "date": r[2]} for r in rows]
        return result

    def get_all_attendance(self):
        """Get all attendance records."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_name, time, date FROM attendance ORDER BY date DESC, time DESC")
        rows = cursor.fetchall()
        conn.close()
        
        result = [{"name": r[0], "time": r[1], "date": r[2]} for r in rows]
        return result
