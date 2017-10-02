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
import math
import arm_controller as arm
#from threading import Thread, Event
from picamera import PiCamera
import cv2_camera_input as camera
camera.camera = PiCamera()
camera.start()
time.sleep(2)
camera.camera.shutter_speed=20*1000
camera.overlay_transparency = 120
print ("starting")
time.sleep(1)
print("\x1b[8;35;52t") # wysokosc x szerokosc [znaki terminala]
print("\x1b[3;790;42t") # szerokosc x wysokosc [piksele od gora/lewo]
buffer=[]

wait_for_printer=20
while arm.moving():
  time.sleep(1)
  """wait_for_printer-=1
  if not wait_for_printer:
    print("ERROR: drukarka nie odpowiada")
    sys.exit()"""


def move_bricks():
  while len(buffer):
    arr=buffer.pop()
    print("X="+str(int(arr[0]))+" Z="+str(int(arr[1]))+" a="+str(int(arr[2]))+"*")
    arm.grab(x=arr[0], y=0, z=arr[1], a=arr[2], zone=2)
    arm.place()
  print("")


def add_brick(cx, cy, a):
  x, z = scale(cx, cy)
  buffer.insert(0, [x, z, a])

def scale(camx, camy):
  xscale=2.0/1.0 # px/mm
  zscale=-2.0/1.0 # px/mm
  dx = 0
  dz = 180
  x = (camy / xscale)+dx
  z = (camx / zscale)+dz
  return x, z

while True:
  crop=cv2.cvtColor(camera.getImage(), cv2.COLOR_BGR2GRAY)
  image = camera.getOverlay()

  cv2.line(image, (359, 359), (359, 0  ), (255, 0, 0))
  cv2.line(image, (359, 359), (0,   359), (255, 0, 0))
  cv2.line(image, (0,   359), (0,   0  ), (255, 0, 0))
  cv2.line(image, (359, 0  ), (0,   0  ), (255, 0, 0))
  #cv2.imshow("Frame", image)

  #cv2.imshow("croppd", crop)

  # threshold

  #tmp,threshold=cv2.threshold(crop, cv2.getTrackbarPos("Val", "binary") , 255, cv2.THRESH_BINARY_INV)
  _ , threshold=cv2.threshold(crop, 128 , 255, cv2.THRESH_BINARY_INV)
  threshold =cv2.morphologyEx(threshold, cv2.MORPH_OPEN, None, iterations=1) # erode i times, dilate i times
  threshold2=cv2.morphologyEx(threshold, cv2.MORPH_OPEN, None, iterations=1) # backup before contours
  #threshold=cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, None, iterations=1) # erode i times, dilate i times
  full_mask = cv2.bitwise_and(threshold, 0)
  

  #th2    =cv2.adaptiveThreshold(crop, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
  # NIE DZIALA NA KOLOROWYM OBRAZIE
  #cv2.imshow("binary", threshold)
  #cv2.imshow("gaussian", th2) #  DOBRE ALE TRZEBA DAC IDEALNIE BIALE TLO

  # conturs
  im2, conturs, _=cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
  threshold = threshold2 # backup before contours
  
  #im2=cv2.drawContours(image, conturs, -1, (0, 255, 0), 2) #  NIE DZIALA NA MONOCHROMATYCZNYM OBRAZIE
  #im2=cv2.drawContours(image, conturs[0], -1, (255, 0, 0), 2) # zerowy
  im2=image
    
  count = 0 # number of good blocks
  bad_count = 0 # number of bad blocks
  errors = 0
  
  # test all conturs, break if any bigger than allowed area
  for cnt in conturs: # first pass, break when any big object on field
    size = cv2.contourArea(cnt)

    if size>10*1000: # one or more too big objects, like hand or shadow
      x,y,_ = im2.shape
      cv2.line(im2, (0, 10), (x, y+10), (255, 255, 255), 5)
      cv2.line(im2, (10, 0), (x+10, y), (255, 255, 255), 5)
      cv2.line(im2, (0+10, y), (x, 0+10), (255, 255, 255), 5)
      cv2.line(im2, (0-10, y), (x, 0-10), (255, 255, 255), 5)
      cv2.line(im2, (0, 0), (x, y), (0, 0, 0), 5)
      cv2.line(im2, (0, y), (x, 0), (0, 0, 0), 5)
      m2=cv2.drawContours(im2, cnt, -1, (0, 0, 255), 8)
      errors=1
      break

  # test all conturs,        
  if not errors:
    for cnt in conturs: # second pass, draw all contours for collision detector
      size = cv2.contourArea(cnt)
      if size<200: # less than 10x10px = 5x5mm
        continue
      cv2.drawContours(full_mask, [cnt], -1, 255, -1)

      
    for cnt in conturs: # third pass, check each brick
      size = cv2.contourArea(cnt)
      if size<100: # less than 10x10px = 5x5mm
        continue
      
      moments=cv2.moments(cnt) # calculate moments for non-zero objects
      cx=int(moments['m10']/moments['m00'])
      cy=int(moments['m01']/moments['m00'])
      
      if size<1014: # skip less than 32x32px = 16x16mm (less than 1 block)
        im2=cv2.circle(im2, (cx, cy), 4, (0, 255, 255), 2) #center circle
        continue
      
      if size>3500: # more than single block
        im2=cv2.drawContours(im2, cnt, -1, (0, 0, 255), 4)
        continue
      
      #count += 1 # found one good brick
      rect=cv2.minAreaRect(cnt) # surrounding square
      cx=rect[0][0]
      cy=rect[0][1]
      box=cv2.boxPoints(rect)
      box=np.int0(box)

      rect2 = (rect[0], (rect[1][0]+40, rect[1][1]+4), rect[2]) # square + free space for manipulator
      # + 10px (5mm) 2 sides, 4px (2mm) other sides just for not cover recentry drawn lines
      box2=cv2.boxPoints(rect2)
      box2=np.int0(box2)
      #cv2.drawContours(full_mask, [box2], 0, (255,0,0), -1)

      mask = cv2.bitwise_and(full_mask, 0)
      cv2.drawContours(mask, [box2], -1, 255, -1)
      mask = cv2.bitwise_and(full_mask, mask)
      _, near_conturs, _=cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
      conturs_count = 0
      for _ in near_conturs:
        conturs_count += 1
      #im2=cv2.putText(im2, "   "+str(conturs_count), (cx+20, cy-50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))

      im2=cv2.drawContours(im2, cnt, -1, (64, 255, 0), 2)
      
      if conturs_count == 1: # no extra parts inside safety area - brick allowed to pick-up
          count += 1
        #if count == 1: # select and pick-up first one
          #im2=cv2.drawContours(im2, cnt, -1, (255, 0, 0), 2) # blue
          #cv2.drawContours(im2, [box], 0, (255, 0, 0), 2)
          cv2.drawContours(im2, [box2], 0, (255, 0, 0), 2)
          add_brick(cx=cx, cy=cy, a=90+rect[2]) # move that brick if possible
        #else: # draw contour for rest
          #im2=cv2.drawContours(im2, cnt, -1, (64, 255, 0), 2) # green
          #cv2.drawContours(im2, [box], 0, (64, 255, 0), 2)
          #cv2.drawContours(im2, [box2], 0, (64, 255, 0), 2)
      else: # draw contour for bad ones
        #im2=cv2.drawContours(im2, cnt, -1, (0, 220, 255), 2) # yellow
        #cv2.drawContours(im2, [box], 0, (0, 220, 255), 2)
        cv2.drawContours(im2, [box2], 0, (0, 120, 255), 2)
        bad_count += 1
        
      #r_size=rect[1][0]*rect[1][1] # size[width] * [height]

      #im2=cv2.putText(im2, "   "+str(int(moments['m00'])), (cx+20, cy+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))
      #im2=cv2.putText(im2, str(cv2.contourArea(cnt)), (cx+20, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))
      #cv2.arrowedLine(im2, (cx, cy), (cx+int(50*math.cos(rect[2]*math.pi/180)), cy+int(50*math.sin(rect[2]*math.pi/180))), (0,0,0), 2)

      x, z = scale(rect[0][0],cy)
      im2=cv2.putText(im2, "   kat: "+str(int(90+rect[2]))+" x="+str(int(x))+"mm z="+str(int(z))+"mm", (int(cx+20), int(cy-20)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))
              
              
      

  #camera.update(cv2.cvtColor(threshold, cv2.COLOR_GRAY2BGR) )
  camera.update(im2)
  #camera.update(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))
  if arm.moving():
    buffer=[]
  else:
    print("good: "+str(count)+" bad: "+str(bad_count))
    time.sleep(1)
    move_bricks()
    time.sleep(1)
    if count+bad_count==0:
      arm.flip(60)
      


  if len(camera.keyboard):
      key = camera.keyboard.pop()
      if key==27:
        break











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

# allow the camera to warmup
time.sleep(0.1)

cv2.namedWindow("binary")
cv2.createTrackbar("Val", "binary", 0, 255, nothing)
cv2.setTrackbarPos("Val", "binary", 70)

cv2.namedWindow("Frame")
cv2.createTrackbar("Speed [ms]", "Frame", 0, 50, s_speed)
cv2.setTrackbarPos("Speed [ms]", "Frame", 35)


# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array

	# crop and grayscale
	crop=cv2.cvtColor(image[cvYstart:cvYend, cvXstart:cvXend], cv2.COLOR_BGR2GRAY)
	
	# show original frame
	cv2.line(image, (cvXstart, cvYstart), (cvXstart, cvYend  ), (255, 0, 0))
	cv2.line(image, (cvXstart, cvYstart), (cvXend,   cvYstart), (255, 0, 0))
	cv2.line(image, (cvXend,   cvYstart), (cvXend,   cvYend  ), (255, 0, 0))
	cv2.line(image, (cvXstart, cvYend  ), (cvXend,   cvYend  ), (255, 0, 0))
	#cv2.imshow("Frame", image)

	#cv2.imshow("croppd", crop)

	# threshold
	tmp,threshold=cv2.threshold(crop, cv2.getTrackbarPos("Val", "binary") , 255, cv2.THRESH_BINARY_INV)
	threshold=cv2.morphologyEx(threshold, cv2.MORPH_OPEN, None, iterations=1) # erode i times, dilate i times
	threshold=cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, None, iterations=1) # erode i times, dilate i times
	#th2    =cv2.adaptiveThreshold(crop, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
	# NIE DZIALA NA KOLOROWYM OBRAZIE
	cv2.imshow("binary", threshold)
	#cv2.imshow("gaussian", th2) #  DOBRE ALE TRZEBA DAC IDEALNIE BIALE TLO

	# conturs
	im2, conturs, hierarchy=cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
	
	#im2=cv2.drawContours(image, conturs, -1, (0, 255, 0), 2) #  NIE DZIALA NA MONOCHROMATYCZNYM OBRAZIE
	#im2=cv2.drawContours(image, conturs[0], -1, (255, 0, 0), 2) # zerowy
	im2=image
	# test all conturs
	for cnt in conturs:
		moments=cv2.moments(cnt)

		#skip noise
		if moments['m00']<5:
			continue

		cx=int(moments['m10']/moments['m00'])
		cy=int(moments['m01']/moments['m00'])
		im2=cv2.circle(im2, (cx, cy), 4, (0, 0, 255), 2) #center circle

		#skip small parts
		if moments['m00']<300:
			continue

		#skip to big parts
		if moments['m00']>7000:
			continue
		

		
		im2=cv2.drawContours(im2, cnt, -1, (0, 255, 0), 2)
		im2=cv2.putText(im2, str(moments['m00']), (cx+20, cy+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))
		#im2=cv2.putText(im2, str(cv2.contourArea(cnt)), (cx+20, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))

		# test shapes
		(x,y), c_radius=cv2.minEnclosingCircle(cnt)
		c_center=(int(x),int(y))
		c_size=(math.pi*c_radius*c_radius)
		
		rect=cv2.minAreaRect(cnt)
		r_size=rect[1][0]*rect[1][1] # size[width] * [height]
		#print repr(r_size)
		
		t_size, triangle=cv2.minEnclosingTriangle(cnt)


		#print repr((c_size, r_size, t_size))

		

		m_size=min(c_size, r_size, t_size)
		if m_size==c_size:
			im2=cv2.circle(im2, c_center, int(c_radius), (0,0,0), 2)
		if m_size==r_size:
			box=cv2.boxPoints(rect)
			box=numpy.int0(box)
			cv2.drawContours(im2, [box], 0, (0,0,0), 1)
			cv2.arrowedLine(im2, (cx, cy), (cx+int(50*math.cos(rect[2]*math.pi/180)), cy+int(50*math.sin(rect[2]*math.pi/180))), (0,0,0), 2)
			xscale=182.0/100.0 # px/mm
			yscale=182.0/100.0 # px/mm
			im2=cv2.putText(im2, "x="+str(int(cx/xscale))+"mm y="+str(int(-cy/yscale))+"mm", (cx+20, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))
		if m_size==t_size:
			for i in range(3):
				cv2.line(im2, (triangle[i][0][0], triangle[i][0][1]), (triangle[(i+1)%3][0][0], triangle[(i+1)%3][0][1]), (0,0,0), 2)

		
        
	cv2.imshow("Frame", im2)
	#cv2.imshow("cont", im2)

	
	key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
# """

