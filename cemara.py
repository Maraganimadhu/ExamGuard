# # openCV it's is open souce computer vision libary 
# # working on cemara video, facedidection,objectdection,imageprocessing

# # opencv doen't take a photo it's self jest it's connect to defalut web cam
# # open recivess continues video frame and we should choose one frame to save as a image

# "modes of working when events handles on s for save q for quite "
import os
import cv2
import datetime
import numpy as np

UPLOAD_FOLDER="static/uploads"

# def capture_photo():
#     os.makedirs("static/uploads",exist_ok=True)
#     cemara= cv2.VideoCapture(0) #open cemara
#     #video capture is a method to enble your defalute camera here 0 defiles 
#     # defalute cemara 1 for defines the other cemara/mutiple if your plugin
#     while(True):
#         success,frame =cemara.read() #here tells the webcam is connected or not and also 

#         if not success: #if cemara was not open 
#             cemara.release()   #to stop the cemara  
#             cv2.destroyAllWindows() # to destroy all the windows related to opencv
#             return None # to exit the loop
#         cv2.imshow("capture photo",frame) # here "capture photo" is the window name and frame is the image to be displayed
#         key=cv2.waitKey(1)   #candidate keyevents 
#         if key==ord('s'):
#             filename=f"candidate{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"     #naming covention
#             photo_path=os.path.join("static/uploads",filename)  #here we are adding capature file with existing filename
#             cv2.imwrite(photo_path,frame) #saved a photo in existing file
#             print("photo was captured")
#             cemara.release()
#             cv2.destroyAllWindows() 
#             return photo_path
#         elif key==ord("q"):
#             cemara.relese()
#             cv2.destroyAllWindows() 
#             return None


# path=capture_photo()
# if path:
#     print(f" photo save location{path}")
# else:
#     print("photo not captured")
        
def capture_photo(image_data):
    os.makedirs(UPLOAD_FOLDER,exist_ok=True)
    image_arry=np.frombuffer(image_data,np.uint8)   #covert image bites into array
    img=cv2.imdecode(image_arry,cv2.IMREAD_COLOR)   #covert array into image frame
    if img is None:
        return None
    filename=(f"candidate{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
    photo_path=os.path.join("static/uploads",filename)
    cv2.imwrite(photo_path,img) #here we are adding capature file with existing filename
    return photo_path     #saved a photo in existing file
    
   
