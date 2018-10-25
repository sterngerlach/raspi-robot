#!/bin/bash
iconv -f utf8 -t eucjp ./command.yomi | ~/work/julius/julius-4.4.2/gramtools/yomi2voca/yomi2voca.pl | iconv -f eucjp -t utf8 > ./command.voca

