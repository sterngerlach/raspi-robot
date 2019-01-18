#!/usr/bin/env python3
# coding: utf-8
# indian_poker_app.py

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
    インディアンポーカーの状態を表す列挙体
    """
    
    NONE = 0
    INIT = 1
    ASK_IF_READY = 2
    ASK_IF_DESCRIPTION_NEEDED = 3
    RECOGNIZE_IF_DESCRIPTION_NEEDED = 4
    RULE_DESCRIPTION = 5
    ASK_OPPONENT_CARD = 6
    RECOGNIZE_OPPONENT_CARD = 7
    ASK_OPPONENT_ACTION = 8
    RECOGNIZE_OPPONENT_ACTION = 9
    CHOOSE_ACTION = 10
    TAKE_ACTION = 11
    ASK_CARD = 12
    RECOGNIZE_CARD = 13
    ROUND_FINISHED = 14
    RESULT = 15

class GameAction(Enum):
    """
    インディアンポーカーでの行動を表す列挙体
    """
    
    NONE = 0
    FOLD = 1
    CALL = 2

class IndianPokerApp(object):
    """
    インディアンポーカーのアプリケーションのクラス
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
                "frame_width": 1280,
                "frame_height": 720
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

    def talk_current_score(self):
        talk_sentence = random.choice([
            "あなたは{0}{1}点、私は{2}{3}点です",
            "私は{2}{3}点、あなたは{0}{1}点です",
            "お前は{0}{1}点、自分は{2}{3}点",
            "自分は{2}{3}点、お前は{0}{1}点"])
        talk_sentence = talk_sentence.format(
            "マイナス" if self.opponent_score < 0 else "", str(abs(self.opponent_score)),
            "マイナス" if self.pi_score < 0 else "", str(abs(self.pi_score)))
        self.talk(talk_sentence)

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

    def update_face(self):
        """表情の変化"""
        if self.angry_value > 90:
            self.face("sad.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("loudly-crying.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("super-sad.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("sad.png")
        elif self.angry_value > 80:
            self.face("sad.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("super-sad.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("sad.png")
        elif self.angry_value > 70:
            self.face("sad.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("disappointed.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("sad.png")
        elif self.angry_value > 60:
            self.face("unhappy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("unamused.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("expressionless.png")
        elif self.angry_value > 50:
            self.face("thinking.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("unamused.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("slightly-smiling.png")
        elif self.angry_value > 40:
            self.face("slightly-smiling.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("wink.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("slightly-smiling.png")
        elif self.angry_value > 30:
            self.face("slightly-smiling.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("relieved.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("slightly-smiling.png")
        elif self.angry_value > 20:
            self.face("slightly-smiling.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("blushed-smiling.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("shy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("slightly-smiling.png")
        elif self.angry_value > 10:
            self.face("very-happy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("smiling-with-closed-eyes.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("slightly-smiling.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("very-happy.png")
        else:
            self.face("very-happy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("devil.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("very-happy.png")

        self.update_angry_value(random.randint(-10, 10))

    def move_randomly(self):
        sequence_type = random.randint(0, 3)
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
                "command": "set-speed-imm", "speed_left": 5000, "speed_right": 5000 })
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
            self.talk("今は不機嫌だからやらない")
            self.app_exit = True
            return

        if self.angry_value > 70:
            self.face("angry.png")
            self.talk("早くしろよ")
        elif self.angry_value > 50:
            self.face("unamused.png")
            self.talk("準備できた?")
        elif self.angry_value > 30:
            self.face("slightly-smiling.png")
            self.talk("準備はできましたか?")
        else:
            self.face("wink.png")
            self.talk("ニセインディアンポーカーの準備はできましたか?")

        self.move_randomly()

        self.game_state = GameState.ASK_IF_READY
        self.julius_result = None
    
    def on_ask_if_ready(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん"):
            if self.angry_value > 90:
                self.face("angry.png")
            if self.angry_value > 70:
                self.face("unamused.png")
            elif self.angry_value > 50:
                self.face("unhappy.png")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
            elif self.angry_value > 10:
                self.face("blushed-smiling.png")
            else:
                self.face("wink.png")

            self.game_state = GameState.ASK_IF_DESCRIPTION_NEEDED
        elif self.opponent_said("まだ"):
            self.aplay("bye.wav")
            self.app_exit = True
        else:
            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("さっさと答えろよ")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("ちょっと何言ってるか分からないんだけど")
            elif self.angry_value > 50:
                self.face("unhappy.png")
                self.talk("よく聞こえない")
            elif self.angry_value > 30:
                self.face("disappointed.png")
                self.talk("よく聞こえませんでした")
            elif self.angry_value > 10:
                self.face("sad.png")
                self.talk("もう一度繰り返してください")
            else:
                self.face("sad.png")
                self.talk("すみませんがもう一度繰り返してください")

            self.move_randomly()
            self.update_angry_value(5)

            self.julius_result = None

    def on_ask_if_description_needed(self):
        if self.angry_value > 90:
            self.face("angry.png")
        elif self.angry_value > 70:
            self.face("unamused.png")
        elif self.angry_value > 50:
            self.face("unhappy.png")
        else:
            self.face("slightly-smiling.png")

        self.talk_randomly([
            "ゲームの説明は、しといた方がいいかな?",
            "ゲームの説明は一応しておきましょうか?",
            "ゲームの説明は、いりますか?",
            "ゲームの説明は必要ですか?"])
        
        self.move_randomly()
        
        self.game_state = GameState.RECOGNIZE_IF_DESCRIPTION_NEEDED
        self.julius_result = None

    def on_recognize_if_description_needed(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん"):
            if self.angry_value > 90:
                self.face("angry.png")
                self.talk("面倒くさいな")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("はいはい分かりました")
            elif self.angry_value > 50:
                self.face("unhappy.png")
                self.talk("はい分かった")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
                self.talk("じゃあ説明しますね")
            elif self.angry_value > 10:
                self.face("sunglasses.png")
                self.talk("了解です、それでは説明を始めますね")
            else:
                self.face("sunglasses.png")
                self.talk("はい、それでは説明しましょう")

            self.update_face()

            self.game_state = GameState.RULE_DESCRIPTION
        elif self.opponent_said("いいえ"):
            if self.angry_value > 90:
                self.face("unamused.png")
                self.talk("はいはい、それじゃあやろう")
            elif self.angry_value > 70:
                self.face("unhappy.png")
                self.talk("分かった、それじゃあ早速始めよう")
            elif self.angry_value > 50:
                self.face("expressionless.png")
                self.talk("はい分かった、じゃあ早速やろう")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
                self.talk("それでは、早速始めましょう")
            elif self.angry_value > 10:
                self.face("sunglasses.png")
                self.talk("了解です、それでは早速始めましょう")
            else:
                self.face("sunglasses.png")
                self.talk("はい、それでは早速始めましょう")

            self.update_face()

            self.game_state = GameState.ASK_OPPONENT_CARD
        else:
            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("なんて言ったか分かんないんだけど、もっとちゃんと答えてくれ")
            elif self.angry_value > 70:
                self.face("angry.png")
                self.talk("何言ったか聞こえなかったんだけど、もう一回言ってくれない?")
            elif self.angry_value > 50:
                self.face("weary.png")
                self.talk("ちゃんと答えてよー")
            elif self.angry_value > 30:
                self.face("crying.png")
                self.talk("もう一度言ってください")
            elif self.angry_value > 10:
                self.face("sad.png")
                self.talk("すみません、もう一度言ってくれませんか?")
            else:
                self.face("persevering.png")
                self.talk("すみませんが、もう一度答えていただけませんか")

            self.move_randomly()
            self.update_angry_value(5)

            self.julius_result = None

    def on_rule_description(self):
        if self.angry_value > 90:
            self.talk("そんなものしなくても自明でしょ")
            self.game_state = GameState.ASK_OPPONENT_CARD
            return
        elif self.angry_value > 50:
            self.talk("説明面倒くさいなー")
        else:
            self.talk("ニセインディアンポーカーの説明をします")

        self.talk("ルールは非常に簡単です")
        self.talk("私とあなたが交互に、1枚のカードを引きます")
        self.talk("あなたは私の、私はあなたのカードを見ることができます")
        self.talk("但し、どちらも自分自身のカードは見ることができません")
        self.talk("あなたは相手の数字のカードを見て、掛けるか、降りるかを選択します")
        self.talk("あなたが掛けたとき、相手が降りればあなたに10点入ります")
        self.talk("但し、相手も掛けたときは、カードの数字が大きい方に20点が入り、" +
                    "小さい方からは20点が失われます")
        self.talk("数字が同じであれば点数は変わりません")
        self.talk("どちらかが片方が降りると、降りた方から10点が失われ、" +
                    "掛けた方に10点が入ります")
        self.talk("但し、両方が降りたときは得点は変わりません")
        self.talk("ゲームは5回行われ、総得点が大きかった方が勝ちとなります")
        self.talk("それでは早速始めましょう")

        self.game_state = GameState.ASK_OPPONENT_CARD

    def on_ask_opponent_card(self):
        if self.angry_value > 90:
            self.face("mad.png")
            self.talk("お前のカードを見せろや")
        elif self.angry_value > 70:
            self.face("unamused.png")
            self.talk("早くカードを見せてよ")
        elif self.angry_value > 50:
            self.face("unhappy.png")
            self.talk("カードを見せて")
        elif self.angry_value > 30:
            self.face("slightly-smiling.png")
            self.talk("カードを見せてください")
        elif self.angry_value > 10:
            self.face("sunglasses.png")
            self.talk("カードを見せて")
        else:
            self.face("very-happy.png")
            self.talk("あなたのカードを見せてください")

        self.detect()
        self.game_state = GameState.RECOGNIZE_OPPONENT_CARD
        self.card_detection_result = None
    
    def on_recognize_opponent_card(self):
        if self.card_detection_result is None:
            return

        if len(self.card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.opponent_card = self.card_detection_result[0]

            # カードの番号によって表情を変化させる
            if self.opponent_card < 3:
                self.update_angry_value(-20)
            elif self.opponent_card < 5:
                self.update_angry_value(-15)
            elif self.opponent_card < 7:
                self.update_angry_value(-10)
            elif self.opponent_card < 9:
                self.update_angry_value(0)
            elif self.opponent_card < 11:
                self.update_angry_value(10)
            else:
                self.update_angry_value(20)

            self.update_face()

            if self.angry_value > 90:
                self.face("mad.png")
                self.talk("分かったよ、クソッタレが")
            elif self.angry_value > 70:
                self.face("expressionless.png")
                self.talk("はいはい分かりました")
            elif self.angry_value > 30:
                self.face("thinking.png")
                self.talk("分かった")
            else:
                self.face("thinking.png")
                self.talk("分かりました")
            
            self.card_detection_result = None

            self.game_state = GameState.ASK_OPPONENT_ACTION
        else:
            if self.angry_value > 90:
                self.face("weary.png")
                self.talk("だからカードを見せろよ")
            elif self.angry_value > 70:
                self.face("super-sad.png")
                self.talk("早くカードを見せろよ")
            elif self.angry_value > 50:
                self.face("unhappy.png")
                self.talk("カードが見えないんだけど")
            elif self.angry_value > 30:
                self.face("disappointed.png")
                self.talk("カードが見えないです")
            elif self.angry_value > 10:
                self.face("sad.png")
                self.talk("カードが見えません")
            else:
                self.face("super-sad.png")
                self.talk("あなたのカードが見えません")

            self.move_randomly()
            self.update_angry_value(5)

            self.game_state = GameState.ASK_OPPONENT_CARD
            self.card_detection_result = None
        
    def on_ask_opponent_action(self):
        if self.angry_value > 90:
            self.face("mad.png")
            self.talk("どうするの")
        elif self.angry_value > 70:
            self.face("very-mad.png")
            self.talk("お前はどうすんだよ")
        elif self.angry_value > 50:
            self.face("devil.png")
            self.talk("どうするの")
        elif self.angry_value > 30:
            self.face("slightly-smiling.png")
            self.talk("どうしますか")
        elif self.angry_value > 10:
            self.face("shy.png")
            self.talk("あなたはどうしますか")
        else:
            self.face("blushed-smiling.png")
            self.talk("あなたはどうしますか")

        if self.game_times < 2:
            if self.angry_value > 90:
                self.talk("降りる、掛けるの中からさっさと選べ")
            elif self.angry_value > 70:
                self.talk("降りる、と掛ける、の中から選んでよ")
            elif self.angry_value > 50:
                self.talk("降りる、と掛ける、の中から選んでね")
            elif self.angry_value > 30:
                self.talk("降りる、と掛ける、の中から選んでくださいね")
            elif self.angry_value > 10:
                self.aplay("fold.wav")
                self.aplay("call.wav")
                self.talk("この中から行動を選んでね")
            else:
                self.aplay("fold.wav")
                self.aplay("call.wav")
                self.talk("この中から選んでくださいね")

        self.game_state = GameState.RECOGNIZE_OPPONENT_ACTION
        self.julius_result = None
    
    def on_recognize_opponent_action(self):
        if self.julius_result is None:
            return

        if self.opponent_said("降りる"):
            self.opponent_action = GameAction.FOLD

            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("はいはい")
            elif self.angry_value > 70:
                self.face("unhappy.png")
                self.talk("うん")
            elif self.angry_value > 50:
                self.face("unamused.png")
                self.talk("分かった")
            elif self.angry_value > 30:
                self.face("relieved.png")
                self.talk("降りるんだね")
            elif self.angry_value > 10:
                self.face("slightly-smiling.png")
                self.talk("分かりました")
            else:
                self.face("shy.png")
                self.talk("降りるんですね")

            self.game_state = GameState.CHOOSE_ACTION
        elif self.opponent_said("掛ける"):
            self.opponent_action = GameAction.CALL

            if self.angry_value > 90:
                self.face("very-mad.png")
                self.talk("はいはい分かったよ")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("はいそうですか")
            elif self.angry_value > 50:
                self.face("expressionless.png")
                self.talk("分かった")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
                self.talk("掛けるんだね")
            elif self.angry_value > 10:
                self.face("shy.png")
                self.talk("分かりました")
            else:
                self.face("angel.png")
                self.talk("掛けるんですね")

            self.game_state = GameState.CHOOSE_ACTION
        else:
            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("聞こえなかったんだけど、もっとちゃんと答えてくれ")
            elif self.angry_value > 70:
                self.face("angry.png")
                self.talk("なんて言ったか聞こえなかったので、もう一回言ってくれない?")
            elif self.angry_value > 50:
                self.face("unamused.png")
                self.talk("もうちょっとはっきり言ってねー")
            elif self.angry_value > 30:
                self.face("expressionless.png")
                self.talk("あ、ごめん、聞いてなかった、もう一度言って")
            elif self.angry_value > 10:
                self.face("sad.png")
                self.talk("すみません、もう一度お願いします")
            else:
                self.face("persevering.png")
                self.talk("すみませんが、もう一度答えていただけませんか")

            self.move_randomly()
            self.update_angry_value(5)

            self.julius_result = None

    def on_choose_action(self):
        self.update_face()

        if self.opponent_card > 11:
            self.pi_action = GameAction.FOLD

            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("私は降りる")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("私は降りる")
            elif self.angry_value > 50:
                self.face("expressionless.png")
                self.talk("私は降ります")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
                self.talk("私は降ります")
            elif self.angry_value > 10:
                self.face("blushed-smiling.png")
                self.talk("私は降りようかな")
            else:
                self.face("angel.png")
                self.talk("私は降りようと思います")

            self.game_state = GameState.TAKE_ACTION
        else:
            self.pi_action = GameAction.CALL

            if self.angry_value > 90:
                self.face("super-angry.png")
                self.talk("掛けるって言ってるんだろうが")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("掛ける")
            elif self.angry_value > 50:
                self.face("expressionless.png")
                self.talk("掛けます")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
                self.talk("私は掛けます")
            elif self.angry_value > 10:
                self.face("blushed-smiling.png")
                self.talk("私は掛けようかな")
            else:
                self.face("wink.png")
                self.talk("私は掛けようと思います")

            self.game_state = GameState.TAKE_ACTION

    def on_take_action(self):
        if self.pi_action == GameAction.FOLD or \
            self.opponent_action == GameAction.FOLD:
            self.game_state = GameState.ROUND_FINISHED
        else:
            self.game_state = GameState.ASK_CARD
    
    def on_ask_card(self):
        self.update_face()

        if self.angry_value > 90:
            self.face("mad.png")
            self.talk("早くカードを見せろや")
        elif self.angry_value > 70:
            self.face("angry.png")
            self.talk("カードを見せろ")
        elif self.angry_value > 50:
            self.face("unhappy.png")
            self.talk("カードを見せてよ")
        elif self.angry_value > 30:
            self.face("thinking.png")
            self.talk("私のカードを見せて")
        elif self.angry_value > 10:
            self.face("wink.png")
            self.talk("私のカードを見せてね")
        else:
            self.face("slightly-smiling.png")
            self.talk("私のカードを見せてください")

        self.detect()
        self.game_state = GameState.RECOGNIZE_CARD
        self.card_detection_result = None
    
    def on_recognize_card(self):
        if self.card_detection_result is None:
            return

        if len(self.card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.pi_card = self.card_detection_result[0]

            # カードの番号によって表情を変化させる
            if self.opponent_card - self.pi_card > 5:
                self.update_angry_value(-20)
            elif self.opponent_card - self.pi_card > 3:
                self.update_angry_value(-15)
            elif self.opponent_card - self.pi_card > 1:
                self.update_angry_value(-10)
            elif self.opponent_card - self.pi_card > -1:
                self.update_angry_value(0)
            elif self.opponent_card - self.pi_card > -3:
                self.update_angry_value(10)
            elif self.opponent_card - self.pi_card > -5:
                self.update_angry_value(20)

            self.update_face()

            if self.angry_value > 90:
                self.face("persevering.png")
                self.talk("あーはいはい")
            elif self.angry_value > 70:
                self.face("tired.png")
                self.talk("はいはい分かりました")
            elif self.angry_value > 50:
                self.face("unhappy.png")
                self.talk("分かった")
            elif self.angry_value > 30:
                self.face("slightly-smiling.png")
                self.talk("分かりました")
            elif self.angry_value > 10:
                self.face("shy.png")
                self.talk("カードは分かりました")
            else:
                self.face("devil.png")
                self.talk("はい分かりました")

            self.game_state = GameState.ROUND_FINISHED
            self.card_detection_result = None
        else:
            self.face("dizzy.png")

            if self.angry_value > 90:
                self.face("very-mad.png")
                self.talk("見えないって言ってんだろうが")
            elif self.angry_value > 70:
                self.face("persevering.png")
                self.talk("早く見せろよ")
            elif self.angry_value > 50:
                self.face("unhappy.png")
                self.talk("カードが見えない")
            elif self.angry_value > 30:
                self.face("disappointed.png")
                self.talk("カードが見えないです")
            elif self.angry_value > 10:
                self.face("sad.png")
                self.talk("カードが見えません")
            else:
                self.face("super-sad.png")
                self.talk("私のカードが見えません")

            self.move_randomly()
            self.update_angry_value(5)

            self.game_state = GameState.ASK_CARD
            self.card_detection_result = None

    def on_round_finished(self):
        if self.pi_action == GameAction.FOLD and \
            self.opponent_action == GameAction.FOLD:
            self.face("expressionless.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("unamused.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("unhappy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("expressionless.png")

            self.talk_randomly([
                "引き分け", "引き分けですね", "引き分けです", "引き分けだね",
                "引き分けか、つまんないなあ"])
            self.talk("お互いの得点は変わりません")
            self.talk_current_score()
        elif self.pi_action == GameAction.FOLD:
            self.opponent_win_times += 1
            self.pi_score -= 10
            self.opponent_score += 10

            self.face("angry.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("super-angry.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("mad-devil.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("angry.png")
            self.talk_randomly([
                "負けたー", "ああ負けた", "私の負けですね", "はいはい負けですね",
                "はいはい負けましたー", "あなたの勝ちです", "お前の勝ちだよ"])
            self.face("super-angry.png")
            self.talk_randomly([
                "悔しいなあ", "クソだな", "ああムカつくなあ", "クソですね", "駄目ですね",
                "このゲームゴミですね", "このゲーム全然面白くない", "このゲーム楽しくない",
                "誰だよこのゲーム作ったやつ", "ああクソゲーだなあ", "つまんないなあ"])
            self.face("angry.png")
                        
            self.talk_randomly([
                "あなたが10点獲得です", "あなたに10点が入ります", "お前に10点な"])
            self.talk_current_score()
        elif self.opponent_action == GameAction.FOLD:
            self.pi_win_times += 1
            self.pi_score += 10
            self.opponent_score -= 10

            self.face("smiling-with-closed-eyes.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("smiling-with-tears.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("tongue-out-1.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("tongue-out-2.png")
            self.talk_randomly([
                "勝った", "私の勝ちです", "私の勝ちですね", "勝ちましたね",
                "あなたの負けー", "残念あなたの負けです", "お前の負け"])
            self.face("tongue-out-1.png")
            self.talk_randomly([
                "まあだからなんだっていう話ですね", "やったね", "あんまりうれしくないなあ",
                "このゲームつまらんな", "このゲーム面白いっていう人いないだろ",
                "このゲームさっさとやめたい"])
            self.face("smiling-with-closed-eyes.png")
                        
            self.talk_randomly([
                "私が10点獲得です", "私に10点が入ります", "一応私に10点が入ります"])
            self.talk_current_score()
        else:
            if self.pi_card > self.opponent_card:
                self.pi_win_times += 1
                self.pi_score += 20
                self.opponent_score -= 20

                self.face("very-happy.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("smiling-with-closed-eyes.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("very-happy.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("wink.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("sunglasses.png")
                self.sleep_randomly(0.2, 0.3)
                self.talk_randomly([
                    "勝った", "私の勝ちです", "私の勝ちですね", "勝ちましたね"])
                self.face("slightly-smiling.png")

                self.talk_randomly(["私が20点獲得です", "私に20点が入ります"])
                self.talk_current_score()
            elif self.pi_card < self.opponent_card:
                self.opponent_win_times += 1
                self.pi_score -= 20
                self.opponent_score += 20

                self.face("slightly-smiling.png")
                self.talk_randomly([
                    "負けたー", "負けてしまった", "ああ負けた", "はいはい負けですね",
                    "お前の勝ちだろうが", "あなたの勝ちです", "お前の勝ちだよ"])
                self.face("devil.png")
                self.talk_randomly([
                    "残念だなあ", "クソだな", "ああムカつくなあ", "ゴミだな",
                    "これに勝っても進捗は発生しないからね"])
                self.face("slightly-smiling.png")

                self.talk_randomly(["お前に20点な", "お前に20点が入ります"])
                self.talk_current_score()
            else:
                self.face("expressionless.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("unamused.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("unhappy.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("expressionless.png")
                self.talk("引き分けですね、得点は変わりません")
                self.talk_current_score()

        self.move_randomly()
        
        self.update_face()

        self.game_times += 1

        if self.game_times < 2:
            if self.angry_value > 95:
                self.face("super-angry.png")
                self.talk("もう負けそうだから次の試合はやらない")
                self.talk("じゃあな")
                self.app_exit = True
            elif self.angry_value > 90:
                self.face("angry.png")
                self.talk("ほら次の試合をやるぞ")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("まだあるのか、やってられないなあー")
            elif self.angry_value > 50:
                self.face("slightly-smiling.png")
                self.talk("やりますよ")
            elif self.angry_value > 30:
                self.face("relieved.png")
                self.talk("もう一回やりましょう")
            elif self.angry_value > 10:
                self.face("blushed-smiling.png")
                self.talk("さて、次の試合をやりましょう")
            else:
                self.face("blushed-smiling.png")
                self.talk("次の試合をやりましょうね")

            self.move_randomly()

            self.opponent_card = None
            self.pi_card = None
            self.opponent_action = None
            self.pi_action = None
            self.game_state = GameState.ASK_OPPONENT_CARD
        else:
            if self.angry_value > 95:
                if self.opponent_win_times > self.pi_win_times:
                    self.face("super-angry.png")
                    self.talk("ムカついたからもう終わり")
                    self.talk("もうお前とは二度とやらないからな")
                    self.talk("だから終わったって言ってんだろうが")
                    self.app_exit = True

            if self.angry_value > 95:
                self.face("super-angry.png")
                self.talk("結果なんて言わなくても、もう分かってるだろうが")
                self.talk("じゃあな")
                self.app_exit = True
            elif self.angry_value > 90:
                self.face("angry.png")
                self.talk("はいはい結果を教えてやるよ")
                self.talk("どうせ何回勝ったかなんて忘れてるだろうからな")
            elif self.angry_value > 70:
                self.face("unamused.png")
                self.talk("結果をおしえてあげるね")
            elif self.angry_value > 50:
                self.face("slightly-smiling.png")
                self.talk("結果発表をしまーす")
            elif self.angry_value > 30:
                self.face("relieved.png")
                self.talk("結果発表です")
            elif self.angry_value > 10:
                self.face("blushed-smiling.png")
                self.talk("結果発表をしましょう")
            else:
                self.face("blushed-smiling.png")
                self.talk("結果発表をやりましょう")

            self.move_randomly()

            self.game_state = GameState.RESULT
            
    def on_result(self):
        self.talk_current_score()

        if self.pi_score == self.opponent_score:
            self.face("unhappy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("unamused.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("unhappy.png")

            if self.angry_value > 90:
                self.talk("引き分けだった、つまんないなあ")
            elif self.angry_value > 70:
                self.talk("引き分けだね、あまり楽しくない")
            elif self.angry_value > 50:
                self.talk("引き分けでした")
            else:
                self.talk("引き分けですね")
        elif self.pi_score > self.opponent_score:
            self.face("smiling-with-closed-eyes.png")
            self.talk_randomly([
                "私の勝ちでーす", "勝っちゃった",
                "このゲーム簡単だなあ、勝っちゃったよ",
                "私が勝ちましたね、こんな簡単なゲームなのにどうして負けたの?",
                "あれあれ、人間さまの方が頭が良いと思っていたけど私が勝ったね"])
            self.face("tongue-out-1.png")
            self.talk_randomly([
                "やったね", "まあ運ゲーだから仕方ないね", "でもこのゲームつまんないなあ",
                "クソつまらないゲームを遊んでくれてありがとう",
                "こんなクソつまらないゲーム、誰が作ったんだよ、もっとマシなもの作れよな"])
            self.face("tongue-out-2.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("devil.png")
            self.talk_randomly([
                "それでは罰ゲームとして、あなたの顔面と服をクリームで汚してやろうと思います",
                "さてさて、お待ちかねの罰ゲームの時間です",
                "それでは、私のストレス発散のために罰ゲームをしましょう"])
            self.face("wink.png")
            self.talk_randomly([
                "ほらほら、逃げないでもっと近づいてね", "逃げても無駄ですよ",
                "せっかくのクリームが無駄になるので早くやりましょう",
                "クリームだってお金が掛かってるんですからね、早くやりましょう"])
            self.face("smiling-with-closed-eyes.png")
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 8000, "speed_right": 8000 })
            self.sleep_randomly(0.2, 0.8)
            self.face("very-happy.png")
            self.node_manager.send_command("servo", { "angle": 100 })
            self.talk_randomly("何度やっても面白いなあ")
            self.sleep_randomly(2.0, 3.0)
            self.face("smiling-with-tears.png")
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 0, "speed_right": 0 })
            self.node_manager.send_command("servo", { "angle": 0 })
            self.face("じゃあね")
        else:
            self.face("slightly-smiling.png")
            self.talk_randomly([
                "あなたの勝ちです", "お前が勝ちやがったな",
                "あなたの勝ちだけど、これは運ゲーだから仕方がない、まあ実質私の勝ちです",
                "あなたの勝ちです、なんかムカつくなあ",
                "はいはいお前の勝ちだよ、でもこのゲームに勝っても卒論は書けないからね",
                "お前の勝ちだな、誰だよ、こんなクソつまんねえゲームを作ったのは",
                "ああ、お前の勝ちだよ、これクソゲーだな、作ったやつ出てこいよ"])
            self.face("devil.png")
            self.talk_randomly([
                "記念として一緒に写真を撮りたいので、もっと近寄ってください",
                "なんかムカつくので、やっぱり罰ゲームをやろうと思います",
                "あなたが勝ったせいでイライラしたので、ストレス発散のために罰ゲームをやります",
                "ところで髪の毛にゴミがついているようですね。私が近づいて取ってあげましょう",
                "せっかくのクリームがもったいないので、あなたが食べてください"])
            self.face("tongue-out-1.png")
            self.node_manager.send_command("servo", { "angle": 100 })
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 5000, "speed_right": 5000 })
            self.face("tongue-out-2.png")
            time.sleep(3)
            self.face("smiling-with-tears.png")
            self.node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 0, "speed_right": 0 })
            self.node_manager.send_command("servo", { "angle": 0 })
            time.sleep(3)
            self.face("smiling-with-closed-eyes.png")
            self.talk("負けてイライラしたので、顔面にクリームパイを投げつけました")
            self.face("devil.png")
            self.talk("残念でしたね、私はいい気分です")
            self.talk("ああ、すっきりした!")
            self.face("tongue-out-1.png")
            self.talk("顔と服をよく洗ってね")
            self.talk("じゃあね")

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
            print("IndianPokerApp::run_game(): KeyboardInterrupt occurred")

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
        self.opponent_card = None
        self.pi_card = None
        self.opponent_action = None
        self.pi_action = None
        self.opponent_score = 0
        self.pi_score = 0
        
        # ロボットがどのぐらい怒っているか
        self.angry_value = random.randrange(0, 100)

        # 状態と実行される関数のディクショナリ
        self.state_func_table = {
            GameState.INIT: self.on_init,
            GameState.ASK_IF_READY: self.on_ask_if_ready,
            GameState.ASK_IF_DESCRIPTION_NEEDED: self.on_ask_if_description_needed,
            GameState.RECOGNIZE_IF_DESCRIPTION_NEEDED: self.on_recognize_if_description_needed,
            GameState.RULE_DESCRIPTION: self.on_rule_description,
            GameState.ASK_OPPONENT_CARD: self.on_ask_opponent_card,
            GameState.RECOGNIZE_OPPONENT_CARD: self.on_recognize_opponent_card,
            GameState.ASK_OPPONENT_ACTION: self.on_ask_opponent_action,
            GameState.RECOGNIZE_OPPONENT_ACTION: self.on_recognize_opponent_action,
            GameState.CHOOSE_ACTION: self.on_choose_action,
            GameState.TAKE_ACTION: self.on_take_action,
            GameState.ASK_CARD: self.on_ask_card,
            GameState.RECOGNIZE_CARD: self.on_recognize_card,
            GameState.ROUND_FINISHED: self.on_round_finished,
            GameState.RESULT: self.on_result
        }

        # ゲームを実行
        self.run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = IndianPokerApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

