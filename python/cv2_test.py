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
import time
from threading import Thread, Event
#from multiprocessing import Process, Pipe
from picamera.array import PiRGBArray
from picamera import PiCamera

import cv2_camera_input as camera
camera.camera = PiCamera()

ti_me = 200
print ("starting")
camera.camera.shutter_speed=45*1000
camera.start()
camera.camera.shutter_speed=35*1000
time.sleep(2)




camera.detector_counter = 0
camera.cam_counter = 0
camera.scaler_counter = 0
camera.mixer_counter = 0
camera.display_counter = 0

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

import os
t_end = time.time()+ti_me
while time.time()<t_end:
#for i in range(0, 200):
  gray = cv2.cvtColor(camera.getImage(), cv2.COLOR_BGR2GRAY)
  ret, gray = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
  color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
  camera.update(color)
  #print("ID: "+str(out_id))
  #local_im = out[out_id]
  #cv2.imshow("test", local_im)
  camera.detector_counter += 1
  print(os.popen("vcgencmd measure_temp").readline())
  if len(camera.keyboard):
    key = camera.keyboard.pop()
    if key==27:
      t_end -= ti_me
      ti_me = time.time()-t_end
      break
  while len(camera.mouse):
    mouse = camera.mouse.pop()
    print (mouse[0],"X",mouse[3 ])


print ("stopping")
camera.stop()
print ("finish")
time.sleep(1)
print("detector FPS: " + str(camera.detector_counter/float(ti_me)) )
print("camera FPS: " + str(camera.cam_counter/float(ti_me)) )
print("scaler FPS: " + str(camera.scaler_counter/float(ti_me)) )
print("scaler2 FPS: " + str(camera.scaler2_counter/float(ti_me)) )
print("mixer FPS: " + str(camera.mixer_counter/float(ti_me)) )
print("display FPS: " + str(camera.display_counter/float(ti_me)) )
print(os.popen("vcgencmd measure_temp").readline())


import sys
print (sys.version_info[0],sys.version_info[1],sys.version_info[2])
print('\033[8;20;100t')
#print("\e")

"""    Avaliable functions and paralell dependent tasks.

start() -> turn on all

stop() -> please terminate at nearest iteration

update(image) -> [ over, upScaler.wait() ]

[ over, upScaler.wait() ] -> upScalerThread -> [ disp_overlay, ?.set() ]

[ camera ] -> camThreadInput -> [ cam_out, downScaler.set() ]

[ cam_out, disp_overlay ] -> camThreadMix -> [ disp_out, imRredraw.set() ]

[ disp_out, imRredraw.set() ] -> camThreadDisplay -> [ cv2.imshow ]

[ cam_out, downScaler.wait() ] -> downScalerThread -> [ out, ?.set() ]


base = 12
in_width = base*16*4 # 832
in_height = base*16*3 # 624
overlay_transparency = 90

out_width = 360 # 2 * working_space (180mm)
out_height = 360
out_left = 250
out_right = 70
out_top = 62
out_bottom = 66
# scale X = out_width / (in_width - left - right)
# scale Y =    height / (in_height - top - bottom)
input_mode = 4
rotate_180 = True
iso = 200
exposure_ms = 30
framerate = 7

transparent = tuple((10,10,10))
cam_img = np.zeros((in_height, in_width, 3), np.uint8)
#cam_img[:] = transparent
detector_img = np.zeros((out_height, out_width, 3), np.uint8)
#detector_img[:] = transparent

running = False
cam_out = cam_img # full out from camera
out = detector_img # scaled input for detector
over = detector_img # small overlay from detector
disp_overlay = cam_img # full overlay for display
disp_out = cam_img # content shoved on display

downScaler = Event()
upScaler = Event()
outImg = Event()
imRredraw = Event()
mixer = Event()

counter = 0
cam_counter = 0
scaler_counter = 0
scaler2_counter = 0
detector_counter = 0
mixer_counter = 0
display_counter = 0

    
class camThreadInput(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global cam_out
    global cam_counter

    camera = PiCamera()
    camera.resolution = (in_width, in_height) # (2592x1944)/3
    camera.framerate = framerate
    camera.hflip=rotate_180
    camera.vflip=rotate_180
    camera.sensor_mode = input_mode
    camera.iso=iso
    camera.shutter_speed=exposure_ms*1000
    rawCapture = PiRGBArray(camera, size=(in_width, in_height))
    time.sleep(0.2)

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
      image = frame.array #get new image from camera
      rawCapture.truncate(0) #and clear buffer for next frame

      cam_out = image
      downScaler.set()
      mixer.set()
      
      cam_counter += 1
      #print (cam_counter, "cam")
      if not running:
        break

    
class downScalerThread(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global out_id
    global out
    global scaler_counter

    while running:
      #cv2.imshow("Frame", image) # show last frame
      #cv2.waitKey(1) # and display it
      downScaler.wait()
      downScaler.clear()
      
        
      image = cam_out #get new image from camera buffer
      image_crop = image[out_top:(in_height-out_bottom),out_left:(in_width-out_right)]
      out = cv2.resize(image_crop, (out_width, out_height)) # crop, resize and upload # , interpolation=cv2.INTER_NEAREST)
      outImg.set()


      #print (scaler_counter, "scaler")
      scaler_counter += 1
      if not running:
        break

    
class upScalerThread(Thread):
  def __init__(self):
    #self.interval = interval
    thread = Thread(target=self.run, args=())
    thread.daemon = True
    thread.start()

  def run(self):
    global disp_overlay
    global disp_overlay_id
    global scaler2_counter
    i=0

    while running:
      over_full = np.zeros((in_height, in_width, 3), np.uint8) # create full size image with "transparent" bg
      over_full[:] = transparent
      upScaler.wait()
      upScaler.clear()

      
      over_small = cv2.resize(over, (in_width-out_left-out_right, in_height-out_top-out_bottom)) # , interpolation=cv2.INTER_NEAREST)
      # get the most actual overlay image and resize to expected size

      over_full[out_top:(in_height-out_bottom), out_left:(in_width-out_right)] = over_small # and paste resized overlay on top
      disp_overlay = over_full
      mixer.set()

      scaler2_counter += 1
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
    global disp_out

    while running:
      mixer.wait()
      mixer.clear()
      bg = cam_out
      overlay = disp_overlay
      transparency=overlay_transparency

      # convert mask to grayscale
      grayscale = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
      # find pixels matching (allow white and black overlay)
      background_mask = cv2.compare(grayscale, transparent[1], cv2.CMP_EQ)
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
      disp_out = cv2.bitwise_or(bg, overlay)
      imRredraw.set()
      
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
      imRredraw.wait()
      imRredraw.clear()
      image = disp_out
      #image = blend_transparent_overlay(bg, overlay, transparent[1], 90)
      
      cv2.imshow("Frame", image) # show last frame
      cv2.moveWindow("Frame", 3, 5)
      cv2.waitKey(5) # and display it
      

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
    
    downScaler.clear()
    down_scaler = downScalerThread()
    
    upScaler.clear()
    up_scaler = upScalerThread()
    
    cam_mixer = camThreadMix()

    imRredraw.set()
    cam_display = camThreadDisplay()

def stop():
  global running
  running = False
  time.sleep(0.5) # delay for last (pending) iteration


def update(image):
  global over
  over = color
  upScaler.set()

def getImage(wait=True):
  if wait:
    outImg.wait()
  outImg.clear()
  return(out)


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
time.sleep(1)
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
#cv2.waitKey(0)

import os

t_end = time.time()+ti_me
while time.time()<t_end:
#for i in range(0, 200):
  gray = cv2.cvtColor(getImage(), cv2.COLOR_BGR2GRAY)
  ret, gray = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
  color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
  update(color)

  #print("ID: "+str(out_id))
  #local_im = out[out_id]
  #cv2.imshow("test", local_im)
  detector_counter += 1
  #print(os.popen("vcgencmd measure_temp").readline())
  


print ("stopping")
stop()
print ("finish")
time.sleep(1)
print("detector FPS: " + str(detector_counter/float(ti_me)) )
print("camera FPS: " + str(cam_counter/float(ti_me)) )
print("scaler FPS: " + str(scaler_counter/float(ti_me)) )
print("scaler2 FPS: " + str(scaler2_counter/float(ti_me)) )
print("mixer FPS: " + str(mixer_counter/float(ti_me)) )
print("display FPS: " + str(display_counter/float(ti_me)) )
print(os.popen("vcgencmd measure_temp").readline())


import sys
print (sys.version_info[0],sys.version_info[1],sys.version_info[2])
print('\033[8;20;100t')
#print("\e")
"""
print ("TEST")

