import math
import numpy
import time
import sys
import threading
import os
import reprap_serial_printer as reprap
reprap.open()
reprap.connect()

Zone = [
  #  X,   Y,   Z   [min];
  #                 X,   Y,   Z   [delta]
  #                                        (max = min + delta) 
  [  0,   0,   0, 280, 200, 280], #zone 0, whole working area, limited by printer
  [100, 150,   0,   0,   0, 280], #zone 1, path between next zones
  [ 46,  50,  20, 180,  40, 180], #zone 2, working area
  [ 85,  86, 200,  80,  60,  80], #zone 3, destination table
  [100, 150,   0,   0,   0,   0], #zone 4, escape area for activate table
  ]

act_zone = 1
allow0 = False


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

def limit(a,b,c):  # input single value and two constants, return middle
  return(sorted((a,b,c))[1]) #of input values, limitting output to range


def move (x=None, y=None, z=None, f=None, a=None, b=None, c=None, d=None,
          dx=None, dy=None, dz=None, da=None, db=None, dc=None, zone=None):
  global act_zone
  
  if zone is None: # use last known one
    zone = act_zone

  if zone == 0 and not allow0:
    print("ERROR: strefa zero zablokowana")
    print("Aby odblokowac zmien parametr globalny allow=True")
    print("Albo uzyj innej strefy np. move(zone=1)") 
    return(0)

  zone=max(zone, 0) # limit to range 0..5
  zone=min(zone, 5)

  if f is not None: #f input max 100 [%]
    f = limit(f, 5, 100) # min speed 5%
    f = f*100 # f out max 10'000
    reprap.move(f=f) # if speed changed, send it once

  if zone==0: # overwrite logic and do direct move() command
    reprap.move(x, y, z, f, a, b, c, d, dx, dy, dz, da, db, dc)
    act_zome = zone
    return(1)
  
  X = None
  Y = None
  Z = None
  # grab X+dX for compability  
  if x is not None:
    X = x
  if dx is not None:
    X += dx
  if y is not None:
    Y = y
  if dy is not None:
    Y += dy
  if z is not None:
    Z = z
  if dz is not None:
    Z += dz

  if X is not None: # if any value applied
    X = limit(X, 0, Zone[zone][3]) # limit to zone X size
    X += Zone[zone][0] # add zone offset
  if Y is not None:
    Y = limit(Y, 0, Zone[zone][4]) 
    Y += Zone[zone][1]
  if Z is not None:
    Z = limit(Z, 0, Zone[zone][5])
    Z += Zone[zone][2]

  
  if zone==act_zone: # same zone, do movement inside
    reprap.move(X, Y, Z) # values already limited
    return(1)

  # else, switch between different zones:

  # move inisde zone (Y max)
  # move to zone 1 (X)
  # move to zone 1 (Y)
  # move inside zone 1 (Z)
  # move to zone a (Y max)
  # move inisde zone a (X)
  # move inisde zone a (Y)

  # terminate if missing destination coordinates
  if X is None or Y is None or Z is None:
    print("ERROR: brakuje danych strefy docelowej")
    return(0)
  
  
  if act_zone is not 1: # go from any zone to to main/top zone
    #skip if already inside zone 1
    # last values isn't important here
    reprap.move(y= Zone[act_zone][1] + Zone[act_zone][4]) # move inisde zone (Y max)
    reprap.move(x= Zone[0][0]) # leave last zone 1 (X)
    reprap.move(y= Zone[1][1]) # move to zone 1 (Y)
    # continue moving

  if zone == 1: # move inside main/top zone
    # only if destined zone is 1
    reprap.move(X, Y, Z) # values already limited
    act_zone = zone # switch last active zone
    # continue moving

  if zone is not 1: # leave main/top zone and go into destined zone
    # skip if destined zone is 1
    act_zone = zone # switch last active zone
    reprap.move(z=Z) # move inside zone 1 (Z)
    reprap.move(y= Zone[act_zone][1] + Zone[act_zone][4]) # move to zone a (Y max)
    reprap.move(x = X) # move inisde zone a (X)
    reprap.move(y = Y) # move inisde zone a (Y)

  act_zone=zone
  return(1)

  





print("_ok_")

"""reprap.move(z=0, f=10000)
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

reprap.close() """



#exit()


