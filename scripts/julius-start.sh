#!/bin/sh

# Juliusを起動
# /usr/local/julius/bin/julius -C ~/work/julius/dictation-kit-v4.4/main.jconf -C ~/work/julius/dictation-kit-v4.4/am-gmm.jconf -nostrip -gram dict/command -module >/dev/null &
/usr/local/julius/bin/julius -C ~/work/julius/dictation-kit-v4.4/am-gmm.jconf -nostrip -gram ~/raspi-robot/julius-dict/command -module >/dev/null &

# プロセスIDを取得
echo $!

