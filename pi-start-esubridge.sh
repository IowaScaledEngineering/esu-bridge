#!/bin/bash
cd /home/iascaled/esu-bridge
GIT_REV=`git rev-parse --short=6 HEAD`
/usr/bin/python esu-bridge.py --config /boot/protothrottle.ini --gitver $GIT_REV

