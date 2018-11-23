# coding: utf-8
# motor_node.py

import multiprocessing as mp
import queue
import time

from command_receiver_node import CommandReceiverNode, UnknownCommandException

class MotorNode(CommandReceiverNode):
    """
    ロボットのモータを操作するクラス
    """
    
    def __init__(self, process_manager, msg_queue, motor_left, motor_right):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # 左右のモータ
        self.motor_left = motor_left
        self.motor_right = motor_right

    def __del__(self):
        """デストラクタ"""

        # 2つのモータを停止
        self.stop()

        # 2つのモータの使用を終了
        self.end()

    def initialize_state_dict(self):
        """ノードの状態を格納するディクショナリを初期化"""
        super().initialize_state_dict()

        # モータの状態をディクショナリに格納
        self.state_dict["speed_left"] = 0
        self.state_dict["speed_right"] = 0

    def process_command(self):
        """モータの命令を処理"""
        
        try:
            while True:
                # モータへの命令をキューから取り出し
                cmd = self.command_queue.get()
                print("MotorNode::process_command(): command received: {0}"
                      .format(cmd))

                # 命令でない場合は例外をスロー
                if "command" not in cmd:
                    raise UnknownCommandException(
                        "MotorNode::process_command(): unknown command: {0}"
                        .format(cmd))

                # 命令の実行開始をアプリケーションに伝達
                self.send_message("motor", { "command": cmd["command"], "state": "start" })
       
                # モータへの命令を実行
                if cmd["command"] == "accel":
                    # 2つのモータを加速
                    self.accelerate(cmd["speed"], cmd["wait_time"])
                elif cmd["command"] == "accel-left":
                    # 左のモータを加速
                    self.accelerate_left(cmd["speed"], cmd["wait_time"])
                elif cmd["command"] == "accel-right":
                    # 右のモータを加速
                    self.accelerate_right(cmd["speed"], cmd["wait_time"])
                elif cmd["command"] == "brake":
                    # 2つのモータを減速
                    self.decelerate(cmd["speed"], cmd["wait_time"])
                elif cmd["command"] == "brake-left":
                    # 左のモータを減速
                    self.decelerate_left(cmd["speed"], cmd["wait_time"])
                elif cmd["command"] == "brake-right":
                    # 右のモータを加速
                    self.decelerate_right(cmd["speed"], cmd["wait_time"])
                elif cmd["command"] == "stop":
                    # 2つのモータを停止
                    self.stop()
                elif cmd["command"] == "end":
                    # 2つのモータの使用を終了
                    self.end()
                elif cmd["command"] == "rotate":
                    # ロボットを回転
                    if "wait_time" in cmd:
                        self.rotate(cmd["direction"], cmd["wait_time"])
                    else:
                        self.rotate(cmd["direction"])
                else:
                    # 不明のコマンドを受信した場合は例外をスロー
                    raise UnknownCommandException(
                        "MotorNode::process_command(): unknown command: {0}"
                        .format(cmd["command"]))

                # 命令の実行終了をアプリケーションに伝達
                self.send_message("motor", { "command": cmd["command"], "state": "done" })

                # モータへの命令が完了
                self.command_queue.task_done()
        
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("MotorNode::process_command(): KeyboardInterrupt occurred")
   
    def accelerate(self, speed, wait_time):
        """2つのモータを加速"""
        
        while self.state_dict["speed_left"] < speed:
            self.state_dict["speed_left"] += 250
            self.state_dict["speed_right"] += 250

            self.motor_left.run(self.state_dict["speed_left"])
            self.motor_right.run(-self.state_dict["speed_right"])

            time.sleep(wait_time)

    def accelerate_left(self, speed, wait_time):
        """左のモータを加速"""
        
        while self.state_dict["speed_left"] < speed:
            self.state_dict["speed_left"] += 250
            self.motor_left.run(self.state_dict["speed_left"])
            time.sleep(wait_time)

    def accelerate_right(self, speed, wait_time):
        """右のモータを加速"""
        
        while self.state_dict["speed_right"] < speed:
            self.state_dict["speed_right"] += 250
            self.motor_right.run(-self.state_dict["speed_right"])
            time.sleep(wait_time)

    def decelerate(self, speed, wait_time):
        """2つのモータを減速"""

        while self.state_dict["speed_left"] > speed:

            self.state_dict["speed_left"] -= 250
            self.state_dict["speed_right"] -= 250

            self.motor_left.run(self.state_dict["speed_left"])
            self.motor_right.run(-self.state_dict["speed_right"])

            time.sleep(wait_time)

    def decelerate_left(self, speed, wait_time):
        """左のモータを減速"""

        while self.state_dict["speed_left"] > speed:
            self.state_dict["speed_left"] -= 250
            self.motor_left.run(self.state_dict["speed_left"])
            time.sleep(wait_time)
    
    def decelerate_right(self, speed, wait_time):
        """右のモータを減速"""

        while self.state_dict["speed_right"] > speed:
            self.state_dict["speed_right"] -= 250
            self.motor_right.run(-self.state_dict["speed_right"])
            time.sleep(wait_time)

    def stop(self):
        """2つのモータを停止"""

        self.state_dict["speed_left"] = 0
        self.state_dict["speed_right"] = 0
        
        self.motor_left.run(self.state_dict["speed_left"])
        self.motor_right.run(self.state_dict["speed_right"])

    def end(self):
        """2つのモータの使用を終了"""

        # モータを減速させて停止
        self.motor_left.softstop()
        self.motor_right.softstop()

        # モータのブリッジを高インピーダンスに設定
        self.motor_left.softhiz()
        self.motor_right.softhiz()

    def rotate(self, direction, wait_time=1.5):
        if direction == "left":
            self.rotate_left(wait_time)
        elif direction == "right":
            self.rotate_right(wait_time)
    
    def rotate_left(self, wait_time=1.5):
        """ロボットを回転"""

        self.state_dict["speed_left"] = 0
        self.state_dict["speed_right"] = 0
        
        while self.state_dict["speed_right"] < 10000:
            self.state_dict["speed_left"] += 250
            self.state_dict["speed_right"] += 250
            self.motor_left.run(-self.state_dict["speed_left"])
            self.motor_right.run(-self.state_dict["speed_right"])
            time.sleep(0.05)

        time.sleep(wait_time)

        while self.state_dict["speed_right"] > 0:
            self.state_dict["speed_left"] -= 250
            self.state_dict["speed_right"] -= 250
            self.motor_left.run(-self.state_dict["speed_left"])
            self.motor_right.run(-self.state_dict["speed_right"])
            time.sleep(0.05)
        
        # 回転後は停止
        self.stop()

    def rotate_right(self, wait_time=1.5):
        """ロボットを回転"""
        
        while self.state_dict["speed_left"] < 10000:
            self.state_dict["speed_left"] += 250
            self.state_dict["speed_right"] += 250
            self.motor_left.run(self.state_dict["speed_left"])
            self.motor_right.run(self.state_dict["speed_right"])
            time.sleep(0.05)

        time.sleep(wait_time)

        while self.state_dict["speed_left"] > 0:
            self.state_dict["speed_left"] -= 250
            self.state_dict["speed_right"] -= 250
            self.motor_left.run(self.state_dict["speed_left"])
            self.motor_right.run(self.state_dict["speed_right"])
            time.sleep(0.05)

        # 回転後は停止
        self.stop()

