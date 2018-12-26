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
    SPEAK2 = 6
    SPEAK3 = 7
    TURN_AROUND = 8
    DETECT_MOTION = 9
    TOUCHED = 10
    RESULT = 11

class DarumaFellOverApp(object):
    """
    ゲーム(だるまさんが転んだ)のアプリケーションのクラス
    """

    def __init__(self):
        """コンストラクタ"""

        # ロボットの各種設定
        self.config = {
            "enable_motor": True,
            "enable_servo": True,
            "enable_srf02": False,
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_speechapi": False,
            "enable_webcam": False,
            "enable_card": False,
            "enable_motion": True,
            "enable_face": True,
            "motor": {},
            "servo": {},
            "openjtalk": {},
            "julius": {},
            "motion": {
                "camera_id": 0,
                "interval": 0.5,
                "frame_width": 640,
                "frame_height": 480,
                "contour_area_min": 2000
            },
            "face": {
                "window_width": 640,
                "window_height": 480
            }
        }

        # ロボットのモジュールの管理クラスを初期化
        self.node_manager = NodeManager(self.config)
    
    def talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.node_manager.send_command("openjtalk", { "sentence": sentence })
        self.openjtalk_node.wait_until_all_command_done()

    def aplay(self, file_name):
        """指定された音声ファイルを再生"""
        self.node_manager.send_command("openjtalk", { "file_name": file_name })
        self.openjtalk_node.wait_until_all_command_done()

    def send_motor_command(self, cmd):
        """モータに指定された命令を送信"""
        self.node_manager.send_command("motor", cmd)

    def detect(self):
        """トランプカードの検出命令を送信"""
        self.node_manager.send_command("card", { "command": "detect" })
    
    def face(self, file_name):
        """表情の設定"""
        self.node_manager.send_command("face", { "file-name": file_name })
    
    def input(self):
        """ノードからアプリケーションへのメッセージを処理"""
        while True:
            # ノードからアプリケーションへのメッセージを取得
            if not self.msg_queue.empty():
                try:
                    msg = self.msg_queue.get_nowait()

                    # メッセージの処理
                    if msg["sender"] == "julius":
                        self.handle_julius_msg(msg["content"])
                    elif msg["sender"] == "card":
                        self.handle_card_msg(msg["content"])
                    elif msg["sender"] == "motion":
                        self.handle_motion_msg(msg["content"])
                except queue.Empty:
                    return
            else:
                return
        
    def julius_msg_word_contains(self, recognized_words, word, accuracy_threshold):
        """音声認識エンジンJuliusからのメッセージに指定された語句が含まれるかを判定"""
        return len([recognized_word[0] for recognized_word in recognized_words \
            if recognized_word[0] == word and recognized_word[1] >= accuracy_threshold]) > 0

    def opponent_said(self, word, accuracy_threshold=0.95):
        return self.julius_msg_word_contains(self.julius_result, word, accuracy_threshold)

    def handle_julius_msg(self, msg_content):
        """音声認識エンジンJuliusからのメッセージを取得"""
        self.julius_result = msg_content["words"]
    
    def handle_card_msg(self, msg_content):
        """トランプカードを検出するノードからのメッセージを取得"""
        if msg_content["state"] == "detected":
            self.card_detection_result = msg_content["cards"]

    def handle_motion_msg(self, msg_content):
        """人の動きを検出するノードからのメッセージを取得"""
        print("DarumaFellOverApp::handle_motion_msg(): " +
              "message sent from MotionDetectionNode: {}"
              .format(msg_content))

        if msg_content["state"] == "motion-detected":
            self.motion_detected = True

    def update(self):
        """ゲームの状態を更新"""
        self.state_func_table[self.game_state]()

    def on_init(self):
        self.face("slightly-smiling.png")
        self.talk("だるまさんが転んだの準備はできましたか")
        self.game_state = GameState.ASK_IF_READY
        self.julius_result = None

    def on_ask_if_ready(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい"):
            self.game_state = GameState.RULE_DESCRIPTION
        elif self.opponent_said("まだ"):
            self.aplay("bye.wav")
            self.app_exit = True
        else:
            self.julius_result = None

    def on_rule_description(self):
        self.face("slightly-smiling.png")
        self.talk("だるまさんが転んだを始めましょう")
        self.face("wink.png")
        self.talk("私がもちろん鬼になるので、あなたは離れてくださいね")
        self.face("slightly-smiling.png")
        self.current_time = time.monotonic()
        self.game_state = GameState.WAIT_A_MOMENT

    def on_wait_a_moment(self):
        self.elapsed_time = time.monotonic() - self.current_time

        if self.elapsed_time > 5.0:
            self.face("very-happy.png")
            self.talk("準備はできましたね")
            self.face("slightly-smiling.png")
            self.talk("それでは始めましょう")
            self.face("")
            self.game_state = GameState.SPEAK
    
    def on_speak(self):
        speech_type = random.randint(0, 4)

        if speech_type == 0:
            self.talk("だるまさんがころん、")
        elif speech_type == 1:
            self.talk("だ、る、ま、さ、ん、が、こ、ろ、ん、")
        elif speech_type == 2:
            self.talk("だーーるーーまーーさーーんーーがーーこーーろーーんーー")
        elif speech_type == 3:
            self.talk("だ、る、ま、さ、ん、がころん")
        elif speech_type == 4:
            self.talk("だるまさん、が、こ、ろーん、")
        
        self.game_state = GameState.SPEAK2
        
    def on_speak2(self):
        if self.opponent_said("タッチ"):
            self.game_state = GameState.TOUCHED
            return

        # 適当な時間だけ待つ
        self.wait_time = random.uniform(0.0, 2.0)
        time.sleep(self.wait_time)

        self.game_state = GameState.SPEAK3
        
    def on_speak3(self):
        if self.opponent_said("タッチ"):
            self.game_state = GameState.TOUCHED
            return
        
        self.talk("だー")
        self.game_state = GameState.TURN_AROUND

    def on_turn_around(self):
        # サーボモータを回転
        self.node_manager.send_command("servo", { "angle": 90 })
        time.sleep(1.0)

        self.face("very-happy.png")
        
        # 人の動きの検出を開始
        self.node_manager.send_command("motion", { "command": "start" })
        self.current_time = time.monotonic()
        self.wait_time = random.uniform(4.0, 8.0)
        self.game_state = GameState.DETECT_MOTION

    def on_detect_motion(self):
        self.elapsed_time = time.monotonic() - self.current_time
        
        if self.elapsed_time > self.wait_time:
            self.game_state = GameState.SPEAK
            self.node_manager.send_command("motion", { "command": "end" })
            self.node_manager.send_command("servo", { "angle": 0 })
            time.sleep(1.0)
            return

        if self.motion_detected:
            self.face("tongue-out-1.png")
            self.talk("動きましたね")
            self.motion_detected = False
            self.pi_win = True
            self.node_manager.send_command("motion", { "command": "end" })
            self.node_manager.send_command("servo", { "angle": 0 })
            time.sleep(1.0)
            self.game_state = GameState.RESULT
            return

    def on_touched(self):
        self.face("weary.png")
        self.talk("ああ捕まった")
        self.pi_win = False
        self.game_state = GameState.RESULT

    def on_result(self):
        if self.pi_win:
            self.face("smiling-with-closed-eyes.png")
            self.talk("私の勝ちです")
        else:
            self.face("angel.png")
            self.talk("あなたの勝ちです")
            self.face("slightly-smiling.png")
            self.talk("悔しいなあ")

        self.app_exit = True
    
    def run_game(self):
        """ゲームの実行"""
        try:
            while True:
                # 入力を処理
                self.input()

                # ゲームの状態を更新
                self.update()
                
                # アプリケーションを終了
                if self.app_exit:
                    break

                time.sleep(0.5)
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("DarumaFellOverApp::run_game(): KeyboardInterrupt occurred")

    def run(self):
        # 使用するノードを取得
        self.msg_queue = self.node_manager.get_msg_queue()
        self.openjtalk_node = self.node_manager.get_node("openjtalk")

        # ノードの実行を開始
        self.node_manager.run_nodes()

        # プログラムを終了させるかどうか
        self.app_exit = False

        self.game_state = GameState.INIT

        self.julius_result = None
        self.card_detection_result = None
        self.motion_detected = False
        self.pi_win = False

        # 状態と実行される関数のディクショナリ
        self.state_func_table = {
            GameState.INIT: self.on_init,
            GameState.ASK_IF_READY: self.on_ask_if_ready,
            GameState.RULE_DESCRIPTION: self.on_rule_description,
            GameState.WAIT_A_MOMENT: self.on_wait_a_moment,
            GameState.SPEAK: self.on_speak,
            GameState.SPEAK2: self.on_speak2,
            GameState.SPEAK3: self.on_speak3,
            GameState.TURN_AROUND: self.on_turn_around,
            GameState.DETECT_MOTION: self.on_detect_motion,
            GameState.TOUCHED: self.on_touched,
            GameState.RESULT: self.on_result
        }

        # ゲームを実行
        self.run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = DarumaFellOverApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

