#!/usr/bin/env python3
# coding: utf-8
# main.py

import multiprocessing as mp
import multiprocessing.managers as mpm
import queue
import time

from robot_config import RobotConfig
from motor_l6470 import MotorL6470, MotorInitFailedException
from motor_controller import MotorController, MotorUnknownCommandException
from julius_controller import JuliusController
from openjtalk_controller import OpenJTalkController
from srf02 import Srf02
from srf02_controller import Srf02Controller
from webcam_controller import WebCamController

class RobotSyncManager(mpm.SyncManager):
    pass

class RobotController(object):
    """
    ロボットの操作クラス
    """

    def __init__(self):
        """コンストラクタ"""

        # マネージャを作成
        # self.process_manager = mp.Manager()
        self.process_manager = RobotSyncManager()
        self.process_manager.start()

        # モータへの命令を管理するためのキューを作成
        self.motor_command_queue = self.process_manager.Queue()
        # モータの情報を管理するためのディクショナリを作成
        self.motor_info = self.process_manager.dict()

        # 音声合成命令を管理するためのキューを作成
        self.talk_command_queue = self.process_manager.Queue()
        
        if RobotConfig.MotorEnabled:
            # 左右のモータを作成
            self.motor_left = MotorL6470(spi_channel=0)
            self.motor_right = MotorL6470(spi_channel=1)
            # モータを操作するクラスを作成
            self.motor_controller = MotorController(
                self.motor_left, self.motor_right,
                self.motor_command_queue, self.motor_info)
        
        if RobotConfig.SpeechRecognitionEnabled:
            # 音声入力エンジンを操作するクラスを作成
            self.julius_controller = JuliusController(self.motor_command_queue)

        if RobotConfig.SpeechSynthesisEnabled:
            # 音声合成システムを操作するクラスを作成
            self.openjtalk_controller = OpenJTalkController(self.talk_command_queue)
        
        if RobotConfig.Srf02Enabled:
            # 超音波センサを作成
            self.srf02 = Srf02()
            # 超音波センサを操作するクラスを作成
            self.srf02_controller = Srf02Controller(self.srf02, self.motor_command_queue)
        
        if RobotConfig.WebCamEnabled:
            # カメラを操作するクラスを作成
            WebCamController.setup_cascade_classifier()
            self.webcam_controller = WebCamController(
                0, self.motor_command_queue, self.talk_command_queue)

        return

    def __del__(self):
        """デストラクタ"""

        # マネージャを停止
        self.process_manager.shutdown()

        return

    def run(self):
        """ロボットの操作を開始"""
        
        if RobotConfig.MotorEnabled:
            # モータの操作を開始
            self.motor_controller.run()
        
        if RobotConfig.SpeechRecognitionEnabled:
            # 音声入力を開始
            self.julius_controller.run()

        if RobotConfig.SpeechSynthesisEnabled:
            # 音声合成を開始
            self.openjtalk_controller.run()
        
        if RobotConfig.Srf02Enabled:
            # 超音波センサの入力を開始
            self.srf02_controller.run()
        
        if RobotConfig.WebCamEnabled:
            # カメラの撮影を開始
            self.webcam_controller.run()
        
        """
        self.motor_controller.send_command({ "command": "accel", "speed": 30000, "slope": 0.01 })
        self.motor_controller.wait_until_all_command_done()
        time.sleep(5)

        self.motor_controller.send_command({ "command": "brake", "speed": 0, "slope": 0.01 })
        self.motor_controller.send_command({ "command": "stop" })
        self.motor_controller.wait_until_all_command_done()
        """
        try:       
            while True:
                if RobotConfig.KeyInputEnabled and RobotConfig.MotorEnabled:
                    motor_cmd = input("> ")

                    if motor_cmd == "accel":
                        self.motor_controller.send_command(
                            { "command": "accel", "speed": 9000, "slope": 0.02 })
                    elif motor_cmd == "brake":
                        self.motor_controller.send_command(
                            { "command": "brake", "speed": 0, "slope": 0.02 })
                    elif motor_cmd == "stop":
                        self.motor_controller.send_command({ "command": "stop" })
                    elif motor_cmd == "end":
                        self.motor_controller.send_command({ "command": "end" })
                    elif motor_cmd == "rotate-left":
                        self.motor_controller.send_command(
                            { "command": "rotate", "direction": "left" })
                    elif motor_cmd == "rotate-right":
                        self.motor_controller.send_command(
                            { "command": "rotate", "direction": "right" })
                    elif motor_cmd == "cancel":
                        self.motor_controller.send_command({ "command": "cancel" })
                    else:
                        print("available motor commands: \n" +
                              "accel, brake, stop, end, rotate-left, rotate-right, cancel")
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass

        return

def main():
    # ロボットの操作クラスを作成
    robot_controller = RobotController()
    
    # ロボットの操作を実行開始
    robot_controller.run()

    return

if __name__ == "__main__":
    main()

