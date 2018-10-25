# coding: utf-8
# util.py

import time

# 指定したマイクロ秒だけスリープ
usleep = lambda x: time.sleep(x / (10.0 ** 6))

