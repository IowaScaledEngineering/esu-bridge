#!/bin/bash
GIT_REV=`git rev-parse --short=6 HEAD`
/usr/bin/python3 esu-bridge.py --config ./protothrottle-config.txt --gitver $GIT_REV

