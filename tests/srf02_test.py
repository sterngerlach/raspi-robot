#!/usr/bin/env python3
# srf02_test.py

import smbus
import time

# 指定したマイクロ秒だけスリープ
usleep = lambda x: time.sleep(x / (10.0 ** 6))

def main():
    # I2Cデータバス(/dev/i2c-1)を開く
    i2c = smbus.SMBus(1)

    # アドレス0xE0のセンサに対して距離を測定
    addr = 0x70
    
    try:
        # コマンドレジスタ0を指定してコマンドを送信
        # コマンド0x51(Real Ranging Mode (Result in centimeters))を送信
        i2c.write_byte_data(addr, 0x00, 0x51)

        # 音波を用いるため適当な時間待機
        usleep(80000)
        
        # コマンドレジスタ2を指定して測距データを取得
        dist = i2c.read_word_data(addr, 2) >> 8

        # コマンドレジスタ4を指定して最小の距離を取得
        mindist = i2c.read_word_data(addr, 4) >> 8

        # コマンドレジスタ2を指定して測距データの上位バイトを取得
        # i2c.write_byte(addr, 0x02)
        # dist = i2c.read_byte(addr)
        # dist = dist << 8
        
        # コマンドレジスタ3を指定して測距データの下位バイトを取得
        # i2c.write_byte(addr, 0x03)
        # dist |= i2c.read_byte(addr)
        
        # 取得された距離を表示
        print("(0xE0) dist: {0} cm, mindist: {1} cm".format(dist, mindist))
    except IOError:
        print("IOError occurred")

    # アドレス0xE2のセンサに対して距離を測定
    addr = 0x71
    
    try:
        # コマンドレジスタ0を指定してコマンドを送信
        # コマンド0x51(Real Ranging Mode (Result in centimeters))を送信
        i2c.write_byte_data(addr, 0x00, 0x51)

        # 音波を用いるため適当な時間待機
        usleep(80000)

        # コマンドレジスタ2を指定して測距データを取得
        dist = i2c.read_word_data(addr, 2) >> 8

        # コマンドレジスタ4を指定して最小の距離を取得
        mindist = i2c.read_word_data(addr, 4) >> 8
        
        # コマンドレジスタ2を指定して測距データの上位バイトを取得
        # i2c.write_byte(addr, 0x02)
        # dist = i2c.read_byte(addr)
        # dist = dist << 8
        
        # コマンドレジスタ3を指定して測距データの下位バイトを取得
        # i2c.write_byte(addr, 0x03)
        # dist |= i2c.read_byte(addr)
        
        # 取得された距離を表示
        print("(0xE0) dist: {0} cm, mindist: {1} cm".format(dist, mindist))
    except IOError:
        print("IOError occurred")

    # I2C通信を閉じる
    i2c.close()

if __name__ == "__main__":
    main()

