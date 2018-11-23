# coding: utf-8
# julius_controller.py

import multiprocessing as mp
import socket
import subprocess as sp
import time
import xml.etree.ElementTree as ET

class JuliusController(object):
    """
    音声認識エンジンJuliusを操作するクラス
    """

    # JuliusサーバのIPアドレスまたはホスト名
    JULIUS_SERVER_HOST = "127.0.0.1"

    # Juliusサーバが使用するポート番号
    JULIUS_SERVER_PORT = 10500

    def __init__(self, motor_command_queue):
        """コンストラクタ"""

        # Juliusをモジュールモードで起動
        self.julius_process = sp.Popen(
            ["./julius-start.sh"], stdout=sp.PIPE, shell=True)

        # JuliusのプロセスIDを取得
        self.julius_pid = str(self.julius_process.stdout.read().decode("utf-8"))
        self.julius_pid = self.julius_pid.strip()

        print("JuliusController::__init__(): " +
              "julius launched with pid {0}"
              .format(self.julius_pid))

        # サーバに接続するまで待機
        time.sleep(5)

        print("JuliusController::__init__(): establishing connection ...")

        # TCPソケットを作成
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TIME_WAIT状態のポートをbindできるように設定
        self.client_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

        # Juliusのサーバに接続
        self.client_socket.connect(
            (JuliusController.JULIUS_SERVER_HOST,
             JuliusController.JULIUS_SERVER_PORT))

        print("JuliusController::__init__(): connected to Julius server")
        
        # モータへの命令を管理するキュー
        self.motor_command_queue = motor_command_queue
        # 音声入力を処理するためのプロセスを作成
        self.process_handler = mp.Process(
            target=self.process_input, args=(self.motor_command_queue,))
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True
        
        return

    def __del__(self):
        """デストラクタ"""

        # プロセスを終了
        # self.process_handler.terminate()

        return

    def process_input(self, motor_command_queue):
        """音声入力を処理"""

        # 認識されると次のようなXML文字列が出力される
        """
        <RECOGOUT>
          <SHYPO RANK="1" SCORE="-3131.938965">
            <WHYPO WORD="" CLASSID="<s>" PHONE="silB" CM="0.724"/>
            <WHYPO WORD="こんにちは"
                CLASSID="こんにちは+感動詞"
                PHONE="k o N n i ch i w a"
                CM="0.390"/>
            <WHYPO WORD="。" CLASSID="</s>" PHONE="silE" CM="1.000"/>
          </SHYPO>
        </RECOGOUT>
        .
        """
        
        try:
            data = ""
            direction = ""

            while True:
                # 音声入力の処理
                            
                # 音声認識ができたとき
                if "</RECOGOUT>\n." in data:
                    # XML文字列を抜き出して整形
                    data_xml = data[data.find("<RECOGOUT>"):data.find("</RECOGOUT>\n.") + 11]
                    # 文章の開始を表す特殊な単語(vocaファイルを参照)
                    data_xml = data_xml.replace("[s]", "start")
                    # 文章の末尾を表す特殊な単語(vocaファイルを参照)
                    data_xml = data_xml.replace("[/s]", "end")
                    # XMLヘッダを付加
                    data_xml = "<?xml version=\"1.0\"?>\n" + data_xml

                    # print("JuliusController::process_input(): " +
                    #       "retrieved xml: \n{0}"
                    #       .format(data_xml))

                    # XML文字列を解析
                    root = ET.fromstring(data_xml)
                    
                    # 認識できた語彙の処理
                    for whypo in root.findall("./SHYPO/WHYPO"):
                        # 認識できた語彙と認識精度を取得
                        word = whypo.get("WORD")
                        accuracy = float(whypo.get("CM"))
                        
                        print("JuliusController::process_input(): " +
                              "recognized word: {0}, accuracy: {1}"
                              .format(word, accuracy))

                        if word == "start" or word == "end":
                            continue

                        if accuracy < 0.95:
                            continue

                        # モータへ命令を送信
                        if word == "進め":
                            motor_cmd = { "command": "accel", "speed": 9000, "slope": 0.02 }
                            print("JuliusController::process_input(): " +
                                  "command has been sent: {0}"
                                  .format(motor_cmd))
                            motor_command_queue.put(motor_cmd)
                        elif word == "ブレーキ":
                            motor_cmd = { "command": "brake", "speed": 0, "slope": 0.02 }
                            print("JuliusController::process_input(): " +
                                  "command has been sent: {0}"
                                  .format(motor_cmd))
                            motor_command_queue.put(motor_cmd)
                        elif word == "ストップ":
                            motor_cmd = { "command": "stop" }
                            print("JuliusController::process_input(): " +
                                  "command has been sent: {0}"
                                  .format(motor_cmd))
                            motor_command_queue.put(motor_cmd)
                        elif word == "黙れ":
                            motor_cmd = { "command": "end" }
                            print("JuliusController::process_input(): " +
                                  "command has been sent: {0}"
                                  .format(motor_cmd))
                            motor_command_queue.put(motor_cmd)
                        elif word == "曲がれ":
                            motor_cmd = { "command": "rotate", "direction": direction }
                            print("JuliusController::process_input(): " +
                                  "command has been sent: {0}"
                                  .format(motor_cmd))
                            motor_command_queue.put(motor_cmd)
                        elif word == "左":
                            direction = "left"
                        elif word == "右":
                            direction = "right"
                    
                    # 入力データをクリア
                    data = ""
                else:
                    # 入力データをクリア
                    data += str(self.client_socket.recv(1024).decode("utf-8"))
                    # print("JuliusController::process_input(): data received: {0}"
                    #       .format(data))

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("JuliusController::process_input(): " +
                  "KeyboardInterrupt occurred")

            # Juliusのプロセスを終了
            self.julius_process.kill()
            sp.run(["kill -s 9 {0}".format(self.julius_pid)], shell=True)
            # ソケットを切断
            self.client_socket.close()

        return
    
    def run(self):
        """音声入力を開始"""

        # プロセスを開始
        self.process_handler.start()

        return
    
    def emergency_stop(self):
        """音声入力を緊急停止"""
        
        # プロセスを終了
        self.process_handler.terminate()

        return

