# *************************************************************************
# Title:    ProtoThrottle bridge for ESU CabControl and JMRI WiThrottle
# Authors:  Michael D. Petersen <railfan@drgw.net>
#           Nathan D. Holmes <maverick@drgw.net>
# File:     esu-bridge.py
# License:  GNU General Public License v3
#
# LICENSE:
#   Copyright (C) 2018 Michael Petersen & Nathan Holmes
#    
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
# DESCRIPTION:
#   This is the main application that allows the ProtoThrottle ( http://www.protothrottle.com/ )
#   to communicate with ESU CabControl command stations or JMRI WiThrottle servers
#   (or compatible, such as the Digitrax LNWI).
#
#   While this is intended to be used on a Raspberry Pi as an embedded system,
#   it will work just fine on a desktop.  The biggest thing it needs is the 
#   "protothrottle.ini" file, of which the default configuration (with usage comments)
#   is included in the Github repository.  
#
#   See test-start-esubridge.sh in the repo to see an example of how to invoke 
#   this sanely.
#
#*************************************************************************


import sys
import time
import traceback
import socket
import argparse
import ConfigParser

import esu
import withrottle
import mrbus
import MRBusThrottle
import netUtils

import datetime

statusInterval = 1
searchDelay = 0.03
baseAddress = 0xD0

ap = argparse.ArgumentParser()
ap.add_argument("-s", "--serial", help="specify serial device for XBee radio", type=str)
ap.add_argument("-i", "--server_ip", help="specify IP address of ESU Command Station or WiThrottle server", type=str)
ap.add_argument("-c", "--config", help="specify file with configuration", type=str)
ap.add_argument("-g", "--gitver", help="6 character Git revision to post in version packet", type=str)
args = ap.parse_args()

cmdStn = None
mrbee = None

esuConnection = True
withrottleConnection = False

gitver = [ 0x00, 0x00, 0x00 ]
ptPktTimeout = 4000
dccConnectionMode = ""
withrottlePort = 12090
server_ip = None

def getMillis():
	return time.time() * 1000.0


# Big loop - runs as long as the program is alive
while 1:

   print ""
   print "-----------------------------------------------"
   print " STARTING CONFIG PHASE"
   print ""
   
   if args.config is not None:
      try:
         print "Reading configuration file [%s]" % (args.config)
         parser = ConfigParser.SafeConfigParser()
         parser.read(args.config)
         print "Configuration file successfully read"         
         try:
            baseOffset = parser.getint("configuration", "baseAddress")
            baseAddress = 0xD0
            if (baseOffset >= 0 and baseOffset < 32):
               baseAddress += baseOffset
               print "Setting base address to %d  (MRBus address 0x%02X)" % (baseOffset, baseAddress)
         except:
            baseAddress = 0xD0

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

         try:
            ptPktTimeout = parser.getint("configuration", "packetTimeout")
            print "Setting packet timeout to %d milliseconds" % (ptPktTimeout)
         except:
            ptPktTimeout = 4000

         try:
            dccConnectionMode = parser.get("configuration", "mode")
            if dccConnectionMode == "esu":
               print "Setting connection to ESU WiFi"
               esuConnection = True
            elif dccConnectionMode == "withrottle":
               print "Setting connection to WiThrottle"
               withrottleConnection = True
               esuConnection = False
            else:
               print "Connection mode [%s] invalid, defaulting to ESU WiFi" % (dccConnectionMode) 
               esuConnection = True

         except Exception as e:
            print "Exception in setting connection mode, defaulting to ESU WiFi"
            print e
            esuConnection = True
            withrottleConnection = False

         try:
            server_ip = parser.get("configuration", "serverIP")
         except Exception as e:
            print "Server IP not set by configuration file"
            server_ip is None

         try:
            withrottlePort = parser.get("configuration", "withrottlePort")
         except Exception as e:
            withrottlePort = 12090
            print "WiThrottle port not set by configuration file - setting to %d" % withrottlePort
            

      except Exception as e:
         print "Yikes!  Exception reading configuration file"
         print e
   
   if args.gitver is not None:
      try:
         gitvernum = int(args.gitver[0:6], 16)
         gitver = [ (gitvernum) & 0xFF, (gitvernum>>8) & 0xFF, (gitvernum >> 16) & 0xFF ]
         print "Setting git version to 0x%06X - %02X%02X%02X" % (gitvernum, gitver[2], gitver[1], gitver[0])
      except:
         gitver = [ 0x00, 0x00, 0x00 ]

   if args.server_ip is not None:
      server_ip = args.server_ip

   print ""
   print " ENDING CONFIG PHASE"
   print "-----------------------------------------------"
   print ""
   print "-----------------------------------------------"
   print " STARTING CONNECTION PHASE"
   print ""

   # Initialization loop - runs until both ESU and MRBus are connected
   while 1:
      try:
         throttles = { }
         print "Looking for XBee / MRBus interface"

         if mrbee is not None:
            mrbee.disconnect()
            
         if cmdStn is not None:
            cmdStn.disconnect()

         xbeePort = None
         if args.serial is not None:
            xbeePort = args.serial
         else:
            xbeePort = netUtils.findXbeePort()

         if xbeePort is None:
            print "No XBee found, waiting and retrying..."
            time.sleep(2)
            continue
         else:
            print "Trying to start XBee / MRBus on port %s" % xbeePort

         mrbee = mrbus.mrbus(xbeePort, baseAddress, logall=True, logfile=sys.stdout, busType='mrbee')

         mrbee.setXbeeLED('D9', True);

         if esuConnection is True:
		      print "Looking for ESU CabControl command station"
		      if server_ip is not None:
		         esuIP = server_ip
		      else:
		         esuIP = netUtils.serverFind(searchDelay, 15471)  # ESU CabControl is port 15471

		      if esuIP is None:
		         print "No ESU command station found, waiting and retrying..."
		         time.sleep(2)
		         continue

		      print "Trying ESU command station connection"
		   
		      cmdStn = esu.ESUConnection()
		      cmdStn.connect(esuIP)

         elif withrottleConnection is True:
            print "Looking for WiThrottle server"
            withrottleIP = None
            if server_ip is not None:
               withrottleIP = server_ip
            else:
               withrottleIP = netUtils.serverFind(searchDelay, withrottlePort)

            if withrottleIP is None:
               print "No WiThrottle server found, waiting and retrying..."
               time.sleep(2)
               continue

            print "Trying WiThrottle server connection"
		   
            cmdStn = withrottle.WiThrottleConnection()
            cmdStn.connect(withrottleIP, withrottlePort)
         
         else:
            print "No configured DCC system type - halting"
            mrbee.setXbeeLED('D6', True);
            while True:
               continue
               
         mrbee.setXbeeLED('D8', True);

         break

      except(KeyboardInterrupt):
         if cmdStn is not None:
            cmdStn.disconnect()
         if mrbee is not None:
            mrbee.disconnect()
         sys.exit()
      except Exception as e:
         print "Connection phase exception!!!"
         print e


   lastStatusTime = time.time()
   lastErrorTime = getMillis()
   errorLightOn = False

   lastPktTime = getMillis()
   pktLightOn = False

   print ""
   print " ENDING CONNECTION PHASE"
   print "-----------------------------------------------"
   print ""
   print "-----------------------------------------------"
   print " STARTING RUN PHASE"
   print ""
   # Main Run Loop - runs until something weird happens
   while 1:
      try:
         currentMillis = getMillis()
         
         if currentMillis > (lastErrorTime + 500) and errorLightOn:
            print "Turning Error light off"
            errorLightOn = False
            mrbee.setXbeeLED('D6', errorLightOn)

         if currentMillis > ( lastPktTime + 4000) and pktLightOn:
            print "Turning ProtoThrottle received light off"
            pktLightOn = False
            mrbee.setXbeeLED('D7', pktLightOn)

         pkt = mrbee.getpkt()

         if time.time() > lastStatusTime + statusInterval:
#            print "Sending status packet"
            statusPacket = [ ord('v'), 0x80, gitver[2], gitver[1], gitver[0], 1, 0, ord('E'), ord('S'), ord('U'), ord('E'), ord('N'), ord('E'), ord('T')]
            mrbee.sendpkt(0xFF, statusPacket)
            lastStatusTime = time.time()

         cmdStn.update()

         if pkt is None:
            continue

         if pkt.src == baseAddress:
            print "Conflicting ProtoThrottle base station detected!!!\nTurning Error light on"
            errorLightOn = True
            lastErrorTime = getMillis()
            mrbee.setXbeeLED('D6', errorLightOn)

         # Bypass anything that doesn't look like a throttle packet
         if pkt.cmd != 0x53 or len(pkt.data) != 10 or baseAddress != pkt.dest:
            continue

         if pkt.src not in throttles:
            throttles[pkt.src] = MRBusThrottle.MRBusThrottle(pkt.src)
      
         throttles[pkt.src].update(cmdStn, pkt)

         lastPktTime = getMillis()
         if False == pktLightOn:
            print "Turning ProtoThrottle received light on"
            pktLightOn = True
            mrbee.setXbeeLED('D7', pktLightOn)

      except (KeyboardInterrupt):
         cmdStn.disconnect()
         mrbee.disconnect()
         sys.exit()
      except Exception as e:
         print "Caught some sort of exception, restarting the whole thing"
         print e
         exc_info = sys.exc_info()
         traceback.print_exception(*exc_info)
         del exc_info         


         cmdStn.disconnect()
         mrbee.disconnect()
         break

