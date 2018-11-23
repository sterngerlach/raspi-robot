# coding: utf-8
# srf02_node.py

import multiprocessing as mp
import time

from data_sender_node import DataSenderNode

class Srf02Node(DataSenderNode):
    """
    超音波センサ(Srf02)を操作するクラス
    """

    def __init__(self,
        state_dict, msg_queue,
        srf02, interval=0.5, addr_list=[0x70]):
        """コンストラクタ"""
        super().__init__(state_dict, msg_queue)

        # 超音波センサ(Srf02)
        self.srf02 = srf02
        # 超音波センサの値を取得する間隔
        self.interval = interval
        # 超音波センサのアドレスのリスト
        self.addr_list = addr_list

        # 各アドレスに対応する超音波センサの情報を初期化
        for addr in self.addr_list:
            self.state_dict[addr] = None
            
    def update(self):
        """入力を処理して状態を更新"""

        try:
            while True:
                for addr in self.addr_list:
                    # 各アドレスの超音波センサから距離を取得
                    result = self.srf02.get_values(addr)

                    if result is not None:
                        # 測距データと最小の距離を取得
                        dist, mindist = result
                        # 各アドレスの超音波センサの情報を更新
                        self.state_dict[addr] = { "dist": dist, "mindist": mindist }

                time.sleep(self.interval)

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("Srf02Node::update(): KeyboardInterrupt occurred")
        
