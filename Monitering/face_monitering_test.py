"""
For monitoring face presence in given frame we use haar cascades from OpenCV library.
Haar cascades uses ML for training models, useful for detecting objects in video or image.
"""
import cv2
from datetime import datetime


def start_face_monitoring():
    # Load face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Open camera
    camera = cv2.VideoCapture(0)
    previous_state = None

    while True:
        success, frame = camera.read()
        if not success:
            print("Failed to capture frame from camera. Exiting...")
            break

        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) > 0:
            current_state = "face_detected"
        else:
            current_state = "face_absent"

        # Log only when state changes
        if current_state != previous_state:
            timestamp = datetime.now()
            print(timestamp, current_state)

        previous_state = current_state

        # Draw rectangle around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the frame
        cv2.imshow("Face Monitoring", frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_face_monitoring()
