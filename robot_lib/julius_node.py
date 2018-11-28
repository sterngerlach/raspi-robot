# coding: utf-8
# julius_node.py

import multiprocessing as mp
import socket
import subprocess as sp
import time
import xml.etree.ElementTree as ET

from data_sender_node import DataSenderNode

class JuliusNode(DataSenderNode):
    """
    音声認識エンジンJuliusを操作するクラス
    """

    # JuliusサーバのIPアドレスまたはホスト名
    JULIUS_SERVER_HOST = "127.0.0.1"

    # Juliusサーバが使用するポート番号
    JULIUS_SERVER_PORT = 10500

    def __init__(self, process_manager, msg_queue,
                 julius_startup_script_path):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # Juliusをモジュールモードで起動
        self.julius_process = sp.Popen(
            [julius_startup_script_path], stdout=sp.PIPE, shell=True)

        # JuliusのプロセスIDを取得
        self.julius_pid = str(self.julius_process.stdout.read().decode("utf-8"))
        self.julius_pid = self.julius_pid.strip()

        print("JuliusNode::__init__(): julius launched with pid {0}"
              .format(self.julius_pid))

        # サーバに接続するまで待機
        time.sleep(5)

        print("JuliusNode::__init__(): establishing connection ...")

        # TCPソケットを作成
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TIME_WAIT状態のポートをbindできるように設定
        self.client_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

        # Juliusのサーバに接続
        self.client_socket.connect(
            (JuliusNode.JULIUS_SERVER_HOST, JuliusNode.JULIUS_SERVER_PORT))

        print("JuliusNode::__init__(): " +
              "connected to Julius server (host: {0}, port: {1})"
              .format(JuliusNode.JULIUS_SERVER_HOST,
                      JuliusNode.JULIUS_SERVER_PORT))
    
    def update(self):
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

            while True:
                # 音声入力の処理
                            
                # 音声認識ができない場合はデータを受信
                if "</RECOGOUT>\n." not in data:
                    # データを受信
                    data += str(self.client_socket.recv(128).decode("utf-8"))
                    continue
                
                # 音声認識ができた場合の処理

                # XML文字列を抜き出して整形
                data_xml = data[data.find("<RECOGOUT>"):data.find("</RECOGOUT>\n.") + 11]
                # 受信データからXML文字列を除去
                data = data[data.find("</RECOGOUT>\n.") + 12:]

                # 文章の開始を表す特殊な単語(vocaファイルを参照)
                data_xml = data_xml.replace("[s]", "start")
                # 文章の末尾を表す特殊な単語(vocaファイルを参照)
                data_xml = data_xml.replace("[/s]", "end")
                # XMLヘッダを付加
                data_xml = "<?xml version=\"1.0\"?>\n" + data_xml
                # XML文字列を解析
                root = ET.fromstring(data_xml)

                # 認識した語彙から認識結果のディクショナリを生成
                result_msg = { "words": [] }
                
                # 認識できた語彙の処理
                for whypo in root.findall("./SHYPO/WHYPO"):
                    # 認識できた語彙と認識精度を取得
                    word = whypo.get("WORD")
                    accuracy = float(whypo.get("CM"))
                    
                    print("JuliusNode::process_input(): word: {0}, accuracy: {1}"
                          .format(word, accuracy))
                    
                    # 最初と最後の語彙は無視
                    if word == "start" or word == "end":
                        continue
                    
                    # 認識した語彙を認識結果に追加
                    result_msg["words"].append((word, accuracy))
                    
                    # 認識した語彙が方向である場合
                    if word in ("左", "右"):
                        result_msg["direction"] = (word, accuracy)
                    # 認識した語彙が命令である場合
                    if word in ("進め", "ブレーキ", "ストップ", "黙れ", "曲がれ"):
                        result_msg["command"] = (word, accuracy)
                
                # 認識した語彙の情報をアプリケーションに送信
                self.send_message("julius", result_msg)
                
        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("JuliusNode::process_input(): KeyboardInterrupt occurred")

        finally:
            # Juliusのプロセスを終了
            self.julius_process.kill()
            sp.run(["kill -s 9 {0}".format(self.julius_pid)], shell=True)

            # ソケットを切断
            self.client_socket.close()

