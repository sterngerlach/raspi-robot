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

        # ウェブカメラのノードを初期化
        if self.__config_dict["webcam"]:
            self.__setup_webcam_node(config_dict["webcam"])

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

    def __setup_servo_motor_node(self, config_dict):
        """サーボモータのノードを初期化"""

        # GPIOを初期化
        self.__setup_gpio()

        # サーボモータの状態を保持するディクショナリ
        self.__servo_motor_dict = self.__process_manager.dict()
        # サーボモータへの命令を保持するキュー
        self.__servo_motor_command_queue = self.__process_manager.Queue()
        # サーボモータが使用するGPIOの端子
        self.__servo_motor_gpio_pin = 18
        # サーボモータのID
        self.__servo_id = 0
        # サーボモータを初期化
        # 48を指定したときに0度, 144を指定したときに180度となることを確認済み
        self.__servo_motor = ServoGwsS03t(
            self.__servo_motor_gpio_pin, min_value=48, max_value=144,
            min_angle=0, max_angle=180, frequency=50)

        # サーボモータのノードを追加
        self.__add_command_receiver_node(
            self.__servo_motor_dict, self.__msg_queue, 
            self.__servo_motor_command_queue, self.__servo_id,
            "servo" + str(self.__servo_id))

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
