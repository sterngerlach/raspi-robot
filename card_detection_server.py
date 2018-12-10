#!/usr/bin/env python3
# coding: utf-8
# card_detection_server.py

import cv2
import os
import sys
import pickle
import socket
import struct
import time
import zlib

def process_image(sock, addr):
    # 画像のサイズを受信
    msg_size = struct.calcsize("!i")

    # 画像の横幅を受信
    recv_data = sock.recv(msg_size)
    frame_width = struct.unpack("!i", recv_data)[0]
    send_data = struct.pack("!i", 123)
    sock.sendall(send_data)
    print("process_image(): frame width: {0}".format(frame_width))

    # 画像の縦幅を受信
    recv_data = sock.recv(msg_size)
    frame_height = struct.unpack("!i", recv_data)[0]
    send_data = struct.pack("!i", 456)
    sock.sendall(send_data)
    print("process_image(): frame height: {0}".format(frame_height))

    while True:
        # 画像のサイズを受信
        msg_header_size = struct.calcsize("!L")
        recv_data = sock.recv(msg_header_size)
        frame_size = struct.unpack("!L", recv_data)
        print("process_image(): frame size: {0}".format(frame_size))

        # 画像を受信
        frame_data = sock.recv(frame_size)
        print("process_image(): image received (shape: {0})".format(frame_data.shape))

        # 画像を検出
        
        # 検出されたカードの枚数を送信
        cards_num = 2
        sock.sendall(struct.pack("!i", cards_num))
        recv_data = sock.recv(msg_size)
        recv_data = struct.unpack("!i", recv_data)[0]
        print("process_image(): magic value received: {0}".format(recv_data))

        # 検出されたカードの数字を送信
        for i in range(cards_num):
            sock.sendall(struct.pack("!i", i))
            recv_data = sock.recv(msg_size)
            recv_data = struct.unpack("!i", recv_data)[0]
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

        process_image(conn, addr)

        cv2.destroyAllWindows()
        conn.close()

if __name__ == "__main__":
    main()

