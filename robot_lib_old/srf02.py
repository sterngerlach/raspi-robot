# coding: utf-8
# srf02.py

import smbus
import time

from util import usleep

class Srf02(object):
    """
    超音波センサ(SRF02)を操作するクラス
    """
    def __init__(self):
        """コンストラクタ"""
        # I2Cデータバス(/dev/i2c-1)をオープン
        # 引数の1はデータバス番号(/dev/i2c-1の1)に対応
        self.i2c = smbus.SMBus(1)

    def __del__(self):
        """デストラクタ"""
        # I2Cデータバス(/dev/i2c-1)をクローズ
        self.i2c.close()
        
    def get_values(self, addr):
        """指定したアドレスを持つ超音波センサから値を取得"""

        try:
            # コマンドレジスタ0を指定してコマンドを送信
            # コマンド0x51(Real Ranging Mode (Result in centimeters))を送信
            self.i2c.write_byte_data(addr, 0x00, 0x51)

            # 音波を用いるため適当な時間待機(66ミリ秒以上)
            usleep(80000)
            
            # コマンドレジスタ2を指定して測距データ(センチメートル)を取得
            dist = self.i2c.read_word_data(addr, 2) >> 8
            # コマンドレジスタ4を指定して最小の距離(センチメートル)を取得
            mindist = self.i2c.read_word_data(addr, 4) >> 8
           
            # 取得された距離を返す
            return (dist, mindist)
        except IOError:
            # データの取得に失敗
            print("Srf02::get_values(): IOError occurred")
            return None

