# coding: utf-8
# srf02_node.py

import multiprocessing as mp
import time

from data_sender_node import DataSenderNode

class Srf02Node(DataSenderNode):
    """
    超音波センサ(Srf02)を操作するクラス
    """

    def __init__(self, process_manager, msg_queue,
                 srf02, distance_threshold=15,
                 near_obstacle_threshold=5,
                 interval=0.5, addr_list=[0x70]):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # 超音波センサ(Srf02)
        self.srf02 = srf02
        # 障害物に接近したと判定する距離の閾値
        self.distance_threshold = distance_threshold
        # 測定値を連続何回下回ったときに障害物の接近を判断するか
        self.near_obstacle_threshold = near_obstacle_threshold
        # 超音波センサの値を取得する間隔
        self.interval = interval
        # 超音波センサのアドレスのリスト
        self.addr_list = addr_list
        # 指数移動平均のパラメータ(平滑化係数)
        self.smoothing_coeff = 0.75

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
                    
                    if result is None:
                        continue

                    # 測距データと最小の距離を取得
                    dist, mindist = result

                    # 各アドレスの超音波センサの情報を更新
                    if self.state_dict[addr] is None:
                        self.state_dict[addr] = {
                            "dist": dist, "mindist": mindist,
                            "near": 1 if dist <= self.distance_threshold else 0 }
                    else:
                        # 指数移動平均により計測値を平滑化
                        dist = self.state_dict[addr]["dist"] * self.smoothing_coeff + \
                            dist * (1.0 - self.smoothing_coeff)
                        # 何回連続して障害物に接近したと判定されているか
                        near = self.state_dict[addr]["near"] + 1 \
                            if dist <= self.distance_threshold else 0
                        self.state_dict[addr] = { "dist": dist, "mindist": mindist, "near": near }
                        
                        # 5回以上連続して障害物の接近と判定された場合
                        if near >= self.near_obstacle_threshold:
                            # アプリケーションにメッセージを送出
                            self.send_message("srf02", { "addr": addr, "state": "obstacle-detected" })

                time.sleep(self.interval)

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("Srf02Node::update(): KeyboardInterrupt occurred")
        
