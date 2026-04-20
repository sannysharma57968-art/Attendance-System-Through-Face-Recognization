import face_recognition
import cv2
import pickle
import os
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceEngine:
    """
    Handles face detection, recognition, and encoding storage.
    Optimized for CPU by processing downscaled frames.
    """
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.encodings_file = os.path.join(data_path, "encodings.pkl")
        self.students_dir = os.path.join(data_path, "students")
        
        # Ensure directories exist
        os.makedirs(self.students_dir, exist_ok=True)
        
        self.known_encodings = []
        self.known_names = []
        self.load_encodings()

    def load_encodings(self):
        """Loads face encodings from pickle file."""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                self.known_encodings = data.get("encodings", [])
                self.known_names = data.get("names", [])
                logger.info(f"Loaded {len(self.known_names)} face encodings.")
            except Exception as e:
                logger.error(f"Error loading encodings: {e}")
                self.known_encodings = []
                self.known_names = []
        else:
            logger.info("No encodings found. Starting fresh.")
            self.known_encodings = []
            self.known_names = []

    def save_encodings(self):
        """Saves current encodings to disk."""
        data = {"encodings": self.known_encodings, "names": self.known_names}
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info("Encodings saved successfully.")
        except Exception as e:
            logger.error(f"Error saving encodings: {e}")

    def register_student(self, name, image_path):
        """
        Registers a new student by processing their image.
        Returns (success, message).
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Detect face
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                # Take the first face found
                encoding = encodings[0]
                
                # Check if already exists (optional, but good for duplicates)
                # For now, just append
                self.known_encodings.append(encoding)
                self.known_names.append(name)
                self.save_encodings()
                return True, f"Student {name} registered successfully."
            else:
                return False, "No face detected in the provided image."
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, str(e)

    def get_registered_names(self):
        """Returns list of registered student names."""
        return list(self.known_names)

    def remove_student(self, name):
        """
        Removes a student by name from known encodings/names.
        Returns (success, message).
        """
        try:
            if name not in self.known_names:
                return False, f"Student '{name}' not found."
            idx = self.known_names.index(name)
            self.known_names.pop(idx)
            self.known_encodings.pop(idx)
            self.save_encodings()
            logger.info(f"Removed student: {name}")
            return True, f"Student '{name}' removed successfully."
        except Exception as e:
            logger.error(f"Error removing student: {e}")
            return False, str(e)

    def process_frame(self, frame):
        """
        Detects and recognizes faces in a frame.
        Returns: (face_locations, face_names)
        """
        # Resize frame of video to 1/4 size for faster face recognition processing
        # This is CRITICAL for CPU performance
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_names[best_match_index]

            face_names.append(name)
            
        # Scale locations back up since the frame we detected in was scaled to 1/4 size
        scaled_locations = []
        for (top, right, bottom, left) in face_locations:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            scaled_locations.append((top, right, bottom, left))
            
        return scaled_locations, face_names
