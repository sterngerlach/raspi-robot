# coding: utf-8
# command_receiver_node.py

import multiprocessing as mp

from node import Node

class UnknownCommandException(Exception):
    """
    受け取ったコマンドが不明であることを表す例外クラス
    """
    pass

class CommandReceiverNode(Node):
    """
    コマンドを受け取って実行するノードを表す基底クラス
    """

    def __init__(self, state_dict, command_queue):
        """コンストラクタ"""
        super().__init__(state_dict)

        # ノードに送られる命令を保持するキュー(プロセス間で共有)
        self.command_queue = command_queue

        # コマンドを実行するためのプロセスを作成
        # ノードの状態を格納するディクショナリstate_dictと,
        # ノードに送られる命令を保持するキューcommand_queueは
        # プロセス間で共有されているが, メソッドの引数として指定
        self.process_handler = mp.Process(target=self.process_command, args=())
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True

    def process_command(self):
        """コマンドをキューから取り出して実行"""
        raise NotImplementedError()

    def send_command(self, cmd):
        """命令キューに新たな命令を追加"""
        self.command_queue.put(cmd)

    def wait_until_all_command_done(self):
        """命令キューに追加された命令が全て実行されるまで待機"""
        self.command_queue.join()

    def run():
        """ノードの実行を開始"""
        self.process_handler.start()

