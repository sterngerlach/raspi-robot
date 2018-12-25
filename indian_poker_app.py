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
        self.__node_manager = NodeManager(self.__config)
        
    def __talk(self, sentence):
        """音声合成エンジンOpenJTalkで指定された文章を話す"""
        self.__node_manager.send_command("openjtalk", { "sentence": sentence })
        self.__openjtalk_node.wait_until_all_command_done()
    
    def __talk_randomly(self, candidates):
        self.__talk(random.choice(candidates))

    def __talk_current_score(self):
        talk_sentence = random.choice([
            "あなたは{0}{1}点、私は{2}{3}点です",
            "私は{2}{3}点、あなたは{0}{1}点です",
            "お前は{0}{1}点、自分は{2}{3}点",
            "自分は{2}{3}点、お前は{0}{1}点"])
        talk_sentence = talk_sentence.format(
            "マイナス" if self.__opponent_score < 0 else "", str(abs(self.__opponent_score)),
            "マイナス" if self.__pi_score < 0 else "", str(abs(self.__pi_score)))
        self.__talk(talk_sentence)

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

    def __update_angry_value(self, delta):
        """ロボットが負けそうかどうかの指標を更新"""
        self.__angry_value = max(0, min(100, self.__angry_value + delta))
        
    def __sleep_randomly(self, sleep_min, sleep_max):
        """ランダムな時間だけスリープ"""
        time.sleep(random.uniform(sleep_min, sleep_max))

    def __face(self, file_name):
        """表情の設定"""
        self.__node_manager.send_command("face", { "file-name": file_name })

    def __update_face(self):
        """表情の変化"""
        if self.__angry_value > 90:
            self.__face("sad.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("loudly-crying.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("super-sad.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("sad.png")
        elif self.__angry_value > 80:
            self.__face("sad.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("super-sad.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("sad.png")
        elif self.__angry_value > 70:
            self.__face("sad.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("disappointed.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("sad.png")
        elif self.__angry_value > 60:
            self.__face("unhappy.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("unamused.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("expressionless.png")
        elif self.__angry_value > 50:
            self.__face("thinking.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("unamused.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("slightly-smiling.png")
        elif self.__angry_value > 40:
            self.__face("slightly-smiling.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("wink.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("slightly-smiling.png")
        elif self.__angry_value > 30:
            self.__face("slightly-smiling.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("relieved.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("slightly-smiling.png")
        elif self.__angry_value > 20:
            self.__face("slightly-smiling.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("blushed-smiling.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("shy.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("slightly-smiling.png")
        elif self.__angry_value > 10:
            self.__face("very-happy.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("smiling-with-closed-eyes.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("slightly-smiling.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("very-happy.png")
        else:
            self.__face("very-happy.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("devil.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("very-happy.png")

        self.__update_angry_value(random.randint(-10, 10))

    def __move_randomly(self):
        sequence_type = random.randint(0, 2)
        wait_time = random.uniform(1.0, 2.0)

        if sequence_type == 0:
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": -5000, "speed_right": 5000 })
            time.sleep(wait_time)
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 5000, "speed_right": -5000 })
            time.sleep(wait_time)
            self.__node_manager.send_command("motor", { "command": "stop" })
        elif sequence_type == 1:
            self.__node_manager.send_command("motor", {
            time.sleep(wait_time)
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": -5000, "speed_right": -5000 })
            time.sleep(wait_time)
            self.__node_manager.send_command("motor", { "command": "stop" })
        
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
        if self.__angry_value > 90:
            self.__face("very-mad.png")
            self.__talk("今は不機嫌だからやらない")
            self.__app_exit = True
            return

        if self.__angry_value > 70:
            self.__face("angry.png")
            self.__talk("早くしろよ")
        elif self.__angry_value > 50:
            self.__face("unamused.png")
            self.__talk("準備できた?")
        elif self.__angry_value > 30:
            self.__face("slightly-smiling.png")
            self.__talk("準備はできましたか?")
        else:
            self.__face("wink.png")
            self.__talk("ニセインディアンポーカーの準備はできましたか?")

        self.__move_randomly()

        self.__game_state = GameState.ASK_IF_READY
        self.__julius_result = None
    
    def __on_ask_if_ready(self):
        if self.__julius_result is None:
            return

        if self.__opponent_said("はい"):
            if self.__angry_value > 90:
                self.__face("angry.png")
            if self.__angry_value > 70:
                self.__face("unamused.png")
            elif self.__angry_value > 50:
                self.__face("unhappy.png")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
            elif self.__angry_value > 10:
                self.__face("blushed-smiling.png")
            else:
                self.__face("wink.png")

            self.__game_state = GameState.ASK_IF_DESCRIPTION_NEEDED
        elif self.__opponent_said("まだ"):
            self.__aplay("bye.wav")
            self.__app_exit = True
        else:
            if self.__angry_value > 90:
                self.__face("super-angry.png")
                self.__talk("さっさと答えろよ")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("ちょっと何言ってるか分からないんだけど")
            elif self.__angry_value > 50:
                self.__face("unhappy.png")
                self.__talk("よく聞こえない")
            elif self.__angry_value > 30:
                self.__face("disappointed.png")
                self.__talk("よく聞こえませんでした")
            elif self.__angry_value > 10:
                self.__face("sad.png")
                self.__talk("もう一度繰り返してください")
            else:
                self.__face("sad.png")
                self.__talk("すみませんがもう一度繰り返してください")

            self.__move_randomly()

            self.__julius_result = None

    def __on_ask_if_description_needed(self):
        if self.__angry_value > 90:
            self.__face("angry.png")
        elif self.__angry_value > 70:
            self.__face("unamused.png")
        elif self.__angry_value > 50:
            self.__face("unhappy.png")
        else:
            self.__face("slightly-smiling.png")

        self.__talk_randomly([
            "ゲームの説明は、しといた方がいいかな?",
            "ゲームの説明は一応しておきましょうか?",
            "ゲームの説明はいりますか?",
            "ゲームの説明は必要ですか?"])
        
        self.__move_randomly()
        
        self.__game_state = GameState.RECOGNIZE_IF_DESCRIPTION_NEEDED
        self.__julius_result = None

    def __on_recognize_if_description_needed(self):
        if self.__julius_result is None:
            return

        if self.__opponent_said("はい"):
            if self.__angry_value > 90:
                self.__face("angry.png")
                self.__talk("面倒くさいな")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("はいはい分かりました")
            elif self.__angry_value > 50:
                self.__face("unhappy.png")
                self.__talk("はい分かった")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
                self.__talk("じゃあ説明しますね")
            elif self.__angry_value > 10:
                self.__face("sunglasses.png")
                self.__talk("了解です、それでは説明を始めますね")
            else:
                self.__face("sunglasses.png")
                self.__talk("はい、それでは説明しましょう")

            self.__update_face()

            self.__game_state = GameState.RULE_DESCRIPTION
        elif self.__opponent_said("いいえ"):
            if self.__angry_value > 90:
                self.__face("unamused.png")
                self.__talk("はいはい、それじゃあやろう")
            elif self.__angry_value > 70:
                self.__face("unhappy.png")
                self.__talk("分かった、それじゃあ早速始めよう")
            elif self.__angry_value > 50:
                self.__face("expressionless.png")
                self.__talk("はい分かった、じゃあ早速やろう")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
                self.__talk("それでは、早速始めましょう")
            elif self.__angry_value > 10:
                self.__face("sunglasses.png")
                self.__talk("了解です、それでは早速始めましょう")
            else:
                self.__face("sunglasses.png")
                self.__talk("はい、それでは早速始めましょう")

            self.__update_face()

            self.__game_state = GameState.ASK_OPPONENT_ACTION
        else:
            if self.__angry_value > 90:
                self.__face("super-angry.png")
                self.__talk("なんて言ったか分かんないんだけど、もっとちゃんと答えてくれ")
            elif self.__angry_value > 70:
                self.__face("angry.png")
                self.__talk("何言ったか聞こえなかったんだけど、もう一回言ってくれない?")
            elif self.__angry_value > 50:
                self.__face("weary.png")
                self.__talk("ちゃんと答えてよー")
            elif self.__angry_value > 30:
                self.__face("crying.png")
                self.__talk("もう一度言ってください")
            elif self.__angry_value > 10:
                self.__face("sad.png")
                self.__talk("すみません、もう一度言ってくれませんか?")
            else:
                self.__face("persevering.png")
                self.__talk("すみませんが、もう一度答えていただけませんか")

            self.__move_randomly()

            self.__julius_result = None

    def __on_rule_description(self):
        if self.__angry_value > 90:
            self.__talk("そんなものしなくても自明でしょ")
            self.__game_state = GameState.ASK_OPPONENT_CARD
            return
        elif self.__angry_value > 50:
            self.__talk("説明面倒くさいなー")
        else:
            self.__talk("ニセインディアンポーカーの説明をします")

        self.__talk("ルールは非常に簡単です")
        self.__talk("私とあなたが交互に、1枚のカードを引きます")
        self.__talk("あなたは私の、私はあなたのカードを見ることができます")
        self.__talk("但し、どちらも自分自身のカードは見ることができません")
        self.__talk("あなたは相手の数字のカードを見て、掛けるか、降りるかを選択します")
        self.__talk("あなたが掛けたとき、相手が降りればあなたに10点入ります")
        self.__talk("但し、相手も掛けたときは、カードの数字が大きい方に20点が入り、" +
                    "小さい方からは20点が失われます")
        self.__talk("数字が同じであれば点数は変わりません")
        self.__talk("どちらかが片方が降りると、降りた方から10点が失われ、" +
                    "掛けた方に10点が入ります")
        self.__talk("但し、両方が降りたときは得点は変わりません")
        self.__talk("ゲームは5回行われ、総得点が大きかった方が勝ちとなります")
        self.__talk("それでは早速始めましょう")

        self.__game_state = GameState.ASK_OPPONENT_CARD

    def __on_ask_opponent_card(self):
        if self.__angry_value > 90:
            self.__face("mad.png")
            self.__talk("お前のカードを見せろや")
        elif self.__angry_value > 70:
            self.__face("unamused.png")
            self.__talk("早くカードを見せてよ")
        elif self.__angry_value > 50:
            self.__face("unhappy.png")
            self.__talk("カードを見せて")
        elif self.__angry_value > 30:
            self.__face("slightly-smiling.png")
            self.__talk("カードを見せてください")
        elif self.__angry_value > 10:
            self.__face("sunglasses.png")
            self.__talk("カードを見せて")
        else:
            self.__face("very-happy.png")
            self.__talk("あなたのカードを見せてください")

        self.__detect()
        self.__game_state = GameState.RECOGNIZE_OPPONENT_CARD
        self.__card_detection_result = None
    
    def __on_recognize_opponent_card(self):
        if self.__card_detection_result is None:
            return

        if len(self.__card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.__opponent_card = self.__card_detection_result[0]

            # カードの番号によって表情を変化させる
            if self.__opponent_card < 3:
                self.__update_angry_value(-20)
            elif self.__opponent_card < 5:
                self.__update_angry_value(-15)
            elif self.__opponent_card < 7:
                self.__update_angry_value(-10)
            elif self.__opponent_card < 9:
                self.__update_angry_value(0)
            elif self.__opponent_card < 11:
                self.__update_angry_value(10)
            else:
                self.__update_angry_value(20)

            self.__update_face()

            if self.__angry_value > 90:
                self.__face("mad.png")
                self.__talk("分かったよ、クソッタレが")
            elif self.__angry_value > 70:
                self.__face("expressionless.png")
                self.__talk("はいはい分かりました")
            elif self.__angry_value > 30:
                self.__face("thinking.png")
                self.__talk("分かった")
            else:
                self.__face("thinking.png")
                self.__talk("分かりました")
            
            self.__card_detection_result = None

            self.__game_state = GameState.ASK_OPPONENT_ACTION
        else:
            if self.__angry_value > 90:
                self.__face("weary.png")
                self.__talk("だからカードを見せろよ")
            elif self.__angry_value > 70:
                self.__face("super-sad")
                self.__talk("早くカードを見せろよ")
            elif self.__angry_value > 50:
                self.__face("unhappy.png")
                self.__talk("カードが見えないんだけど")
            elif self.__angry_value > 30:
                self.__face("disappointed.png")
                self.__talk("カードが見えないです")
            elif self.__angry_value > 10:
                self.__face("sad.png")
                self.__talk("カードが見えません")
            else:
                self.__face("super-sad.png")
                self.__talk("あなたのカードが見えません")

            self.__move_randomly()

            self.__game_state = GameState.ASK_OPPONENT_CARD
            self.__card_detection_result = None
        
    def __on_ask_opponent_action(self):
        if self.__angry_value > 90:
            self.__face("mad.png")
            self.__talk("どうするの")
        elif self.__angry_value > 70:
            self.__face("very-mad.png")
            self.__talk("お前はどうすんだよ")
        elif self.__angry_value > 50:
            self.__face("devil.png")
            self.__talk("どうするの")
        elif self.__angry_value > 30:
            self.__face("slightly-smiling.png")
            self.__talk("どうしますか")
        elif self.__angry_value > 10:
            self.__face("shy.png")
            self.__talk("あなたはどうしますか")
        else:
            self.__face("blushed-smiling.png")
            self.__talk("あなたはどうしますか")

        if self.__game_times < 2:
            if self.__angry_value > 90:
                self.__talk("降りる、掛けるの中からさっさと選べ")
            elif self.__angry_value > 70:
                self.__talk("降りる、と掛ける、の中から選んでよ")
            elif self.__angry_value > 50:
                self.__talk("降りる、と掛ける、の中から選んでね")
            elif self.__angry_value > 30:
                self.__talk("降りる、と掛ける、の中から選んでくださいね")
            elif self.__angry_value > 10:
                self.__aplay("fold.wav")
                self.__aplay("call.wav")
                self.__talk("この中から行動を選んでね")
            else:
                self.__aplay("fold.wav")
                self.__aplay("call.wav")
                self.__talk("この中から選んでくださいね")

        self.__game_state = GameState.RECOGNIZE_OPPONENT_ACTION
        self.__julius_result = None
    
    def __on_recognize_opponent_action(self):
        if self.__julius_result is None:
            return

        if self.__opponent_said("降りる"):
            self.__opponent_action = GameAction.FOLD

            if self.__angry_value > 90:
                self.__face("super-angry.png")
                self.__talk("はいはい")
            elif self.__angry_value > 70:
                self.__face("unhappy.png")
                self.__talk("うん")
            elif self.__angry_value > 50:
                self.__face("unamused.png")
                self.__talk("分かった")
            elif self.__angry_value > 30:
                self.__face("relieved.png")
                self.__talk("降りるんだね")
            elif self.__angry_value > 10:
                self.__face("slightly-smiling.png")
                self.__talk("分かりました")
            else:
                self.__face("shy.png")
                self.__talk("降りるんですね")

            self.__game_state = GameState.CHOOSE_ACTION
        elif self.__opponent_said("掛ける"):
            self.__opponent_action = GameAction.CALL

            if self.__angry_value > 90:
                self.__face("very-mad.png")
                self.__talk("はいはい分かったよ")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("はいそうですか")
            elif self.__angry_value > 50:
                self.__face("expressionless.png")
                self.__talk("分かった")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
                self.__talk("掛けるんだね")
            elif self.__angry_value > 10:
                self.__face("shy.png")
                self.__talk("分かりました")
            else:
                self.__face("angel.png")
                self.__talk("掛けるんですね")

            self.__game_state = GameState.CHOOSE_ACTION
        else:
            if self.__angry_value > 90:
                self.__face("super-angry.png")
                self.__talk("聞こえなかったんだけど、もっとちゃんと答えてくれ")
            elif self.__angry_value > 70:
                self.__face("angry.png")
                self.__talk("なんて言ったか聞こえなかったので、もう一回言ってくれない?")
            elif self.__angry_value > 50:
                self.__face("unamused.png")
                self.__talk("もうちょっとはっきり言ってねー")
            elif self.__angry_value > 30:
                self.__face("expressionless.png")
                self.__talk("あ、ごめん、聞いてなかった、もう一度言って")
            elif self.__angry_value > 10:
                self.__face("sad.png")
                self.__talk("すみません、もう一度お願いします")
            else:
                self.__face("persevering.png")
                self.__talk("すみませんが、もう一度答えていただけませんか")

            self.__move_randomly()

            self.__julius_result = None

    def __on_choose_action(self):
        self.__update_face()

        if self.__opponent_card > 11:
            self.__pi_action = GameAction.FOLD

            if self.__angry_value > 90:
                self.__face("super-angry.png")
                self.__talk("私は降りる")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("私は降りる")
            elif self.__angry_value > 50:
                self.__face("expressionless.png")
                self.__talk("私は降ります")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
                self.__talk("私は降ります")
            elif self.__angry_value > 10:
                self.__face("blushed-smiling.png")
                self.__talk("私は降りようかな")
            else:
                self.__face("angel.png")
                self.__talk("私は降りようと思います")

            self.__game_state = GameState.TAKE_ACTION
        else:
            self.__pi_action = GameAction.CALL

            if self.__angry_value > 90:
                self.__face("super-angry.png")
                self.__talk("掛けるって言ってるんだろうが")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("掛ける")
            elif self.__angry_value > 50:
                self.__face("expressionless.png")
                self.__talk("掛けます")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
                self.__talk("私は掛けます")
            elif self.__angry_value > 10:
                self.__face("blushed-smiling.png")
                self.__talk("私は掛けようかな")
            else:
                self.__face("wink.png")
                self.__talk("私は掛けようと思います")

            self.__game_state = GameState.TAKE_ACTION

    def __on_take_action(self):
        if self.__pi_action == GameAction.FOLD or \
            self.__opponent_action == GameAction.FOLD:
            self.__game_state = GameState.ROUND_FINISHED
        else:
            self.__game_state = GameState.ASK_CARD
    
    def __on_ask_card(self):
        self.__update_face()

        if self.__angry_value > 90:
            self.__face("mad.png")
            self.__talk("早くカードを見せろや")
        elif self.__angry_value > 70:
            self.__face("angry.png")
            self.__talk("カードを見せろ")
        elif self.__angry_value > 50:
            self.__face("unhappy.png")
            self.__talk("カードを見せてよ")
        elif self.__angry_value > 30:
            self.__face("thinking.png")
            self.__talk("私のカードを見せて")
        elif self.__angry_value > 10:
            self.__face("wink.png")
            self.__talk("私のカードを見せてね")
        else:
            self.__face("slightly-smiling.png")
            self.__talk("私のカードを見せてください")

        self.__detect()
        self.__game_state = GameState.RECOGNIZE_CARD
        self.__card_detection_result = None
    
    def __on_recognize_card(self):
        if self.__card_detection_result is None:
            return

        if len(self.__card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.__pi_card = self.__card_detection_result[0]

            # カードの番号によって表情を変化させる
            if self.__opponent_card - self.__pi_card > 5:
                self.__update_angry_value(-20)
            elif self.__opponent_card - self.__pi_card > 3:
                self.__update_angry_value(-15)
            elif self.__opponent_card - self.__pi_card > 1:
                self.__update_angry_value(-10)
            elif self.__opponent_card - self.__pi_card > -1:
                self.__update_angry_value(0)
            elif self.__opponent_card - self.__pi_card > -3:
                self.__update_angry_value(10)
            elif self.__opponent_card - self.__pi_card > -5:
                self.__update_angry_value(20)

            self.__update_face()

            if self.__angry_value > 90:
                self.__face("persevering.png")
                self.__talk("あーはいはい")
            elif self.__angry_value > 70:
                self.__face("tired.png")
                self.__talk("はいはい分かりました")
            elif self.__angry_value > 50:
                self.__face("unhappy.png")
                self.__talk("分かった")
            elif self.__angry_value > 30:
                self.__face("slightly-smiling.png")
                self.__talk("分かりました")
            elif self.__angry_value > 10:
                self.__face("shy.png")
                self.__talk("カードは分かりました")
            else:
                self.__face("devil.png")
                self.__talk("はい分かりました")

            self.__game_state = GameState.ROUND_FINISHED
            self.__card_detection_result = None
        else:
            self.__face("dizzy.png")

            if self.__angry_value > 90:
                self.__face("very-mad.png")
                self.__talk("見えないって言ってんだろうが")
            elif self.__angry_value > 70:
                self.__face("persevering.png")
                self.__talk("早く見せろよ")
            elif self.__angry_value > 50:
                self.__face("unhappy.png")
                self.__talk("カードが見えない")
            elif self.__angry_value > 30:
                self.__face("disappointed.png")
                self.__talk("カードが見えないです")
            elif self.__angry_value > 10:
                self.__face("sad.png")
                self.__talk("カードが見えません")
            else:
                self.__face("super-sad.png")
                self.__talk("私のカードが見えません")

            self.__move_randomly()

            self.__game_state = GameState.ASK_CARD
            self.__card_detection_result = None

    def __on_round_finished(self):
        if self.__pi_action == GameAction.FOLD and \
            self.__opponent_action == GameAction.FOLD:
            self.__face("expressionless.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("unamused.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("unhappy.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("expressionless.png")

            self.__talk_randomly([
                "引き分け", "引き分けですね", "引き分けです", "引き分けだね",
                "引き分けか、つまんないなあ"])
            self.__talk("お互いの得点は変わりません")
            self.__talk_current_score()
        elif self.__pi_action == GameAction.FOLD:
            self.__opponent_win_times += 1
            self.__pi_score -= 10
            self.__opponent_score += 10

            self.__face("angry.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("super-angry.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("mad-devil.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("angry.png")
            self.__talk_randomly([
                "負けたー", "ああ負けた", "私の負けですね", "はいはい負けですね",
                "はいはい負けましたー", "あなたの勝ちです", "お前の勝ちだよ"])
            self.__face("super-angry.png")
            self.__talk_randomly([
                "悔しいなあ", "クソだな", "ああムカつくなあ", "クソですね", "駄目ですね",
                "このゲームゴミですね", "このゲーム全然面白くない", "このゲーム楽しくない",
                "誰だよこのゲーム作ったやつ", "ああクソゲーだなあ", "つまんないなあ"])
            self.__face("angry.png")
                        
            self.__talk_randomly([
                "あなたが10点獲得です", "あなたに10点が入ります", "お前に10点な"])
            self.__talk_current_score()
        elif self.__opponent_action == GameAction.FOLD:
            self.__pi_win_times += 1
            self.__pi_score += 10
            self.__opponent_action -= 10

            self.__face("smiling-with-closed-eyes.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("smiling-with-tears.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("tongue-out-1.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("tongue-out-2.png")
            self.__talk_randomly([
                "勝った", "私の勝ちです", "私の勝ちですね", "勝ちましたね",
                "あなたの負けー", "残念あなたの負けです", "お前の負け"])
            self.__face("tongue-out-1.png")
            self.__talk_randomly([
                "まあだからなんだっていう話ですね", "やったね", "あんまりうれしくないなあ",
                "このゲームつまらんな", "このゲーム面白いっていう人いないだろ",
                "このゲームさっさとやめたい"])
            self.__face("smiling-with-closed-eyes.png")
                        
            self.__talk_randomly([
                "私が10点獲得です", "私に10点が入ります", "一応私に10点が入ります"])
            self.__talk_current_score()
        else:
            if self.__pi_card > self.__opponent_card:
                self.__pi_win_times += 1
                self.__pi_score += 20
                self.__opponent_score -= 20

                self.__face("very-happy.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("smiling-with-closed-eyes.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("very-happy.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("wink.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("sunglasses.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__talk_randomly([
                    "勝った", "私の勝ちです", "私の勝ちですね", "勝ちましたね"])
                self.__face("slightly-smiling.png")

                self.__talk_randomly(["私が20点獲得です", "私に20点が入ります"])
                self.__talk_current_score()
            elif self.__pi_card < self.__opponent_card:
                self.__opponent_win_times += 1
                self.__pi_score -= 20
                self.__opponent_score += 20

                self.__face("slightly-smiling.png")
                self.__talk_randomly([
                    "負けたー", "負けてしまった", "ああ負けた", "はいはい負けですね",
                    "お前の勝ちだろうが", "あなたの勝ちです", "お前の勝ちだよ"])
                self.__face("devil.png")
                self.__talk_randomly([
                    "残念だなあ", "クソだな", "ああムカつくなあ", "ゴミだな",
                    "これに勝っても進捗は発生しないからね"])
                self.__face("slightly-smiling.png")

                self.__talk_randomly(["お前に20点な", "お前に20点が入ります"])
                self.__talk_current_score()
            else:
                self.__face("expressionless.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("unamused.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("unhappy.png")
                self.__sleep_randomly(0.2, 0.3)
                self.__face("expressionless.png")
                self.__talk("引き分けですね、得点は変わりません")
                self.__talk_current_score()

        self.__move_randomly()
        
        self.__update_face()

        self.__game_times += 1

        if self.__game_times < 5:
            if self.__angry_value > 95:
                self.__face("super-angry.png")
                self.__talk("もう負けそうだから次の試合はやらない")
                self.__talk("じゃあな")
                self.__app_exit = True
            elif self.__angry_value > 90:
                self.__face("angry.png")
                self.__talk("ほら次の試合をやるぞ")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("まだあるのか、やってられないなあー")
            elif self.__angry_value > 50:
                self.__face("slightly-smiling.png")
                self.__talk("やりますよ")
            elif self.__angry_value > 30:
                self.__face("relieved.png")
                self.__talk("もう一回やりましょう")
            elif self.__angry_value > 10:
                self.__face("blushed-smiling.png")
                self.__talk("さて、次の試合をやりましょう")
            else:
                self.__face("blushed-smiling.png")
                self.__talk("次の試合をやりましょうね")

            self.__move_randomly()

            self.__opponent_card = None
            self.__pi_card = None
            self.__opponent_action = None
            self.__pi_action = None
            self.__game_state = GameState.ASK_OPPONENT_CARD
        else:
            if self.__angry_value > 95:
                if self.__opponent_win_times > self.__pi_win_times:
                    self.__face("super-angry.png")
                    self.__talk("ムカついたからもう終わり")
                    self.__talk("もうお前とは二度とやらないからな")
                    self.__talk("だから終わったって言ってんだろうが")
                    self.__app_exit = True

            if self.__angry_value > 95:
                self.__face("super-angry.png")
                self.__talk("結果なんて言わなくても、もう分かってるだろうが")
                self.__talk("じゃあな")
                self.__app_exit = True
            elif self.__angry_value > 90:
                self.__face("angry.png")
                self.__talk("はいはい結果を教えてやるよ")
                self.__talk("どうせ何回勝ったかなんて忘れてるだろうからな")
            elif self.__angry_value > 70:
                self.__face("unamused.png")
                self.__talk("結果をおしえてあげるね")
            elif self.__angry_value > 50:
                self.__face("slightly-smiling.png")
                self.__talk("結果発表をしまーす")
            elif self.__angry_value > 30:
                self.__face("relieved.png")
                self.__talk("結果発表です")
            elif self.__angry_value > 10:
                self.__face("blushed-smiling.png")
                self.__talk("結果発表をしましょう")
            else:
                self.__face("blushed-smiling.png")
                self.__talk("結果発表をやりましょう")

            self.__move_randomly()

            self.__game_state = GameState.RESULT
            
    def __on_result(self):
        self.__talk_current_score()

        if self.__pi_score == self.__opponent_score:
            self.__face("unhappy.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("unamused.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("unhappy.png")

            if self.__angry_value > 90:
                self.__talk("引き分けだった、つまんないなあ")
            elif self.__angry_value > 70:
                self.__talk("引き分けだね、あまり楽しくない")
            elif self.__angry_value > 50:
                self.__talk("引き分けでした")
            else:
                self.__talk("引き分けですね")
        elif self.__pi_score > self.__opponent_score:
            self.__face("smiling-with-closed-eyes.png")
            self.__talk_randomly([
                "私の勝ちでーす", "勝っちゃった",
                "このゲーム簡単だなあ、勝っちゃったよ",
                "私が勝ちましたね、こんな簡単なゲームなのにどうして負けたの?",
                "あれあれ、人間さまの方が頭が良いと思っていたけど私が勝ったね"])
            self.__face("tongue-out-1.png")
            self.__talk_randomly([
                "やったね", "まあ運ゲーだから仕方ないね", "でもこのゲームつまんないなあ",
                "クソつまらないゲームを遊んでくれてありがとう",
                "こんなクソつまらないゲーム、誰が作ったんだよ、もっとマシなもの作れよな"])
            self.__face("tongue-out-2.png")
            self.__sleep_randomly(0.2, 0.3)
            self.__face("devil.png")
            self.__talk_randomly([
                "それでは罰ゲームとして、あなたの顔面と服をクリームで汚してやろうと思います",
                "さてさて、お待ちかねの罰ゲームの時間です",
                "それでは、私のストレス発散のために罰ゲームをしましょう"])
            self.__face("wink.png")
            self.__talk_randomly([
                "ほらほら、逃げないでもっと近づいてね", "逃げても無駄ですよ",
                "せっかくのクリームが無駄になるので早くやりましょう",
                "クリームだってお金が掛かってるんですからね、早くやりましょう"])
            self.__face("smiling-with-closed-eyes.png")
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 8000, "speed_right": 8000 })
            self.__sleep_randomly(0.2, 0.8)
            self.__face("very-happy.png")
            self.__node_manager.send_command("servo", { "angle": 100 })
            self.__talk_randomly("何度やっても面白いなあ")
            self.__sleep_randomly(2.0, 3.0)
            self.__face("smiling-with-tears.png")
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 0, "speed_right": 0 })
            self.__node_manager.send_command("servo", { "angle": 0 })
            self.__face("じゃあね")
        else:
            self.__face("slightly-smiling.png")
            self.__talk_randomly([
                "あなたの勝ちです", "お前が勝ちやがったな",
                "あなたの勝ちだけど、これは運ゲーだから仕方がない、まあ実質私の勝ちです",
                "あなたの勝ちです、なんかムカつくなあ",
                "はいはいお前の勝ちだよ、でもこのゲームに勝っても卒論は書けないからね",
                "お前の勝ちだな、誰だよ、こんなクソつまんねえゲームを作ったのは",
                "ああ、お前の勝ちだよ、これクソゲーだな、作ったやつ出てこいよ"])
            self.__face("devil.png")
            self.__talk_randomly([
                "記念として一緒に写真を撮りたいので、もっと近寄ってください",
                "なんかムカつくので、やっぱり罰ゲームをやろうと思います",
                "あなたが勝ったせいでイライラしたので、ストレス発散のために罰ゲームをやります",
                "ところで髪の毛にゴミがついているようですね。私が近づいて取ってあげましょう",
                "せっかくのクリームがもったいないので、あなたが食べてください"])
            self.__face("tongue-out-1.png")
            self.__node_manager.send_command("servo", { "angle": 100 })
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 5000, "speed_right": 5000 })
            self.__face("tongue-out-2.png")
            time.sleep(3)
            self.__face("smiling-with-tears.png")
            self.__node_manager.send_command("motor", {
                "command": "set-speed-imm", "speed_left": 0, "speed_right": 0 })
            self.__node_manager.send_command("servo", { "angle": 0 })
            time.sleep(3)
            self.__face("smiling-with-closed-eyes.png")
            self.__talk("負けてイライラしたので、顔面にクリームパイを投げつけました")
            self.__face("devil.png")
            self.__talk("残念でしたね、私はいい気分です")
            self.__talk("ああ、すっきりした!")
            self.__face("tongue-out-1.png")
            self.__talk("顔と服をよく洗ってね")
            self.__talk("じゃあね")

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
            print("IndianPokerApp::__run_game(): KeyboardInterrupt occurred")

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
        self.__opponent_card = None
        self.__pi_card = None
        self.__opponent_action = None
        self.__pi_action = None
        self.__opponent_score = 0
        self.__pi_score = 0
        
        # ロボットがどのぐらい怒っているか
        self.__angry_value = random.randrange(0, 100)

        # 状態と実行される関数のディクショナリ
        self.__state_func_table = {
            GameState.INIT: self.__on_init,
            GameState.ASK_IF_READY: self.__on_ask_if_ready,
            GameState.ASK_IF_DESCRIPTION_NEEDED: self.__on_ask_if_description_needed,
            GameState.RECOGNIZE_IF_DESCRIPTION_NEEDED: self.__on_recognize_if_description_needed,
            GameState.RULE_DESCRIPTION: self.__on_rule_description,
            GameState.ASK_OPPONENT_CARD: self.__on_ask_opponent_card,
            GameState.RECOGNIZE_OPPONENT_CARD: self.__on_recognize_opponent_card,
            GameState.ASK_OPPONENT_ACTION: self.__on_ask_opponent_action,
            GameState.RECOGNIZE_OPPONENT_ACTION: self.__on_recognize_opponent_action,
            GameState.CHOOSE_ACTION: self.__on_choose_action,
            GameState.TAKE_ACTION: self.__on_take_action,
            GameState.ASK_CARD: self.__on_ask_card,
            GameState.RECOGNIZE_CARD: self.__on_recognize_card,
            GameState.ROUND_FINISHED: self.__on_round_finished,
            GameState.RESULT: self.__on_result
        }

        # ゲームを実行
        self.__run_game()

def main():
    # アプリケーションのインスタンスを作成
    app = IndianPokerApp()
    # アプリケーションを実行
    app.run()

if __name__ == "__main__":
    main()

