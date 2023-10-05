import time
from RF24 import *
import RPi.GPIO as GPIO

radio = RF24(22, 0);
 
address = ["001", "002"]
millis = lambda: int(round(time.time() * 1000))

def normInt(value):
    if(value > 255):
        return 255
    elif(value < 0):
        return 0
    else:
        return value

channels = [0, 0]
currentChannel = 0
STEPSIZE = 6
resp = bytearray(3)

radio.begin()
radio.setAddressWidth(3)
radio.setPALevel(RF24_PA_MIN)
radio.setDataRate(RF24_250KBPS)
#radio.setPayloadSize = 8
radio.setChannel(115)

radio.openReadingPipe(1, address[0]) 
radio.openWritingPipe(address[1])
radio.startListening()

print("Start Listening")
while(True):
    if(radio.available()):
        data = bytearray(radio.read(4))
        radio.stopListening()
        if(data[0] == 1):
            currentChannel = (currentChannel+1) % 2
        elif(data[1] == 1 and channels[currentChannel] < 255):
            channels[currentChannel] = normInt(channels[currentChannel]+STEPSIZE)
        elif(data[1] == 0 and channels[currentChannel] > 0):
            channels[currentChannel] = normInt(channels[currentChannel]-STEPSIZE)

        i = (data[3]<<8)|data[2]
        result = str(data[0]) + "  " + str(data[1]) + "  " + str(i)
        print(result)
        if(currentChannel == 0):
            resp[0] = channels[currentChannel]
            resp[1] = 0
            resp[2] = 0
        elif(currentChannel == 1):
            resp[0] = 0
            resp[1] = channels[currentChannel]
            resp[2] = 0
        result2 = str(resp[0]) + "  " + str(resp[1]) + "  " + str(resp[2])
        print(result2)
        radio.write(resp)
        radio.startListening()
    time.sleep(0.05)
