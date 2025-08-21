#!/usr/bin/env bash

mkdir -p 'export'

rsync --archive --delete main.py text images fonts lib modes export/

# rshell --buffer-size=512 -p /dev/ttyACM0 -f rshell_instructions
rshell --buffer-size=512 rsync --mirror export/ /pyboard
