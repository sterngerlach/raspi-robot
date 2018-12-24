# coding: utf-8
# tkinter_test.py

import multiprocessing as mp
import os
import pathlib
import sys
import threading as th
import time

import tkinter as tk
from PIL import Image, ImageTk

class TkinterTest(object):
    def __init__(self):
        __file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
        self.__img_dir = __file_dir.parent.joinpath("facial-expression-images")
        
        self.__manager = mp.Manager()
        self.__command_queue = self.__manager.Queue()
        self.__handler = mp.Process(target=self.__handle_command, args=())
        self.__handler.start()
        
    def __handle_command(self):
        self.__tk_root = tk.Tk()
        self.__label = tk.Label(self.__tk_root)
        self.__label.pack()
        
        try:
            while True:
                while not self.__command_queue.empty():
                    cmd = self.__command_queue.get_nowait()
                    img_path = self.__img_dir.joinpath(cmd)
                    img = ImageTk.PhotoImage(Image.open(str(img_path)))
                    self.__label.configure(image=img, width=640, height=480)
                    self.__command_queue.task_done()

                self.__tk_root.update_idletasks()
                self.center()
                self.__tk_root.update()
        except BrokenPipeError:
            print("TkinterTest::__handle_command(): BrokenPipeError occurred")

    def center(self):
        width = self.__tk_root.winfo_width()
        height = self.__tk_root.winfo_height()
        screen_width = self.__tk_root.winfo_screenwidth()
        screen_height = self.__tk_root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.__tk_root.geometry("{}x{}+{}+{}".format(width, height, x, y))
    
    def send_command(self, cmd):
        self.__command_queue.put(cmd)

    def join_command_queue(self):
        self.__command_queue.join()
 
def main():
    app = TkinterTest()

    app.send_command("sad.png")
    time.sleep(1)
    app.send_command("thinking.png")
    time.sleep(1)
    app.join_command_queue()

if __name__ == "__main__":
    main()

