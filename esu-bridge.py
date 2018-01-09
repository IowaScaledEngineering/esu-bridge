#!/usr/bin/python

import sys
import time
import traceback
import socket
import argparse
import ConfigParser

import esu
import mrbus
import MRBusThrottle
import netUtils

statusInterval = 1
searchDelay = 0.03
baseAddress = 0xD0


ap = argparse.ArgumentParser()
ap.add_argument("-s", "--serial", help="specify serial device for XBee radio", type=str)
ap.add_argument("-e", "--esuip", help="specify IP address of ESU CabControl command station", type=str)
ap.add_argument("-c", "--config", help="specify file with configuration", type=str)
ap.add_argument("-g", "--gitver", help="6 character Git revision to post in version packet", type=str)
args = ap.parse_args()

cmdStn = None
mrbee = None
gitver = [ 0x00, 0x00, 0x00 ]

# Big loop - runs as long as the program is alive
while 1:

   if args.config is not None:
      try:
         print "Reading configuration file"
         parser = ConfigParser.SafeConfigParser()
         parser.read(args.config)
         
         try:
            baseOffset = parser.getint("configuration", "baseAddress")
            baseAddress = 0xD0
            if (baseOffset >= 0 and baseOffset < 32):
               baseAddress += baseOffset
               print "Setting base address to %d  (MRBus address 0x%02X)" % (baseOffset, baseAddress)
         except:
            baseAddress = 0xD0
            pass            

         try:
            newSearchDelay = parser.getfloat("configuration", "searchDelay")
            if (newSearchDelay >= 0.01 and newSearchDelay < 1):
               searchDelay = newSearchDelay
               print "Setting search delay to %f" % (baseOffset, baseAddress)
            else:
               print "Config search delay of %f is insane, setting to 0.03"
               searchDelay = 0.03
         except:
            searchDelay = 0.03
            pass            

      except:
         pass         
   
   if args.gitver is not None:
      try:
         gitvernum = int(args.gitver[0:6], 16)
         gitver = [ (gitvernum) & 0xFF, (gitvernum>>8) & 0xFF, (gitvernum >> 16) & 0xFF ]
         print "Setting git version to 0x%06X - %02X%02X%02X" % (gitvernum, gitver[2], gitver[1], gitver[0])
      except:
         gitver = [ 0x00, 0x00, 0x00 ]



   # Initialization loop - runs until both ESU and MRBus are connected
   while 1:
      try:
         throttles = { }
         
         print "Looking for ESU CabControl command station"

         esuIP = None
         if args.esuip is not None:
            esuIP = args.esuip
         else:
            esuIP = netUtils.esuFind(searchDelay)

         if esuIP is None:
            print "No command station found, waiting and retrying..."
            time.sleep(2)
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
            cmdStn.disconnect()
            time.sleep(2)
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
#            print "Sending status packet"
            statusPacket = [ ord('v'), 0x80, gitver[2], gitver[1], gitver[0], 1, 0, ord('E'), ord('S'), ord('U'), ord('E'), ord('N'), ord('E'), ord('T')]
            mrbee.sendpkt(0xFF, statusPacket)
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
         exc_info = sys.exc_info()
         traceback.print_exception(*exc_info)
         del exc_info         


         cmdStn.disconnect()
         mrbee.disconnect()
         break

