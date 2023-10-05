import socket
import thread
import threading
import time

asdf = 0

lock = threading.Lock()

def socketThread():
    global asdf
    soc = socket.socket()
    host = "192.168.0.101"
    port = 2004
    soc.bind((host, port))
    soc.listen(5)
    conn, addr = soc.accept()
    print("ready")
    while True:
        try:
#            conn, addr = soc.accept()
            msg = conn.recv(6)
            if(msg):
                with lock:
                    asdf = int(msg[2:])
            else:
                conn, addr = soc.accept()
        except KeyboardInterrupt:
            break
        except socket.error:
            print("Error!")
            time.sleep(1)

thread.start_new_thread(socketThread, ())

while(True):
    print(asdf)
    time.sleep(1)

soc.shutdown(socket.SHUT_RDWR)
soc.close()

