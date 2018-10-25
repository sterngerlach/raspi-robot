# coding: utf-8
# motor_client_test.py

import pickle
import socket
import time

from motor_command import *

HOST = "127.0.0.1"
PORT = 12345

def main():
    # TCP/IPでIPv4のソケットを作成
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TIME_WAIT状態のポートをbindできるように設定
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    # 作成したソケットをアドレスにbind
    sock.connect((HOST, PORT))

    # モータのコマンドオブジェクトを作成
    motor_cmd = MotorCommand("accel", { "speed": 30000, "slope": 3.0 })
    # モータへの命令オブジェクトをバイト列に変換
    motor_cmd = pickle.dumps(motor_cmd)

    # サーバにモータへの命令を送信
    sock.send(motor_cmd)

    # ソケットをclose
    sock.close()

    time.sleep(30)

    # TCP/IPでIPv4のソケットを作成
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TIME_WAIT状態のポートをbindできるように設定
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    # 作成したソケットをアドレスにbind
    sock.connect((HOST, PORT))

    # モータのコマンドオブジェクトを作成
    motor_cmd = MotorCommand("brake", { "speed": 0, "slope": 1.0 })
    # モータへの命令オブジェクトをバイト列に変換
    motor_cmd = pickle.dumps(motor_cmd)

    # サーバにモータへの命令を送信
    sock.send(motor_cmd)

    # ソケットをclose
    sock.close()

if __name__ == "__main__":
    main()

