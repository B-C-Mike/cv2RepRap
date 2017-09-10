import math
import numpy
import time
import cv2
import serial
import sys
import threading
import os
import datetime
author = "Ertew"
owner = "PUT"

print("Oprogramowanie: cv2reprap \nAutor: "+author+", dla: "+owner+" \nWersja: "+datetime.datetime.fromtimestamp(os.path.getmtime(os.path.realpath(__file__))).strftime("%y.%m.%d.%H")) # welcome message
print("Python: "+".".join(map(str,sys.version_info[0:3]))+" \nOpencv: "+cv2.__version__+" \n -- --- --") # welcome message


import reprap_serial_printer as reprap
reprap.open()
reprap.connect()

print("_ok_")

reprap.move(z=0, f=2000)
reprap.move(x=30, y=30)
reprap.move(y=200)
reprap.move(x=200)
reprap.move(y=30)
reprap.move(x=30)
reprap.move(x=200, y=200)
reprap.move(x=30)
reprap.move(x=200, y=30)
reprap.move(z=300)

time.sleep(100)
#reprap.comport = False

reprap.close()

exit()
if reprap.open():
  print ("SUCCESS")
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

print ("Gotowe")
time.sleep(10)

exit()


