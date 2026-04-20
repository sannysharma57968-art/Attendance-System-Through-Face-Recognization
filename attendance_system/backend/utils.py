import cv2

def draw_overlays(frame, face_locations, face_names):
    """
    Draws rectangles and names on the frame.
    """
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Choose color: Green for known, Red for Unknown
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        
        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        # Draw a label with a name below the face
        # Calculate text size to make background rectangle dynamic
        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = 0.8
        thickness = 1
        (text_width, text_height), baseline = cv2.getTextSize(name, font, font_scale, thickness)
        
        cv2.rectangle(frame, (left, bottom - text_height - 10), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), font, font_scale, (255, 255, 255), thickness)
        
    return frame
