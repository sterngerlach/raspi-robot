# coding: utf-8
# node.py

class Node(object):
    """
    ノードを表す基底クラス
    """

    def __init__(self, state_dict):
        """コンストラクタ"""

        # ノードの状態を格納するディクショナリ(プロセス間で共有)
        self.state_dict = state_dict

    def run():
        """ノードの実行を開始"""
        raise NotImplementedError()

