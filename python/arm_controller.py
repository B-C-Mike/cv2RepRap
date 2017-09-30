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


X = reprap.X
Y = reprap.Y
Z = reprap.Z


lastX = X
lastY = Y
lastZ = Z

packing_position=0


def limit(a,b,c):  # input single value and two constants, return middle
  return(sorted((a,b,c))[1]) #of input values, limitting output to range

def new_position():
  global packing_position
  a = packing_position
  b = int(a/3.0)
  c = int(b/3.0)
  packing_position += 1
  return(( (a-3*b), (b-3*c), c))

def place():
  pos = new_position()
  release(pos[0]*30, pos[2]*20, pos[1]*30, 90, 3)

def servo(a=None, b=None, c=None, d=None):
  if a: # skip 0 (OFF) and none (not changed)
    a = limit(a, 0, 90) # 0: | verical angle; 45: / middle position; 90: -- horizontal angle
    a *= 0.91 # set scale
    a += 90 # set 
    a = int(a)

  if b: # skip 0 (OFF) and none (not changed)
    if b==1: # activated = closed
      b=11
    else:
      b=25

  reprap.move(a=a, b=b) # update A and B servos

  if c is not None: # input: 0 = off, 100 = max, negatve = [open, wait, close]
    animation=0
    Min=90
    Max=50
    if c<0:
      animation=1
      c=-c

    c = limit(c, 0, 100)
    if c==0:
      reprap.move(c=Min) # standard delay
      reprap.move(c=0) # disable servo
      return(0) # end
    #c = Min-int(c*(Min-Max)/100.0 ) # scale
    c = c*(Min-Max)
    c=int(c/100.0 )
    c=Min-c
    reprap.move(c=c) # update
    if animation:
      c=int((c+2*Min)/3) # div by three
      reprap.move(c=c) # update
      c=int((c+2*Min)/3) # div by three
      reprap.move(c=c) # update
      c=int((c+2*Min)/3) # div by three
      reprap.move(c=c) # update
      reprap.move(c=Min) # zero
      reprap.move(c=0) # disable servo
    

def flip(power):
  move(x=0, y=0, z=0, zone=4, f=100) # fast frward to safe zone
  servo(c=-power)
  global packing_position
  packing_position=0

def grab(x, y, z, a, zone=None, f=50):
  move(x=x, y=y+20, z=z, f=f, zone=zone)
  servo(a=a, b=2) # b = open
  move(y=y, f=1) # slow down
  servo(a=0, b=1) # release a, grab
  move(y=y+20) # slow up
  move(f=f) # standard speed

def release(x, y, z, a, zone=None, f=50):
  move(x=x, y=y+20, z=z, f=f, zone=zone)
  servo(a=a) # b = not change
  move(y=y+1, f=1) # slow down
  servo(a=0, b=2) # release a, open
  move(y=y+20) # slow up
  move(f=f) # standard speed
  servo(b=0)

  

def move (x=None, y=None, z=None, f=None, d=None, zone=None):
  global act_zone
  
  if zone is None: # use last known one
    zone = act_zone

  if zone == 0 and not allow0:
    print("ERROR: strefa zero zablokowana")
    print("Aby odblokowac zmien parametr globalny allow0=True")
    print("Albo uzyj innej strefy np. move(zone=1)") 
    return(0)

  zone=max(zone, 0) # limit to range 0..5
  zone=min(zone, 4)

  if f is not None: #f input max 100 [%]
    f = limit(f, 5, 100) # min speed 5%
    f = f*100 # f out max 10'000
    reprap.move(f=f) # if speed changed, send it once

  if zone==0: # overwrite logic and do direct move() command
    reprap.move(x, y, z, f, d=d)
    act_zome = zone
    return(1)


  X = x
  Y = y
  Z = z
  if x is not None: # if any value applied
    X = limit(x, 0, Zone[zone][3]) # limit to zone X size
    X += Zone[zone][0] # add zone offset
  if y is not None:
    Y = limit(y, 0, Zone[zone][4]) 
    Y += Zone[zone][1]
  if z is not None:
    Z = limit(z, 0, Zone[zone][5])
    Z += Zone[zone][2]

  
  if zone==act_zone: # same zone, do movement inside
    reprap.move(X, Y, Z, d=d) # values already limited
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
  reprap.move(d=d) # delay
  return(1)


def moving():
  return reprap.moving()





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


