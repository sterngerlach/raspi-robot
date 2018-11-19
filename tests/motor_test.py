#!/usr/bin/env python3
# motor_test.py

import struct
import sys
import time
import wiringpi as w

L6470_SPI_CHANNEL = 0
L6470_SPI_SPEED = 1000000

# 黒い導線が結びつけてあるSPIケーブルはチャネル0番
# チャネル0番のSPIケーブルは左側のモータのモータドライバに接続

def main(argv=sys.argv[1:]):
    global L6470_SPI_CHANNEL

    print("starting up motor test program ...")

    if w.wiringPiSPISetup(0, L6470_SPI_SPEED) < 0:
        print("wiringpi.wiringPiSPISetup() failed")
        return

    if w.wiringPiSPISetup(1, L6470_SPI_SPEED) < 0:
        print("wiringpi.wiringPiSPISetup() failed")
        return

    # ステッピングモータL6470の初期化
    L6470_SPI_CHANNEL = 0
    motor_l6470_init()
    L6470_SPI_CHANNEL = 1
    motor_l6470_init()

    if argv[0] == "accel":
        speed = 0

        # モータを徐々に加速
        for i in range(10):
            speed += 2000

            L6470_SPI_CHANNEL = 0
            motor_l6470_run(speed)
            L6470_SPI_CHANNEL = 1
            motor_l6470_run(-1 * speed)

            time.sleep(1)
    elif argv[0] == "brake":
        speed = 20000

        # モータを徐々に減速
        for i in range(10):
            speed -= 2000

            L6470_SPI_CHANNEL = 0
            motor_l6470_run(speed)
            L6470_SPI_CHANNEL = 1
            motor_l6470_run(-1 * speed)

            time.sleep(1)
    elif argv[0] == "stop":
        # モータを停止
        L6470_SPI_CHANNEL = 0
        motor_l6470_softstop()
        motor_l6470_softhiz()

        L6470_SPI_CHANNEL = 1
        motor_l6470_softstop()
        motor_l6470_softhiz()

    return

def motor_l6470_write(data):
    global L6470_SPI_CHANNEL

    # 1バイトのデータを書き込み
    data = struct.pack("B", data)
    w.wiringPiSPIDataRW(L6470_SPI_CHANNEL, data)

    return

def motor_l6470_init():
    # レジスタアドレス(MAX_SPEEDレジスタ)
    motor_l6470_write(0x07)
    
    # 最大回転スピード値(10ビット)
    # 初期値は0x41
    motor_l6470_write(0x00)
    motor_l6470_write(0x25)

    # レジスタアドレス(KVAL_HOLDレジスタ)
    motor_l6470_write(0x09)
    # モータ停止中の電圧(8ビット)
    motor_l6470_write(0xFF)

    # レジスタアドレス(KVAL_RUNレジスタ)
    motor_l6470_write(0x0A)
    # モータ定速回転中の電圧(8ビット)
    motor_l6470_write(0xFF)

    # レジスタアドレス(KVAL_ACCレジスタ)
    motor_l6470_write(0x0B)
    # モータ加速中の電圧(8ビット)
    motor_l6470_write(0xFF)

    # レジスタアドレス(KVAL_DECレジスタ)
    motor_l6470_write(0x0C)
    # モータ減速中の電圧(8ビット)
    motor_l6470_write(0x40)

    # レジスタアドレス(OCD_THレジスタ)
    motor_l6470_write(0x13)
    # オーバーカレントスレッショルド(4ビット)
    # 最大値の6Aに設定
    motor_l6470_write(0x0F)

    # レジスタアドレス(STALL_THレジスタ)
    motor_l6470_write(0x14)
    # ストール電流スレッショルド(4ビット)
    # 最大値の4Aに設定
    motor_l6470_write(0x7F)

    # レジスタアドレス(ST_SLPレジスタ)
    motor_l6470_write(0x0E)
    # スタートスロープ
    motor_l6470_write(0x00)

    # レジスタアドレス(FN_SLP_DECレジスタ)
    motor_l6470_write(0x10)
    # デセラレーションファイナルスロープ
    motor_l6470_write(0x29)

    return

def motor_l6470_run(speed):
    global L6470_SPI_CHANNEL

    print("motor_l6470_run() channel: {0}, speed: {1}".format(L6470_SPI_CHANNEL, speed))
    
    # スピードが正であれば前進, 負であれば後進
    cmd = 0x50 if speed < 0 else 0x51
    speed = abs(speed)

    print(speed)

    # モータ回転のコマンドを送信
    motor_l6470_write(cmd)

    # モータの回転速度を送信
    motor_l6470_write((0x0F0000 & speed) >> 16)
    motor_l6470_write((0x00FF00 & speed) >> 8)
    motor_l6470_write((0x0000FF & speed))

    return

def motor_l6470_softstop():
    print("motor_l6470_softstop()")

    # モータを減速させて停止
    motor_l6470_write(0xB0)

    # 1秒待つ
    # TODO: モータが停止するまでの間はビジーフラグが立つ
    time.sleep(1)

    return

def motor_l6470_softhiz():
    print("motor_l6470_softhiz()")

    # ブリッジを高インピーダンスに設定
    motor_l6470_write(0xA0)

    # 1秒待つ
    # TODO: モータが停止するまでの間はビジーフラグが立つ
    time.sleep(1)

    return

if __name__ == "__main__":
    main()

