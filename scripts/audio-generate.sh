#!/bin/bash

# -m /usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice \
echo "$1" | open_jtalk \
-m /usr/share/hts-voice/mei/mei_happy.htsvoice \
-x /var/lib/mecab/dic/open-jtalk/naist-jdic \
-ow "$2"

