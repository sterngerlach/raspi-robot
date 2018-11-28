# coding: utf-8
# servo_gws_s03t.py

import wiringpi as wp

class ServoGwsS03t(object):
    """
    サーボモータ(GWSサーボS03T/2BBMG/F)を操作するクラス
    """

    def __init__(self,
        gpio_pin, min_value, max_value,
        min_angle=0, max_angle=180, frequency=50):
        """コンストラクタ"""
        print("ServoGwsS03t::__init__(): gpio_pin: {0}".format(gpio_pin))

        # GPIOはwiringpi::wiringPiSetupGpio()関数の呼び出しによって,
        # 初期化済みであると仮定する

        # min_valueを端子に書き込んだときの角度がmin_angle,
        # max_valueを端子に書き込んだときの角度がmax_angleとなるように設定

        # 使用するGPIOの端子
        self.gpio_pin = gpio_pin
        # 書き込む値の最小値(サーボモータによって異なる)
        self.min_value = min_value
        # 書き込む値の最大値(サーボモータによって異なる)
        self.max_value = max_value
        # 指定する角度の最小値(min_valueを書き込んだときの角度)
        self.min_angle = min_angle
        # 指定する角度の最大値(max_valueを書き込んだときの角度)
        self.max_angle = max_angle
        # PWMの動作周波数(通常は50Hz)
        self.pwm_frequency = frequency
        # PWMの分解能(WiringPiの場合はデフォルトで1024)
        self.pwm_range = 1024

        # 指定されたGPIOの端子を出力モードに設定
        wp.pinMode(self.gpio_pin, wp.GPIO.PWM_OUTPUT)
        # デフォルトのBalancedモードからMark:Spaceモードに設定
        wp.pwmSetMode(wp.GPIO.PWM_MODE_MS)

        # PWMの動作周波数の計算式は以下のようになっているが,
        # サーボモータの周期と一致するようにClockとRangeを設定する必要がある
        # PWMの動作周波数 = 19.2MHz / Clock / Range

        # 19.2MHzはハードウェアPWMが持つベースクロックの周波数
        # 19.2MHz / ClockはハードウェアPWMのカウンタの周期を表し,
        # この周期ごとにPWMのカウンタがインクリメントされる
        # RangeはハードウェアPWMの分解能に相当する値で, WiringPiの場合は1024を設定

        # PWMの動作周波数は50Hz(20ms周期)であるから, Clockに375, Rangeに1024を設定
        wp.pwmSetClock(int(19.2 * (10 ** 6) / self.pwm_range / self.pwm_frequency))
        wp.pwmSetRange(self.pwm_range)

    def __del__(self):
        """デストラクタ"""
        
        # サーボモータの位置を復元
        wp.pwmWrite(self.gpio_pin, self.min_value)

        # サーボモータの使用を停止
        wp.pwmWrite(self.gpio_pin, 0)

    def write(self, val):
        """GPIOに値を書き込み"""

        # 書き込もうとしている値が小さ過ぎる場合は例外をスロー
        if val < self.min_value:
            raise ValueError("ServoGwsS03t::write(): " +
                             "specified value {0} is less than the minimum value {1}"
                             .format(val, self.min_value))

        # 書き込もうとしている値が大き過ぎる場合は例外をスロー
        if val > self.max_value:
            raise ValueError("ServoGwsS03t::write(): " +
                             "specified value {0} is greater than the maximum value {1}"
                             .format(val, self.max_value))
        
        # 値をGPIOの端子に書き込み
        wp.pwmWrite(self.gpio_pin, int(val))
    
    def set_angle(self, angle):
        """角度(0度から180度まで)を指定"""

        # 指定された角度が0度より小さい場合は例外をスロー
        if angle < self.min_angle:
            raise ValueError("ServoGwsS03t::set_angle(): " +
                             "specified angle {0} is less than the minimum angle {1}"
                             .format(angle, self.min_angle))

        # 指定された角度が180度より大きい場合は例外をスロー
        if angle > self.max_angle:
            raise ValueError("ServoGwsS03t::set_angle(): " +
                             "specified angle {0} is greater than the maximum angle {1}"
                             .format(angle, self.max_angle))
        
        # 書き込む値を計算してGPIOの端子に書き込み
        val = self.min_value + \
            (self.max_value - self.min_value) / (self.max_angle - self.min_angle) * \
            (angle - self.min_angle)
        wp.pwmWrite(self.gpio_pin, int(val))

