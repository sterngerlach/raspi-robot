# coding: utf-8
# srf02_controller.py

import multiprocessing as mp
import time

class Srf02Controller(object):
    """
    超音波センサ(SRF02)を操作するクラス
    """

    def __init__(self, srf02, motor_command_queue):
        """コンストラクタ"""

        # モータへの命令を管理するキュー
        self.motor_command_queue = motor_command_queue
        # 超音波センサの入力を処理するためのプロセスを作成
        self.process_handler = mp.Process(
            target=self.process_input, args=(self.motor_command_queue,))
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True

        # 超音波センサ(SRF02)
        self.srf02 = srf02

        return

    def __del__(self):
        """デストラクタ"""
        
        # プロセスを終了
        # self.process_handler.terminate()

        return

    def process_input(self, motor_command_queue):
        """超音波センサの入力を処理"""

        while True:
            # 距離の取得(アドレス0xE0のセンサ)
            result = self.srf02.get_values(0x70)

            if result is not None:
                # 測距データと最小の距離を取得
                dist, mindist = result

                # print("Srf02Controller::process_input(): " +
                #       "address: {0}, dist: {1} cm, mindist: {2} cm"
                #       .format(0xE0, dist, mindist))

                if dist < 15:
                    print("Srf02Controller::process_input(): " +
                          "motor will be stopped, since obstacle has been detected")
                    motor_command_queue.put({ "command": "stop" })

            time.sleep(0.5)

    def run(self):
        """超音波センサの利用を開始"""

        # プロセスを開始
        self.process_handler.start()

        return

    def emergency_stop(self):
        """超音波センサの利用を緊急停止"""

        # プロセスを終了
        self.process_handler.terminate()

        return

