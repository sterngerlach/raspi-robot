#!/usr/bin/env python3
# coding: utf-8
# card_ssd_dummy.py

import cv2
import random

def card_detect(image):
    """ダミーのトランプカード検出関数"""
    print("card_detect(): image.shape: {}".format(image.shape))
    
    card_num = random.randint(0, 3)
    cards = []

    for i in range(card_num):
        cards.append(random.randint(1, 13))

    return cards

