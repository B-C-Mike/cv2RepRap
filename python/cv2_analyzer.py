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
#from threading import Thread, Event
from picamera import PiCamera
import cv2_camera_input as camera
camera.camera = PiCamera()
camera.camera.shutter_speed=35*1000
camera.start()
camera.overlay_transparency = 160
print ("starting")
time.sleep(2)




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
    tmp,threshold=cv2.threshold(crop, 128 , 255, cv2.THRESH_BINARY_INV)
    threshold=cv2.morphologyEx(threshold, cv2.MORPH_OPEN, None, iterations=1) # erode i times, dilate i times
    threshold=cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, None, iterations=1) # erode i times, dilate i times
    #th2    =cv2.adaptiveThreshold(crop, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # NIE DZIALA NA KOLOROWYM OBRAZIE
    #cv2.imshow("binary", threshold)
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
                    box=np.int0(box)
                    cv2.drawContours(im2, [box], 0, (0,0,0), 1)
                    cv2.arrowedLine(im2, (cx, cy), (cx+int(50*math.cos(rect[2]*math.pi/180)), cy+int(50*math.sin(rect[2]*math.pi/180))), (0,0,0), 2)

                    x, z = scale(cx,cy)
                    im2=cv2.putText(im2, "x="+str(int(x))+"mm z="+str(int(z))+"mm", (cx+20, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0))
            if m_size==t_size:
                    for i in range(3):
                            cv2.line(im2, (triangle[i][0][0], triangle[i][0][1]), (triangle[(i+1)%3][0][0], triangle[(i+1)%3][0][1]), (0,0,0), 2)
            

    camera.update(im2)
    #cv2.imshow("Frame", im2)
    #cv2.imshow("cont", im2)

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

