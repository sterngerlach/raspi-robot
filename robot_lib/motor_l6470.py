# coding: utf-8
# motor_l6470.py

import struct
import sys
import time
import wiringpi as wp

class MotorInitFailedException(Exception):
    """
    モータの初期化に失敗したことを表す例外クラス
    """
    pass

class MotorL6470(object):
    """
    ステッピングモータ(L6470)を操作するクラス
    """

    # SPIのクロック周波数
    L6470_SPI_SPEED = 10 ** 6

    def __init__(self, spi_channel, speed=L6470_SPI_SPEED):
        """コンストラクタ"""
        print("MotorL6470::__init__(): channel: {0}, speed: {1}"
              .format(spi_channel, speed))
        
        # 使用するSPIチャネル
        self.channel = spi_channel

        # SPIチャネルはwiringpi::wiringPiSPISetup()関数の呼び出しによって,
        # 初期化済みであると仮定する

        # モータのセットアップ
        self.setup()

    def read_byte(self):
        """1バイトのデータを読み込み"""
        
        # 空のbytesオブジェクト(バイト数1)を作成
        data = bytes(1)
        # 1バイトのデータを読み込み
        retlen, retdata = wp.wiringPiSPIDataRW(self.channel, data)

        if retlen < 1:
            print("MotorL6470::read_byte(): " +
                  "could not receive the byte data")

        return data
        
    def write_byte(self, data):
        """1バイトのデータを書き込み"""

        # bytesオブジェクトを作成
        # byteorderにbigを指定すると配列の最初が最上位バイトとなる
        data = data.to_bytes(1, byteorder="big")
        wp.wiringPiSPIDataRW(self.channel, data)

    def read_bytes(self, length_in_bytes):
        """指定されたバイト数のデータを読み込み"""

        # 空のbytesオブジェクト(バイト数length_in_bytes)を作成
        data = bytes(length_in_bytes)
        # length_in_bytesバイトのデータを読み込み
        retlen, retdata = wp.wiringPiSPIDataRW(self.channel, data)

        if retlen < length_in_bytes:
            print("MotorL6470::read_bytes(): " +
                  "the number of bytes received is less than the desired one")
        
        return data

    def write_bytes(self, data, length_in_bytes):
        """指定されたバイト数のデータを書き込み"""

        # bytesオブジェクトを作成
        data = data.to_bytes(length_in_bytes, byteorder="big")
        wp.wiringPiSPIDataRW(self.channel, data)

    def setup(self):
        """モータのセットアップ"""

        print("MotorL6470::setup(): channel: {0}".format(self.channel))

        # レジスタアドレス(MAX_SPEEDレジスタ)
        self.write_byte(0x07)
        
        # 最大回転スピード値(10ビット)
        # 初期値は0x41
        self.write_byte(0x00)
        self.write_byte(0x25)

        # レジスタアドレス(KVAL_HOLDレジスタ)
        self.write_byte(0x09)
        # モータ停止中の電圧(8ビット)
        self.write_byte(0xFF)

        # レジスタアドレス(KVAL_RUNレジスタ)
        self.write_byte(0x0A)
        # モータ定速回転中の電圧(8ビット)
        self.write_byte(0xFF)

        # レジスタアドレス(KVAL_ACCレジスタ)
        self.write_byte(0x0B)
        # モータ加速中の電圧(8ビット)
        self.write_byte(0xFF)

        # レジスタアドレス(KVAL_DECレジスタ)
        self.write_byte(0x0C)
        # モータ減速中の電圧(8ビット)
        self.write_byte(0x40)

        # レジスタアドレス(OCD_THレジスタ)
        self.write_byte(0x13)
        # オーバーカレントスレッショルド(4ビット)
        # 最大値の6Aに設定
        self.write_byte(0x0F)

        # レジスタアドレス(STALL_THレジスタ)
        self.write_byte(0x14)
        # ストール電流スレッショルド(4ビット)
        # 最大値の4Aに設定
        self.write_byte(0x7F)

        # レジスタアドレス(ST_SLPレジスタ)
        self.write_byte(0x0E)
        # スタートスロープ
        self.write_byte(0x00)

        # レジスタアドレス(FN_SLP_DECレジスタ)
        self.write_byte(0x10)
        # デセラレーションファイナルスロープ
        self.write_byte(0x29)

    def get_status(self):
        """モータの状態を取得"""

        print("MotorL6470::get_status(): channel: {0}".format(self.channel))
        
        # モータの状態取得のコマンドを送信
        self.write_byte(0xD0)

        # モータの状態を取得
        data_bytes = self.read_bytes(2)
        status = ((data_bytes[0] << 8) | data_bytes[1]) & 0xFFFF

        return status

    def run(self, speed):
        """モータを所定の速度で回転"""
        
        # print("MotorL6470::run(): channel: {0}, speed: {1}"
        #       .format(self.channel, speed))
        
        # スピードが正であれば前進, 負であれば後進
        cmd = 0x50 if speed < 0 else 0x51
        speed = abs(speed)

        # モータ回転のコマンドを送信
        self.write_byte(cmd)

        # モータの回転速度を送信
        self.write_byte((0x0F0000 & speed) >> 16)
        self.write_byte((0x00FF00 & speed) >> 8)
        self.write_byte((0x0000FF & speed))

    def softstop(self):
        """モータを減速させて停止"""

        print("MotorL6470::softstop(): channel: {0}".format(self.channel))

        # モータ停止のコマンドを送信
        self.write_byte(0xB0)
        
        while True:
            # モータの状態を取得
            status = self.get_status()

            # ビジーフラグが立っている場合は適当な時間だけ待つ
            if (status & 0x2):
                print("MotorL6470::softstop(): busy flag is set")
                time.sleep(0.05)

            break

    def softhiz(self):
        """モータのブリッジを高インピーダンスに設定"""

        print("MotorL6470::softhiz(): channel: {0}".format(self.channel))

        # ブリッジを高インピーダンスに設定
        self.write_byte(0xA0)

        while True:
            # モータの状態を取得
            status = self.get_status()

            # ビジーフラグが立っている場合は適当な時間だけ待つ
            if (status & 0x2):
                print("MotorL6470::softstop(): busy flag is set")
                time.sleep(0.05)

            break

