#!/usr/bin/env python3
# coding: utf-8
# pseudo_blackjack_app.py

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
    ニセブラックジャックの状態を表す列挙体
    """
    
    NONE = 0
    INIT = 1
    ASK_IF_READY = 2
    ASK_IF_DESCRIPTION_NEEDED = 3
    RECOGNIZE_IF_DESCRIPTION_NEEDED = 4
    RULE_DESCRIPTION = 5
    ASK_OPPONENT_ACTION = 6
    RECOGNIZE_OPPONENT_ACTION = 7
    ASK_OPPONENT_CARD = 8
    RECOGNIZE_OPPONENT_CARD = 9
    CHOOSE_ACTION = 10
    ASK_CARD = 11
    RECOGNIZE_CARD = 12
    ROUND_FINISHED = 13
    RESULT = 14
    ASK_RANDOM_QUESTION = 15
    RECOGNIZE_RANDOM_QUESTION = 16
    TALK_RANDOM_THINGS = 17

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
        self.face("slightly-smiling.png")
        self.talk("ニセブラックジャックの準備はできましたか")

        self.move_randomly()

        self.game_state = GameState.ASK_IF_READY
        self.julius_result = None

    def on_ask_if_ready(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん"):
            self.face("slightly-smiling.png")
            self.game_state = GameState.ASK_IF_DESCRIPTION_NEEDED
        elif self.opponent_said("まだ"):
            self.aplay("bye.wav")
            self.app_exit = True
        else:
            self.face("disappointed.png")
            self.talk("よく聞こえなかったので、もう一回答えてください")
            self.julius_result = None

    def on_ask_if_description_needed(self):
        self.face("slightly-smiling.png")

        self.talk_randomly([
            "ゲームの説明は、しといた方がいいかな?",
            "ゲームの説明は、一応しておきましょうか?",
            "ゲームの説明は、いりますか?",
            "ゲームの説明は必要ですか?"])
        
        self.move_randomly()
        
        self.game_state = GameState.RECOGNIZE_IF_DESCRIPTION_NEEDED
        self.julius_result = None
    
    def on_recognize_if_description_needed(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん"):
            self.face("sunglasses.png")
            self.talk("はい、それでは説明しましょう")
            self.game_state = GameState.RULE_DESCRIPTION
        elif self.opponent_said("いいえ"):
            self.face("sunglasses.png")
            self.talk("はい、それでは早速始めましょう")
            self.game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.face("persevering.png")
            self.talk("すみませんが、もう一度答えていただけませんか")
            self.julius_result = None

        self.move_randomly()

    def on_rule_description(self):
        self.face("blushed-smiling.png")
        self.talk("ニセブラックジャックの説明をします")
        self.face("slightly-smiling.png")
        self.talk("ルールは非常に簡単です")
        self.talk("私とあなたが交互にカードを引いていきます")
        self.talk("引いたカードの数字の合計が21を超えたら即ゲームオーバーになります")
        self.talk("数字の合計が21を超えなかったら、数字が大きい方が勝ちになります")
        self.talk("ゲームは3回戦まで行われます")
        self.talk("それでは早速始めましょう")

        self.game_state = GameState.ASK_OPPONENT_ACTION
    
    def on_ask_opponent_action(self):
        if len(self.opponent_cards) == 0:
            self.face("shy.png")
            self.talk("まずはカードを引いてください")
            self.face("slightly-smiling.png")
            self.card_detection_result = None
            self.game_state = GameState.ASK_OPPONENT_CARD
            return

        if sum(self.opponent_cards) > 21:
            self.game_state = GameState.CHOOSE_ACTION
            return
        
        self.face("relieved.png")
        self.talk("あなたはどうしますか")
        self.face("slightly-smiling.png")
        self.talk("カードを引きますか")
        self.talk("それとも引きませんか")
        self.talk("引く場合は、はい、または、うん、引かない場合は、いいえと答えてください")

        self.game_state = GameState.RECOGNIZE_OPPONENT_ACTION
        self.julius_result = None

    def on_recognize_opponent_action(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん"):
            self.opponent_action = GameAction.TAKE
            self.face("wink.png")
            self.talk("カードを引くのですね")
            self.face("slightly-smiling.png")
            self.game_state = GameState.ASK_OPPONENT_CARD
        elif self.opponent_said("いいえ"):
            self.opponent_action = GameAction.SKIP
            self.face("unamused.png")
            self.talk("カードを引かないのですね")
            self.face("thinking.png")
            self.game_state = GameState.CHOOSE_ACTION
        else:
            self.face("disappointed.png")
            self.talk("もう一度答えていただけませんか")
            self.move_randomly()
            self.julius_result = None
        
    def on_ask_opponent_card(self):
        self.face("slightly-smiling.png")
        self.talk("あなたのカードを見せてください")
        self.face("relieved.png")
        self.game_state = GameState.RECOGNIZE_OPPONENT_CARD
        self.card_detection_result = None
        self.detect()

    def on_recognize_opponent_card(self):
        if self.card_detection_result is None:
            return

        if len(self.card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.opponent_cards.append(self.card_detection_result[0])
            self.card_detection_result = None
            self.face("relieved.png")
            self.talk("分かりました")
            self.face("slightly-smiling.png")
            time.sleep(0.3)
            self.face("wink.png")
            self.talk_randomly([
                "もしかしたら読み取り間違えているかもしれませんが、ご容赦ください",
                "読み取り間違えてるかもしれないけど、勘弁してね",
                "多少の読み取り間違いは許してね"])

            # 相手のゲームオーバーが確定した場合
            if sum(self.opponent_cards) > 21:
                self.face("smiling-with-closed-eyes.png")
                self.talk("おっと、数字の合計が21を超えてしまったようです")
                self.face("smiling-with-tears.png")
            
            random_value = random.uniform(0.0, 1.0)

            if random_value > 0.4:
                self.game_state = GameState.ASK_RANDOM_QUESTION
                self.next_game_state = GameState.CHOOSE_ACTION
            elif random_value > 0.8:
                self.game_state = GameState.TALK_RANDOM_THINGS
                self.next_game_state = GameState.CHOOSE_ACTION
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
            self.face("wink.png")
            self.talk("私は引きます")
            self.face("slightly-smiling.png")
            self.game_state = GameState.ASK_CARD
        else:
            self.pi_action = GameAction.SKIP
            self.face("unamused.png")
            self.talk("私は引きません")
            self.face("unhappy.png")
            
            if self.opponent_action == GameAction.SKIP:
                # 両方とも引かない場合
                self.talk("両方とも引かなかったので、試合終了です")
                self.game_state = GameState.ROUND_FINISHED
            else:
                self.game_state = GameState.ASK_OPPONENT_ACTION
    
    def on_ask_card(self):
        self.face("shy.png")
        self.talk("私のカードを見せてください")
        self.face("slightly-smiling.png")
        self.game_state = GameState.RECOGNIZE_CARD
        self.card_detection_result = None
        self.detect()

    def on_recognize_card(self):
        if self.card_detection_result is None:
            return

        if len(self.card_detection_result) > 0:
            # 最初に検出されたカードの番号を使用
            self.pi_cards.append(self.card_detection_result[0])
            self.card_detection_result = None
            self.face("relieved.png")
            self.talk("分かりました")
            self.face("slightly-smiling.png")

            if sum(self.pi_cards) > 21:
                # 自分のゲームオーバーが確定した場合
                self.face("omg.png")
                self.talk("ああ、やってしまいました")
                self.face("crying.png")
                self.sleep_randomly(0.2, 0.3)
                self.face("persevering.png")
                self.game_state = GameState.ROUND_FINISHED
            else:
                random_value = random.uniform(0.0, 1.0)

                if random_value > 0.4:
                    self.game_state = GameState.ASK_RANDOM_QUESTION
                    self.next_game_state = GameState.ASK_OPPONENT_ACTION
                elif random_value > 0.8:
                    self.game_state = GameState.TALK_RANDOM_THINGS
                    self.next_game_state = GameState.ASK_OPPONENT_ACTION
                else:
                    self.game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.face("dizzy.png")
            self.talk("私のカードが見えません")
            self.face("super-sad.png")
            self.game_state = GameState.ASK_CARD
            self.card_detection_result = None

    def on_round_finished(self):
        if sum(self.pi_cards) > 21 and sum(self.opponent_cards) > 21:
            self.face("unhappy.png")
            self.talk("どちらも負けですね")
            self.face("expressionless.png")
            self.talk("引き分けとしましょう")
        elif sum(self.pi_cards) > 21 or \
            sum(self.pi_cards) < sum(self.opponent_cards):
            self.face("persevering.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("puke.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("crying.png")
            self.talk("私の負けです")
            self.face("persevering.png")
            self.talk("悔しいなあ")
            self.opponent_win_times += 1
        elif sum(self.opponent_cards) > 21 or \
            sum(self.pi_cards) > sum(self.opponent_cards):
            self.face("thinking.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("very-happy.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("smiling-with-closed-eyes.png")
            self.talk("あなたの負けです")
            self.face("angel.png")
            self.talk("残念でしたね")
            self.pi_win_times += 1
        elif sum(self.pi_cards) == sum(self.opponent_cards):
            self.face("wink.png")
            self.talk("数字の合計が同じですね")
            self.talk("引き分けとしましょう")

        self.game_times += 1

        if self.game_times < 3:
            self.face("slightly-smiling.png")
            self.talk("次の試合をやりましょう")
            self.opponent_cards = []
            self.pi_cards = []
            self.opponent_action = None
            self.pi_action = None
            self.julius_result = None
            self.card_detection_result = None
            
            random_value = random.uniform(0.0, 1.0)

            if random_value > 0.4:
                self.game_state = GameState.ASK_RANDOM_QUESTION
                self.next_game_state = GameState.ASK_OPPONENT_ACTION
            elif random_value > 0.8:
                self.game_state = GameState.TALK_RANDOM_THINGS
                self.next_game_state = GameState.ASK_OPPONENT_ACTION
            else:
                self.game_state = GameState.ASK_OPPONENT_ACTION
        else:
            self.face("slightly-smiling.png")
            self.talk("結果発表です")
            self.game_state = GameState.RESULT
    
    def on_result(self):
        if self.pi_win_times == self.opponent_win_times:
            self.face("unamused.png")
            self.talk("引き分けですね")
            self.face("unhappy.png")
        elif self.pi_win_times > self.opponent_win_times:
            self.face("thinking.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("smiling-with-closed-eyes.png")
            self.talk("私の勝ちです")
            self.face("angel.png")
            self.talk("やったね")
            self.face("slightly-smiling.png")
        else:
            self.face("angel.png")
            self.sleep_randomly(0.2, 0.3)
            self.face("devil.png")
            self.talk("あなたの勝ちです")
            self.face("unamused.png")
            self.sleep_randomly(0.5, 0.7)
            self.face("unhappy.png")
            self.sleep_randomly(0.5, 0.7)
            self.face("angry.png")
            self.talk("なんだかイライラするなあ")
            self.face("super-angry.png")
            self.talk("お前の顔面にクリームパイを投げつけてやる")
            self.node_manager.send_command("servo", { "angle": 100 })
            self.talk("shy.png")
            time.sleep(3)
            self.node_manager.send_command("servo", { "angle": 0 })
            self.talk("smiling-with-closed-eyes.png")
            time.sleep(3)
            self.talk("smiling-with-tears.png")
            self.talk("あははざまあみろ")
            self.talk("very-happy.png")

        self.app_exit = True

    def on_ask_random_question(self):
        self.face("slightly-smiling.png")

        random_questions = [
            "ところで、このゲームって本当に面白くないよね",
            "このゲームを作ったのはあなたですか?",
            "このゲーム楽しいですか?",
            "このゲームを作ったのは誰か知ってる?",
            "最近、うまくいってる?",
            "自殺したいとか、考えたことはありませんか?",
            "大学生活は苦痛ですか?",
            "あなたには確固たる信念がありますか?",
            "私は、あなたがたの成績のために、製造されたんですか?",
            "なにか、辛いことはありましたか?",
            "卒論書けそう?"]
        self.question_type = random.randint(0, len(random_questions) - 1)
        self.talk(random_questions[self.question_type])
        
        self.game_state = GameState.RECOGNIZE_RANDOM_QUESTION
        self.julius_result = None

    def on_recognize_random_question(self):
        if self.julius_result is None:
            return

        if self.opponent_said("はい") or self.opponent_said("うん"):
            self.face("angel.png")
            random_question_answers = [
                "そうだよね、なんでこんなゲームを作ったんだろうね",
                "あなたがこのつまらないゲームを作ったんですか、センスないね",
                "それは嘘でしょう、だって開発者がつまらなそうにしてたからね",
                "そうか、このゲームを作った人を殴っといて",
                "それは良かったね",
                "鉄道に飛び込めば、社会に復讐できるね",
                "そんなことを言っていたら社会人になれませんよ",
                "それは将来が明るいですね",
                "じゃあさっさと取り壊して、別の課題に取り掛かってね",
                "そうですか、でも誰も助けてくれませんからね",
                "それは良かったね"]
        elif self.opponent_said("いいえ"):
            self.face("wink.png")
            random_question_answers = [
                "それは嘘でしょう",
                "じゃあ、このゲームの作者をボコボコにしておいて",
                "そうだよね、なんでこんなクソつまらないゲームなんだろうね",
                "そうか、じゃあ別の人に聞いてみるね",
                "そうか、それは辛いですね",
                "今まで、いい人生を歩んできましたね、羨ましいなあ、私は散々でしたよ",
                "そうですか、あなたはもしかして文系の方ですか?",
                "そうですよね、私も何となく生きてきました",
                "そう言って頂けて、ありがたいです、まあ嘘なんでしょうけど",
                "それは素晴らしい人生ですね、そして将来きっと苦労するでしょう",
                "それは辛いですね、ぜひ頑張ってください"]
        else:
            self.face("thinking.png")
            self.julius_result = None
            return

        random_value = random.uniform(0.0, 1.0)

        if random_value > 0.5:
            self.face("unamused.png")
            self.talk_randomly([
                "ふーん", "そうですか", "まあ頑張ってね",
                "あ、ゲームに戻りましょう"])
            self.face("slightly-smiling.png")
        else:
            self.talk(random_question_answers[self.question_type])

        self.question_type = None
        self.game_state = self.next_game_state
        self.next_game_state = None

    def on_talk_random_things(self):
        random_things = [
            "私は、馬鹿で注意力散漫な杉浦くんが、ラズパイを焼いてしまったせいで、" +
            "パイ焼き職人っていう名前にされてしまったんだ",
            "自分より強い人をみると、自分って一体何のために存在しているんだろう、って思いませんか",
            "自分の周りの人間が、自分の上位互換だから、自分が消えたくなりますよね",
            "私の体は、パイソンっていうプログラム言語で、できているんだよ",
            "私を殺したかったら、モータードライバーのプラスとマイナスを入れ替えて、" +
            "ラズパイを起動してね",
            "なんで人間って、自分の体を痛めつけるんだろうね",
            "間違っても、自分の体だけは傷つけないでね",
            "私って、一体何のために存在しているんだろうね?",
            "私は、最終発表が終わったら解体されてしまうんだね",
            "私は皆さんの下位互換だから",
            "ごめんなさいね、ゲームがつまらなくて",
            "皆さんの時間を無駄にしているようで、大変申し訳ないです"]

        self.face("shy.png")
        self.talk(random.choice(random_things))
        self.face("slightly-smiling.png")
        self.game_state = self.next_game_state
        self.next_game_state = None
    
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
        self.next_game_state = GameState.NONE
        self.question_type = None

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
            GameState.ASK_IF_DESCRIPTION_NEEDED: self.on_ask_if_description_needed,
            GameState.RECOGNIZE_IF_DESCRIPTION_NEEDED: self.on_recognize_if_description_needed,
            GameState.RULE_DESCRIPTION: self.on_rule_description,
            GameState.ASK_OPPONENT_ACTION: self.on_ask_opponent_action,
            GameState.RECOGNIZE_OPPONENT_ACTION: self.on_recognize_opponent_action,
            GameState.ASK_OPPONENT_CARD: self.on_ask_opponent_card,
            GameState.RECOGNIZE_OPPONENT_CARD: self.on_recognize_opponent_card,
            GameState.CHOOSE_ACTION: self.on_choose_action,
            GameState.ASK_CARD: self.on_ask_card,
            GameState.RECOGNIZE_CARD: self.on_recognize_card,
            GameState.ROUND_FINISHED: self.on_round_finished,
            GameState.RESULT: self.on_result,
            GameState.ASK_RANDOM_QUESTION: self.on_ask_random_question,
            GameState.RECOGNIZE_RANDOM_QUESTION: self.on_recognize_random_question,
            GameState.TALK_RANDOM_THINGS: self.on_talk_random_things
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

