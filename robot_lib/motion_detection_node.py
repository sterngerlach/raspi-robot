# coding: utf-8
# motion_detection_node.py

import cv2
import multiprocessing as mp
import time
import queue

from command_receiver_node import CommandReceiverNode, UnknownCommandException

class MotionDetectionNode(CommandReceiverNode):
    """
    人の動きを検出するクラス
    """

    def __init__(self, process_manager, msg_queue,
                 camera_id, interval, frame_width, frame_height,
                 contour_area_min):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)

        # ビデオ撮影デバイスの作成
        self.camera_id = camera_id
        self.interval = interval
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.video_capture = cv2.VideoCapture(camera_id)
        self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        
        # 人の動きを検出中であるかどうか
        self.is_tracking = False
        # 人の動きを検出するための基準画像
        self.first_frame = None
        # 輪郭の面積の閾値
        self.contour_area_min = contour_area_min

    def __del__(self):
        """デストラクタ"""

        # ビデオ撮影デバイスの解放
        self.video_capture.release()

    def process_command(self):
        """アプリケーションからノードへの命令を処理"""

        try:
            while True:
                while not self.command_queue.empty():
                    try:
                        # 命令をキューから取り出し
                        cmd = self.command_queue.get_nowait()
                        print("MotionDetectionNode::process_command(): command received: {}".format(cmd))
                        self.execute_command(cmd)
                    except queue.Empty:
                        break
                
                if self.is_tracking:
                    # 撮影した動画から人の動きを検出
                    self.detect_motion()

                time.sleep(self.interval)

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("MotionDetectionNode::process_command(): KeyboardInterrupt occurred")

    def execute_command(self, cmd):
        """コマンドを実行"""

        # 命令でない場合は例外をスロー
        if "command" not in cmd:
            raise UnknownCommandException(
                "MotionDetectionNode::process_command(): unknown command: {}"
                .format(cmd))

        # 命令の実行開始をアプリケーションに伝達
        self.send_message("motion", { "command": cmd["command"], "state": "start" })

        if cmd["command"] == "start":
            # 人の動きの検出を開始
            self.is_tracking = True
            # 命令の実行終了をアプリケーションに伝達
            self.send_message("motion", { "command": cmd["command"], "state": "done" })
        elif cmd["command"] == "end":
            # 人の動きの検出を終了
            self.is_tracking = False
            # 基準の画像を破棄
            self.first_frame = None
            # 命令の実行終了をアプリケーションに伝達
            self.send_message("motion", { "command": cmd["command"], "state": "done" })
        else:
            # 解釈できない命令の無視をアプリケーションに伝達
            self.send_message("motion", { "command": cmd["command"], "state": "ignored" })

        # 命令の実行を完了
        self.command_queue.task_done()
        
    def detect_motion(self):
        """撮影した動画から人の動きを検出"""

        # 画像データを読み捨て
        ret, frame = self.video_capture.read()

        # 画像データを取得
        ret, frame = self.video_capture.read()
        frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (15, 15), 0)
        
        # 基準の画像を設定
        if self.first_frame is None:
            self.first_frame = frame
            return

        # 基準の画像と現在の画像との差分を計算
        frame_delta = cv2.absdiff(self.first_frame, frame)
        # 差分が小さいものはノイズと考えて無視
        frame_delta = cv2.threshold(frame_delta, 40, 255, cv2.THRESH_BINARY)[1]
        # 差分が一定値以上の部分を広げて輪郭を形成
        frame_delta = cv2.dilate(frame_delta, None, iterations=2)

        cv2.imshow("thresholded", frame_delta)
        cv2.waitKey(1)
        
        # 輪郭を差分画像から取り出し
        contours = cv2.findContours(frame_delta.copy(),
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[1]

        for contour in contours:
            if cv2.contourArea(contour) < self.contour_area_min:
                continue
            else:
                # 人の動きが検出されたことをアプリケーションに伝達
                self.send_message("motion", { "state": "motion-detected" })
                break

