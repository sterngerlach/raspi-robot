# -*- coding: utf-8 -*-
# image_server.py

import cv2
import pickle
import socket
import struct
import zlib

def receive_image(conn, addr):
    while True:
        data = b""
        msg_header_size = struct.calcsize(">L")
        
        while len(data) < msg_header_size:
            chunk = conn.recv(1024)
            
            if not chunk:
                print("receive_image(): connection closed")
                return
            else:
                data += chunk
        
        payload_size = data[:msg_header_size]
        data = data[msg_header_size:]
        payload_size = struct.unpack(">L", payload_size)[0]
        print("receive_image(): image size: {0}".format(payload_size))
        
        while len(data) < payload_size:
            chunk = conn.recv(1024)
            
            if not chunk:
                print("receive_image(): connection closed")
                return
            else:
                data += chunk
        
        frame = data[:payload_size]
        data = data[payload_size:]
        frame = zlib.decompress(frame)
        frame = pickle.loads(frame)
        
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        cv2.imshow("Received image", frame)
        cv2.waitKey(1)

def main():
    host = "localhost"
    port = 12345

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)
    
    while True:
        conn, addr = sock.accept()
        print("main(): client connected: address: {0}, client: {1}"
              .format(conn, addr))
        
        receive_image(conn, addr)
        
        cv2.destroyAllWindows()
        conn.close()
        
if __name__ == "__main__":
    main()
    