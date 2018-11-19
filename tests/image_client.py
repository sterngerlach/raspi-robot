# coding: utf-8
# client.py

import cv2
import pickle
import socket
import struct
import time
import zlib

def main():
    host = "localhost"
    port = 12345
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    try:
        while True:
            ret, frame = cam.read()
            data = pickle.dumps(frame)
            data = zlib.compress(data)
            size = len(data)
            
            sock.sendall(struct.pack(">L", size) + data)
            
            time.sleep(0.2)
    finally:
        sock.close()

if __name__ == "__main__":
    main()
    