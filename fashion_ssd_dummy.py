#!/usr/bin/env python3
# coding: utf-8
# fashion_ssd_dummy.py

import cv2
import random

def is_fashionable(image):
    """服装がおしゃれかどうかを判定するダミーの関数"""
    print("is_fashionable(): image.shape: {}".format(image.shape))
    
    rand_result = random.randint(0, 1)
    print("is_fashionable(): result: {}".format(rand_result))

    return rand_result

