# coding: utf-8
# motor_server_test.py

from motor_server import *

def main():
    # モータの操作命令を待ち受けるサーバを作成
    motor_server = MotorServer(
        MotorServer.MOTOR_SERVER_HOST,
        MotorServer.MOTOR_SERVER_PORT)

    # モータの操作命令を待つ
    motor_server.run()

if __name__ == "__main__":
    main()

