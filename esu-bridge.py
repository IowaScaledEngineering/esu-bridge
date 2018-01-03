#!/usr/bin/python

import sys
import time
import socket
import argparse

import esu
import mrbus
import MRBusThrottle
import netUtils

statusInterval = 2
baseAddress = 0xD4

ap = argparse.ArgumentParser()
ap.add_argument("-s", "--serial", help="specify serial device for XBee radio", type=str)
ap.add_argument("-e", "--esuip", help="specify IP address of ESU CabControl command station", type=str)
args = ap.parse_args()

cmdStn = None
mrbee = None

# Big loop - runs as long as the program is alive
while 1:

   # Initialization loop - runs until both ESU and MRBus are connected
   while 1:
      try:
         throttles = { }
         print "Looking for ESU CabControl command station"

         esuIP = None
         if args.esuip is not None:
            esuIP = args.esuip
         else:
            esuIP = netUtils.esuFind()

         if esuIP is None:
            print "No command station found, waiting and retrying..."
            sleep(1)
            continue


         if cmdStn is not None:
            cmdStn.disconnect()

         print "Trying ESU command station connection"
      
         cmdStn = esu.ESUConnection()
         cmdStn.connect(esuIP)
         
         print "Looking for XBee / MRBus interface"
 
         xbeePort = None
         if args.serial is not None:
            xbeePort = args.serial
         else:
            xbeePort = netUtils.findXbeePort()

         if xbeePort is None:
            print "No XBee found, waiting and retrying..."
            sleep(1)
            continue
         else:
            print "Trying to start XBee / MRBus on port %s" % xbeePort

         if mrbee is not None:
            mrbee.disconnect()



         mrbee = mrbus.mrbus(xbeePort, baseAddress, logall=True, logfile=sys.stdout, busType='mrbee')
         break

      except(KeyboardInterrupt):
         cmdStn.disconnect()
         mrbee.disconnect()
         sys.exit()
      except:
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

