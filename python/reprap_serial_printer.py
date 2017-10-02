# import reprap_serial_printer as rp
# rp.comport = "/dev/serial/by-id/usb-Arduino_Srl_Arduino_Mega_556393031353516111E0-if00"

# na starcie wylaczyc wszystkie serwa (0)


import time
import serial
import sys
import threading
import math
import numpy
import re
import os

class commands:
	NULL = 0
	HOME = 1
	SERVO_WAIT = 2
	WAIT1s = 3
	STARTUP = 4
	READ_POS = 5
	init57_0 = 6
	init58_0 = 7
	init59_0 = 8
	init57_1 = 9
	init58_1 = 10
	init59_1 = 11
	
ser = serial.Serial(
  parity=serial.PARITY_NONE,
  stopbits=serial.STOPBITS_ONE,
  bytesize=serial.EIGHTBITS,
  timeout=0, #non-block read
  xonxoff = False,
  rtscts = False,
  writeTimeout = 2,
)

comport = 0 #null, please update from main module
speed = 115200 #default for reprap
port_open = 0 #do not read/send, wait for port open command
busy = 1 #do not send, wait for reply from reprap
reply_time = 0
sleep_time = 0
debug_r = 0 # print all data read from serial
debug_r_begin = ""
debug_r_end = ""
debug_w = 1 # print all data write to serial
debug_w_begin = ""
debug_w_end = ""
debug_s = 0 # print data read from stack
debug_s_begin = ""
debug_s_end = ""

X = 70
Y = 150
Z = 280
F = 1000
A = 0
B = 0
C = 0
servo_time = 500

startup = [commands.init59_1, commands.init57_0, commands.init58_0, [0,0], [1,0], [2,0], [X, Y, Z, F], commands.READ_POS, commands.SERVO_WAIT, commands.HOME, commands.init59_0, commands.init57_1, commands.init58_1 ]

stack = startup

def moving(): # true when reprap have orders to do
  # return number of commands to send
  # d + 1 if reprap have one in internal buffer
  return (len(stack) + busy)

def move (x=None, y=None, z=None, f=None, a=None, b=None, c=None, d=None,
          dx=None, dy=None, dz=None, da=None, db=None, dc=None):
  move_xyz = 0
  move_abc = 0
  global X
  global Y
  global Z
  global F
  global A
  global B
  global C
  

  if x is not None:
    X = x
    move_xyz = 1
  if dx is not None:
    X += dx
    move_xyz = 1
  if y is not None:
    Y = y
    move_xyz = 1
  if dy is not None:
    Y += dy
    move_xyz = 1
  if z is not None:
    Z = z
    move_xyz = 1
  if dz is not None:
    Z += dz
    move_xyz = 1
  if f is not None:
    F = f
  if move_xyz:
    stack.insert(0, [X, Y, Z, F])

  if a is not None:
    A = a
    move_abc = 1
    stack.insert(0, [0, A])
  if da is not None:
    A += da
    move_abc = 1
    stack.insert(0, [0, A])
  if b is not None:
    B = b
    move_abc = 1
    stack.insert(0, [1, B])
  if db is not None:
    B += db
    move_abc = 1
    stack.insert(0, [1, B])
  if c is not None:
    C = c
    move_abc = 1
    stack.insert(0, [2, C])
  if dc is not None:
    C += dc
    move_abc = 1
    stack.insert(0, [2, C])
  if d is not None:
    stack.insert(0, [100, d])
    move_abc = 0
    
  if move_abc:
    stack.insert(0, [100, servo_time])



def home():
  stack.insert(0, commands.HOME)

def wait():
  stack.insert(0, commands.WAIT1s)


def open(): # public
  global port_open
  ser.port=comport
  ser.baudrate=speed
  try:
    ser.open()
  except:
    print ("ERROR, wrong port!")
    exit()
  time.sleep(0.5)
  ser.setDTR(True)
  time.sleep(0.5)
  ser.setDTR(False) # reset reprap
  time.sleep(6) #wait until reprap boot
  if ser.inWaiting() < 300:
    print ("ERROR, no reprap connected") 
    exit()
  ser.flushInput()
  port_open = 1
  ser.write("G4 P200\n".encode()) #wait P [ms]
  stack = startup # do homing, etc
  return(1)


def close(): # public close port
  global port_open
  if port_open:
    ser.close()
    port_open = 0

def read(): # private check serial port and read
  try:
    if ser.inWaiting():
      inp = ser.readline().decode()
      if not inp.endswith("\n"):
        time.sleep(0.1)
        print("---- ??? ----")
        inp = inp+ser.readline()
      
      if debug_r:
        print (debug_r_begin + "[IN]" + inp + debug_r_end)
      return(inp)
  except:
    print ("ERROR: port szeregowy niedostepny do odczytu! ")
    exit()
  return (0)


def write(string): # private check serial port and send command
  global busy
  busy = 1
  try: 
    ser.write(string.encode())
    ser.write("\n".encode())
    if debug_w:
      print (debug_w_begin + "[OUT]" + string + debug_w_end)
  except:
    print ("ERROR: port szeregowy niedostepny do zapisu! ")
    exit()

class ThreadingExample(object): # private create commands dispatcher
  """ Threading example class
  The run() method will be started and it will run in the background
  until the application exits.
  """

  def __init__(self, interval=0.1):
    """ Constructor
    :type interval: int
    :param interval: Check interval, in seconds
    """
    self.interval = interval

    thread = threading.Thread(target=self.run, args=())
    thread.daemon = True                            # Daemonize thread
    thread.start()                                  # Start the execution

  def run(self):
    """ Method that runs forever """
    global port_open # 0 = do not read/send, wait for port
    global busy  # 1 = do not send, wait for reply
    global reply_time
    global sleep_time
    global X
    global Y
    global Z
    global A
    global B
    global C

    while True:
      # Do something
      if port_open: 
        input = str(read())
        #print input
        if "ok" in input:
          busy = 0
          #print ("_ok")
        if "X:" in input:
          list1 = input.split("X:")
          list2 = list1[1].split(":")
          #X = float(re.sub(r'[^\d-]+', '',list2[0]))
          #print "_X", X
        if "Y:" in input:
          list1 = input.split("Y:")
          list2 = list1[1].split(":")
          #Y = float(re.sub(r'[^\d-]+', '',list2[0]))
        if "Z:" in input:
          list1 = input.split("Z:")
          list2 = list1[1].split(":")
          #Z = float(re.sub(r'[^\d-]+', '',list2[0]))

        # more input tests

        if busy: 
          reply_time += 1 # every 100ms
          if reply_time==500: # 50s - lost ACK from printer
            print ("WARNING: Reprap nie odpowiada, proboje przywrocic lacznosc... ")
            write("M114")
          if reply_time>1200: # 120s
            print ("ERROR: Reprap nie odpowiada, utracono polaczenie!")
            exit()
        if not busy:
          reply_time=0
          if not len(stack): # empty command stack
            sleep_time +=1
            if sleep_time>3000: # 300s = 5min
              write("M114") # ping reprap with question: actual position?
              sleep_time = 0
          if len(stack):
            order = stack.pop()
            if debug_s:
              print (debug_s_begin + "[STCK]" + order + debug_s_end)
            #return(inp)
            if isinstance(order, list):
              if len(order) == 2: # servo controll or delay
                if order[0]<100:
                  var = "M280 P"+str(order[0])+" S"+str(order[1])
                if order[0]==100:
                  var = "G4 P" + str(order[1])
                if order[0]>100:
                  var = "G4 P1000"
                write(var)
                #print(var)
              if len(order) == 4: # stepper controll
                var = "G1 X"+str(order[0])+" Y"+str(order[1])+" Z"+str(order[2])+" F"+str(order[3])
                write(var)
              #print (order)
            if not isinstance(order, list):
              if order == commands.NULL:
                write("M82")
                if debug_s:
                  print (debug_s_begin + "[=] NULL M82" + debug_s_end)
              if order == commands.HOME:
                write("G28")
                if debug_s:
                  print (debug_s_begin + "[=] HOME" + debug_s_end)
              if order == commands.SERVO_WAIT:
                write("G4 P" + str(servo_time))
                if debug_s:
                  print (debug_s_begin + "[=] SERVO_WAIT" + debug_s_end)
              if order == commands.WAIT1s:
                write("G4 P1000")
                if debug_s:
                  print (debug_s_begin + "[=] WAIT1s" + debug_s_end)
              if order == commands.READ_POS:
                write("M114")
                if debug_s:
                  print (debug_s_begin + "[=] READ_POS" + debug_s_end)
              if order == commands.init57_0:
                write("M42 P57 S0")
              if order == commands.init58_0:
                write("M42 P58 S0")
              if order == commands.init59_0:
                write("M42 P59 S0")
              if order == commands.init57_1:
                write("M42 P57 S255")
              if order == commands.init58_1:
                write("M42 P58 S255")
              if order == commands.init59_1:
                write("M42 P59 S255")


      time.sleep(self.interval)
      

def connect(): # public run commands dispatcher
  example = ThreadingExample()
  print ("connect")



# test ports and halt on broken port
print ("Inicjalizacja sterownika RepRap. Szukam portu... ")
if os.path.isdir("/dev/serial/by-path"): # check if any serial (usb) port installed 
  ports = os.listdir("/dev/serial/by-path")
  if len(ports)>1: # if too many serial ports available
    print("Dostepne porty szeregowe: "+str(len(ports))+". Prosze pozostawic RepRap i odlaczyc pozostale urzadzenia.")
    exit() # halt program
  comport = "/dev/serial/by-path/"+ports[0]
  print("Port znaleziony: "+comport) # print comport 
else: # if no port found, halt
  print("ERROR: nie znaleziono portu szeregowego")
  exit()
  
# = "/dev/ttyUSB0"
# = "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"
# = "/dev/serial/by-id/usb-Arduino_Srl_Arduino_Mega_556393031353516111E0-if00"


