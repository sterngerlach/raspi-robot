# coding: utf-8
# openjtalk_node.py

import multiprocessing as mp
import pathlib
import os
import subprocess as sp
import time

from command_receiver_node import CommandReceiverNode

class OpenJTalkNode(CommandReceiverNode):
    """
    音声合成システムOpenJTalkを操作するクラス
    """

    def __init__(self, process_manager, msg_queue):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

        # OpenJTalkを開始するスクリプトのパス
        self.openjtalk_startup_script_path = \
            file_dir.parent.joinpath("scripts", "openjtalk-start.sh")

        # 音声ファイルが保存されているディレクトリ
        self.audio_files_dir = file_dir.parent.joinpath("audio")

    def process_command(self):
        """音声合成命令を処理"""

        try:
            while True:
                # 音声合成命令をキューから取り出し
                cmd = self.command_queue.get()
                print("OpenJTalkNode::process_command(): command received: {0}".format(cmd))

                if "file_name" in cmd:
                    # 音声ファイルが指定された場合は再生
                    audio_file_path = self.audio_files_dir.joinpath(cmd["file_name"])
                    self.send_message("openjtalk", { "file_name": cmd["file_name"], "state": "start" })
                    sp.run(["aplay", "--quiet", str(audio_file_path)])
                    self.send_message("openjtalk", { "file_name": cmd["file_name"], "state": "done" })
                elif "sentence" in cmd:
                    # 文章が指定された場合は音声合成を実行
                    self.send_message("openjtalk", { "sentence": cmd["sentence"], "state": "start" })
                    sp.run([str(self.openjtalk_startup_script_path), cmd["sentence"]])
                    self.send_message("openjtalk", { "sentence": cmd["sentence"], "state": "done" })
                
                # 音声合成を完了
                self.command_queue.task_done()
        
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("OpenJTalkNode::process_command(): KeyboardInterrupt occurred")

