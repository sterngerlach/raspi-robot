# coding: utf-8
# data_sender_node.py

import multiprocessing as mp

from node import Node

class DataSenderNode(Node):
    """
    データを読み取るノードを表す基底クラス
    """

    def __init__(self, state_dict):
        """コンストラクタ"""
        super().__init__(state_dict)

        # 入力を処理するためのプロセスを作成
        # ノードの状態を格納するディクショナリstate_dictは
        # プロセス間で共有されているが, メソッドの引数として指定
        self.process_handler = mp.Process(target=self.update, args=())
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True

    def update(self):
        """入力を処理して状態を更新"""
        raise NotImplementedError()

    def run():
        """ノードの実行を開始"""
        self.process_handler.start()

