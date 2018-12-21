# coding: utf-8
# node_manager.py

import multiprocessing as mp
import os
import pathlib
import wiringpi as wp

from data_sender_node import DataSenderNode
from command_receiver_node import CommandReceiverNode, UnknownCommandException
from motor_l6470 import MotorL6470
from motor_node import MotorNode
from servo_gws_s03t import ServoGwsS03t
from servo_motor_node import ServoMotorNode
from srf02 import Srf02
from srf02_node import Srf02Node
from julius_node import JuliusNode
from openjtalk_node import OpenJTalkNode
from google_speech_api_node import GoogleSpeechApiNode
from webcam_node import WebCamNode
from card_detection_node import CardDetectionNode
from motion_detection_node import MotionDetectionNode

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
        
        # SPIチャネルの個数
        self.__spi_channels_num = 2
        # GPIOが初期化されたかどうか
        self.__gpio_initialized = False
        # SPIが初期化されたかどうか
        self.__spi_initialized = [False for i in range(self.__spi_channels_num)]

        # モータのノードを初期化
        if self.__config_dict["enable_motor"]:
            self.__setup_motor_node(config_dict["motor"])

        # サーボモータのノードを初期化
        if self.__config_dict["enable_servo"]:
            self.__setup_servo_motor_node(config_dict["servo"])
        
        # 超音波センサのノードを初期化
        if self.__config_dict["enable_srf02"]:
            self.__setup_srf02_node(config_dict["srf02"])

        # 音声認識エンジンJuliusのノードを初期化
        if self.__config_dict["enable_julius"]:
            self.__setup_julius_node(config_dict["julius"])

        # 音声合成システムOpenJTalkのノードを初期化
        if self.__config_dict["enable_openjtalk"]:
            self.__setup_openjtalk_node(config_dict["openjtalk"])

        # Google Cloud Speech APIを利用した音声認識のノードを初期化
        if self.__config_dict["enable_speechapi"]:
            self.__setup_speechapi_node(config_dict["speechapi"])

        # ウェブカメラのノードを初期化
        if self.__config_dict["enable_webcam"]:
            self.__setup_webcam_node(config_dict["webcam"])

        # カード検出のノードを初期化
        if self.__config_dict["enable_card"]:
            self.__setup_card_detection_node(config_dict["card"])

        # 人の動き検出のノードを初期化
        if self.__config_dict["enable_motion"]:
            self.__setup_motion_detection_node(config_dict["motion"])

    def __setup_gpio(self):
        """GPIOの初期化"""
        
        if not all(self.__spi_initialized):
            # 全てのSPIチャネルが初期化されていない場合はエラー
            raise Exception("NodeManager::__setup_gpio(): " +
                            "You must initialize all spi channels by calling " +
                            "NodeManager::__setup_spi() before initializing gpio")

        if not self.__gpio_initialized:
            # GPIOを初期化
            if wp.wiringPiSetupGpio() == -1:
                raise Exception("NodeManager::__setup_gpio(): " +
                                "wiringpi::wiringPiSetupGpio() failed")
            
            # GPIOは初期化済み
            self.__gpio_initialized = True

    def __setup_spi(self, spi_channel, speed):
        """SPIチャネルの初期化"""

        if not self.__spi_initialized[spi_channel]:
            if wp.wiringPiSPISetup(spi_channel, speed) == -1:
                raise Exception("NodeManager::__setup_spi(): " +
                                "wiringpi::wiringPiSPISetup() failed")

            # 指定されたSPIチャネルは初期化済み
            self.__spi_initialized[spi_channel] = True

    def __setup_motor_node(self, config_dict):
        """モータのノードを初期化"""
        
        # SPIチャネルを全て初期化
        self.__setup_spi(spi_channel=0, speed=MotorL6470.L6470_SPI_SPEED)
        self.__setup_spi(spi_channel=1, speed=MotorL6470.L6470_SPI_SPEED)

        # 左右のモータを初期化
        self.__motor_left = MotorL6470(spi_channel=0)
        self.__motor_right = MotorL6470(spi_channel=1)
        # モータのノードを作成
        self.__motor_node = MotorNode(
            self.__process_manager, self.__msg_queue,
            self.__motor_left, self.__motor_right)

        # モータのノードを追加
        self.__add_command_receiver_node("motor", self.__motor_node)

    def __setup_servo_motor_node(self, config_dict):
        """サーボモータのノードを初期化"""

        # GPIOを初期化
        self.__setup_gpio()

        # サーボモータが使用するGPIOの端子
        self.__servo_motor_gpio_pin = 18
        # サーボモータを初期化
        # 48を指定したときに0度, 144を指定したときに180度となることを確認済み
        self.__servo_motor = ServoGwsS03t(
            self.__servo_motor_gpio_pin, min_value=48, max_value=144,
            min_angle=0, max_angle=180, frequency=50)
        # サーボモータのノードを作成
        self.__servo_motor_node = ServoMotorNode(
            self.__process_manager, self.__msg_queue,
            self.__servo_motor)

        # サーボモータのノードを追加
        self.__add_command_receiver_node("servo", self.__servo_motor_node)

    def __setup_srf02_node(self, config_dict):
        """超音波センサのノードを初期化"""

        # 超音波センサを初期化
        self.__srf02 = Srf02()
        # 超音波センサのノードを作成
        self.__srf02_node = Srf02Node(
            self.__process_manager, self.__msg_queue, self.__srf02,
            config_dict["distance_threshold"],
            config_dict["near_obstacle_threshold"],
            config_dict["interval"],
            config_dict["addr_list"])

        # 超音波センサのノードを追加
        self.__add_data_sender_node("srf02", self.__srf02_node)

    def __setup_julius_node(self, config_dict):
        """音声認識エンジンJuliusのノードを初期化"""

        # 音声認識エンジンJuliusのノードを初期化
        self.__julius_node = JuliusNode(
            self.__process_manager, self.__msg_queue)

        # 音声認識エンジンJuliusのノードを追加
        self.__add_data_sender_node("julius", self.__julius_node)

    def __setup_openjtalk_node(self, config_dict):
        """音声合成システムOpenJTalkのノードを初期化"""

        # 音声合成システムOpenJTalkのノードを初期化
        self.__openjtalk_node = OpenJTalkNode(self.__process_manager, self.__msg_queue)

        # 音声合成システムOpenJTalkのノードを追加
        self.__add_command_receiver_node("openjtalk", self.__openjtalk_node)

    def __setup_speechapi_node(self, config_dict):
        """Google Cloud Speech APIを利用した音声認識のノードを初期化"""

        # Google Cloud Speech APIのノードを作成
        self.__google_speech_api_node = GoogleSpeechApiNode(
            self.__process_manager, self.__msg_queue)

        # Google Cloud Speech APIのノードを追加
        self.__add_data_sender_node("speechapi", self.__google_speech_api_node)

    def __setup_webcam_node(self, config_dict):
        """ウェブカメラを操作するノードを初期化"""
        
        # カスケード分類器の初期化
        WebCamNode.setup_cascade_classifier()

        # ウェブカメラのノードを作成
        self.__webcam_node = WebCamNode(
            self.__process_manager, self.__msg_queue,
            config_dict["camera_id"],
            config_dict["interval"],
            config_dict["frame_width"],
            config_dict["frame_height"])
        
        # ウェブカメラのノードを追加
        self.__add_data_sender_node("webcam", self.__webcam_node)

    def __setup_card_detection_node(self, config_dict):
        """トランプのカードを検出するノードを初期化"""

        # カードを検出するノードを作成
        self.__card_detection_node = CardDetectionNode(
            self.__process_manager, self.__msg_queue,
            config_dict["server_host"],
            config_dict["camera_id"],
            config_dict["frame_width"],
            config_dict["frame_height"])

        # カードを検出するノードを追加
        self.__add_command_receiver_node("card", self.__card_detection_node)

    def __setup_motion_detection_node(self, config_dict):
        """人の動きを検出するノードを初期化"""

        # 人の動きを検出するノードを作成
        self.__motion_detection_node = MotionDetectionNode(
            self.__process_manager, self.__msg_queue,
            config_dict["camera_id"], config_dict["interval"],
            config_dict["frame_width"], config_dict["frame_height"],
            config_dict["contour_area_min"])

        # 人の動きを検出するノードを追加
        self.__add_command_receiver_node("motion", self.__motion_detection_node)

    def __add_data_sender_node(self, name, node):
        """指定された名前を持つノードを追加"""
        self.__data_sender_nodes[name] = node
        
    def __add_command_receiver_node(self, name, node):
        """指定された名前を持つノードを追加"""
        self.__command_receiver_nodes[name] = node

    def run_nodes(self):
        """ノードの実行を開始"""
        for name, data_sender in self.__data_sender_nodes.items() :
            data_sender.run()
        for name, command_receiver in self.__command_receiver_nodes.items():
            command_receiver.run()
    
    def send_command(self, name, cmd):
        """指定された名前のノードにコマンドを送信"""
        self.__command_receiver_nodes[name].send_command(cmd)

    def get_node(self, name):
        """指定された名前のノードを取得"""
        if name in self.__data_sender_nodes:
            return self.__data_sender_nodes[name]
        elif name in self.__command_receiver_nodes:
            return self.__command_receiver_nodes[name]
        else:
            return None

    def get_node_state(self, name):
        """指定された名前のノードの状態を取得"""
        if name in self.__data_sender_nodes:
            return self.__data_sender_nodes[name].state_dict
        elif name in self.__command_receiver_nodes:
            return self.__command_receiver_nodes[name].state_dict
        else:
            return None

    def get_msg_queue(self):
        """アプリケーションへのメッセージのキューを取得"""
        return self.__msg_queue

