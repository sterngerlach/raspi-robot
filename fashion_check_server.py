#!/usr/bin/env python3
# coding: utf-8
# fashion_check_server.py

import cv2
import os
import sys
import pickle
import socket
import struct
import time
import zlib

try:
    from fashionSSD import is_fashionable
except ImportError:
    from fashion_ssd_dummy import is_fashionable

def recvall(sock, data_length):
    data = b""

    while len(data) < data_length:
        chunk = sock.recv(data_length - len(data))
        data += chunk

    return data

def process_image(sock, addr):
    # 画像のサイズを受信
    msg_size = struct.calcsize("!I")

    # 画像の横幅を受信
    recv_data = sock.recv(msg_size)
    frame_width = struct.unpack("!I", recv_data)[0]
    sock.sendall(struct.pack("!I", 123))
    print("process_image(): frame width: {0}".format(frame_width))

    # 画像の縦幅を受信
    recv_data = sock.recv(msg_size)
    frame_height = struct.unpack("!I", recv_data)[0]
    sock.sendall(struct.pack("!I", 456))
    print("process_image(): frame height: {0}".format(frame_height))

    while True:
        # 画像のサイズを受信
        recv_data = sock.recv(msg_size)
        frame_size = struct.unpack("!I", recv_data)[0]
        print("process_image(): frame size: {0}".format(frame_size))

        # 画像を受信
        frame_data = recvall(sock, frame_size)
        frame_data = zlib.decompress(frame_data)
        frame_data = pickle.loads(frame_data)
        frame_data = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
        print("process_image(): image received (shape: {0})".format(frame_data.shape))

        # 画像を検出
        check_result = is_fashionable(frame_data)
        
        # 判定結果を送信
        sock.sendall(struct.pack("!I", check_result))
        recv_data = sock.recv(msg_size)
        recv_data = struct.unpack("!I", recv_data)[0]
        print("process_image(): magic value received: {0}".format(recv_data))

def main():
    host = sys.argv[1]
    port = 12345

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.bind((host, port))
    sock.listen(5)

    while True:
        conn, addr = sock.accept()
        print("main(): client connected: address: {0}, client: {1}"
              .format(conn, addr))
        
        try:
            process_image(conn, addr)
        except Exception as e:
            print("main(): exception occurred in process_image(): {}".format(e))

        cv2.destroyAllWindows()
        conn.close()

if __name__ == "__main__":
    main()

