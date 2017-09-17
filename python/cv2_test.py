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



