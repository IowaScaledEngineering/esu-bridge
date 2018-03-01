# *************************************************************************
# Title:    Client for Digitrax LNWI Wireless Throttle Connections
# Authors:  Nathan D. Holmes <maverick@drgw.net>
#           Michael D. Petersen <railfan@drgw.net>
# File:     withrottle.py
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
#   This class provides a client to connect to a Digitrax LNWI
#   adapter.  The standard WiThrottle driver cannot be used because
#   Digitrax only chose to implement a subset of the JMRI protocol.
# 
# *************************************************************************

import socket
import re
import time

WITHROTTLE_RCV_SZ = 4096

class LNWIConnection:
   """A client object to talk to a JMRI WiFi Throttle server or compatible.  
      This class is capable of handling multiple locomotives simultaneously via
      independent socket connections."""

   conn = socket.socket()
   recvBuffer = ""
   activeThrottles = { }
   lastUpdate = 0
   recvData = ""
   ip = None
   port = None

   version = ""
   trackPowerOn = False
   heartbeatMaxInterval = 10
   serverName = ""
   serverID = ""

   def __init__(self):
      """Constructor for the object.  Any internal initialization should occur here."""
      
   def connect(self, ip, port):
      """Since the LNWI only understands a subset of Multithrottle commands, open up a single connection
         to multiplex everything through."""
      print "Storing off server [%s] and port [%d] for later use" % (ip, port)
      self.ip = ip
      self.port = port
      self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.conn.settimeout(0.01)
      self.conn.connect((self.ip, self.port))
      self.recvData = ""
      self.rxtx("NProtoThrottle LNWI\n")
      self.rxtx("HUProtoThrottle LNWI\n")
      self.activeThrottles = { }


   def disconnect(self):
      """Shut down all throttle socket connections and disconnect from the WiThrottle server in a clean way."""
      for cabID,mtID in self.activeThrottles.iteritems():
         self.rxtx("M%1.1sA*<;>r\n" % (mtID))
         self.rxtx("M%1.1s-*<;>\n" % (mtID))
         time.sleep(0.1)
         connection.close()
      self.rxtx(addr, "Q\n")
      self.activeThrottles = { }
      print "Disconnected"

   def parseIncomingData(self):
      # If there's no carriage returns, we don't have a complete response of any sort yet
      if '\n' not in self.recvData:
         return

      responseStrings = self.recvData.split(recvData, '\n')

      # If there's trailing unfinished data, put it back in the recieve data queue, otherwise clear it
      if not self.recvData.endswith('\n'):
         self.recvData = responseStrings.pop()
      else:
         self.recvData = ""

      for resp in responseStrings:
         # Trim whitespace
         resp = resp.strip()

         # No length?  Nothing to do
         if len(resp) == 0:
            continue


         if ('VN' == resp[0:2]):  # Protocol version
            self.version = cmdChr[2:]
         elif ('RL' == resp[0:2]):  # Roster List, don't care right now
            pass
         elif ('PPA' == resp[0:3]):  # Track Power
            if resp[3:4] == '1': # Track power on
               trackPowerOn = True
            elif resp[3:4] == '0':  # Track power off
               trackPowerOn = False
            elif resp[3:4] == '2': # Track power unknown - assume the best, on...
               trackPowerOn = True
         elif ('PT' == resp[0:2]):  # Turnout lists, don't care right now
            pass
         elif ('PR' == resp[0:2]):  # Route lists, don't care right now
            pass
         elif ('*' == resp[0:1]):  # Heartbeat interval
            try:
               self.heartbeatMaxInterval = int(resp[1:])
            except:
               self.heartbeatMaxInterval = 10
         elif ('N' == resp[0:1]):  # Host controller name
            serverName = resp[1:]
         elif ('U' == resp[0:1]):  # Host controller name
            serverID = resp[1:]
         elif ('M' == resp[0:1]):  # Some sort of multithrottle response - parse this
            pass  # FIXME
         else:
            print "Got unknown host->client string of [%s], ignoring\n" % resp


   def rxtx(self, cmdStr):
      """Internal shared function for transacting with the WiThrottle server."""
      self.lastUpdate = time.time()
      self.conn.sendall(cmdStr)
      try:
         self.recvBuffer += self.conn.recv(WITHROTTLE_RCV_SZ)
      except:
         pass
      self.parseIncomingData()

   def getAvailableMultithrottleLetter():
      mtLetters = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZ012345')
      usedMTLetters = set(activeThrottles.values())
      mtLetters.difference(usedMTLetters)
      return mtLetters.pop()

   def locomotiveObjectGet(self, locoNum, cabID, isLongAddress=True):
      """Acquires and returns a handle that will be used to control a locomotive address.  This will release
         any locomotive that cabID was previously controlling."""
      print "WiThrottle locomotiveObjectGet"

      if cabID not in activeThrottles:
         activeThrottles[cabID] = getAvailableMultithrottleLetter()

      objID = {'addr':cabID, 'locoNum':locoNum, 'isLong':isLongAddress }

      #Drop anything this cab might have had before.  If nothing, no harm
      self.rxtx("M%1.1sA*<;>r\n" % (activeThrottles[objID['addr']]))
      self.rxtx("M%1.1s-*<;>\n" % (activeThrottles[objID['addr']]))

      if objID['isLong']:
         # Acquire new locomotive at long address
         self.rxtx("M%1.1s+L%d<;>L%d\n" % (activeThrottles[objID['addr']], objID['locoNum']))
      else:
         self.rxtx("M%1.1s+S%d<;>S%d\n" % (activeThrottles[objID['addr']], objID['locoNum']))
      return objID
         
   def locomotiveEmergencyStop(self, objID):
      """Issues an emergency stop command to a locomotive handle that has been previously acquired with locomotiveObjectGet()."""
      self.rxtx("M%1.1sA*<;>X\n", activeThrottles[objID['addr']])

   # For the purposes of this function, direction of 0=forward, 1=reverse
   def locomotiveSpeedSet(self, objID, speed, direction=0):
      """Sets the speed and direction of a locomotive via a handle that has been previously acquired with locomotiveObjectGet().  
         Speed is 0-127, Direction is 0=forward, 1=reverse."""
      speed = int(speed)
      direction = int(direction)
      
      if direction != 0 and direction != 1:
         speed = 0
         direction = 0
      
      if speed >= 127 or speed < 0:
         speed = 0

      self.rxtx("M%1.1sA*<;>V%d\n" % (activeThrottles[objID['addr']], speed))
      # Direction is 0=REV, 1=FWD on WiThrottle
      self.rxtx("M%1.1sA*<;>R%d\n" % (activeThrottles[objID['addr']], [1,0][direction]))

      print "Set speed on locomotive ID %d to %d, %s" % (objID['locoNum'], speed, ["FWD","REV"][direction])
   
   def locomotiveFunctionSet(self, objID, funcNum, funcVal):
      """Sets or clears a function on a locomotive via a handle that has been previously acquired with locomotiveObjectGet().  
         funcNum is 0-28 for DCC, funcVal is 0 or 1."""
      funcNum = int(funcNum)
      funcVal = int(funcVal)

      # This is the nasty part.  The LNWI doesn't support the "force function" ('f') command, so we have to do 
      # weird crap here to actually get the function in the state we want.
      # FIXME, this is wrong
      self.rxtx("M%1.1sA*<;>F1%d\n" % (activeThrottles[objID['addr']], funcNum))
      self.rxtx("M%1.1sA*<;>F0%d\n" % (activeThrottles[objID['addr']], funcNum))

      print "Set function %d on locomotive ID %d to %d" % (funcNum, objID['locoNum'],  funcVal)

   def update(self):
      """This should be called frequently within the main program loop.  This implements the keepalive heartbeat
         within the WiThrottle protocol... badly.  Right now it's hard-wired to 10 seconds."""
      heartbeatInterval = (self.heartbeatMaxInterval / 2)
      if heartbeatInterval < 1:
         heartbeatInterval = 1

      if time.time() > lastUpdate + heartbeatInterval:
         self.rxtx("*\n")

      self.parseIncomingData()


   
   
