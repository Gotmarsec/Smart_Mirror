#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import socket
import thread
import threading

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

WAITING_TIME=60

RELAY_PIN=22
PIR_PIN = 23
BUTTON_PIN=24

active = True

GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(BUTTON_PIN, GPIO.IN)

GPIO.output(RELAY_PIN, GPIO.LOW)

lock = threading.Lock()

def button_interrupt(channel):
	time.sleep(0.01)
	if (GPIO.input(BUTTON_PIN) == True):
		global active
        	active=not active
        	if (not active == True):
#			GPIO.remove_event_detect(PIR_PIN)
#        	        GPIO.remove_event_detect(BUTTON_PIN)

			GPIO.output(RELAY_PIN, GPIO.LOW)

#			GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=button_interrupt, bouncetime=2000)
#                	GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=PIR_interrupt, bouncetime=200)

def PIR_interrupt(channel):
#	print "PIR triggered"
	if (active == True):

		GPIO.remove_event_detect(PIR_PIN)
		GPIO.remove_event_detect(BUTTON_PIN)
       		GPIO.output(RELAY_PIN, GPIO.HIGH)
		GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=button_interrupt, bouncetime=2000)
#       		print "Displays on"
##       		time.sleep(WAITING_TIME)
##		while (GPIO.input(PIR_PIN) == True):
##			time.sleep(1)
		resetTime = 0
		while (resetTime < WAITING_TIME):
			resetTime = resetTime + 1
			if (GPIO.input(PIR_PIN) == True):
				resetTime = 0
			time.sleep(1)
		resetTime = 0

		GPIO.remove_event_detect(BUTTON_PIN)
       		GPIO.output(RELAY_PIN, GPIO.LOW)
		GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=button_interrupt, bouncetime=2000)

		GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=PIR_interrupt, bouncetime=200)
#		print "Displays off"

GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=PIR_interrupt, bouncetime=200)
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=button_interrupt, bouncetime=2000)

def socketThread():
    socr = socket.socket()
    socf = socket.socket()

    hostr = "192.168.178.45"
    hostf = "192.168.0.101"
    port = 2004
    first = True
    #socf.connect((hostf, port))

    socr.bind((hostr, port))
    socr.listen(5)

    while True:
        try:
            if(first == True):
                socf.connect((hostf, port))
                first = False
            conn, addr = socr.accept()
            msg = conn.recv(6)
            recVal = int(msg[2:])
            if(recVal < 4095):
                socf.send(msg)
            else:
                if(recVal == 9999):
                    print("pir active")
                else:
                    print("pir inactive")
        except KeyboardInterrupt:
            socf.shutdown(socket.SHUT_RDWR)
            socf.close()

            socr.shutdown(socket.SHUT_RDWR)
            socr.close()
            break
        except socket.error:
            time.sleep(1)
            first=True

thread.start_new_thread(socketThread, ())

while True:
	try:
      		time.sleep(1)           # Sleep for a full second before restarting our loop
	except KeyboardInterrupt:
		break
print "\n"
GPIO.cleanup()           # clean up GPIO on normal exit
