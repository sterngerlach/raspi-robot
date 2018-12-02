# coding: utf-8
# motor_node.py

import math
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

        # 車輪の直径(センチメートル)
        self.wheel_diameter = 9.8
        # 車輪と車輪との距離(センチメートル)
        self.distance_between_wheels = 21.3
        # 1回転に要するステップ数
        self.steps_per_revolution = 200

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
                
                try:
                    # 複数のコマンドを連続実行させる場合
                    if cmd["command"] == "sequential":
                        # 各コマンドを順番に実行
                        for single_cmd in cmd["sequence"]:
                            self.execute_command(single_cmd)
                    else:
                        # 指定されたコマンドを実行
                        self.execute_command(cmd)

                    # 命令の実行終了をアプリケーションに伝達
                    self.send_message("motor", { "command": cmd["command"], "state": "done" })
                except (KeyError, ValueError, UnknownCommandException) as e:
                    print("MotorNode::process_command(): exception was thrown: {0}"
                          .format(e))
                    print("MotorNode::process_command(): operation was ignored")

                    # 命令が無視されたことをアプリケーションに伝達
                    self.send_message("motor", { "command": cmd["command"], "state": "ignored" })
                
                # モータへの命令が完了
                self.command_queue.task_done()
        
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("MotorNode::process_command(): KeyboardInterrupt occurred")

    def execute_command(self, cmd):
        """指定されたコマンドを実行"""
        # モータへの命令を実行
        if cmd["command"] == "set-speed":
            # 2つのモータの速度を設定(速度は階段状に変化)
            self.set_speed(cmd["speed_left"], cmd["speed_right"],
                           cmd["step_left"], cmd["step_right"],
                           cmd["wait_time"])
        elif cmd["command"] == "set-left-speed":
            # 左側のモータの速度を設定(速度は階段状に変化)
            self.set_left_speed(cmd["speed"], cmd["step"], cmd["wait_time"])
        elif cmd["command"] == "set-right-speed":
            # 右側のモータの速度を設定(速度は階段状に変化)
            self.set_right_speed(cmd["speed"], cmd["step"], cmd["wait_time"])
        elif cmd["command"] == "set-speed-imm":
            # 2つのモータの速度を設定(即変更)
            self.set_speed_immediately(cmd["speed_left"], cmd["speed_right"])
        elif cmd["command"] == "set-left-speed-imm":
            # 左側のモータの速度を設定(即変更)
            self.set_left_speed_immediately(cmd["speed"])
        elif cmd["command"] == "set-right-speed-imm":
            # 右側のモータの速度を設定(即変更)
            self.set_right_speed_immediately(cmd["speed"])
        elif cmd["command"] == "move-distance":
            # 現在の速度を保った状態で, 指定された距離(センチメートル)を移動
            self.move_distance(cmd["distance"])
        elif cmd["command"] == "rotate0":
            # ロボットの中心速度, 旋回半径, 旋回角度を指定して回転
            self.rotate0(cmd["center_velocity"], cmd["turning_radius"], cmd["turning_angle"])
        elif cmd["command"] == "rotate1":
            # ロボットの中心速度, 旋回角度, 時間を指定して回転
            self.rotate1(cmd["center_velocity"], cmd["turning_angle"], cmd["rotate_time"])
        elif cmd["command"] == "rotate2":
            # 現在の速度を保った状態で, ロボットの旋回角度を指定して回転
            self.rotate2(cmd["turning_angle"])
        elif cmd["command"] == "wait":
            # 指定された時間だけ待機
            time.sleep(cmd["seconds"])
        elif cmd["command"] == "stop":
            # 2つのモータを停止
            self.stop()
        elif cmd["command"] == "end":
            # 2つのモータの使用を終了
            self.end()
        else:
            # 不明のコマンドを受信した場合は例外をスロー
            raise UnknownCommandException(
                "MotorNode::execute_command(): unknown command: {0}"
                .format(cmd["command"]))
    
    def convert_speed_to_steps_per_second(self, speed):
        """モータの速度を1秒間あたりのステップ数に変換"""
        return int(speed * (2 ** (-28)) / (250 * (10 ** (-9)))
    
    def convert_steps_per_second_to_speed(self, steps_per_second):
        """1秒間あたりのステップ数をモータの速度に変換"""
        return int(steps_per_second * (250 * (10 ** (-9))) / (2 ** (-28)))

    def convert_speed_to_centimeters_per_second(self, speed):
        """モータの速度を車輪の回転速度(センチメートル毎秒)に変換"""
        return self.convert_speed_to_steps_per_second(speed) * \
            (self.wheel_diameter * math.pi) / self.steps_per_revolution

    def convert_centimeters_per_second_to_speed(self, centimeters_per_second):
        """車輪の回転速度(センチメートル毎秒)をモータの速度に変換"""
        return self.convert_steps_per_second_to_speed(
            centimeters_per_second * self.steps_per_revolution / \
            (self.wheel_diameter * math.pi))

    def convert_speed_to_revolutions_per_second(self, speed):
        """モータの速度を1秒間あたりの車輪の回転数に変換"""
        return self.convert_speed_to_steps_per_second(speed) / \
            self.steps_per_revolution

    def convert_revolutions_per_second_to_speed(self, revolutions_per_second):
        """1秒間あたりの車輪の回転数をモータの速度に変換"""
        return self.convert_steps_per_second_to_speed(
            revolutions_per_second * self.steps_per_revolution)

    def calculate_turning_angle_velocity(self, left_velocity, right_velocity):
        """左右の車輪の回転速度(センチメートル毎秒)からロボットの旋回角速度を計算"""
        return (right_velocity - left_velocity) / self.distance_between_wheels

    def calculate_center_velocity(self, left_velocity, right_velocity):
        """左右の車輪の回転速度(センチメートル毎秒)からロボットの中心速度を計算"""
        return (right_velocity + left_velocity) / 2.0

    def calculate_turning_radius(self, left_velocity, right_velocity):
        """左右の車輪の回転速度(センチメートル毎秒)からロボットの旋回半径を計算"""
        return (self.distance_between_wheels / 2.0) * \
            (right_velocity + left_velocity) / (right_velocity - left_velocity)

    def calculate_left_velocity(self, turning_radius, turning_angle_velocity):
        """ロボットの旋回半径と旋回角速度から左の車輪の回転速度(センチメートル毎秒)を計算"""
        return (turning_radius - self.distance_between_wheels / 2.0) * \
            turning_angle_velocity

    def calculate_right_velocity(self, turning_radius, turning_angle_velocity):
        """ロボットの旋回半径と旋回角速度から右の車輪の回転速度(センチメートル毎秒)を計算"""
        return (turning_radius + self.distance_between_wheels / 2.0) * \
            turning_angle_velocity

    def set_speed(self, speed_left, speed_right, step_left, step_right, wait_time):
        """2つのモータの速度を設定(速度は階段状に変化)"""
        
        if step_left <= 0:
            raise ValueError("MotorNode::set_speed(): " +
                             "the argument 'step_left' must be positive")
        if step_right <= 0:
            raise ValueError("MotorNode::set_speed(): " +
                             "the argument 'step_right' must be positive")
        if wait_time <= 0:
            raise ValueError("MotorNode::set_speed(): " +
                             "the argument 'wait_time' must be positive")

        left_op = 1 if speed_left > self.state_dict["speed_left"] \
                  else -1 if speed_left < self.state_dict["speed_left"] \
                  else 0
        right_op = 1 if speed_right > self.state_dict["speed_right"] \
                   else -1 if speed_right < self.state_dict["speed_right"] \
                   else 0

        while True:
            # モータの速度変更の終了を判定
            left_done = \
                self.state_dict["speed_left"] >= speed_left if left_op == 1 \
                else self.state_dict["speed_left"] <= speed_right if left_op == -1 \
                else True
            right_done = \
                self.state_dict["speed_right"] >= speed_right if right_op == 1 \
                else self.state_dict["speed_right"] <= speed_right if right_op == -1 \
                else True

            if left_done and right_done:
                break
            
            # モータの速度を段階的に変更
            if not left_done:
                self.state_dict["speed_left"] = \
                    min(self.state_dict["speed_left"] + step_left, speed_left) if left_op == 1 \
                    else max(self.state_dict["speed_left"] - step_left, speed_left) if left_op == -1 \
                    else self.state_dict["speed_left"]
                self.motor_left.run(self.state_dict["speed_left"])

            if not right_done:
                self.state_dict["speed_right"] = \
                    min(self.state_dict["speed_right"] + step_right, speed_right) if right_op == 1 \
                    else max(self.state_dict["speed_right"] - step_right, speed_right) if right_op == -1 \
                    else self.state_dict["speed_right"]
                self.motor_right.run(self.state_dict["speed_right"])
            
            time.sleep(wait_time)
    
    def set_single_motor_speed(self, which, speed, step, wait_time):
        """片方のモータの速度を設定(速度は階段状に変化)"""
        if not (which == "left" or which == "right"):
            raise KeyError("MotorNode::set_single_motor_speed(): " +
                           "the argument 'which' must be set to 'left' or 'right'")
        if step <= 0:
            raise ValueError("MotorNode::set_single_motor_speed(): " +
                             "the argument 'step' must be positive")
        if wait_time <= 0:
            raise ValueError("MotorNode::set_single_motor_speed(): " +
                             "the argument 'wait_time' must be positive")

        key = "speed_left" if which == "left" else "speed_right"
        motor = self.motor_left if which == "left" else self.motor_right
        op = 1 if speed > self.state_dict[key] \
             else -1 if speed < self.state_dict[key] \
             else 0

        while True:
            # モータの速度変更の終了を判定
            is_done = self.state_dict[key] >= speed if op == 1 \
                      else self.state_dict[key] <= speed if op == -1 \
                      else True

            if is_done:
                break

            # モータの速度を段階的に変更
            self.state_dict[key] = \
                min(self.state_dict[key] + step, speed) if op == 1 \
                else max(self.state_dict[key] - step, speed) if op == -1 \
                else self.state_dict[key]
            motor.run(self.state_dict[key])

            time.sleep(wait_time)

    def set_left_speed(self, speed, step, wait_time):
        """左側のモータの速度を設定(速度は階段状に変化)"""
        self.set_single_motor_speed("left", speed, step, wait_time)

    def set_right_speed(self, speed, step, wait_time):
        """右側のモータの速度を設定(速度は階段状に変化)"""
        self.set_single_motor_speed("right", speed, step, wait_time)

    def set_speed_immediately(self, speed_left, speed_right):
        """2つのモータの速度を設定(即変更)"""
        self.state_dict["speed_left"] = speed_left
        self.state_dict["speed_right"] = speed_right

        self.motor_left.run(self.state_dict["speed_left"])
        self.motor_right.run(self.state_dict["speed_right"])
    
    def set_single_motor_speed_immediately(self, which, speed):
        """片方のモータの速度を設定(即変更)"""
        if not (which == "left" or which == "right"):
            raise KeyError("MotorNode::set_single_motor_speed_immediately(): " +
                           "the argument 'which' must be set to 'left' or 'right'")
        if speed < 0:
            raise ValueError("MotorNode::set_single_motor_speed_immediately(): " +
                             "the argument 'speed' must be positive or zero")
        
        key = "speed_left" if which == "left" else "speed_right"
        motor = self.motor_left if which == "left" else self.motor_right

        self.state_dict[key] = speed
        motor.run(self.state_dict[key])
    
    def set_left_speed_immediately(self, speed):
        """左側のモータの速度を設定(即変更)"""
        self.set_single_motor_speed_immediately("left", speed)

    def set_right_speed_immediately(self, speed):
        """右側のモータの速度を設定(即変更)"""
        self.set_single_motor_speed_immediately("right", speed)
    
    def move_distance(self, distance):
        """現在の速度を保った状態で, 指定された距離(センチメートル)を移動"""
        # 左右の車輪の回転速度(センチメートル毎秒)を計算
        left_velocity = self.convert_speed_to_centimeters_per_second(
            self.state_dict["speed_left"])
        right_velocity = self.convert_speed_to_centimeters_per_second(
            self.state_dict["speed_right"])
        # ロボットの中心速度(センチメートル毎秒)を計算
        center_velocity = self.calculate_center_velocity(
            left_velocity, right_velocity)
        # 所要時間を計算
        required_time = distance / center_velocity
        
        time.sleep(required_time)

    def rotate0(self, center_velocity, turning_radius, turning_angle):
        """ロボットの中心速度, 旋回半径, 旋回角度を指定して回転"""
        # 命令の実行前の左右のモータの速度を保存
        left_speed_0 = self.state_dict["speed_left"]
        right_speed_0 = self.state_dict["speed_right"]

        # ロボットの旋回角速度(ラジアン毎秒)を計算
        turning_angle_velocity = center_velocity / turning_radius
        # 回転に必要な時間を計算
        rotate_time = self.radians(turning_angle) / turning_angle_velocity
        # 左右の車輪の回転速度(センチメートル毎秒)を計算
        left_velocity = (turning_radius - self.distance_between_wheels / 2.0) * \
            turning_angle_velocity
        right_velocity = (turning_radius + self.distance_between_wheels / 2.0) * \
            turning_angle_velocity
        # 左右のモータの速度を計算
        left_speed = self.convert_centimeters_per_second_to_speed(left_velocity)
        right_speed = self.convert_centimeters_per_second_to_speed(right_velocity)

        self.set_speed_immediately(left_speed, right_speed)
        time.sleep(rotate_time)
        self.set_speed_immediately(left_speed_0, right_speed_0)
    
    def rotate1(self, center_velocity, turning_angle, rotate_time):
        """ロボットの中心速度, 旋回角度, 時間を指定して回転"""
        # 命令の実行前の左右のモータの速度を保存
        left_speed_0 = self.state_dict["speed_left"]
        right_speed_0 = self.state_dict["speed_right"]

        # ロボットの旋回角速度(ラジアン毎秒)を計算
        turning_angle_velocity = self.radians(turning_angle) / rotate_time
        # ロボットの旋回半径(センチメートル)を計算
        turning_radius = center_velocity / turning_angle_velocity
        # 左右の車輪の回転速度(センチメートル毎秒)を計算
        left_velocity = (turning_radius - self.distance_between_wheels / 2.0) * \
            turning_angle_velocity
        right_velocity = (turning_radius + self.distance_between_wheels / 2.0) * \
            turning_angle_velocity
        # 左右のモータの速度を計算
        left_speed = self.convert_centimeters_per_second_to_speed(left_velocity)
        right_speed = self.convert_centimeters_per_second_to_speed(right_velocity)

        self.set_speed_immediately(left_speed, right_speed)
        time.sleep(rotate_time)
        self.set_speed_immediately(left_speed_0, right_speed_0)

    def rotate2(self, turning_angle):
        """現在の速度を保った状態で, ロボットの旋回角度を指定して回転"""
        # 左右の速度が殆ど同じ場合は回転できない
        diff = math.abs(self.state_dict["speed_left"] - self.state_dict["speed_right"]) 

        if diff< 500:
            raise ValueError(
                "MotorNode::rotate2(): " +
                "absolute difference of the left and right speed must be greater than 500: " +
                "absolute difference was {0}"
                .format(diff))

        # 左右の車輪の回転速度(センチメートル毎秒)を計算
        left_velocity = self.convert_speed_to_centimeters_per_second(
            self.state_dict["speed_left"])
        right_velocity = self.convert_speed_to_centimeters_per_second(
            self.state_dict["speed_right"])
        # ロボットの旋回角速度(ラジアン毎秒)を計算
        turning_angle_velocity = self.calculate_turning_angle_velocity(
            left_velocity, right_velocity)
        # 所要時間を計算
        rotate_time = self.radians(turning_angle) / turning_angle_velocity

        # 所要時間が長過ぎる場合は回転できない
        if rotate_time > 60.0:
            raise ValueError(
                "MotorNode::rotate2(): " +
                "estimated time to complete the operation must be shorter than 60 seconds: "  +
                "estimated time was {0} seconds"
                .format(rotate_time))
        
        # 現在の速度を保った状態で回転
        time.sleep(rotate_time)

    def stop(self):
        """2つのモータを停止"""
        self.set_speed_immediately(0, 0)

    def end(self):
        """2つのモータの使用を終了"""

        # モータを減速させて停止
        self.motor_left.softstop()
        self.motor_right.softstop()

        # モータのブリッジを高インピーダンスに設定
        self.motor_left.softhiz()
        self.motor_right.softhiz()

