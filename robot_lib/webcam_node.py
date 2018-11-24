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

    def __init__(self, process_manager, msg_queue, camera_id):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # ビデオ撮影デバイスの作成
        self.camera_id = camera_id
        self.video_capture = cv2.VideoCapture(camera_id)
        # self.video_capture.set(cv2.CAP_PROP_FPS, 2)
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 240)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 180)
        
        # キャプチャする画像のサイズをプロセス間で共有
        self.state_dict["capture_width"] = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.state_dict["capture_height"] = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
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
                faces = WebCamController.cascade_classifier_face.detectMultiScale(
                    frame_gray, scaleFactor=1.1,
                    minNeighbors=5, minSize=(15, 15))

                # 検出された顔領域を更新
                self.state_dict["faces"] = faces if len(faces) >= 1 else None

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("WebCamNode::update(): KeyboardInterrupt occurred")

