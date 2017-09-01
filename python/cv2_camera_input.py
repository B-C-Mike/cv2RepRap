##############################################
##                                          ##
##  REMEMBER:                               ##
##  OpenCV color(B,G,R)                     ##
##  OpenCV resize(image, (width, height))   #
##  python numpy.zeros( (height, width)   <=- !!!!1
##                                          #
##############################################

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import math
import numpy
import time
import cv2
import sys
import threading
# import re
#from multiprocessing import Process, Pipe

def nothing(self):
    pass

def s_speed(ms):
    camera.shutter_speed=(ms*1000)
    pass

# cv2.inRange


in_width = 864
in_height = 640

out_width = 360 # 2 * working_space (180mm)
out_height = 360
out_left = 340
out_right = 164
out_top = 140
out_bottom = 140
# scale X = out_width / (in_width - left - right)
# scale Y =    height / (in_height - top - bottom)

transparent = tuple((10,10,10))

img = np.zeros((out_height, out_width, 3), np.uint8)
img[:] = transparent

running = False
out_id = 0
out = [img, img, img]
over_id = 0
over = tuple((img, img, img))

counter = 0


def blend_transparent_overlay(bg, overlay, transparent_color, transparency=0):
  # if tranparency is array, get average

  # convert mask to grayscale
  grayscale = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
  # find pixels matching (allow white and black overlay)
  background_mask = cv2.compare(grayscale, transparent_color, cv2.CMP_EQ)
  # convert mas values to 0/1
  background_mask = np.clip(background_mask, 0, 1)
  # inverse - create bg mask
  overlay_mask = 1 - background_mask
  
  # turn masks to color and use them as weights
  overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
  background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

  # mix bg with overlay - create transparent overlay
  overlay = cv2.addWeighted(bg, transparency/255.0, overlay, 1-transparency/255.0, 0)
  
  # cut bg and overlay by mask 
  # return sum of both masked images
  return (bg * background_mask + overlay*overlay_mask)



class camThread(threading.Thread):
  def __init__(self):
    #self.interval = interval
    thread = threading.Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global running
    global out_id
    global out
    global over_id
    global over
    global counter
    global in_width
    global in_height
    global out_width
    global out_height
    global out_left
    global out_right
    global out_top
    global out_bottom
    global transparent

    #global camera
    #global rawCapture

    camera = PiCamera()
    camera.resolution = (in_width, in_height) # (2592x1944)/3
    camera.framerate = 20
    camera.hflip=True
    camera.vflip=True
    rawCapture = PiRGBArray(camera, size=(in_width, in_height))
    time.sleep(0.2)
    image = np.zeros((in_height, in_width, 3), np.uint8)

    
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    #while True:
      cv2.imshow("Frame", image) # show last frame
      cv2.waitKey(1) # and display it
      
      image = frame.array #get new image from camera
      rawCapture.truncate(0) #and clear buffer for next frame
      #print("raw image "+str(image.shape[1])+" x "+str(image.shape[0]))


      out_next = out_id+1 # switch index 
      if out_next>=3:     # (analying thread get last frame from
        out_next = 0      #       modlue.out[module.out_id]    )

      image_crop = image[out_top:(in_height-out_bottom),out_left:(in_width-out_right)]
      out[out_next] = cv2.resize(image_crop, (out_width, out_height)) # crop, resize and upload
#print(" "+str(.shape[1])+" x "+str(.shape[0]))
      out_id = out_next # indicate the most actual image

      over_small = cv2.resize(over[over_id], (in_width-out_left-out_right, in_height-out_top-out_bottom)) #
      # get the most actual overlay image and resize to expected size
      
      over_full = np.zeros((in_height, in_width, 3), np.uint8) # create full size transparent image
      over_full[:] = transparent
      over_full[out_top:(in_height-out_bottom), out_left:(in_width-out_right)] = over_small # and paste resized overlay on top
      image = blend_transparent_overlay(image, over_full, transparent[1], 70)
      #cv2.imshow("small", over_small)
      #cv2.imshow("full", over_full)
      
      counter += 1
      print (counter)
      if not running:
        cv2.destroyAllWindows()
        #camera.close()
        break

    


def start():
  global running
  if not running:
    running = True
    example = camThread()

def stop():
  global running
  running = False
  time.sleep(0.5) # delay for last (pending) iteration


#####>
#
#  TEST code below. Please remove it
#
#####>

ti_me = 14
print ("starting")
start()
#time.sleep(ti_me)
"""time.sleep(1)
local_im = out[out_id]
#cv2.imshow("test", local_im)
#cv2.waitKey(1)
time.sleep(2)
cv2.line(over[1], (0,0), (0,360), (70,120,240), 10)
time.sleep(1)
cv2.line(over[1], (0,360), (360,360), (70,120,240), 10)
time.sleep(1)
cv2.line(over[1], (360,360), (360,0), (70,120,240), 10)
time.sleep(1)
cv2.line(over[1], (360,0), (0,0), (250,128,70), 10)
over_id=1
time.sleep(10)
#cv2.waitKey(0)"""

for i in range(0, 200):
  gray = cv2.cvtColor(out[out_id], cv2.COLOR_BGR2GRAY)
  ret, gray = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
  color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
  over[0][:] = color
  #print("ID: "+str(out_id))
  #local_im = out[out_id]
  #cv2.imshow("test", local_im)
  time.sleep(0.050)

print ("stopping")
stop()
print ("finish")
time.sleep(1)
#print("FPS: " + str(counter/float(ti_me)) )



# camera settings
input_mode = 5
rotate_180 = True
iso = 200
exposure_ms = 20
framerate = 5


# """ # < uncomment
  """   < comment all below

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (camx, camy)
camera.sensor_mode = 5
camera.hflip=True
camera.vflip=True
camera.iso=200
camera.shutter_speed=20*1000 #us
camera.framerate = 4
rawCapture = PiRGBArray(camera, size=(camx, camy))



