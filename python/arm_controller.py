import math
import numpy
import time
import sys
import threading
import os
import reprap_serial_printer as reprap
reprap.open()
reprap.connect()

Zone = [ # X, Y, X [min]; X, Y, X [delta] (max = min + delta) 
  [  0,   0,   0, 280, 200, 300], #zone 0, whole working area 
  [ 60, 150,   0, 100,   0, 300], #zone 1, path between next zones
  [ 20,  50, 280,   0,  40,   0], #zone 2, table for rotate bricks
  [ 60,  80, 200, 100,  40,  80], #zone 3, destination table
  [ 35,  35,  35, 180,  50, 180], #zone 4, working area
  [ 60, 100,   0, 100, 100,   0], #zone 5, escape area for activate table
  ]

act_zone = 0

servos = [ # in min, in max, out min, out max
  ]


X = reprap.X
Y = reprap.Y
Z = reprap.Z
A = reprap.A
B = reprap.B
C = reprap.C

lastX = X
lastY = Y
lastZ = Z
lastA = A
lastB = B
lastC = C



def move (x=None, y=None, z=None, f=None, a=None, b=None, c=None, d=None,
          dx=None, dy=None, dz=None, da=None, db=None, dc=None, zone):
  global act_zone
  
  if zone is None: # use last known one
    zone = act_zone

  zone=max(zone, 0) # limit to range 0..5
  zone=min(zone, 5)

  if zone==0: # overwrite logic and do direct move() command
    reprap.move(x, y, z, f, a, b, c, d, dx, dy, dz, da, db, dc)
    act_zome = zone
    return(1)

  # do something with input values
  
  if zone==act_zone: # same zone, do movement inside
    # ...
    return(1)
    
  # else, different zone

  # move inisde zone (Y max)
  # move to zone 1 (X)
  # move to zone 1 (Y)
  # move inside zone 1 (Z)
  # move to zone a (Y max)
  # move inisde zone a (X)
  # move inisde zone a (Y)
  

  act_zone=zone

  





print("_ok_")

reprap.move(z=0, f=10000)
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


