#!/usr/bin/env python
from ctypes import cast, pointer, POINTER, c_char, c_int
import numpy as np
from array import array
import wiringpi
import RPi.GPIO as GPIO
import time
from RF24 import *
import socket
import thread
import threading

KNOBCHANNELCOUNT = 5

ledpin1 = 18
ledpin2 = 19
buttonpin1 = 23
buttonpin2 = 24
RF24_IRQ = 12
#state1 = 0
#state2 = 0

GPIO.setwarnings(False)			#disable warnings
GPIO.setmode(GPIO.BCM)		#set pin numbering system

#GPIO.setup(ledpin1, GPIO.OUT)
#GPIO.setup(ledpin2, GPIO.OUT)
wiringpi.wiringPiSetupGpio()
wiringpi.pinMode(ledpin1, 2)      # pwm only works on GPIO port 18
wiringpi.pinMode(ledpin2, 2)

GPIO.setup(buttonpin1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(buttonpin2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RF24_IRQ, GPIO.IN, pull_up_down=GPIO.PUD_UP)

radio = RF24(22, 0);

address = ["001", "002"]
millis = lambda: int(round(time.time() * 1000))

def convert(c):
    return cast(pointer(c_char(c)), POINTER(c_int)).contents.value

def tobits(s):
    result = []
    for c in s:
        bits = bin(ord(c))[2:]
        bits = '00000000'[len(bits):] + bits
        result.extend([int(b) for b in bits])
    return result

def tobytes(number):
    byte_array = []
    while number != 0:
        byte_array = [number % 256] + byte_array
        number = number // 256
    return byte_array

def normInt(value):
    if(value > 1023):
        return 1023
    elif(value < 0):
        return 0
    else:
        return value

channels = [0] * KNOBCHANNELCOUNT
currentChannel = 0
STEPSIZE = 200
resp = bytearray(5)

currentMirrorVal0 = 0
currentMirrorVal1 = 0
#enterPWMLoop = True

radio.begin()
radio.setAddressWidth(3)
radio.setPALevel(RF24_PA_MIN)
radio.setDataRate(RF24_250KBPS)
#radio.setPayloadSize = 8
radio.setChannel(115)

radio.txDelay = 130
radio.csDelay = 0

radio.openReadingPipe(1, address[0])
radio.openWritingPipe(address[1])
radio.startListening()


lock = threading.Lock()
wLock = threading.Lock()
#cond = threading.Condition()
event = threading.Event()

#pwm1 = GPIO.PWM(ledpin1, 1000)
#pwm2 = GPIO.PWM(ledpin2, 28000)		#create PWM instance with frequency
#pwm1.start(state1)				#start PWM of required Duty Cycle
#pwm2.start(state2)
wiringpi.pwmWrite(ledpin1, 0)    # duty cycle between 0 and 1024. 0 = off, 1024 = fully on
wiringpi.pwmWrite(ledpin2, 0)    # duty cycle between 0 and 1024. 0 = off, 1024 = fully on

def pwmThread(event):
#    global enterPWMLoop
#    if(enterPWMLoop is False):
#        return

#    enterPWMLoop = False
    global currentMirrorVal0
    global currentMirrorVal1
    while(True):
        event.wait(10)
        event.clear()
#        print("ok")
#        time.sleep(1)
        while(channels[0] != currentMirrorVal0 or channels[1] != currentMirrorVal1):
#            print(channels[0])
            if(channels[0] != currentMirrorVal0):
                if(channels[0] > currentMirrorVal0):
                    currentMirrorVal0 += 1
                else:
                    currentMirrorVal0 -= 1
                wiringpi.pwmWrite(ledpin1, currentMirrorVal0)
            if(channels[1] != currentMirrorVal1):
                if(channels[1] > currentMirrorVal1):
                    currentMirrorVal1 += 1
                else:
                    currentMirrorVal1 -= 1
                wiringpi.pwmWrite(ledpin2, currentMirrorVal1)
            time.sleep(0.0005)
#    enterPWMLoop = True

def socketThread():
    global channels
    soc = socket.socket()
    host = "192.168.0.101"
    port = 2004
    soc.bind((host, port))
    soc.listen(5)
    conn, addr = soc.accept()
    sendLeaf = 0
    blackout = 0
    while True:
        try:
#            conn, addr = soc.accept()
#            msg = np.asarray(list(conn.recv(6))).astype(byte)
#            msg = array('B', conn.recv(6))
            msg = map(convert, conn.recv(256000))
            if(len(msg)>0):
#                val = (msg[1] << 8) | msg[2]
                with lock:
                    if(len(msg)==1):
                        if(msg[0] == 200):
                            conn.sendall("0,"+str(currentMirrorVal0))
                        elif(msg[0] == 201):
                            conn.sendall("1,"+str(currentMirrorVal1))
                    elif(len(msg)==3):
                        if(msg[0] == 0):
                            channels[0] = (msg[1] << 8) | msg[2]
#                            wiringpi.pwmWrite(ledpin1, channels[0])
                            event.set()
                        elif(msg[0] == 1):
                            channels[1] = (msg[1] << 8) | msg[2]
#                            wiringpi.pwmWrite(ledpin2, channels[1])
                            event.set()
                        elif(msg[0] == 2):
                            resp[0] = 0
                            resp[1] = ((msg[1] << 8) | msg[2])/4
                            sendLeaf = 1
                        elif(msg[0] == 3):
                            resp[0] = 1
                            resp[1] = ((msg[1] << 8) | msg[2])/4
                            sendLeaf = 1
                        elif(msg[0] == 4):
                            resp[0] = 2
                            resp[1] = ((msg[1] << 8) | msg[2])/4
                            sendLeaf = 1
                        elif(msg[0] == 6):
                            channels[0] = 0
                            channels[1] = 0
#                            wiringpi.pwmWrite(ledpin1, channels[0])
#                            wiringpi.pwmWrite(ledpin2, channels[1])
                            event.set()
                            blackout = 1
                    if(blackout == 1):
                        blackout = 0 #TODO: insert leaf blackout here
                    elif(len(msg)==5):
                        if(msg[0] == 5):
                            resp[0] = 3
                            resp[1] = msg[1]
                            resp[2] = msg[2]
                            resp[3] = msg[3]
                            resp[4] = msg[4]
                            sendLeaf = 1
                    else:
#                        print(msg)
                        print(len(msg))

#                        resp[1] = (msg[1] << 8) | msg[2]
                    if(sendLeaf == 1):
                        sendLeaf = 0
                        radio.stopListening()
                        radio.setChannel(114)
                        radio.write(resp)
                        radio.setChannel(115)
                        radio.startListening()
            else:
                conn, addr = soc.accept()
        except KeyboardInterrupt:
            soc.shutdown(socket.SHUT_RDWR)
            soc.close()
            break
        except socket.error:
#            print("Error!")
            time.sleep(1)

def button1_interrupt(channel):
    if (GPIO.input(buttonpin1) == True):
#        print "button1 triggered"
        global channels
        channels[0] = channels[0] + 256
        if (channels[0] > 1024):
            channels[0] = 0
#        pwm1.ChangeDutyCycle(state1)
#        wiringpi.pwmWrite(ledpin1, channels[0])
        event.set()

def button2_interrupt(channel):
    if (GPIO.input(buttonpin2) == True):
#        print "button2 triggered"
        global channels
        channels[1] = channels[1] + 256
        if (channels[1] > 1024):
            channels[1] = 0
#        pwm2.ChangeDutyCycle(state2)
#        wiringpi.pwmWrite(ledpin2, channels[1])
        event.set()

def RF24_IRQ_interrupt(channel):
    global currentChannel
    global channels

    with wLock:
#        print("asdf")
        if(radio.available()):
            while(radio.available()):
                data = bytearray(radio.read(32))
#                radio.stopListening()
#                if(data[0] == 1):
#                    currentChannel = (currentChannel+1) % 2
                currentChannel = data[0] % KNOBCHANNELCOUNT

                if(data[1] == 1):
                    channels[currentChannel] = normInt(channels[currentChannel]+STEPSIZE)
                elif(data[1] == 0):
                    channels[currentChannel] = normInt(channels[currentChannel]-STEPSIZE)

                if(currentChannel == 2 or currentChannel == 3 or currentChannel == 4):
                    if(currentChannel == 2):
                        resp[0] = 0
                    elif(currentChannel == 3):
                        resp[0] = 1
                    else:
                        resp[0] = 2

                    resp[1] = channels[currentChannel]/4
#                    print(str(currentChannel) + "  " + str(resp[1]))
                    radio.stopListening()
                    radio.setChannel(114)
                    radio.write(resp)
                    radio.setChannel(115)
                    radio.startListening()
                    continue;

                radio.stopListening()
#                if(data[1] == 1 and channels[currentChannel] < 1023):
#                    channels[currentChannel] = normInt(channels[currentChannel]+STEPSIZE)
#                elif(data[1] == 0 and channels[currentChannel] > 0):
#                    channels[currentChannel] = normInt(channels[currentChannel]-STEPSIZE)

                i = (data[3]<<8)|data[2]

                if(currentChannel == 0):
#                    wiringpi.pwmWrite(ledpin1, channels[currentChannel])
                    event.set()
                    resp[0] = channels[currentChannel]/4
                    resp[1] = channels[currentChannel]/4
                    resp[2] = 0
                elif(currentChannel == 1):
#                    wiringpi.pwmWrite(ledpin2, channels[currentChannel])
                    event.set()
                    resp[0] = channels[currentChannel]/4
                    resp[1] = channels[currentChannel]/4
                    resp[2] = channels[currentChannel]/4
                radio.write(resp)
                radio.startListening()

GPIO.add_event_detect(buttonpin1, GPIO.RISING, callback=button1_interrupt, bouncetime=200)
GPIO.add_event_detect(buttonpin2, GPIO.RISING, callback=button2_interrupt, bouncetime=200)
GPIO.add_event_detect(RF24_IRQ, GPIO.FALLING, callback=RF24_IRQ_interrupt, bouncetime=1)

thread.start_new_thread(socketThread, ())
thread.start_new_thread(pwmThread, (event,))
while True:
    try:
        time.sleep(1)           # Sleep for a full second before restarting our loop
    except KeyboardInterrupt:
        break
print "\n"
#wiringpi.pwmWrite(ledpin1, 0)
#wiringpi.pwmWrite(ledpin2, 0)
channels[0] = 0
channels[1] = 0
event.set()
GPIO.cleanup()           # clean up GPIO on normal exit

