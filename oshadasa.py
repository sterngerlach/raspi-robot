#!/usr/bin/env python3
# coding: utf-8
# oshadasa.py

import os
import queue
import random
import sys
import time

from enum import Enum

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot_lib"))

from robot_lib.node_manager import NodeManager

class AppState(Enum):
    """
    おしゃれになりたい
    1: 初期状態
    2: 準備ができたかどうかを聞く
    3: 撮影の準備ができたかどうかを聞く
    4: 撮影の準備ができていれば, 撮影の開始を伝える
    5: カウントダウンの後に写真を撮影する
    6: おしゃれかどうかを判定し, 結果を発表
    7: まだやるのかを聞く
    8: 聞いた結果によって繰り返すかどうかを決める
    """

    NONE = 0
    INIT = 1
    ASK_IF_READY = 2
    ASK_IF_PHOTO_READY = 3
    RECOGNIZE_IF_PHOTO_READY = 4
    TAKE_PHOTO = 5
    RECOGNIZE_PHOTO = 6
    ASK_NEXT_ROUND = 7
    RECOGNIZE_NEXT_ROUND = 8

class OshaDasaApp(object):
    def __init__(self):
        """コンストラクタ"""

        # ロボットの各種設定
        self.config = {
            "enable_motor": False,
            "enable_servo": False,
            "enable_srf02": False,
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_speechapi": False,
            "enable_webcam": False,
            "enable_card": False,
            "enable_motion": False,
            "enable_face": True,
            "enable_fashion": True,
            "motor": {},
            "servo": {},
            "openjtalk": {},
            "julius": {},
            "fashion": {
                "server_host": sys.argv[1],
                "camera_id": 0,
                "frame_width": 1280,
                "frame_height": 720
            },
            "face": {
                "window_width": 640,
                "window_height": 480
            }
        }

        self.node_manager = NodeManager(self.config)

    def talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.node_manager.send_command("openjtalk", { "sentence": sentence })
        self.openjtalk_node.wait_until_all_command_done()
    
    def talk_randomly(self, candidates):
        self.talk(random.choice(candidates))

    def aplay(self, file_name):
        """指定された音声ファイルを再生"""
        self.node_manager.send_command("openjtalk", { "file_name": file_name })
        self.openjtalk_node.wait_until_all_command_done()

    def check_if_fashionable(self):
        """トランプカードの検出命令を送信"""
        self.node_manager.send_command("fashion", { "command": "check" })

    def sleep_randomly(self, sleep_min, sleep_max):
        """ランダムな時間だけスリープ"""
        time.sleep(random.uniform(sleep_min, sleep_max))

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
                    elif msg["sender"] == "fashion":
                        self.handle_fashion_msg(msg["content"])
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
    
    def handle_fashion_msg(self, msg_content):
        """服装がおしゃれかどうかを判定するノードからのメッセージを取得"""
        if msg_content["state"] == "done":
            if msg_content["is_fashionable"] == -1:
                # 何らかの原因で画像をキャプチャできなかったことを表す
                self.fashion_result = None
            else:
                # おしゃれであれば1, おしゃれでなければ0が設定される
                self.fashion_result = msg_content["is_fashionable"]

    def update(self):
        """ゲームの状態を更新"""
        self.state_func_table[self.app_state]()

    def on_init(self):
        self.face("slightly-smiling.png")
        self.talk("おしゃれ判定アプリを起動しますか?")

        self.app_state = AppState.ASK_IF_READY
        self.julius_result = None
    
    def on_ask_if_ready(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん") or self.opponent_said("お願い"):
            self.face("slightly-smiling.png")
            self.app_state = AppState.ASK_IF_PHOTO_READY
        elif self.opponent_said("まだ"):
            self.aplay("bye.wav")
            self.app_exit = True
        else:
            self.face("disappointed.png")
            self.talk("よく聞こえなかったので、もう一回答えてください")
            self.julius_result = None
    
    def on_ask_if_photo_ready(self):
        self.face("slightly-smiling.png")
        self.talk("撮影の準備はできましたか?")
        
        self.app_state = AppState.RECOGNIZE_IF_PHOTO_READY
        self.julius_result = None

    def on_recognize_if_photo_ready(self):
        if self.julius_result is None:
            return
        
        if self.opponent_said("はい") or self.opponent_said("うん") or self.opponent_said("お願い"):
            self.face("sunglasses.png")
            self.talk("はい、それでは撮影を開始します")
            self.app_state = AppState.TAKE_PHOTO
        elif self.opponent_said("いいえ") or self.opponent_said("まだ"):
            self.talk("承知しました。3秒後にもう一度お伺いします")
            time.sleep(3.0)

            # 3秒後にまた撮影の準備ができたかどうかを確認
            self.app_state = AppState.ASK_IF_PHOTO_READY
        else:
            self.face("persevering.png")
            self.talk("すみませんが、もう一度お答えください")
            self.julius_result = None

    def on_take_photo(self):
        self.face("shy.png")
        self.talk("撮影を3秒後に行います")
        time.sleep(1.0)
        self.talk("さん")
        time.sleep(1.0)
        self.talk("に")
        time.sleep(1.0)
        self.talk("いち")
        self.aplay("camera.wav")

        self.app_state = AppState.RECOGNIZE_PHOTO
        self.fashion_result = None
        self.check_if_fashionable()
    
    def on_recognize_photo(self):
        if self.fashion_result is None:
            return
        
        self.face("relieved.png")
        time.sleep(0.3)
        self.face("slightly-smiling.png")
        time.sleep(0.3)
        self.face("wink.png")

        #判定結果によって喋る結果を変えて欲しい
        self.talk_randomly([
            "読み間違えていても許してね",
            "自分の予想と結果が違くても、怒らないでね"
        ])
        self.talk("撮影した画像によれば")

        #画像処理の結果は恐らく数字で返す予定
        if self.fashion_result == self.osha_dict["osha"]:
            self.talk_randomly([
                "あなたはおしゃれです",
                "素敵な装いです",
                "似合っています"
            ])
        else:
            self.talk_randomly([
                "身だしなみが乱れていませんか?",
                "おしゃれに興味はありますか?",
                "ダサいですね"
            ])

        self.check_times += 1
        self.app_state = AppState.ASK_NEXT_ROUND
        self.fashion_result = None

    def on_ask_next_round(self):
        # 1回測定が終わったから、またやるのかどうかを聞く
        # それによって状態遷移先を変更する
        self.talk("一度結果が出ましたが、まだ判定を行いますか?")
        self.app_state = AppState.RECOGNIZE_NEXT_ROUND
        self.julius_result = None

    def on_recognize_next_round(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん") or self.opponent_said("お願い"):
            self.face("thinking.png")
            self.talk("わかりました")
            self.app_state = AppState.ASK_IF_PHOTO_READY
            self.julius_result = None
        elif self.check_times > 3:
            self.talk("そんなに急いでもおしゃれにはなれませんよ")
            self.aplay("bye.wav")
            self.app_exit = True
        elif self.opponent_said("いいえ"):
            self.talk("ありがとうございました")
            self.aplay("bye.wav")
            self.app_exit = True
        else:
            self.face("persevering.png")
            self.talk("すみませんが、もう一度お答えください")
            self.julius_result = None
    
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
            print("OshaDasaApp::run_game(): KeyboardInterrupt occurred")

    def run(self):
        # 使用するノードを取得
        self.msg_queue = self.node_manager.get_msg_queue()
        self.openjtalk_node = self.node_manager.get_node("openjtalk")

        # ノードの実行を開始
        self.node_manager.run_nodes()

        # プログラムを終了させるかどうか
        self.app_exit = False

        self.app_state = AppState.INIT
        self.check_times = 0
        self.question_type = None

        self.julius_result = None
        self.fashion_result = None
        self.osha_dict = { "osha": 1, "dasa": 0 }

        # 状態と実行される関数のディクショナリ
        self.state_func_table = {
            AppState.INIT: self.on_init,
            AppState.ASK_IF_READY: self.on_ask_if_ready,
            AppState.ASK_IF_PHOTO_READY: self.on_ask_if_photo_ready,
            AppState.RECOGNIZE_IF_PHOTO_READY: self.on_recognize_if_photo_ready,
            AppState.TAKE_PHOTO: self.on_take_photo,
            AppState.RECOGNIZE_PHOTO: self.on_recognize_photo,
            AppState.ASK_NEXT_ROUND: self.on_ask_next_round,
            AppState.RECOGNIZE_NEXT_ROUND: self.on_recognize_next_round
        }

        self.run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = OshaDasaApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

