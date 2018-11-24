#!/usr/bin/env python3
# coding: utf-8
# servo_motor_test.py

import time
import wiringpi as w

def setup_servo_motor(pin):
    # GPIOの初期化
    if w.wiringPiSetupGpio() == -1:
        print("wiringpi::wiringPiSetupGpio() failed")
        return
    else:
        print("wiringpi::wiringPiSetupGpio() succeeded")

    # GPIOを出力モードに設定
    w.pinMode(pin, w.GPIO.PWM_OUTPUT)
    
    # WiringPiではデフォルトでBalancedモードであるため, Mark:Spaceモードに変換
    w.pwmSetMode(w.PWM_MODE_MS)
    
    # PWM周波数(PwmFrequency)を以下の式で計算できるため, サーボモータの周期と
    # 一致するようにClockとRangeを設定する必要がある
    # PwmFrequency = 19.2 MHz / Clock / Range

    # 19.2 MHzはRaspberry PiのハードウェアPWMが持つベースクロックの周波数
    # 19.2 MHz / ClockはハードウェアPWMのカウンタの周期を表し,
    # この周期でPWMのカウンタがインクリメントされる
    # RangeはハードウェアPWMの分解能に相当する値

    # PWM動作周波数は50Hz(20ms周期)
    w.pwmSetClock(375)
    w.pwmSetRange(1024)

def main():
    # GPIO18からサーボモータを使用
    SERVO_GPIO_PIN = 18
    
    setup_servo_motor(SERVO_GPIO_PIN)

    while True:
        pulse = int(input())
        if pulse == -1:
            break
        w.pwmWrite(SERVO_GPIO_PIN, pulse)

    w.pwmWrite(SERVO_GPIO_PIN, 0)
    
if __name__ == "__main__":
    main()

