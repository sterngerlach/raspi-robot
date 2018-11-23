# coding: utf-8
# node.py

class Node(object):
    """
    ノードを表す基底クラス
    """

    def __init__(self, process_manager, msg_queue):
        """コンストラクタ"""
        
        # プロセス間でオブジェクトを共有するために使用するマネージャ
        self.process_manager = process_manager
        # ノードの状態を格納するディクショナリ(プロセス間で共有)
        self.initialize_state_dict()
        # ノードからアプリケーションへのメッセージのキュー(プロセス間で共有)
        self.msg_queue = msg_queue
    
    def initialize_state_dict(self):
        """ノードの状態を格納するディクショナリを初期化"""
        self.state_dict = self.process_manager.dict()

    def run(self):
        """ノードの実行を開始"""
        raise NotImplementedError()

    def send_message(self, sender_name, msg):
        """アプリケーションにメッセージを送信"""
        send_msg = { "sender": sender_name, "content": msg }
        self.msg_queue.put(send_msg)

