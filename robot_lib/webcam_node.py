# coding: utf-8
# webcam_node.py

import cv2
import multiprocessing as mp
import time

from data_sender_node import DataSenderNode

class WebCamNode(DataSenderNode):
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

    def __init__(self, process_manager, msg_queue,
                 camera_id, interval, frame_width, frame_height):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # ビデオ撮影デバイスの作成
        self.camera_id = camera_id
        self.video_capture = cv2.VideoCapture(camera_id)
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

        # 画像をキャプチャする間隔
        self.interval = interval
        
    def __del__(self):
        """デストラクタ"""

        # ビデオ撮影デバイスの解放
        self.video_capture.release()

        # ウィンドウを全て破棄
        cv2.destroyAllWindows()
    
    def update(self):
        """撮影した動画を処理"""
        
        try:
            while True:
                # 撮影した動画を取り込み
                ret, frame = self.video_capture.read()
                # グレースケール画像に変換
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 顔検出の処理
                faces = WebCamNode.cascade_classifier_face.detectMultiScale(
                    frame_gray, scaleFactor=1.1,
                    minNeighbors=5, minSize=(15, 15))

                # 検出された顔領域をアプリケーションに伝達
                if len(faces) > 0:
                    self.send_message("webcam", { "state": "face-detected", "faces": faces })
                else:
                    self.send_message("webcam", { "state": "face-not-detected", "faces": faces })

                time.sleep(self.interval)

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("WebCamNode::update(): KeyboardInterrupt occurred")

