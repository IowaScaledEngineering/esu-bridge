#!/usr/bin/python

import esu
import mrbus
import sys
import time
import socket
import MRBusThrottle
import netUtils

statusInterval = 2
baseAddress = 0xD4

# Big loop - runs as long as the program is alive
while 1:

   # Initialization loop - runs until both ESU and MRBus are connected
   while 1:
      try:
         throttles = { }
         print "Looking for ESU CabControl command station"
         esuIP = ""
         esuIP = netUtils.esuFind()
         if esuIP is None:
            print "No command station found, waiting and retrying..."
            sleep(1)
            continue
      
         cmdStn = esu.ESUConnection()
         cmdStn.connect(esuIP)
 
         mrbee = mrbus.mrbus("/dev/ttyUSB2", baseAddress, logall=True, logfile=sys.stdout, busType='mrbee')
         break

      except(KeyboardInterrupt):
         cmdStn.disconnect()
         mrbee.disconnect()
         sys.exit()
      except:
         cmdStn.disconnect()
         mrbee.disconnect()
         continue


   lastStatusTime = time.time()

   # Main Run Loop - runs until something weird happens
   while 1:
      try:
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

      except (KeyboardInterrupt):
         cmdStn.disconnect()
         mrbee.disconnect()
         sys.exit()
      except:
         print "Caught some sort of exception, restarting the whole thing"
         cmdStn.disconnect()
         mrbee.disconnect()
         break

