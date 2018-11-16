# coding: utf-8
# motor_controller.py

import multiprocessing as mp
import queue
import time

class MotorUnknownCommandException(Exception):
    """
    モータへ送信されたコマンドが未知であることを表す例外クラス
    """
    pass

class MotorController(object):
    """
    ロボットのモータを操作するクラス
    """
    
    def __init__(self, motor_left, motor_right,
        command_queue, waiting_command_queue, info):
        """コンストラクタ"""

        # モータへの命令を管理するキュー
        self.command_queue = command_queue
        # 実行待ちのモータの命令を管理するキュー
        self.waiting_command_queue = waiting_command_queue
        # モータの情報を管理するためのディクショナリ
        self.info = info
        self.info["speed_left"] = 0
        self.info["speed_right"] = 0
        self.info["is_command_executing"] = False

        # モータへの命令を監視するためのプロセスを作成
        # キューとディクショナリはいずれもプロセス間で共有されているので
        # メソッドの引数に渡す必要がない
        self.process_watcher = mp.Process(target=self.handle_command, args=())
        # モータの命令を実行するためのプロセスを作成
        self.process_executor = None
        
        # 左右のモータ
        self.motor_left = motor_left
        self.motor_right = motor_right

        return

    def __del__(self):
        """デストラクタ"""

        # プロセスを終了
        # self.process_watcher.terminate()

        return

    def handle_command(self):
        """モータの命令を処理"""
        
        while True:
            # モータへの命令をキューから取り出し
            cmd = self.command_queue.get()
            print("MotorController::handle_command(): " +
                  "command received: {0}"
                  .format(cmd))

            # キャンセルのコマンドが送られた場合は現在のコマンドの実行を中止
            if cmd["command"] == "cancel":
                if self.process_executor is not None:
                    # プロセスが存在する場合は強制終了
                    print("MotorController::handle_command(): " +
                          "terminating executor process")
                    self.process_executor.terminate()
                    self.process_executor = None

                    # キャンセル命令が完了
                    self.command_queue.task_done()
                    
                    # コマンドが実行途中であった場合にのみ完了したことを通知
                    if self.info["is_command_executing"]:
                        # 実行中であったコマンドが完了
                        self.waiting_command_queue.task_done()

                    continue
            
            # モータへの命令を実行
            if self.process_executor is None:
                # モータへの命令を実際に実行するためのプロセスを作成
                self.process_executor = mp.Process(
                    target=self.execute_command, args=())
                # デーモンプロセスに設定
                # 親プロセスが終了するときに子プロセスが自動的に終了
                self.process_executor.daemon = True
                self.process_executor.start()

            # モータの命令キューに命令を追加
            self.waiting_command_queue.put(cmd)
            self.command_queue.task_done()

        return

    def execute_command(self):
        """モータへの命令を実行"""

        # コマンドは実行されていない
        self.info["is_command_executing"] = False

        while True:
            # モータへの命令をキューから取り出し
            cmd = self.waiting_command_queue.get()
            print("MotorController::execute_command(): " +
                  "command will be executed: {0}"
                  .format(cmd))

            # コマンドは実行されている
            self.info["is_command_executing"] = True

            if cmd["command"] == "accel":
                # 2つのモータを加速
                self.accelerate(cmd["speed"], cmd["slope"])
            elif cmd["command"] == "accel-left":
                # 左のモータを加速
                self.accelerate_left(cmd["speed"], cmd["slope"])
            elif cmd["command"] == "accel-right":
                # 右のモータを加速
                self.accelerate_right(cmd["speed"], cmd["slope"])
            elif cmd["command"] == "brake":
                # 2つのモータを減速
                self.decelerate(cmd["speed"], cmd["slope"])
            elif cmd["command"] == "brake-left":
                # 左のモータを減速
                self.decelerate_left(cmd["speed"], cmd["slope"])
            elif cmd["command"] == "brake-right":
                # 右のモータを加速
                self.decelerate_right(cmd["speed"], cmd["slope"])
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
                # 不明のコマンドを受信した場合は無視
                print("MotorController::execute_command(): " +
                      "unknown command ignored: {0}"
                      .format(cmd["command"]))
            
            # コマンドは実行されていない
            self.info["is_command_executing"] = False

            # モータへの命令が完了
            self.waiting_command_queue.task_done()
            
        return

    def send_command(self, cmd):
        """モータの命令キューに新たな命令を追加"""
        self.command_queue.put(cmd)
        return

    def wait_until_all_command_done(self):
        """モータへ送信した命令が全て実行されるまで待機"""
        self.waiting_command_queue.join()
        return

    def run(self):
        """モータの動作を開始"""

        # プロセスを開始
        self.process_watcher.start()

        return

    def emergency_stop(self):
        """モータを緊急停止"""

        # プロセスを終了
        self.process_watcher.terminate()

        # モータを停止
        self.stop()

        return

    def accelerate(self, speed, wait_time):
        """2つのモータを加速"""
        
        while self.info["speed_left"] < speed:
            self.info["speed_left"] += 250
            self.info["speed_right"] += 250

            self.motor_left.run(self.info["speed_left"])
            self.motor_right.run(-self.info["speed_right"])

            time.sleep(wait_time)

        return

    def accelerate_left(self, speed, wait_time):
        """左のモータを加速"""
        
        while self.info["speed_left"] < speed:
            self.info["speed_left"] += 250
            self.motor_left.run(self.info["speed_left"])
            time.sleep(wait_time)

        return

    def accelerate_right(self, speed, wait_time):
        """右のモータを加速"""
        
        while self.info["speed_right"] < speed:
            self.info["speed_right"] += 250
            self.motor_right.run(-self.info["speed_right"])
            time.sleep(wait_time)

        return

    def decelerate(self, speed, wait_time):
        """2つのモータを減速"""

        while self.info["speed_left"] > speed:

            self.info["speed_left"] -= 250
            self.info["speed_right"] -= 250

            self.motor_left.run(self.info["speed_left"])
            self.motor_right.run(-self.info["speed_right"])

            time.sleep(wait_time)

        return

    def decelerate_left(self, speed, wait_time):
        """左のモータを減速"""

        while self.info["speed_left"] > speed:
            self.info["speed_left"] -= 250
            self.motor_left.run(self.info["speed_left"])
            time.sleep(wait_time)

        return
    
    def decelerate_right(self, speed, wait_time):
        """右のモータを減速"""

        while self.info["speed_right"] > speed:
            self.info["speed_right"] -= 250
            self.motor_right.run(-self.info["speed_right"])
            time.sleep(wait_time)

        return


    def stop(self):
        """2つのモータを停止"""

        self.info["speed_left"] = 0
        self.info["speed_right"] = 0
        
        self.motor_left.run(self.info["speed_left"])
        self.motor_right.run(self.info["speed_right"])
        
        return

    def end(self):
        """2つのモータの使用を終了"""

        # モータを減速させて停止
        self.motor_left.softstop()
        self.motor_right.softstop()

        # モータのブリッジを高インピーダンスに設定
        self.motor_left.softhiz()
        self.motor_right.softhiz()
        
        return

    def rotate(self, direction, wait_time=1.5):
        if direction == "left":
            self.rotate_left(wait_time)
        elif direction == "right":
            self.rotate_right(wait_time)
    
    def rotate_left(self, wait_time=1.5):
        """ロボットを回転"""

        self.info["speed_left"] = 0
        self.info["speed_right"] = 0
        
        while self.info["speed_right"] < 10000:
            self.info["speed_left"] += 250
            self.info["speed_right"] += 250
            self.motor_left.run(-self.info["speed_left"])
            self.motor_right.run(-self.info["speed_right"])
            time.sleep(0.05)

        time.sleep(wait_time)

        while self.info["speed_right"] > 0:
            self.info["speed_left"] -= 250
            self.info["speed_right"] -= 250
            self.motor_left.run(-self.info["speed_left"])
            self.motor_right.run(-self.info["speed_right"])
            time.sleep(0.05)
        
        # 回転後は停止
        self.stop()

        return

    def rotate_right(self, wait_time=1.5):
        """ロボットを回転"""
        
        while self.info["speed_left"] < 10000:
            self.info["speed_left"] += 250
            self.info["speed_right"] += 250
            self.motor_left.run(self.info["speed_left"])
            self.motor_right.run(self.info["speed_right"])
            time.sleep(0.05)

        time.sleep(wait_time)

        while self.info["speed_left"] > 0:
            self.info["speed_left"] -= 250
            self.info["speed_right"] -= 250
            self.motor_left.run(self.info["speed_left"])
            self.motor_right.run(self.info["speed_right"])
            time.sleep(0.05)

        # 回転後は停止
        self.stop()

        return

