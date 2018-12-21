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
    RULE_DESCRIPTION = 3
    ASK_OPPONENT_ACTION = 4
    RECOGNIZE_OPPONENT_ACTION = 5
    ASK_OPPONENT_CARD = 6
    RECOGNIZE_OPPONENT_CARD = 7
    CHOOSE_ACTION = 8
    ASK_CARD = 9
    RECOGNIZE_CARD = 10
    ROUND_FINISHED = 11
    RESULT = 12

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
        self.__config = {
            "enable_motor": True,
            "enable_servo": True,
            "enable_srf02": False,
            "enable_julius": True,
            "enable_openjtalk": True,
            "enable_speechapi": False,
            "enable_webcam": False,
            "enable_card": True,
            "enable_motion": False,
            "motor": {},
            "servo": {},
            "openjtalk": {},
            "julius": {},
            "card": {
                "server_host": sys.argv[1],
                "camera_id": 0,
                "frame_width": 640,
                "frame_height": 480
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

    def __update(self):
        """ゲームの状態を更新"""
        self.__state_func_table[self.__game_state]()

    def __on_init(self):
        self.__talk("ニセブラックジャックの準備はできましたか")
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
        self.__talk("ニセブラックジャックの説明をします")
        self.__talk("ルールは非常に簡単です")
        self.__talk("私とあなたが交互にカードを引いていきます")
        self.__talk("引いたカードの数字の合計が21を超えたら即ゲームオーバーになります")
        self.__talk("数字の合計が21を超えなかったら、数字が大きい方が勝ちになります")
        self.__talk("ゲームは5回戦まで行われます")
        self.__talk("それでは早速始めましょう")
        self.__game_state = GameState.ASK_OPPONENT_ACTION
    
    def __on_ask_opponent_action(self):
        if self.__julius_result is None:
            return

        if len(self.__opponent_cards) == 0:
            self.__talk("まずはカードを引いてください")
            self.__card_detection_result = None
            self.__game_state = GameState.ASK_OPPONENT_CARD
            return

        self.__talk("あなたはどうしますか")
        self.__talk("カードを引きますか")
        self.__talk("それとも引きませんか")
        self.__talk("引く場合は、はい、引かない場合は、いいえと答えてください")
        self.__game_state = GameState.RECOGNIZE_OPPONENT_ACTION
        self.__julius_result = None

    def __on_recognize_opponent_action(self):
        if self.__julius_result is None:
            return

        if self.__opponent_said("はい"):
            self.__opponent_action = GameAction.TAKE
            self.__talk("カードを引くのですね")
            self.__game_state = GameState.ASK_OPPONENT_CARD
        elif self.__opponent_said("いいえ"):
            self.__opponent_action = GameAction.SKIP
            self.__talk("カードを引かないのですね")
            self.__game_state = GameState.CHOOSE_ACTION
        else:
            self.__julius_result = None
        
    def __on_ask_opponent_card(self):
        self.__talk("あなたのカードを見せてください")
        self.__detect()
        self.__game_state = GameState.RECOGNIZE_OPPONENT_CARD
        self.__card_detection_result = None

    def __on_recognize_opponent_card(self):
        if self.__card_detection_result is None:
            return

        if len(self.__card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.__opponent_cards.append(self.__card_detection_result[0])
            self.__card_detection_result = None
            self.__talk("分かりました")
            self.__talk("もしかしたら読み取り間違えているかもしれませんが、ご容赦ください")

            # 相手のゲームオーバーが確定した場合
            if sum(self.__opponent_cards) > 21:
                self.__talk("おっと、数字の合計が21を超えてしまったようです")
                self.__game_state = GameState.ROUND_FINISHED
            else:
                self.__game_state = GameState.CHOOSE_ACTION
        else:
            self.__talk("あなたのカードが見えません")
            self.__game_state = GameState.ASK_OPPONENT_CARD
            self.__card_detection_result = None

    def __on_choose_action(self):
        if len(self.__pi_cards) == 0:
            self.__card_detection_result = None
            self.__game_state = GameState.ASK_CARD
            return

        if sum(self.__pi_cards) < 15:
            self.__pi_action = GameAction.TAKE
            self.__talk("私は引きます")
            self.__game_state = GameState.ASK_CARD
        else:
            self.__pi_action = GameAction.SKIP
            self.__talk("私は引きません")
            
            if self.__opponent_action == GameAction.SKIP:
                # 両方とも引かない場合
                self.__game_state = GameState.ROUND_FINISHED
            else:
                self.__game_state = GameState.ASK_OPPONENT_ACTION
    
    def __on_ask_card(self):
        self.__talk("私のカードを見せてください")
        self.__detect()
        self.__game_state = GameState.RECOGNIZE_CARD
        self.__card_detection_result = None

    def __on_recognize_card(self):
        if self.__card_detection_result is None:
            return

        if len(self.__card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.__pi_cards.append(self.__card_detection_result[0])
            self.__card_detection_result = None
            self.__talk("分かりました")

            if sum(self.__pi_cards) > 21:
                # 自分のゲームオーバーが確定した場合
                self.__talk("ああ、やってしまいました")
                self.__game_state = GameState.ROUND_FINISHED
            else:
                self.__game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.__talk("私のカードが見えません")
            self.__game_state = GameState.ASK_CARD
            self.__card_detection_result = None

    def __on_round_finished(self):
        if sum(self.__pi_cards) > 21 and sum(self.__opponent_cards) > 21:
            self.__talk("どちらも負けですね")
            self.__talk("引き分けとしましょう")
        elif sum(self.__pi_cards) > 21:
            self.__talk("私の負けです")
            self.__talk("悔しいなあ")
            self.__opponent_win_times += 1
        elif sum(self.__opponent_cards) > 21:
            self.__talk("あなたの負けです")
            self.__talk("残念でしたね")
            self.__pi_win_times += 1
        else:
            if sum(self.__pi_cards) > sum(self.__opponent_cards):
                self.__talk("私の勝ちです")
                self.__pi_win_times += 1
            elif sum(self.__pi_cards) < sum(self.__opponent_cards):
                self.__talk("あなたの勝ちです")
                self.__talk("悔しいなあ")
                self.__opponent_win_times += 1
            else:
                self.__talk("引き分けですね")

        self.__game_times += 1

        if self.__game_times < 5:
            self.__talk("次の試合をやりましょう")
            self.__opponent_cards = []
            self.__pi_cards = []
            self.__opponent_action = None
            self.__pi_action = None
            self.__julius_result = None
            self.__card_detection_result = None
            self.__game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.__talk("結果発表です")
            self.__game_state = GameState.RESULT
    
    def __on_result(self):
        if self.__pi_win_times == self.__opponent_win_times:
            self.__talk("引き分けですね")
        elif self.__pi_win_times > self.__opponent_win_times:
            self.__talk("私の勝ちです")
            self.__talk("やったね")
        else:
            self.__talk("あなたの勝ちです")
            self.__talk("なんだかイライラするなあ")
            self.__talk("お前の顔面にクリームパイを投げつけてやる")
            self.__node_manager.send_command("servo", { "angle": 105 })
            time.sleep(5)
            self.__node_manager.send_command("servo", { "angle": 0 })
            time.sleep(3)
            self.__talk("あははざまあみろ")

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
            print("PseudoBlackjackApp::__run_game(): KeyboardInterrupt occurred")

    def run(self):
        # 使用するノードを取得
        self.__msg_queue = self.__node_manager.get_msg_queue()
        self.__openjtalk_node = self.__node_manager.get_node("openjtalk")

        # ノードの実行を開始
        self.__node_manager.run_nodes()

        # プログラムを終了させるかどうか
        self.__app_exit = False

        self.__game_state = GameState.INIT
        self.__game_times = 0
        self.__opponent_win_times = 0
        self.__pi_win_times = 0

        self.__julius_result = None
        self.__card_detection_result = None
        self.__opponent_action = None
        self.__pi_action = None
        self.__opponent_cards = []
        self.__pi_cards = []

        # 状態と実行される関数のディクショナリ
        self.__state_func_table = {
            GameState.INIT: self.__on_init,
            GameState.ASK_IF_READY: self.__on_ask_if_ready,
            GameState.RULE_DESCRIPTION: self.__on_rule_description,
            GameState.ASK_OPPONENT_ACTION: self.__on_ask_opponent_action,
            GameState.RECOGNIZE_OPPONENT_ACTION: self.__on_recognize_opponent_action,
            GameState.ASK_OPPONENT_CARD: self.__on_ask_opponent_card,
            GameState.RECOGNIZE_OPPONENT_CARD: self.__on_recognize_opponent_card,
            GameState.CHOOSE_ACTION: self.__on_choose_action,
            GameState.ASK_CARD: self.__on_ask_card,
            GameState.RECOGNIZE_CARD: self.__on_recognize_card,
            GameState.ROUND_FINISHED: self.__on_round_finished,
            GameState.RESULT:  self.__on_result
        }

        # ゲームを実行
        self.__run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = PseudoBlackjackApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

