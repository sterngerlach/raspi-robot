# coding: utf-8
# openjtalk_controller.py

import multiprocessing as mp
import subprocess as sp
import time

class OpenJTalkController(object):
    """
    音声合成システムOpenJTalkを操作するクラス
    """

    def __init__(self, talk_command_queue):
        """コンストラクタ"""
        
        # 音声合成命令を管理するキュー(共有変数)
        self.talk_command_queue = talk_command_queue
        # 音声合成命令を処理するためのプロセスを作成
        self.process_handler = mp.Process(target=self.process_input, args=())
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True

        return

    def __del__(self):
        """デストラクタ"""

        # プロセスを終了
        # self.process_handler.terminate()

        return

    def process_input(self):
        """音声合成命令を処理"""

        while True:
            # 音声合成命令をキューから取り出し
            cmd = self.talk_command_queue.get()
            print("OpenJTalkController::process_input(): " +
                  "command received: {0}"
                  .format(cmd))

            # 音声合成を実行
            sp.run(["./openjtalk-start.sh", cmd["sentence"]])
            
            # 音声合成を完了
            self.talk_command_queue.task_done()

        return
    
    def send_command(self, cmd):
        """命令キューに新たな命令を追加"""
        self.talk_command_queue.put(cmd)
        return

    def wait_until_all_command_done(self):
        """命令キューに追加された命令が全て実行されるまで待機"""
        self.talk_command_queue.join()
        return

    def run(self):
        """音声合成命令を処理するプロセスを起動"""
        self.process_handler.start()
        return
    
    def emergency_stop(self):
        """音声合成命令を処理するプロセスを緊急停止"""
        self.process_handler.terminate()
        return

