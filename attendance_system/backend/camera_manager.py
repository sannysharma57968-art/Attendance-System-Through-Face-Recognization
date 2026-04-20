import cv2
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraManager:
    """
    Advanced Camera Manager for efficient frame capturing.
    - Runs frame capture in a separate thread (non-blocking).
    - Auto-reconnects if camera is lost.
    - Thread-safe frame access.
    """
    def __init__(self, source=0):
        self.source = source
        # On Windows, CAP_DSHOW is often more stable and faster than MSMF
        import platform
        if platform.system() == "Windows":
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.source)
        
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        
        if not self.cap.isOpened():
            logger.error(f"Cannot open camera {self.source}. Trying default backend...")
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.source} with any backend.")
            else:
                logger.info(f"Camera {self.source} opened with default backend.")
        else:
            logger.info(f"Camera {self.source} initialized with DSHOW (Windows).")

    def start(self):
        """Starts the background thread for frame capturing."""
        if self.running:
            return 
        
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logger.info("Camera capture thread started.")

    def _update(self):
        """Background loop to read frames from camera."""
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                else:
                    logger.warning("Frame read failed. Reconnecting...")
                    self.cap.release()
                    time.sleep(0.5)
                    import platform
                    if platform.system() == "Windows":
                        self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
                    else:
                        self.cap = cv2.VideoCapture(self.source)
            else:
                logger.warning("Camera not open. Retrying...")
                time.sleep(1.0)
                self.cap = cv2.VideoCapture(self.source)
        
        self.cap.release()

    def get_frame(self):
        """Returns the latest frame in a thread-safe manner."""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        """Stops the camera thread and releases resources."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.cap.release()
        logger.info("Camera stopped.")
