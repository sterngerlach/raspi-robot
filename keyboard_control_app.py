#!/usr/bin/env python3
# coding: utf-8
# keyboard_control_app.py

import os
import queue
import sys
import threading
import time

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot_lib"))

from robot_lib.node_manager import NodeManager

class KeyboardControlApp(object):
    """
    ロボットをキーボード入力で操作するアプリケーションのクラス
    """

    def __init__(self):
        """コンストラクタ"""

        # ロボットの各種設定
        self.__config = {
            "enable_motor": True,
            "enable_servo": True,
            "enable_srf02": True,
            "enable_julius": False,
            "enable_openjtalk": True,
            "enable_speechapi": True,
            "enable_webcam": True,
            "motor": {},
            "servo": {},
            "srf02": {
                "near_obstacle_threshold": 15,
                "interval": 0.25,
                "addr_list": [0x70]
            },
            "openjtalk": {},
            "speechapi": {},
            "webcam": {}
        }

        # ロボットのモジュールの管理クラスを初期化
        self.__node_manager = NodeManager(self.__config)
        self.__msg_queue = self.__node_manager.get_msg_queue()
        self.__motor_node = self.__node_manager.get_node("motor")
        self.__servo_motor_node = self.__node_manager.get_node("servo0")
        self.__srf02_state = self.__node_manager.get_node_state("srf02")

    def __talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.__node_manager.send_command("openjtalk", { "sentence": sentence })

    def __send_motor_command(self, cmd):
        """モータに指定された命令を送信"""
        self.__node_manager.send_command("motor", cmd)

    def run(self):
        # ノードの実行を開始
        self.__node_manager.run_nodes()

        # モータが命令を実行中かどうか
        self.__is_motor_executing = False

        # ロック
        self.__lock = threading.Lock()
        
        # スレッドを開始
        msg_thread = threading.Thread(target=self.__handle_msg, args=())
        msg_thread.setDaemon(True)
        msg_thread.start()

        keyboard_input_thread = threading.Thread(target=self.__handle_keyboard_input, args=())
        keyboard_input_thread.setDaemon(True)
        keyboard_input_thread.start()
        
        # スレッドの終了を待機(Ctrl-Cで終了)
        msg_thread.join()
        keyboard_input_thread.join()
            
    def __handle_msg(self):
        """ノードからアプリケーションに届くメッセージの処理"""
        try:
            while True:
                if not self.__msg_queue.empty():
                    try:
                        # 各ノードからアプリケーションへのメッセージを取得
                        msg = self.__msg_queue.get_nowait()

                        # メッセージを表示
                        with self.__lock:
                            print("message from {0}: {1}".format(msg["sender"], msg["content"]))
                    except queue.Empty:
                        time.sleep(0.1)
                        continue
                else:
                    time.sleep(0.1)
                    continue
                
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            with self.__lock:
                print("KeyboardControlApp::__handle_msg(): KeyboardInterrupt occurred")

    def __handle_keyboard_input(self):
        """キーボード入力を処理"""
        try:
            while True:
                # コマンドを入力
                input_cmd = input("> ")

                if len(input_cmd) == 0:
                    with self.__lock:
                        print("available commands: \n" +
                              "accel, brake, brake-left, brake-right, " +
                              "stop, end, rotate-left, rotate-right, cancel, " +
                              "cream, srf02, talk")
                    continue

                commands = input_cmd.split()
                command = commands[0]
                
                # 入力されたコマンドに応じて命令を送信
                if command == "accel":
                    self.__send_motor_command(
                        { "command": "accel", "speed": 9000, "wait_time": 0.2 })
                elif command == "brake":
                    self.__send_motor_command(
                        { "command": "brake", "speed": 0, "wait_time": 0.2 })
                elif command == "brake-left":
                    self.__send_motor_command(
                        { "command": "brake-left", "speed": 3000, "wait_time": 0.06 })
                elif command == "brake-right":
                    self.__send_motor_command(
                        { "command": "brake-right", "speed": 3000, "wait_time": 0.06 })
                elif command == "stop":
                    self.__send_motor_command({ "command": "stop" })
                elif command == "end":
                    self.__send_motor_command({ "command": "end" })
                elif command == "rotate-left":
                    self.__send_motor_command(
                        { "command": "rotate", "direction": "left" })
                elif command == "rotate-right":
                    self.__send_motor_command(
                        { "command": "rotate", "direction": "right" })
                elif command == "cancel":
                    self.__motor_node.terminate()
                    self.__motor_node.stop()
                    self.__motor_node.run()
                elif command == "cream":
                    self.__node_manager.send_command("servo0", { "angle": 180 })
                    time.sleep(3)
                    self.__node_manager.send_command("servo0", { "angle": 0 })
                    time.sleep(3)
                elif command == "srf02":
                    print("srf02({0}): dist: {1} cm, mindist: {2} cm, near: {3}"
                          .format(self.__srf02_state[0x70]["dist"],
                                  self.__srf02_state[0x70]["mindist"],
                                  self.__srf02_state[0x70]["near"]))
                elif command == "talk":
                    if len(commands) < 2:
                        with self.__lock:
                            print("talk usage: talk <sentence>")
                        continue

                    self.__talk(commands[1])
                else:
                    with self.__lock:
                        print("available commands: \n" +
                              "accel, brake, brake-left, brake-right, " +
                              "stop, end, rotate-left, rotate-right, cancel, " +
                              "cream, srf02, talk")

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            with self.__lock:
                print("KeyboardControlApp::__handle_keyboard_input(): KeyboardInterrupt occurred")

def main():
    # アプリケーションのインスタンスを作成
    app = KeyboardControlApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

