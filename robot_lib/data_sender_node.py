# coding: utf-8
# data_sender_node.py

import multiprocessing as mp

from node import Node

class DataSenderNode(Node):
    """
    データを読み取るノードを表す基底クラス
    """

    def __init__(self, process_manager, msg_queue):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # 入力を処理するためのプロセス
        self.initialize_process_handler()

    def initialize_process_handler(self):
        """入力を処理するためのプロセスを作成"""
        # ノードの状態を格納するディクショナリstate_dictは
        # プロセス間で共有されているため, メソッドの引数として指定しない
        self.process_handler = mp.Process(target=self.update, args=())
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True

    def update(self):
        """入力を処理して状態を更新"""
        raise NotImplementedError()

    def run(self):
        """ノードの実行を開始"""
        self.process_handler.start()
    
