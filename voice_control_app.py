#!/usr/bin/env python3
# coding: utf-8
# voice_control_app.py

import os
import queue
import sys
import time

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot_lib"))

from robot_lib.node_manager import NodeManager

class VoiceControlApp(object):
    """
    ロボットを音声で操作するアプリケーションのクラス
    """
    
    def __init__(self):
        """コンストラクタ"""

        # ロボットの各種設定
        self.__config = {
            "enable_motor": True,
            "enable_servo": False,
            "enable_srf02": False,
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_speechapi": False,
            "enable_webcam": False,
            "enable_card": False,
            "enable_motion": False,
            "enable_face": False,
            "motor": {},
            "srf02": {
                "distance_threshold": 15,
                "near_obstacle_threshold": 10,
                "interval": 5,
                "addr_list": [0x70]
            },
            "julius": {},
            "openjtalk": {}
        }
        
        # ロボットのモジュールの管理クラスを初期化
        self.__node_manager = NodeManager(self.__config)
        self.__msg_queue = self.__node_manager.get_msg_queue()
        self.__openjtalk_node = self.__node_manager.get_node("openjtalk")
        self.__motor_node = self.__node_manager.get_node("motor")

    def run(self):
        # ノードの実行を開始
        self.__node_manager.run_nodes()

        # モータが命令を実行中かどうか
        self.__is_motor_executing = False

        # アプリケーションを終了するかどうか
        self.__app_exit = False
        
        # 受信したメッセージ
        msg = None

        try:
            while True:
                # ノードからアプリケーションへのメッセージを取得
                # get()メソッドを使用するとデッドロックが発生する可能性があるため
                # get_nowait()メソッドを使用
                if not self.__msg_queue.empty():
                    try:
                        # empty()メソッドがFalseを返しても実際には空である可能性があり,
                        # キューが空であったときにget_nowait()メソッドを呼び出すと
                        # queue.Empty例外がスローされるため, これを捕捉する必要がある
                        msg = self.__msg_queue.get_nowait()
                    except queue.Empty:
                        # 適当な時間だけ待機
                        time.sleep(0.1)
                        continue
                else:
                    # 適当な時間だけ待機
                    time.sleep(0.1)
                    continue

                if msg["sender"] == "motor":
                    # モータからのメッセージを処理
                    self.__handle_motor_msg(msg["content"])
                elif msg["sender"] == "julius":
                    # 音声認識エンジンJuliusからのメッセージを処理
                    self.__handle_julius_msg(msg["content"])
                elif msg["sender"] == "srf02":
                    # 超音波センサからのメッセージを処理
                    self.__handle_srf02_msg(msg["content"])
                
                # アプリケーションを終了
                if self.__app_exit:
                    self.__aplay("bye.wav")
                    break
                    
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("VoiceControlApp::run(): KeyboardInterrupt occurred")

    def __talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.__node_manager.send_command("openjtalk", { "sentence": sentence })

    def __aplay(self, file_name):
        """指定された音声ファイルを再生"""
        self.__node_manager.send_command("openjtalk", { "file_name": file_name })

    def __send_motor_command(self, cmd):
        """モータに指定された命令を送信"""
        self.__node_manager.send_command("motor", cmd)

    def __handle_motor_msg(self, msg_content):
        """モータからのメッセージを処理"""
        if msg_content["state"] == "start":
            # モータは命令を実行中である
            self.__is_motor_executing = True
        elif msg_content["state"] == "ignored":
            # モータは命令を実行中でない
            self.__is_motor_executing = False
        elif msg_content["state"] == "done":
            # モータは命令を実行中でない
            self.__is_motor_executing = False

            # モータの使用を終了した場合はアプリケーションも終了
            if msg_content["command"] == "end":
                self.__app_exit = True

    def __handle_srf02_msg(self, msg_content):
        """超音波センサからのメッセージを処理"""

        # 障害物を検知した場合は緊急停止
        if msg_content["state"] == "obstacle-detected":
            # モータを緊急停止
            self.__motor_node.terminate()
            self.__motor_node.stop()
            
            # 障害物を検知したことをユーザに知らせる
            self.__aplay("obstacle-detected.wav")

            # モータは命令を実行中でない
            self.__is_motor_executing = False

            # モータのノードを再実行
            self.__motor_node.run()

    def __handle_julius_msg(self, msg_content):
        """音声認識エンジンJuliusからのメッセージを処理"""

        # モータが命令を実行中であれば無視
        if self.__is_motor_executing:
            self.__aplay("wait-a-moment.wav")
            return

        # 認識語彙が命令ではない場合は無視
        if "command" not in msg_content:
            self.__aplay("unknown-command.wav")
            return

        # 認識語彙と認識精度を取得
        command = msg_content["command"][0]
        command_accuracy = msg_content["command"][1]

        # 認識精度が低い場合は無視
        if command_accuracy < 0.95:
            self.__aplay("unknown-command.wav")
            return

        # 認識した語彙に応じてモータに命令を送信
        if command == "進め":
            # モータに命令を送信
            self.__send_motor_command({
                "command": "set-speed", "speed_left": 9000, "speed_right": 9000,
                "step_left": 150, "step_right": 150, "wait_time": 0.05 })
        elif command == "ブレーキ":
            # モータに命令を送信
            self.__send_motor_command({
                "command": "set-speed", "speed_left": 0, "speed_right": 0,
                "step_left": 150, "step_right": 150, "wait_time": 0.05 })
        elif command == "ストップ":
            # モータに命令を送信
            self.__send_motor_command({ "command": "stop" })
        elif command == "黙れ":
            # モータに命令を送信
            self.__send_motor_command({ "command": "end" })
        elif command == "曲がれ":
            # 方向の語彙と認識精度を取得
            direction = msg_content["direction"][0]
            direction_accuracy = msg_content["direction"][1]

            # 方向の語彙の認識精度が低い場合は無視
            if direction_accuracy < 0.95:
                self.__aplay("unknown-direction.wav")
                return

            # 指定された方向に曲がる
            if direction == "左":
                self.__send_motor_command({
                    "command": "rotate1", "center_velocity": 15,
                    "turning_angle": 90, "rotate_time": 3.0 })
            elif direction == "右":
                self.__send_motor_command({
                    "command": "rotate1", "center_velocity": 15,
                    "turning_angle": -90, "rotate_time": 3.0 })
            else:
                # 方向の語彙でない場合は無視
                self.__aplay("unknown-direction.wav")
        else:
            # 命令でない場合は無視
            self.__aplay("unknown-direction.wav")

        return

def main():
    # アプリケーションのインスタンスを作成
    app = VoiceControlApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

