#!/usr/bin/env python3
# coding: utf-8
# daruma_fell_over_app.py

import os
import queue
import random
import sys
import time

from enum import Enum

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot_lib"))

from robot_lib.node_manager import NodeManager

class GameState(Enum):
    """
    ゲーム(だるまさんが転んだ)の状態を表す列挙体
    """

    NONE = 0
    INIT = 1
    ASK_IF_READY = 2
    RULE_DESCRIPTION = 3
    WAIT_A_MOMENT = 4
    SPEAK = 5
    TURN_AROUND = 6
    DETECT_MOTION = 7
    TOUCHED = 8
    RESULT = 9

class DarumaFellOverApp(object):
    """
    ゲーム(だるまさんが転んだ)のアプリケーションのクラス
    """

    def __init__(self):
        """コンストラクタ"""

        # ロボットの各種設定
        self.__config = {
            "enable_motor": True,
            "enable_servo": True,
            "enable_srf02": False,
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_speechapi": False,
            "enable_webcam": False,
            "enable_card": False,
            "enable_motion": True,
            "motor": {},
            "servo": {},
            "openjtalk": {},
            "julius": {}
            "motion": {
                "camera_id": 0,
                "interval": 0.5,
                "frame_width": 640,
                "frame_height": 480,
                "contour_area_min": 750
            }
        }

        # ロボットのモジュールの管理クラスを初期化
        self.__node_manager = NodeManager(self.__config)
    
    def __talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.__node_manager.send_command("openjtalk", { "sentence": sentence })
        self.__openjtalk_node.wait_until_all_command_done()

    def __aplay(self, file_name):
        """指定された音声ファイルを再生"""
        self.__node_manager.send_command("openjtalk", { "file_name": file_name })
        self.__openjtalk_node.wait_until_all_command_done()

    def __send_motor_command(self, cmd):
        """モータに指定された命令を送信"""
        self.__node_manager.send_command("motor", cmd)

    def __detect(self):
        """トランプカードの検出命令を送信"""
        self.__node_manager.send_command("card", { "command": "detect" })
    
    def __input(self):
        """ノードからアプリケーションへのメッセージを処理"""
        while True:
            # ノードからアプリケーションへのメッセージを取得
            if not self.__msg_queue.empty():
                try:
                    msg = self.__msg_queue.get_nowait()

                    # メッセージの処理
                    if msg["sender"] == "julius":
                        self.__handle_julius_msg(msg["content"])
                    elif msg["sender"] == "card":
                        self.__handle_card_msg(msg["content"])
                    elif msg["sender"] == "motion":
                        self.__handle_motion_msg(msg["content"])
                except queue.Empty:
                    return
            else:
                return
        
    def __julius_msg_word_contains(self, recognized_words, word, accuracy_threshold):
        """音声認識エンジンJuliusからのメッセージに指定された語句が含まれるかを判定"""
        return len([recognized_word[0] for recognized_word in recognized_words \
            if recognized_word[0] == word and recognized_word[1] >= accuracy_threshold]) > 0

    def __opponent_said(self, word, accuracy_threshold=0.95):
        return self.__julius_msg_word_contains(self.__julius_result, word, accuracy_threshold)

    def __handle_julius_msg(self, msg_content):
        """音声認識エンジンJuliusからのメッセージを取得"""
        self.__julius_result = msg_content["words"]
    
    def __handle_card_msg(self, msg_content):
        """トランプカードを検出するノードからのメッセージを取得"""
        if msg_content["state"] == "detected":
            self.__card_detection_result = msg_content["cards"]

    def __handle_motion_msg(self, msg_content):
        """人の動きを検出するノードからのメッセージを取得"""
        if msg_content["state"] == "motion-detected":
            self.__motion_detected = True

    def __update(self):
        """ゲームの状態を更新"""
        self.__state_func_table[self.__game_state]()

    def __on_init(self):
        self.__talk("だるまさんが転んだの準備はできましたか")
        self.__game_state = GameState.ASK_IF_READY
        self.__julius_result = None

    def __on_ask_if_ready(self):
        if self.__julius_result is None:
            return

        if self.__opponent_said("はい"):
            self.__game_state = GameState.RULE_DESCRIPTION
        elif self.__opponent_said("まだ"):
            self.__aplay("bye.wav")
            self.__app_exit = True
        else:
            self.__julius_result = None

    def __on_rule_description(self):
        self.__talk("だるまさんが転んだを始めましょう")
        self.__talk("私がもちろん鬼になるので、あなたは離れてくださいね")
        self.__current_time = time.monotonic()
        self.__game_state = GameState.WAIT_A_MOMENT

    def __on_wait_a_moment(self):
        self.__elapsed_time = time.monotonic() - self.__current_time

        if self.__elapsed_time > 5.0:
            self.__talk("準備はできましたね")
            self.__talk("それでは始めましょう")
            self.__game_state = GameState.SPEAK
    
    def __on_speak(self):
        __speech_type = random.randint(0, 4)

        if __speech_type == 0:
            self.__talk("だるまさんがころん、")
        elif __speech_type == 1:
            self.__talk("だ、る、ま、さ、ん、が、こ、ろ、ん、")
        elif __speech_type == 2:
            self.__talk("だーーるーーまーーさーーんーーがーーこーーろーーんーー")
        elif __speech_type == 3:
            self.__talk("だ、る、ま、さ、ん、がころん")
        elif __speech_type == 4:
            self.__talk("だるまさん、が、こ、ろ、ん、")

        if self.__opponent_said("タッチ"):
            self.__game_state = GameState.TOUCHED
            return

        # 適当な時間だけ待つ
        self.__wait_time = random.uniform(0.0, 1.0)
        time.sleep(self.__wait_time)
        
        if self.__opponent_said("タッチ"):
            self.__game_state = GameState.TOUCHED
            return

        self.__talk("だ")

        self.__game_state = GameState.TURN_AROUND

    def __on_turn_around(self):
        if self.__opponent_said("タッチ"):
            self.__game_state = GameState.TOUCHED
            return

        # サーボモータを回転
        self.__node_manager.send_command("servo", { "angle": 90 })
        time.sleep(1.0)

        if self.__opponent_said("タッチ"):
            self.__game_state = GameState.TOUCHED
            self.__node_manager.send_command("servo", { "angle": 0 })
            time.sleep(1.0)
            return
        
        # 人の動きの検出を開始
        self.__node_manager.send_command("motion", { "command": "start" })
        self.__current_time = time.monotonic()
        self.__wait_time = random.uniform(4.0, 8.0)
        self.__game_state = GameState.DETECT_MOTION

    def __on_detect_motion(self):
        self.__elapsed_time = time.monotonic() - self.__current_time
        
        if self.__elapsed_time > self.__wait_time:
            self.__game_state = GameState.SPEAK
            self.__node_manager.send_command("motion", { "command": "end" })
            self.__node_manager.send_command("servo", { "angle": 0 })
            time.sleep(1.0)
            return

        if self.__motion_detected:
            self.__game_state = GameState.RESULT
            self.__pi_win = True
            self.__node_manager.send_command("motion", { "command": "end" })
            self.__node_manager.send_command("servo", { "angle": 0 })
            time.sleep(1.0)
            return

    def __on_touched(self):
        self.__talk("ああ捕まった")
        self.__pi_win = False
        self.__game_state = GameState.RESULT

    def __on_result(self):
        if self.__pi_win:
            self.__talk("私の勝ちです")
        else:
            self.__talk("あなたの勝ちです")
            self.__talk("悔しいなあ")

        self.__app_exit = True
    
    def __run_game(self):
        """ゲームの実行"""
        try:
            while True:
                # 入力を処理
                self.__input()

                # ゲームの状態を更新
                self.__update()
                
                # アプリケーションを終了
                if self.__app_exit:
                    break

                time.sleep(0.5)
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("DarumaFellOverApp::__run_game(): KeyboardInterrupt occurred")

    def run(self):
        # 使用するノードを取得
        self.__msg_queue = self.__node_manager.get_msg_queue()
        self.__openjtalk_node = self.__node_manager.get_node("openjtalk")

        # ノードの実行を開始
        self.__node_manager.run_nodes()

        # プログラムを終了させるかどうか
        self.__app_exit = False

        self.__game_state = GameState.INIT

        self.__julius_result = None
        self.__card_detection_result = None
        self.__motion_detected = False
        self.__pi_win = False

        # 状態と実行される関数のディクショナリ
        self.__state_func_table = {
            GameState.INIT: self.__on_init,
            GameState.ASK_IF_READY: self.__on_ask_if_ready,
            GameState.RULE_DESCRIPTION: self.__on_rule_description,
            GameState.WAIT_A_MOMENT: self.__on_wait_a_moment,
            GameState.SPEAK: self.__on_speak:
            GameState.TURN_AROUND: self.__on_turn_around,
            GameState.DETECT_MOTION: self.__on_detect_motion,
            GameState.TOUCHED: self.__on_touched,
            GameState.RESULT: self.__on_result
        }

        # ゲームを実行
        self.__run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = DarumaFellOverApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

