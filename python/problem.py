##############################################
##                                          ##
##  REMEMBER:                               ##
##  OpenCV color(B,G,R)                     ##
##  OpenCV resize(image, (width, height))   #
##  python numpy.zeros( (height, width)   <=- !!!!1
##                                          #
##############################################

import numpy as np
#import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
from threading import Thread, Event
#from multiprocessing import Process, Pipe

class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


import os


import sys
print (sys.version_info[0],sys.version_info[1],sys.version_info[2])
print "\033[8;20;100t"
print bcolors.WARNING+'Doing something imporant in the background, '+bcolors.ENDC, 


time.sleep(1)
print(os.popen("vcgencmd measure_temp").readline())
#print("\e")






