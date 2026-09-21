"""for monitering face precence in given frame we using harrcas open souce computer vision libary 
harrcas using ML for training models
here we use ml method is called haar cascades
this method id useful for detecting the object in the video or image """
# haar cascades detector is a simple rectangler patterns called haar features
# image >simple check>more detaied check >classfir >objected detectord 
# haar cascade looks for lighter and darker region for detectiing the face
# it trained to easy to reconize object easy to detect face
import cv2
from datetime import datetime


def start_face_monitoring():
    #Load face detector 
    face_cascade=cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    #open camera
    camera=cv2.VideoCapture(0)
    previous_state = None

    while True:
        success, frame=camera.read()
        if not success:
            print("Failed to capture frame from camera. Exiting...")
            break

        #convert frame to grayscale
        gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #detect faces
        faces=face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces)>0:
            current_state="face_detected"
        else:
            current_state="face_absent"


        #log only whwn state change
        if current_state!=previous_state:
            timestamp=datetime.now()
            print(timestamp,current_state)

        previous_state=current_state

        #draw rectangle around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        #display the frame
        cv2.imshow("Face Monitoring", frame)

        #press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()


if __name__ == "main":
    start_face_monitoring() 
    #this is function call for start_face_monitering() this function is run for monitering the face detection
    # this program is run for monitering the face precence in the webcam
    # and detect the face and draw a rectangle around the face
    # and display the resulting frame