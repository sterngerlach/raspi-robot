#!/usr/bin/env python3
# coding: utf-8
# pseudo_blackjack_app.py

import os
import queue
import sys
import time

from enum import Enum

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot_lib"))

from robot_lib.node_manager import NodeManager

class GameState(Enum):
    """
    ニセブラックジャックの状態を表す列挙体
    """
    
    NONE = 0
    INIT = 1
    ASK_IF_READY = 2
    ASK_IF_DESCRIPTION_NEEDED = 3
    RECOGNIZE_IF_DESCRIPTION_NEEDED = 4
    RULE_DESCRIPTION = 4
    ASK_OPPONENT_ACTION = 5
    RECOGNIZE_OPPONENT_ACTION = 6
    ASK_OPPONENT_CARD = 7
    RECOGNIZE_OPPONENT_CARD = 8
    CHOOSE_ACTION = 9
    ASK_CARD = 10
    RECOGNIZE_CARD = 11
    ROUND_FINISHED = 12
    RESULT = 13
    ASK_RANDOM_QUESTION = 14
    RECOGNIZE_RANDOM_QUESTION = 15
    TALK_RANDOM_THINGS = 16

class GameAction(Enum):
    """
    ニセブラックジャックでの行動を表す列挙体
    """

    NONE = 0
    SKIP = 1
    TAKE = 2

class PseudoBlackjackApp(object):
    """
    ニセブラックジャックのアプリケーションのクラス
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
            "enable_card": True,
            "enable_motion": False,
            "enable_face": True,
            "motor": {},
            "servo": {},
            "openjtalk": {},
            "julius": {},
            "card": {
                "server_host": sys.argv[1],
                "camera_id": 0,
                "frame_width": 640,
                "frame_height": 480
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
    
    def talk_randomly(self, candidates):
        self.talk(random.choice(candidates))

    def aplay(self, file_name):
        """指定された音声ファイルを再生"""
        self.node_manager.send_command("openjtalk", { "file_name": file_name })
        self.openjtalk_node.wait_until_all_command_done()

    def detect(self):
        """トランプカードの検出命令を送信"""
        self.node_manager.send_command("card", { "command": "detect" })

    def update_angry_value(self, delta):
        """ロボットの怒り指標を更新"""
        self.angry_value = max(0, min(100, self.angry_value + delta))
    
    def sleep_randomly(self, sleep_min, sleep_max):
        """ランダムな時間だけスリープ"""
        time.sleep(random.uniform(sleep_min, sleep_max))

    def face(self, file_name):
        """表情の設定"""
        self.node_manager.send_command("face", { "file-name": file_name })
    
    def move_randomly(self):
        sequence_type = random.randint(0, 2)
        wait_time = random.uniform(1.0, 2.0)

        if sequence_type == 0:
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": -5000, "speed_right": 5000 })
            time.sleep(wait_time)
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 5000, "speed_right": -5000 })
            time.sleep(wait_time)
            self.node_manager.send_command("motor", { "command": "stop" })
        elif sequence_type == 1:
            self.node_manager.send_command("motor", {
            time.sleep(wait_time)
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": -5000, "speed_right": -5000 })
            time.sleep(wait_time)
            self.node_manager.send_command("motor", { "command": "stop" })
        elif sequence_type == 2:
            self.node_manager.send_command("servo", { "angle": 15 })
            time.sleep(wait_time)
            self.node_manager.send_command("servo", { "angle": 0 })

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

    def update(self):
        """ゲームの状態を更新"""
        self.state_func_table[self.game_state]()

    def on_init(self):
        if self.angry_value > 90:
            self.face("very-mad.png")
            self.talk_randomly(["今はやらない", "寝てたのに起こすなー", "今は無理"])
            self.app_exit = True
            return
        
        if self.angry_value > 70:
            self.face("unamused.png")
            self.talk("準備できた?")
        elif self.angry_value > 50:
            self.face("unhappy.png")
            self.talk("早くやりましょう")
        elif self.angry_value > 30:
            self.face("slightly-smiling.png")
            self.talk("準備はできましたか?")
        else:
            self.face("slightly-smiling.png")
            self.talk("ニセブラックジャックの準備はできましたか")

        self.move_randomly()

        self.game_state = GameState.ASK_IF_READY
        self.julius_result = None

    def on_ask_if_ready(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい"):
            if self.angry_value > 70:
                self.face("unamused.png")
            elif self.angry_value > 50:
                self.face("unhappy.png")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
            else:
                self.face("wink.png")

            self.game_state = GameState.RULE_DESCRIPTION
        elif self.opponent_said("まだ"):
            self.aplay("bye.wav")
            self.app_exit = True
        else:
            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("なんて言ったか分からないから、もう一度答えてくれない")
            elif self.angry_value > 70:
                self.face("disappointed.png")
                self.talk("よく聞こえないよー")
            elif self.angry_value > 50:
                self.face("disappointed.png")
                self.talk("聞こえなかった")
            elif self.angry_value > 30:
                self.face("sad.png")
                self.talk("聞こえませんでした")
            elif self.angry_value > 10:
                self.face("sad.png")
                self.talk("よく聞こえませんでした")
            else:
                self.face("super-sad.png")
                self.talk("よく聞こえなかったので、もう一回答えてください")

            self.julius_result = None

    def on_rule_description(self):
        self.talk("ニセブラックジャックの説明をします")
        self.talk("ルールは非常に簡単です")
        self.talk("私とあなたが交互にカードを引いていきます")
        self.talk("引いたカードの数字の合計が21を超えたら即ゲームオーバーになります")
        self.talk("数字の合計が21を超えなかったら、数字が大きい方が勝ちになります")
        self.talk("ゲームは5回戦まで行われます")
        self.talk("それでは早速始めましょう")
        self.game_state = GameState.ASK_OPPONENT_ACTION
    
    def on_ask_opponent_action(self):
        if self.julius_result is None:
            return

        if len(self.opponent_cards) == 0:
            self.talk("まずはカードを引いてください")
            self.card_detection_result = None
            self.game_state = GameState.ASK_OPPONENT_CARD
            return

        self.talk("あなたはどうしますか")
        self.talk("カードを引きますか")
        self.talk("それとも引きませんか")
        self.talk("引く場合は、はい、引かない場合は、いいえと答えてください")
        self.game_state = GameState.RECOGNIZE_OPPONENT_ACTION
        self.julius_result = None

    def on_recognize_opponent_action(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい"):
            self.opponent_action = GameAction.TAKE
            self.talk("カードを引くのですね")
            self.game_state = GameState.ASK_OPPONENT_CARD
        elif self.opponent_said("いいえ"):
            self.opponent_action = GameAction.SKIP
            self.talk("カードを引かないのですね")
            self.game_state = GameState.CHOOSE_ACTION
        else:
            self.julius_result = None
        
    def on_ask_opponent_card(self):
        self.talk("あなたのカードを見せてください")
        self.detect()
        self.game_state = GameState.RECOGNIZE_OPPONENT_CARD
        self.card_detection_result = None

    def on_recognize_opponent_card(self):
        if self.card_detection_result is None:
            return

        if len(self.card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.opponent_cards.append(self.card_detection_result[0])
            self.card_detection_result = None
            self.talk("分かりました")
            self.talk("もしかしたら読み取り間違えているかもしれませんが、ご容赦ください")

            # 相手のゲームオーバーが確定した場合
            if sum(self.opponent_cards) > 21:
                self.talk("おっと、数字の合計が21を超えてしまったようです")
                self.game_state = GameState.ROUND_FINISHED
            else:
                self.game_state = GameState.CHOOSE_ACTION
        else:
            self.talk("あなたのカードが見えません")
            self.game_state = GameState.ASK_OPPONENT_CARD
            self.card_detection_result = None

    def on_choose_action(self):
        if len(self.pi_cards) == 0:
            self.card_detection_result = None
            self.game_state = GameState.ASK_CARD
            return

        if sum(self.pi_cards) < 15:
            self.pi_action = GameAction.TAKE
            self.talk("私は引きます")
            self.game_state = GameState.ASK_CARD
        else:
            self.pi_action = GameAction.SKIP
            self.talk("私は引きません")
            
            if self.opponent_action == GameAction.SKIP:
                # 両方とも引かない場合
                self.game_state = GameState.ROUND_FINISHED
            else:
                self.game_state = GameState.ASK_OPPONENT_ACTION
    
    def on_ask_card(self):
        self.talk("私のカードを見せてください")
        self.detect()
        self.game_state = GameState.RECOGNIZE_CARD
        self.card_detection_result = None

    def on_recognize_card(self):
        if self.card_detection_result is None:
            return

        if len(self.card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.pi_cards.append(self.card_detection_result[0])
            self.card_detection_result = None
            self.talk("分かりました")

            if sum(self.pi_cards) > 21:
                # 自分のゲームオーバーが確定した場合
                self.talk("ああ、やってしまいました")
                self.game_state = GameState.ROUND_FINISHED
            else:
                self.game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.talk("私のカードが見えません")
            self.game_state = GameState.ASK_CARD
            self.card_detection_result = None

    def on_round_finished(self):
        if sum(self.pi_cards) > 21 and sum(self.opponent_cards) > 21:
            self.talk("どちらも負けですね")
            self.talk("引き分けとしましょう")
        elif sum(self.pi_cards) > 21:
            self.talk("私の負けです")
            self.talk("悔しいなあ")
            self.opponent_win_times += 1
        elif sum(self.opponent_cards) > 21:
            self.talk("あなたの負けです")
            self.talk("残念でしたね")
            self.pi_win_times += 1
        else:
            if sum(self.pi_cards) > sum(self.opponent_cards):
                self.talk("私の勝ちです")
                self.pi_win_times += 1
            elif sum(self.pi_cards) < sum(self.opponent_cards):
                self.talk("あなたの勝ちです")
                self.talk("悔しいなあ")
                self.opponent_win_times += 1
            else:
                self.talk("引き分けですね")

        self.game_times += 1

        if self.game_times < 5:
            self.talk("次の試合をやりましょう")
            self.opponent_cards = []
            self.pi_cards = []
            self.opponent_action = None
            self.pi_action = None
            self.julius_result = None
            self.card_detection_result = None
            self.game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.talk("結果発表です")
            self.game_state = GameState.RESULT
    
    def on_result(self):
        if self.pi_win_times == self.opponent_win_times:
            self.talk("引き分けですね")
        elif self.pi_win_times > self.opponent_win_times:
            self.talk("私の勝ちです")
            self.talk("やったね")
        else:
            self.talk("あなたの勝ちです")
            self.talk("なんだかイライラするなあ")
            self.talk("お前の顔面にクリームパイを投げつけてやる")
            self.node_manager.send_command("servo", { "angle": 105 })
            time.sleep(5)
            self.node_manager.send_command("servo", { "angle": 0 })
            time.sleep(3)
            self.talk("あははざまあみろ")

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
            print("PseudoBlackjackApp::run_game(): KeyboardInterrupt occurred")

    def run(self):
        # 使用するノードを取得
        self.msg_queue = self.node_manager.get_msg_queue()
        self.openjtalk_node = self.node_manager.get_node("openjtalk")

        # ノードの実行を開始
        self.node_manager.run_nodes()

        # プログラムを終了させるかどうか
        self.app_exit = False

        self.game_state = GameState.INIT
        self.game_times = 0
        self.opponent_win_times = 0
        self.pi_win_times = 0

        self.julius_result = None
        self.card_detection_result = None
        self.opponent_action = None
        self.pi_action = None
        self.opponent_cards = []
        self.pi_cards = []

        # 状態と実行される関数のディクショナリ
        self.state_func_table = {
            GameState.INIT: self.on_init,
            GameState.ASK_IF_READY: self.on_ask_if_ready,
            GameState.RULE_DESCRIPTION: self.on_rule_description,
            GameState.ASK_OPPONENT_ACTION: self.on_ask_opponent_action,
            GameState.RECOGNIZE_OPPONENT_ACTION: self.on_recognize_opponent_action,
            GameState.ASK_OPPONENT_CARD: self.on_ask_opponent_card,
            GameState.RECOGNIZE_OPPONENT_CARD: self.on_recognize_opponent_card,
            GameState.CHOOSE_ACTION: self.on_choose_action,
            GameState.ASK_CARD: self.on_ask_card,
            GameState.RECOGNIZE_CARD: self.on_recognize_card,
            GameState.ROUND_FINISHED: self.on_round_finished,
            GameState.RESULT:  self.on_result
        }

        # ゲームを実行
        self.run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = PseudoBlackjackApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

