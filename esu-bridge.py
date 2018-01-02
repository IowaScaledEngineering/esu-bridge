#!/usr/bin/python

import esu
import mrbus
import sys
import time
import MRBusThrottle


mrbee = mrbus.mrbus("/dev/ttyUSB2", 0x20, logall=True, logfile=sys.stdout, busType='mrbee')
cmdStn = esu.ESUConnection()
cmdStn.connect('192.168.7.191')

throttles = { }

while 1:
   pkt = mrbee.getpkt()
   if pkt is None:
      continue

   # Bypass anything that doesn't look like a throttle packet
   if pkt.cmd != 0x53 or len(pkt.data) != 10:
      continue

   if pkt.src not in throttles:
      throttles[pkt.src] = MRBusThrottle.MRBusThrottle()
      
   throttles[pkt.src].update(cmdStn, pkt)


cmdStn.disconnect()

