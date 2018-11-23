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

    def __init__(self, process_manager, msg_queue):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)
        
        # ノードに送られる命令を保持するキュー(プロセス間で共有)
        self.initialize_command_queue()

        # コマンドを実行するためのプロセス
        self.initialize_process_handler()

    def initialize_command_queue(self):
        """ノードに送られる命令を保持するキューを初期化"""
        self.command_queue = self.process_manager.Queue()
    
    def initialize_process_handler(self):
        """コマンドを実行するためのプロセスを作成"""
        # ノードの状態を格納するディクショナリstate_dictと,
        # ノードに送られる命令を保持するキューcommand_queueは
        # プロセス間で共有されているため, メソッドの引数として指定しない
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

    def run(self):
        """ノードの実行を開始"""
        self.process_handler.start()
    
    def terminate(self):
        """ノードの実行を停止"""
        self.process_handler.terminate()

        # ノードの状態を格納するディクショナリを再初期化
        self.initialize_state_dict()
        # ノードに送られる命令を格納するキューを再初期化
        self.initialize_command_queue()
        # コマンドを実行するためのプロセスを再初期化
        # プロセスを再度初期化することで再び実行を開始できるようになる
        self.initialize_process_handler()
        
