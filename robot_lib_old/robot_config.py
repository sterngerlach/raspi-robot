# coding: utf-8
# robot_config.py

class RobotConfig(object):
    """
    ロボットの各種設定用のクラス
    """
    
    # モータを有効にするかどうか
    MotorEnabled = True

    # 超音波センサを有効にするかどうか
    Srf02Enabled = True

    # 音声認識を有効にするかどうか
    SpeechRecognitionEnabled = False

    # 音声合成を有効にするかどうか
    SpeechSynthesisEnabled = True

    # Webカメラを有効にするかどうか
    WebCamEnabled = True
    
    # キーボード入力による操作を有効にするかどうか
    KeyInputEnabled = True

