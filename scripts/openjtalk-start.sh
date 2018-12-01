#!/bin/bash

# https://gist.github.com/shokai/2892965
# https://qiita.com/lutecia16v/items/8d220885082e40ace252

# 保存先のファイル名を設定
OUT_FILE=/tmp/out.wav

# コマンドライン引数に指定した日本語の文字列を音声ファイルに変換
# 作成した音声ファイルを再生して削除
echo "$1" | open_jtalk \
-m /usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice \
-x /var/lib/mecab/dic/open-jtalk/naist-jdic \
-ow $OUT_FILE && \
aplay --quiet $OUT_FILE

