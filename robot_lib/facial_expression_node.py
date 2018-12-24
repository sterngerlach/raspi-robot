# coding: utf-8
# facial_expression_node.py

import multiprocessing as mp
import pathlib
import os
import time

import tkinter as tk
import PIL

from command_receiver_node import CommandReceiverNode

class FacialExpressionNode(CommandReceiverNode):
    """
    顔の表情を画面に表示するクラス
    """

    def __init__(self, process_manager, msg_queue,
                 window_width, window_height):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)
        
        # 顔の表情の画像が保存されたクラス
        file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
        self.img_dir = file_dir.parent.joinpath("facial-expression-images")

        # 画面の横幅と縦幅
        self.window_width = window_width
        self.window_height = window_height

    def process_command(self):
        """表情の表示命令を処理"""

        self.tk_root = tk.Tk()
        self.tk_label = tk.Label(self.tk_root)
        self.tk_label.pack()

        try:
            while True:
                while not self.command_queue.empty():
                    # 表情の命令をキューから取り出し
                    cmd = self.command_queue.get_nowait()
                    print("FacialExpressionNode::process_command(): command received: {}"
                          .format(cmd))

                    if "file-name" in cmd:
                        # 指定された表情を表示
                        img_path = self.img_dir.joinpath(cmd["file-name"])
                        img = PIL.ImageTk.PhotoImage(PIL.Image.open(str(img_path)))
                        self.tk_label.configure(image=img,
                                                width=self.window_width,
                                                height=self.window_height)

                    # 表情の更新を完了
                    self.command_queue.task_done()

                self.tk_root.update_idletasks()
                self.center_window()
                self.tk_root.update()

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("FacialExpressionNode::process_command(): KeyboardInterrupt occurred")
    
    def center_window(self):
        """画面をスクリーンの中央に移動"""
        width = self.tk_root.winfo_width()
        height = self.tk_root.winfo_height()
        screen_width = self.tk_root.winfo_screenwidth()
        screen_height = self.tk_root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.tk_root.geometry("{}x{}+{}+{}".format(width, height, x, y))

