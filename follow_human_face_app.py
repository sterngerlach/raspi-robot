#!/usr/bin/env python3
# coding: utf-8
# follow_human_face_app.py

import queue
import time

from robot_lib.node_manager import NodeManager

class FollowHumanFaceApp(object):
    """
    人の顔を追跡するアプリケーションのクラス
    """

    def __init__(self):
        """コンストラクタ"""

        # ロボットの各種設定
        self.__config = {
            "enable_motor": True,
            "enable_servo": False,
            "enable_srf02": True,
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_webcam": True,
            "motor": {},
            "srf02": {
                "near_obstacle_threshold": 15,
                "interval": 0.25,
                "addr_list": [0x70]
            },
            "julius": {},
            "openjtalk": {},
            "webcam": {}
        }

        # ロボットのモジュールの管理クラスを初期化
        self.__node_manager = NodeManager(self.__config)
        self.__msg_queue = self.__node_manager.get_msg_queue()
        self.__webcam_state = self.__node_manager.get_node_state("webcam")
        self.__webcam_capture_width = self.__webcam_state["capture_width"]
        self.__webcam_capture_height = self.__webcam_state["capture_height"]
        self.__motor_node = self.__node_manager.get_node("motor")
        self.__openjtalk_node = self.__node_manager.get_node("openjtalk")

    def run(self):
        # ノードの実行を開始
        self.__node_manager.run_nodes()

        # モータが命令を実行中かどうか
        self.__is_motor_executing = False

        # アプリケーションを終了するかどうか
        self.__app_exit = False

        try:
            while True:
                if not self.__msg_queue.empty():
                    try:
                        # ノードからアプリケーションへのメッセージを取得
                        msg = self.__msg_queue.get_nowait()
                        # メッセージを処理
                        self.__handle_msg(msg)
                    except queue.Empty:
                        pass

                # アプリケーションを終了
                if self.__app_exit:
                    self.__talk("じゃあね")
                    self.__openjtalk_node.wait_until_all_command_done()
                    break

                # モータが命令を実行中である場合は顔検出を行わない
                if self.__is_motor_executing:
                    time.sleep(0.1)
                    continue

                # 検出された顔を元にモータへの命令を決定
                faces = self.__webcam_state["faces"]

                if faces is None:
                    # 適当な時間だけ待機
                    time.sleep(0.1)
                    continue

                # 最初に検出された顔の座標を取得
                face_x, face_y, face_w, face_h = faces[0]
                center_x = face_x + face_w / 2
                center_y = face_y + face_h / 2
                
                # キャプチャされた画像内の顔の中心位置によって進行方向を決定
                if center_x < self.__webcam_capture_width / 3:
                    self.__talk("左に曲がります")
                    self.__send_motor_command(
                        { "command": "accel-right", "speed": 12000, "wait_time": 0.06 })
                    self.__send_motor_command(
                        { "command": "brake-right", "speed": 9000, "wait_time": 0.06 })
                else if center_x > self.__webcam_capture_width / 3 * 2:
                    self.__talk("右に曲がります")
                    self.__send_motor_command(
                        { "command": "accel-left", "speed": 12000, "wait_time": 0.06 })
                    self.__send_motor_command(
                        { "command": "brake-left", "speed": 9000, "wait_time": 0.06 })
                else:
                    self.__talk("直進します")
                    self.__send_motor_command(
                        { "command": "accel", "speed": 9000, "wait_time": 0.02 })

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("FollowHumanFaceApp::run(): KeyboardInterrupt occurred")

    def __handle_msg(self, msg):
        """ノードからアプリケーションへのメッセージを処理"""
        if msg["sender"] == "motor":
            # モータからのメッセージを処理
            self.__handle_motor_msg(msg["content"])
        elif msg["sender"] == "srf02":
            # 超音波センサからのメッセージを処理
            self.__handle_srf02_msg(msg["content"])
        elif msg["sender"] == "julius":
            # 音声認識エンジンJuliusからのメッセージを処理
            self.__handle_julius_msg(msg["content"])

    def __talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.__node_manager.send_command("openjtalk", { "sentence": sentence })

    def __send_motor_command(self, cmd):
        """モータに指定された命令を送信"""
        self.__node_manager.send_command("motor", cmd)

    def __handle_motor_msg(self, msg_content):
        """モータからのメッセージを処理"""

        if msg_content["state"] == "start":
            # モータは命令を実行中である
            self.__is_motor_executing = True
        elif msg_content["state"] == "done":
            # ロボットはまだ左右に曲がっている途中
            if msg_content["command"] == "accel-right" or \
                msg_content["command"] == "accel-left":
                # モータは命令を実行中である
                self.__is_motor_executing = True
            else:
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
            self.__talk("ぶつかる")

            # モータは命令を実行中でない
            self.__is_motor_executing = False

            # モータのノードを再実行
            self.__motor_node.run()

    def __handle_julius_msg(self, msg_content):
        """音声認識エンジンJuliusからのメッセージを処理"""

        # モータが命令を実行中であれば無視
        if self.__is_motor_executing:
            self.__talk("今は無理です")
            return

        # 認識語彙が命令ではない場合は無視
        if "command" not in msg_content:
            return

        # 認識語彙と認識精度を取得
        command = msg_content["command"][0]
        command_accuracy = msg_content["command"][1]

        # 認識精度が低い場合は無視
        if command_accuracy < 0.95:
            return

        # 認識語彙に応じてモータに命令を送信
        if command == "ストップ":
            # モータを停止
            self.__send_motor_command({ "command": "stop" })
        elif command == "黙れ":
            # モータの利用を停止
            self.__send_motor_command({ "command": "end" })
        else:
            self.__talk("えっ、何?")

def main():
    # アプリケーションのインスタンスを作成
    app = FollowHumanFaceApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

