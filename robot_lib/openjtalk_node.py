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

    def __init__(self, state_dict, command_queue,
        openjtalk_startup_script_path="../scripts/openjtalk-start.sh"):
        """コンストラクタ"""
        super().__init__(state_dict, command_queue)

    def process_command(self):
        """音声合成命令を処理"""

        while True:
            # 音声合成命令をキューから取り出し
            cmd = self.command_queue.get()
            print("OpenJTalkNode::process_input(): command received: {0}".format(cmd))

            # 音声合成を実行
            sp.run(["./openjtalk-start.sh", cmd["sentence"]])
            
            # 音声合成を完了
            self.talk_command_queue.task_done()
    
