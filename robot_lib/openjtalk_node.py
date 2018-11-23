# coding: utf-8
# openjtalk_node.py

import multiprocessing as mp
import subprocess as sp
import time

from command_receiver_node import CommandReceiverNode

class OpenJTalkNode(CommandReceiverNode):
    """
    音声合成システムOpenJTalkを操作するクラス
    """

    def __init__(self, process_manager, msg_queue,
                 openjtalk_startup_script_path="../scripts/openjtalk-start.sh"):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # OpenJTalkを開始するスクリプトのパス
        self.openjtalk_startup_script_path = openjtalk_startup_script_path

    def process_command(self):
        """音声合成命令を処理"""

        try:
            while True:
                # 音声合成命令をキューから取り出し
                cmd = self.command_queue.get()
                print("OpenJTalkNode::process_command(): command received: {0}".format(cmd))

                # 音声合成を実行
                sp.run([self.openjtalk_startup_script_path, cmd["sentence"]])
                
                # 音声合成を完了
                self.command_queue.task_done()
        
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("OpenJTalkNode::process_command(): KeyboardInterrupt occurred")

