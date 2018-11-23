# coding: utf-8
# node.py

class Node(object):
    """
    ノードを表す基底クラス
    """

    def __init__(self, state_dict, msg_queue):
        """コンストラクタ"""

        # ノードの状態を格納するディクショナリ(プロセス間で共有)
        self.state_dict = state_dict
        # ノードからアプリケーションへのメッセージのキュー(プロセス間で共有)
        self.msg_queue = msg_queue

    def run(self):
        """ノードの実行を開始"""
        raise NotImplementedError()
    
    def send_message(self, sender_name, msg):
        """アプリケーションにメッセージを送信"""
        send_msg = { "sender": sender_name, "content": msg }
        self.msg_queue.put(send_msg)

