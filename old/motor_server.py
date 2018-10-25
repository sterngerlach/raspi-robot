# coding: utf-8
# motor_server.py

import pickle
import socket
import threading

from motor_l6470 import *
from motor_controller import *
from motor_command import *

class MotorServer(object):
    """
    モータの操作命令を待ち受けるサーバのクラス
    """

    # サーバのIPアドレスまたはホスト名
    MOTOR_SERVER_HOST = "127.0.0.1"

    # サーバが使用するポート番号
    MOTOR_SERVER_PORT = 12345

    def __init__(self, host, port):
        """コンストラクタ"""
        self.host = host
        self.port = port
        
        # モータの初期化
        self.motor0 = MotorL6470(0)
        self.motor1 = MotorL6470(1)
        self.motor_controller = MotorController(self.motor0, self.motor1)

    def run(self):
        """サーバの動作開始"""

        # TCP/IPでIPv4のソケットを作成
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        # TIME_WAIT状態のポートをbindできるように設定
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

        # 作成したソケットをアドレスにbind
        self.server_socket.bind((self.host, self.port))

        # 作成したソケットでlisten
        self.server_socket.listen(5)

        while True:
            # クライアントからの接続を受け付ける
            client_socket, (client_address, client_port) = \
                self.server_socket.accept()
            print("MotorServer::run(): client connected: " +
                  "address: {0}, port: {1}"
                  .format(client_address, client_port))

            # クライアントからの要求を処理するスレッドを作成
            client_thread = threading.Thread(
                target=self.client_handler,
                args=(client_socket, client_address, client_port))
            
            # 作成したスレッドをデーモンスレッドに設定
            # メインスレッドが終了したときにスレッドを終了させる
            client_thread.daemon = True

            # 作成したスレッドを起動
            client_thread.start()
                    
        return
    
    def client_handler(self, client_socket, client_address, client_port):
        """クライアントからの要求の処理"""
        
        # クライアントからデータを受信
        while True:
            try:
                data_recv = b""

                while True:
                    data_chunk = client_socket.recv(16)
                    if not data_chunk:
                        break
                    data_recv += data_chunk
            except Exception:
                break
            
            print("MotorServer::client_handler(): " +
                  "received data chunk from client: {0}"
                  .format(data_recv))

            # バイト列をモータへの命令オブジェクトに変換
            motor_cmd = pickle.loads(data_recv)

            print("MotorServer::client_handler(): " +
                  "command received: {0}"
                  .format(motor_cmd.command))

            # モータへの命令を解釈して実行
            self.motor_controller.execute_command(motor_cmd)
            
            # クライアントのソケットをclose
            client_socket.close()
            print("MotorServer::client_handler(): " +
                  "client disconnected: address: {0}, port: {1}"
                  .format(client_address, client_port))

        return

