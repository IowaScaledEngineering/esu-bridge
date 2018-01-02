#!/usr/bin/python

import esu
import mrbus
import sys
import time
import MRBusThrottle


statusInterval = 2
baseAddress = 0xD4

mrbee = mrbus.mrbus("/dev/ttyUSB2", baseAddress, logall=True, logfile=sys.stdout, busType='mrbee')
cmdStn = esu.ESUConnection()
cmdStn.connect('192.168.7.191')

throttles = { }

lastStatusTime = time.time()


while 1:
   pkt = mrbee.getpkt()

   if time.time() > lastStatusTime + statusInterval:
      mrbee.sendpkt(0xFF, [ord('A')])
      lastStatusTime = time.time()

   if pkt is None:
      continue

   # Bypass anything that doesn't look like a throttle packet
   if pkt.cmd != 0x53 or len(pkt.data) != 10 or baseAddress != pkt.dest:
      continue

   if pkt.src not in throttles:
      throttles[pkt.src] = MRBusThrottle.MRBusThrottle()
      
   throttles[pkt.src].update(cmdStn, pkt)

   

cmdStn.disconnect()

