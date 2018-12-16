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
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_speechapi": False,
            "enable_webcam": False,
            "enable_card": True,
            "motor": {},
            "servo": {},
            "srf02": {
                "distance_threshold": 15,
                "near_obstacle_threshold": 10,
                "interval": 0.25,
                "addr_list": [0x70]
            },
            "openjtalk": {},
            "julius": {},
            "speechapi": {},
            "webcam": {
                "camera_id": 0,
                "interval": 2.0,
                "frame_width": 320,
                "frame_height": 240
            },
            "card": {
                "server_host": sys.argv[1],
                "camera_id": 0,
                "frame_width": 640,
                "frame_height": 480
            }
        }

        # ロボットのモジュールの管理クラスを初期化
        self.__node_manager = NodeManager(self.__config)
        self.__msg_queue = self.__node_manager.get_msg_queue()
        self.__motor_node = self.__node_manager.get_node("motor")
        self.__servo_motor_node = self.__node_manager.get_node("servo")
        self.__srf02_state = self.__node_manager.get_node_state("srf02")

    def __talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.__node_manager.send_command("openjtalk", { "sentence": sentence })

    def __aplay(self, file_name):
        """指定された音声ファイルを再生"""
        self.__node_manager.send_command("openjtalk", { "file_name": file_name })

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
    
    def __print_available_commands(self):
        with self.__lock:
            print("available commands: \n" +
                  "set-speed, set-left-speed, set-right-speed, " +
                  "set-speed-imm, set-left-speed-imm, set-right-speed-imm, " +
                  "move-distance, rotate0, rotate1, rotate2, " +
                  "pivot-turn, spin-turn, wait, stop, end, " +
                  "cancel, cream, srf02, talk, aplay, detect")

    def __print_set_speed_usage(self):
        with self.__lock:
            print("set-speed usage: " +
                  "talk <speed-left> <speed-right> <step-left> <step-right> <wait-time>")

    def __print_set_left_speed_usage(self):
        with self.__lock:
            print("set-left-speed usage: " +
                  "set-left-speed <speed> <step> <wait-time>")
    
    def __print_set_right_speed_usage(self):
        with self.__lock:
            print("set-right-speed usage: " +
                  "set-right-speed <speed> <step> <wait-time>")

    def __print_set_speed_imm_usage(self):
        with self.__lock:
            print("set-speed-imm usage: " +
                  "set-speed-imm <speed-left> <speed-right>")
    
    def __print_set_left_speed_imm_usage(self):
        with self.__lock:
            print("set-left-speed-imm usage: set-left-speed-imm <speed>")

    def __print_set_right_speed_imm_usage(self):
        with self.__lock:
            print("set-right-speed-imm usage: set-right-speed-imm <speed>")
    
    def __print_move_distance_usage(self):
        with self.__lock:
            print("move-distance usage: move-distance <distance>")

    def __print_rotate0_usage(self):
        with self.__lock:
            print("rotate0 usage: " +
                  "rotate0 <center-velocity> <turning-radius> <turning-angle>")

    def __print_rotate1_usage(self):
        with self.__lock:
            print("rotate1 usage: " +
                  "rotate1 <center-velocity> <turning-angle> <rotate-time>")

    def __print_rotate2_usage(self):
        with self.__lock:
            print("rotate2 usage: rotate2 <turning-angle>")
    
    def __print_pivot_turn_usage(self):
        with self.__lock:
            print("pivot-turn usage: pivot-turn <turning-angle> <rotate-time>")

    def __print_spin_turn_usage(self):
        with self.__lock:
            print("spin-turn usage: spin-turn <turning-angle> <rotate-time>")

    def __print_wait_usage(self):
        with self.__lock:
            print("wait usage: wait <seconds>")
    
    def __print_talk_usage(self):
        with self.__lock:
            print("talk usage: talk <sentence>")

    def __print_aplay_usage(self):
        with self.__lock:
            print("aplay usage: aplay <file-name>")

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
                    self.__print_available_commands()
                    continue

                commands = input_cmd.split()
                command = commands[0]
                
                # 入力されたコマンドに応じて命令を送信
                if command == "set-speed":
                    if len(commands) != 6:
                        self.__print_set_speed_usage()
                    else:
                        self.__send_motor_command({
                            "command": "set-speed",
                            "speed_left": int(commands[1]),
                            "speed_right": int(commands[2]),
                            "step_left": int(commands[3]),
                            "step_right": int(commands[4]),
                            "wait_time": float(commands[5])
                        })
                elif command == "set-left-speed":
                    if len(commands) != 4:
                        self.__print_set_left_speed_usage()
                    else:
                        self.__send_motor_command({
                            "command": "set-left-speed",
                            "speed": int(commands[1]),
                            "step": int(commands[2]),
                            "wait_time": float(commands[3])
                        })
                elif command == "set-right-speed":
                    if len(commands) != 4:
                        self.__print_set_right_speed_usage()
                    else:
                        self.__send_motor_command({
                            "command": "set-right-speed",
                            "speed": int(commands[1]),
                            "step": int(commands[2]),
                            "wait_time": float(commands[3])
                        })
                elif command == "set-speed-imm":
                    if len(commands) != 3:
                        self.__print_set_speed_imm_usage()
                    else:
                        self.__send_motor_command({
                            "command": "set-speed-imm",
                            "speed_left": int(commands[1]),
                            "speed_right": int(commands[2])
                        })
                elif command == "set-left-speed-imm":
                    if len(commands) != 2:
                        self.__print_set_left_speed_imm_usage()
                    else:
                        self.__send_motor_command({
                            "command": "set-left-speed-imm",
                            "speed": int(commands[1])
                        })
                elif command == "set-right-speed-imm":
                    if len(commands) != 2:
                        self.__print_set_right_speed_imm_usage()
                    else:
                        self.__send_motor_command({
                            "command": "set-right-speed-imm",
                            "speed": int(commands[1])
                        })
                elif command == "move-distance":
                    if len(commands) != 2:
                        self.__print_move_distance_usage()
                    else:
                        self.__send_motor_command({
                            "command": "move-distance",
                            "distance": int(commands[1])
                        })
                elif command == "rotate0":
                    if len(commands) != 4:
                        self.__print_rotate0_usage()
                    else:
                        self.__send_motor_command({
                            "command": "rotate0",
                            "center_velocity": float(commands[1]),
                            "turning_radius": float(commands[2]),
                            "turning_angle": float(commands[3])
                        })
                elif command == "rotate1":
                    if len(commands) != 4:
                        self.__print_rotate1_usage()
                    else:
                        self.__send_motor_command({
                            "command": "rotate1",
                            "center_velocity": float(commands[1]),
                            "turning_angle": float(commands[2]),
                            "rotate_time": float(commands[3])
                        })
                elif command == "rotate2":
                    if len(commands) != 2:
                        self.__print_rotate2_usage()
                    else:
                        self.__send_motor_command({
                            "command": "rotate2",
                            "turning_angle": float(commands[1])
                        })
                elif command == "pivot-turn":
                    if len(commands) != 3:
                        self.__print_pivot_turn_usage()
                    else:
                        self.__send_motor_command({
                            "command": "pivot-turn",
                            "turning_angle": float(commands[1]),
                            "rotate_time": float(commands[2])
                        })
                elif command == "spin-turn":
                    if len(commands) != 3:
                        self.__print_spin_turn_usage()
                    else:
                        self.__send_motor_command({
                            "command": "spin-turn",
                            "turning_angle": float(commands[1]),
                            "rotate_time": float(commands[2])
                        })
                elif command == "wait":
                    if len(commands) != 2:
                        self.__print_wait_usage()
                    else:
                        self.__send_motor_command({
                            "command": "wait",
                            "seconds": float(commands[1])
                        })
                elif command == "stop":
                    self.__send_motor_command({ "command": "stop" })
                elif command == "end":
                    self.__send_motor_command({ "command": "end" })
                elif command == "cancel":
                    self.__motor_node.terminate()
                    self.__motor_node.stop()
                    self.__motor_node.run()
                elif command == "cream":
                    self.__node_manager.send_command("servo", { "angle": 180 })
                    time.sleep(3)
                    self.__node_manager.send_command("servo", { "angle": 0 })
                    time.sleep(3)
                elif command == "srf02":
                    print("srf02({0}): dist: {1} cm, mindist: {2} cm, near: {3}"
                          .format(0x70,
                                  self.__srf02_state[0x70]["dist"],
                                  self.__srf02_state[0x70]["mindist"],
                                  self.__srf02_state[0x70]["near"]))
                elif command == "talk":
                    if len(commands) < 2:
                        self.__print_talk_usage()
                    else:
                        self.__talk(commands[1])
                elif command == "aplay":
                    if len(commands) < 2:
                        self.__print_aplay_usage()
                    else:
                        self.__aplay(commands[1])
                elif command == "detect":
                    self.__node_manager.send_command("card", { "command": "detect" })
                else:
                    self.__print_available_commands()

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

