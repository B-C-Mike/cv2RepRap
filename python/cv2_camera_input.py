##############################################
##                                          ##
##  REMEMBER:                               ##
##  OpenCV color(B,G,R)                     ##
##  OpenCV resize(image, (width, height))   #
##  python numpy.zeros( (height, width)   <=- !!!!1
##                                          #
##############################################

import numpy as np
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
from threading import Thread, Event
#from multiprocessing import Process, Pipe


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

cam_img = np.zeros((in_height, in_width, 3), np.uint8)
cam_img[:] = transparent
detector_img = np.zeros((out_height, out_width, 3), np.uint8)
detector_img[:] = transparent

running = False
cam_out_id = 0 # full out from camera
cam_out = [cam_img,cam_img,cam_img]
out_id = 0 # scaled input for detector
out = [detector_img,detector_img,detector_img]
over_id = 0 # small overlay from detector
over = [detector_img,detector_img,detector_img]
disp_overlay_id = 0 # full overlay for display
disp_overlay = [cam_img,cam_img,cam_img]
disp_out_id = 0 # content shoved on display
disp_out = [cam_img,cam_img,cam_img]

counter = 0
cam_counter = 0
scaler_counter = 0
detector_counter = 0
mixer_counter = 0
display_counter = 0




def blend_transparent_overlay(bg, overlay, transparent_color, transparency=0):
  # if tranparency is array, get average

  # convert mask to grayscale
  grayscale = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
  # find pixels matching (allow white and black overlay)
  background_mask = cv2.compare(grayscale, transparent_color, cv2.CMP_EQ)
  # inverse - create bg mask
  overlay_mask = cv2.bitwise_not(background_mask)
  if transparency:
    # mix bg with overlay - create transparent overlay
    transparency = transparency/250.0
    overlay = cv2.addWeighted(bg, transparency, overlay, 1-transparency, 0)
  # cut bg and overlay by mask 
  bg = cv2.bitwise_and(bg, bg, mask=background_mask)
  overlay = cv2.bitwise_and(overlay,overlay, mask=overlay_mask)
  # return sum of both masked images
  return (cv2.bitwise_or(bg, overlay))



    
class camThreadInput(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global cam_out_id
    global cam_out
    global cam_counter

    camera = PiCamera()
    camera.resolution = (in_width, in_height) # (2592x1944)/3
    camera.framerate = 20
    camera.hflip=True
    camera.vflip=True
    rawCapture = PiRGBArray(camera, size=(in_width, in_height))
    time.sleep(0.2)

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
      image = frame.array #get new image from camera
      rawCapture.truncate(0) #and clear buffer for next frame

      out_next = cam_out_id+1 # switch index 
      if out_next>=3:     # (analying thread get last frame from
        out_next = 0      #       modlue.out[module.out_id]    )

      cam_out[out_next] = image
      cam_out_id = out_next # indicate the most actual image
      
      cam_counter += 1
      #print (cam_counter, "cam")
      if not running:
        break

    
class camThreadScaler(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global out_id
    global out
    global disp_overlay_id
    global disp_overlay
    global scaler_counter

    while running:
      #cv2.imshow("Frame", image) # show last frame
      #cv2.waitKey(1) # and display it
      
      out_next = out_id+1 # switch index 
      if out_next>=3:     # (analying thread get last frame from
        out_next = 0      #       modlue.out[module.out_id]    )
        
      image = cam_out[cam_out_id] #get new image from camera buffer
      image_crop = image[out_top:(in_height-out_bottom),out_left:(in_width-out_right)]
      out[out_next] = cv2.resize(image_crop, (out_width, out_height)) # crop, resize and upload # , interpolation=cv2.INTER_NEAREST)
      out_id = out_next # indicate the most actual image

      over_small = cv2.resize(over[over_id], (in_width-out_left-out_right, in_height-out_top-out_bottom)) # , interpolation=cv2.INTER_NEAREST)
      # get the most actual overlay image and resize to expected size
      
      over_full = np.zeros((in_height, in_width, 3), np.uint8) # create full size image with "transparent" bg
      over_full[:] = transparent
      over_full[out_top:(in_height-out_bottom), out_left:(in_width-out_right)] = over_small # and paste resized overlay on top

      disp_overlay[out_next] = over_full
      disp_overlay_id = out_next
      
      scaler_counter += 1
      time.sleep(0.05)
      #print (scaler_counter, "scaler")
      if not running:
        break

    
class camThreadMix(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global mixer_counter
    global disp_out_id
    global disp_out

    while running:
      bg = cam_out[cam_out_id]
      overlay = disp_overlay[disp_overlay_id]
      image = blend_transparent_overlay(bg, overlay, transparent[1], 0)
      
      disp_out[0] = image
      
      mixer_counter += 1
      #print (mixer_counter, "disp")
      if not running:
        break

    
class camThreadDisplay(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global display_counter

    while running:
      #bg = cam_out[cam_out_id]
      #overlay = disp_overlay[disp_overlay_id]
      image = disp_out[disp_out_id]
      #image = blend_transparent_overlay(bg, overlay, transparent[1], 90)
      
      cv2.imshow("Frame", image) # show last frame
      cv2.waitKey(100) # and display it
      

#print(" "+str(.shape[1])+" x "+str(.shape[0]))
      
      display_counter += 1
      #print (display_counter, "disp")
      if not running:
        cv2.destroyAllWindows()
        break

    


def start():
  global running
  if not running:
    running = True
    cam_input = camThreadInput()
    cam_scaler = camThreadScaler()
    cam_mixer = camThreadMix()
    cam_display = camThreadDisplay()

def stop():
  global running
  running = False
  time.sleep(0.5) # delay for last (pending) iteration


ti_me = 10
print ("starting")
start()
time.sleep(2)

detector_counter = 0
cam_counter = 0
scaler_counter = 0
mixer_counter = 0
display_counter = 0

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

t_end = time.time()+ti_me
while time.time()<t_end:
#for i in range(0, 200):
  gray = cv2.cvtColor(out[out_id], cv2.COLOR_BGR2GRAY)
  ret, gray = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
  color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
  over[0][:] = color
  #print("ID: "+str(out_id))
  #local_im = out[out_id]
  #cv2.imshow("test", local_im)
  time.sleep(.10)
  detector_counter += 1
  
#"""

print ("stopping")
stop()
print ("finish")
time.sleep(1)
print("detector FPS: " + str(detector_counter/float(ti_me)) )
print("camera FPS: " + str(cam_counter/float(ti_me)) )
print("scaler FPS: " + str(scaler_counter/float(ti_me)) )
print("mixer FPS: " + str(mixer_counter/float(ti_me)) )
print("display FPS: " + str(display_counter/float(ti_me)) )

import os
print(os.popen("vcgencmd measure_temp").readline())
import sys
print (sys.version_info)





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

"""

