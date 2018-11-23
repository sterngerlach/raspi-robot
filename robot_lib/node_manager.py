# coding: utf-8
# node_manager.py

import multiprocessing as mp
import os
import pathlib

from data_sender_node import DataSenderNode
from command_receiver_node import CommandReceiverNode, UnknownCommandException
from motor_l6470 import MotorL6470
from motor_node import MotorNode
from srf02 import Srf02
from srf02_node import Srf02Node
from julius_node import JuliusNode
from openjtalk_node import OpenJTalkNode
from webcam_node import WebCamNode

class NodeManager(object):
    """
    ロボットの各モジュールの管理クラス
    """

    def __init__(self, config_dict):
        """コンストラクタ"""

        # マネージャを作成
        self.__process_manager = mp.Manager()

        # データを読み取るノード
        self.__data_sender_nodes = {}
        # コマンドを受け取って実行するノード
        self.__command_receiver_nodes = {}

        # ロボットの設定を保持するディクショナリ
        self.__config_dict = config_dict

        # ノードからアプリケーションへのメッセージのキュー
        self.__msg_queue = self.__process_manager.Queue()
        
        # モータのノードを初期化
        if self.__config_dict["enable_motor"]:
            self.__setup_motor_node(config_dict["motor"])
        
        # 超音波センサのノードを初期化
        if self.__config_dict["enable_srf02"]:
            self.__setup_srf02_node(config_dict["srf02"])

        # 音声認識エンジンJuliusのノードを初期化
        if self.__config_dict["enable_julius"]:
            self.__setup_julius_node(config_dict["julius"])

        # 音声合成システムOpenJTalkのノードを初期化
        if self.__config_dict["enable_openjtalk"]:
            self.__setup_openjtalk_node(config_dict["openjtalk"])

        # ウェブカメラのノードを初期化
        if self.__config_dict["webcam"]:
            self.__setup_webcam_node(config_dict["webcam"])

    def __setup_motor_node(self, config_dict):
        """モータのノードを初期化"""

        # モータの状態を保持するディクショナリ
        self.__motor_state_dict = self.__process_manager.dict()
        # モータへの命令を保持するキュー
        self.__motor_command_queue = self.__process_manager.Queue()
        # 左右のモータを初期化
        self.__motor_left = MotorL6470(spi_channel=0)
        self.__motor_right = MotorL6470(spi_channel=1)
        # モータのノードを作成
        self.__motor_node = MotorNode(
            self.__motor_state_dict, self.__msg_queue,
            self.__motor_command_queue,
            self.__motor_left, self.__motor_right)

        # モータのノードを追加
        self.__add_command_receiver_node(
            "motor", self.__motor_state_dict, self.__motor_node)

    def __setup_srf02_node(self, config_dict):
        """超音波センサのノードを初期化"""

        # 超音波センサの状態を保持するディクショナリ
        self.__srf02_state_dict = self.__process_manager.dict()
        # 超音波センサを初期化
        self.__srf02 = Srf02()
        # 超音波センサのノードを作成
        self.__srf02_node = Srf02Node(
            self.__srf02_state_dict, self.__msg_queue, self.__srf02,
            config_dict["interval"], config_dict["addr_list"])

        # 超音波センサのノードを追加
        self.__add_data_sender_node(
            "srf02", self.__srf02_state_dict, self.__srf02_node)

    def __setup_julius_node(self, config_dict):
        """音声認識エンジンJuliusのノードを初期化"""

        # 音声認識エンジンJuliusの状態を保持するディクショナリ
        self.__julius_state_dict = self.__process_manager.dict()
        
        # 音声認識エンジンJuliusを開始するスクリプトのパスを設定
        file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
        script_path = file_dir.parent.joinpath("scripts", "julius-start.sh")

        # 音声認識エンジンJuliusのノードを初期化
        self.__julius_node = JuliusNode(
            self.__julius_state_dict, self._msg_queue,
            str(script_path))

        # 音声認識エンジンJuliusのノードを追加
        self.__add_data_sender_node(
            "julius", self.__julius_state_dict, self.__julius_node)

    def __setup_openjtalk_node(self, config_dict):
        """音声合成システムOpenJTalkのノードを初期化"""

        # 音声合成システムOpenJTalkの状態を保持するディクショナリ
        self.__openjtalk_state_dict = self.__process_manager.dict()
        # 音声合成システムOpenJTalkへの命令を保持するキュー
        self.__openjtalk_command_queue = self.__process_manager.Queue()
        
        # 音声合成システムOpenJTalkを開始するスクリプトのパスを設定
        file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__))
        script_path = file_dir.parent.joinpath("scripts", "openjtalk-start.sh")

        # 音声合成システムOpenJTalkのノードを初期化
        self.__openjtalk_node = OpenJTalkNode(
            self.__openjtalk_state_dict, self.__msg_queue,
            self.__openjtalk_command_queue, str(script_path))

        # 音声合成システムOpenJTalkのノードを追加
        self.__add_command_receiver_node(
            "openjtalk", self.__openjtalk_state_dict, self.__openjtalk_node)

    def __setup_webcam_node(self, config_dict):
        """ウェブカメラを操作するノードを初期化"""

        # ウェブカメラの状態を保持するディクショナリ
        self.__webcam_state_dict = self.__process_manager.dict()
        # ウェブカメラのノードを作成
        self.__webcam_node = WebCamNode(
            self.__webcam_state_dict, self.__msg_queue, camera_id=0)
        
        # ウェブカメラのノードを追加
        self.__add_data_sender_node(
            "webcam", self.__webcam_state_dict, self.__webcam_node)

    def __add_data_sender_node(self, name, state_dict, node):
        """指定された名前を持つノードを追加"""
        self.__data_sender_nodes[name] = { "states": state_dict, "node": node }
        
    def __add_command_receiver_node(self, name, state_dict, node):
        """指定された名前を持つノードを追加"""
        self.__command_receiver_nodes[name] = { "states": state_dict, "node": node }

    def run_nodes(self):
        """ノードの実行を開始"""
        for data_sender in self.__data_sender_nodes:
            data_sender["node"].run()

        for command_receiver in self.__command_receiver_nodes:
            command_receiver["node"].run()
    
    def send_command(self, name, cmd):
        """指定された名前のノードにコマンドを送信"""
        self.__command_receiver_nodes[name]["node"].send_command(cmd)

    def get_node_state(self, name):
        """指定された名前のノードの状態を取得"""
        if name in self.__data_sender_nodes:
            return self.__data_sender_nodes[name]["states"]
        elif name in self.__command_receiver_nodes:
            return self.__command_receiver_nodes[name]["states"]
        else:
            return None

    def get_msg_queue(self):
        """アプリケーションへのメッセージのキューを取得"""
        return self.__msg_queue

