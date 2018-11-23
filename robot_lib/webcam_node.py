# coding: utf-8
# webcam_controller.py

import cv2
import multiprocessing as mp
import time

class WebCamController(object):
    """
    カメラを操作するクラス
    """

    # カスケード分類器のファイル名
    cascade_file_path = "haarcascade_frontalface_default.xml"
    # カスケード分類器
    cascade_classifier_face = None

    @classmethod
    def setup_cascade_classifier(cls):
        """カスケード分類器の作成"""
        cls.cascade_classifier_face = cv2.CascadeClassifier(cls.cascade_file_path)
        return

    def __init__(self, camera_id, motor_command_queue, talk_command_queue):
        """コンストラクタ"""

        # ビデオ撮影デバイスの作成
        self.camera_id = camera_id
        self.video_capture = cv2.VideoCapture(camera_id)
        # self.video_capture.set(cv2.CAP_PROP_FPS, 2)
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 240)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 180)

        self.capture_width = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.capture_height = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # 音声合成命令を管理するキュー
        self.talk_command_queue = talk_command_queue
        # モータへの命令を管理するキュー
        self.motor_command_queue = motor_command_queue
        # 撮影した動画を処理するためのプロセスを作成
        self.process_handler = mp.Process(target=self.process_input, args=())
        # デーモンプロセスに設定
        # 親プロセスが終了するときに子プロセスを終了させる
        self.process_handler.daemon = True

        return
        
    def __del__(self):
        """デストラクタ"""

        # ビデオ撮影デバイスの解放
        self.video_capture.release()

        # ウィンドウを全て破棄
        cv2.destroyAllWindows()

        return
    
    def process_input(self):
        """撮影した動画を処理"""
        
        while True:
            # 撮影した動画を取り込み
            ret, frame = self.video_capture.read()
            # グレースケール画像に変換
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 顔検出の処理
            faces = WebCamController.cascade_classifier_face.detectMultiScale(
                frame_gray, scaleFactor=1.1,
                minNeighbors=5, minSize=(15, 15))

            if len(faces) < 1:
                continue

            # 検出された顔領域の表示
            # for (x, y, w, h) in faces:
            #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 検出された顔領域を取得
            x, y, w, h = faces[0]
            center_x = x + w / 2
            center_y = y + h / 2

            if center_x < self.capture_width / 3:
                self.talk_command_queue.put({ "sentence": "左" })
                self.motor_command_queue.put(
                    { "command": "brake-left", "speed": 3000, "slope": 0.06 })
                self.motor_command_queue.join()
                self.motor_command_queue.put(
                    { "command": "accel-left", "speed": 9000, "slope": 0.06 })
                self.motor_command_queue.join()
            elif center_x > self.capture_width / 3 * 2:
                self.talk_command_queue.put({ "sentence": "右" })
                self.motor_command_queue.put(
                    { "command": "brake-right", "speed": 3000, "slope": 0.06 })
                self.motor_command_queue.join()
                self.motor_command_queue.put(
                    { "command": "accel-right", "speed": 9000, "slope": 0.06 })
                self.motor_command_queue.join()
            else:
                self.talk_command_queue.put({ "sentence": "直進" })
                self.motor_command_queue.put(
                    { "command": "accel", "speed": 9000, "slope": 0.02 })
                self.motor_command_queue.join()
            
            # self.talk_command_queue.join()
            
            # cv2.imshow("Camera (id: {0}".format(self.camera_id), frame)
            # cv2.waitKey(1)

        return

    def run(self):
        """動画の撮影を開始"""
        self.process_handler.start()
        return

    def emergency_stop(self):
        """動画の撮影を終了"""
        self.process_handler.terminate()
        return

