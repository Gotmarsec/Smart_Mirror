import socket
import time
import thread
import threading

lock = threading.Lock()


#def tobits(s):
#    result = []
#    for c in s:
#        bits = bin(ord(c))[2:]
#        bits = '00000000'[len(bits):] + bits
#        result.extend([int(b) for b in bits])
#    return result

#def frombits(bits):
#    chars = []
#    for b in range(len(bits) / 8):
#        byte = bits[b*8:(b+1)*8]
#        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
#    return ''.join(chars)

def socketThread():
#    a=0
    socr = socket.socket()
    socf = socket.socket()

#    hostr = "192.168.178.45"
    hostr = "192.168.178.226"
    hostf = "192.168.0.101"
    port = 2004
    first = True
    #socf.connect((hostf, port))

    socr.bind((hostr, port))
    socr.listen(5)

    print("ready")
    while True:
        try:
            if(first == True):
                socf.connect((hostf, port))
                socf.settimeout(1)
                first = False
            conn, addr = socr.accept()
            msg = conn.recv(256000)
#            recVal = int(msg[2:])
#            if(recVal < 4095):
            print(len(msg))
            socf.send(msg)

            if (len(msg)==1):
                ans = socf.recv(16)
#                print(bytearray(ans))
                conn.sendall(ans)

#            print(tobits(msg))
#                a=a+1
#            else:
#                if(recVal == 9999):
#                    print("pir active")
#                else:
#                    print("pir inactive")
        except KeyboardInterrupt:
            break
        except socket.error:
	    print("Error!")
            time.sleep(1)
            first=True

thread.start_new_thread(socketThread, ())

while(True):
    time.sleep(1)

socf.shutdown(socket.SHUT_RDWR)
socf.close()

socr.shutdown(socket.SHUT_RDWR)
socr.close()
