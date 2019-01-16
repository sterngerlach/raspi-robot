# coding: utf-8
# card_detection_node.py

import cv2
import multiprocessing as mp
import os
import pathlib
import pickle
import socket
import struct
import subprocess as sp
import time
import zlib

from command_receiver_node import CommandReceiverNode, UnknownCommandException

class CardDetectionNode(CommandReceiverNode):
    """
    トランプのカードを検出するクラス
    """

    # 検出サーバとの通信で使用するポート番号
    SERVER_PORT = 12345
    
    def __init__(self, process_manager, msg_queue, server_host,
                 camera_id, frame_width, frame_height):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # 検出サーバのIPアドレスまたはホスト名
        self.server_host = server_host
        # TCPソケットを作成
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TIME_WAIT状態のポートをbindできるように設定
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

        # 検出サーバに接続
        self.client_socket.connect((self.server_host, CardDetectionNode.SERVER_PORT))

        print("CardDetectionNode::__init__(): " +
              "connected to card detection server (host: {0}, port: {1})"
              .format(self.server_host, CardDetectionNode.SERVER_PORT))

        # ビデオ撮影デバイスの作成
        self.camera_id = camera_id
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # ビデオ撮影デバイスのパラメータの設定
        self.video_capture = cv2.VideoCapture(camera_id)
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

        # キャプチャする画像のサイズを送信
        msg_size = struct.calcsize("!I")
        
        # キャプチャする画像の横幅を送信
        send_data = struct.pack("!I", self.frame_width)
        self.client_socket.sendall(send_data)
        recv_data = self.client_socket.recv(msg_size)
        recv_data = struct.unpack("!I", recv_data)[0]
        print("CardDetectionNode::__init__(): magic value received: {0}".format(recv_data))
        
        # キャプチャする画像の縦幅を送信
        send_data = struct.pack("!I", self.frame_height)
        self.client_socket.sendall(send_data)
        recv_data = self.client_socket.recv(msg_size)
        recv_data = struct.unpack("!I", recv_data)[0]
        print("CardDetectionNode::__init__(): magic value received: {0}".format(recv_data))

    def __del__(self):
        """デストラクタ"""

        # ビデオ撮影デバイスの解放
        self.video_capture.release()

    def process_command(self):
        """カードの検出命令を処理"""

        try:
            while True:
                # カードの検出命令をキューから取り出し
                cmd = self.command_queue.get()
                print("CardDetectionNode::process_command(): command received: {0}".format(cmd))

                # 命令でない場合は例外をスロー
                if "command" not in cmd:
                    raise UnknownCommandException(
                        "CardDetectionNode::process_command(): unknown command: {0}"
                        .format(cmd))

                if cmd["command"] == "detect":
                    # 命令の実行開始をアプリケーションに伝達
                    self.send_message("card", { "command": cmd["command"], "state": "start" })

                    # カードの検出を実行
                    try:
                        cards = self.detect()

                        print("CardDetectionNode::process_command(): number of cards detected: {0}"
                              .format(len(cards)))

                        # 検出結果をアプリケーションに伝達
                        self.send_message("card",
                            { "command": cmd["command"], "state": "detected", "cards": cards })
                    except Exception as e:
                        print("CardDetectionNode::process_command(): exception occurred: {}"
                              .format(e))

                        # 命令の無視をアプリケーションに伝達
                        self.send_message("card", { "command": cmd["command"], "state": "ignored" })
                else:
                    # 解釈できない命令の無視をアプリケーションに伝達
                    self.send_message("card", { "command": cmd["command"], "state": "ignored" })
                
                # 命令の実行を完了
                self.command_queue.task_done()
        
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("CardDetectionNode::process_command(): KeyboardInterrupt occurred")
    
    def detect(self):
        """カードの検出"""

        # 画像データを読み捨て
        ret, frame0 = self.video_capture.read()

        # 画像データを作成
        ret, frame = self.video_capture.read()

        # 画像がキャプチャできなかった場合はエラー
        if frame is None:
            if frame0 is not None:
                frame = frame0
            else
                return []

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ret, frame = cv2.imencode(".png", frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 5])
        frame_data = pickle.dumps(frame)
        frame_data = zlib.compress(frame_data)
        frame_size = len(frame_data)
        
        # 画像データを送信
        self.client_socket.sendall(struct.pack("!I", frame_size) + frame_data)

        # 検出されたカードの枚数を取得
        msg_size = struct.calcsize("!I")
        recv_data = self.client_socket.recv(msg_size)
        cards_num = struct.unpack("!I", recv_data)[0]
        self.client_socket.sendall(struct.pack("!I", 789))

        # 検出されたカードの数字を取得
        cards = []

        for i in range(cards_num):
            recv_data = self.client_socket.recv(msg_size)
            card_num = struct.unpack("!I", recv_data)[0]
            cards.append(card_num)
            self.client_socket.sendall(struct.pack("!I", 789))

        return cards

