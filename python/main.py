import math
import numpy
import time
import cv2
import serial
import sys
import threading

import reprap_serial_printer as reprap

#print "TEST"
reprap.comport = sys.argv[1]
if reprap.open():
  print "SUCCESS"
reprap.connect()

"""moveAB([90, 90]) # (P0, P1)
wait() # 1 sec
move3dS([99, 100, 0, 1000])
move3dS([0, 80, 0])
wait()
wait()
wait()
wait()
wait()

moveAB([0, 20])
wait()
wait()

move3dS([0,   100, 0])
move3dS([149,   0, 0])

moveAB([175, 0])
wait()
wait()

move3dS([0, 80, 0])

moveAB([0, 90])
wait()
wait()

move3dS([0, 100, 0])
move3dS([99, 0, 0])

moveAB([90, 0])
wait()
wait()
"""
#while moving(): 
#  time.sleep(1)

print "Gotowe"
time.sleep(10)

exit()


