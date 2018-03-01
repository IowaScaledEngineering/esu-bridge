# *************************************************************************
# Title:    Client for JMRI Wireless Throttle Connections
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
#   This class provides a client to connect to a JMRI WiThrottle server (or
#   compatible, such as Digitrax's LNWI or the MRC thingy) and control multiple
#   locomotives.  
# 
# *************************************************************************

import socket
import re
import time

WITHROTTLE_RCV_SZ = 4096

class WiThrottleConnection:
   """A client object to talk to a JMRI WiFi Throttle server or compatible.  
      This class is capable of handling multiple locomotives simultaneously via
      independent socket connections."""

   conn = socket.socket()
   recvBuffer = ""
   activeThrottles = { }
   lastUpdates = { }
   ip = None
   port = None
   
   def __init__(self):
      """Constructor for the object.  Any internal initialization should occur here."""
      self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.conn.settimeout(0.01)
      
   def connect(self, ip, port):
      """Normally connect() should actually connect the object to the command station, but
         since WiThrottle needs essentially one socket per cab, this just saves off the ip 
         and port for later connections."""
      print "Storing off server [%s] and port [%d] for later use" % (ip, port)
      self.ip = ip
      self.port = port

   def disconnect(self):
      """Shut down all throttle socket connections and disconnect from the WiThrottle server in a clean way."""
      for addr,connection in self.activeThrottles.iteritems():
         self.rxtx(addr, "Q\n")
         time.sleep(0.1)
         connection.close()
      self.activeThrottles = { }
      self.lastUpdates = { }
      print "Disconnected"
      
   def rxtx(self, cabID, cmdStr):
      """Internal shared function for transacting with the WiThrottle server."""
      connection = self.activeThrottles[cabID]
      self.lastUpdates[cabID] = time.time()
      connection.sendall(cmdStr)
      try:
         recvBuffer = connection.recv(WITHROTTLE_RCV_SZ)
      except:
         pass
      
   def locomotiveObjectGet(self, locoNum, cabID):
      """Acquires and returns a handle that will be used to control a locomotive address.  This will release
         any locomotive that cabID was previously controlling."""
      print "WiThrottle locomotiveObjectGet"
      objID = {'addr':cabID, 'locoNum':locoNum, 'isLong':True }

      if cabID in self.activeThrottles:
         self.rxtx(objID['addr'], "Tr\n")
      else:
         self.activeThrottles[cabID] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         self.activeThrottles[cabID].settimeout(0.01)
         self.activeThrottles[cabID].connect((self.ip, self.port))
         self.rxtx(objID['addr'], "NProtoThrottle 0x%02X\n" % (cabID))
         self.rxtx(objID['addr'], "*60\n")

      if objID['isLong']:
         self.rxtx(objID['addr'], "TL%d\n" % (objID['locoNum']))
      else:
         self.rxtx(objID['addr'], "TS%d\n" % (objID['locoNum']))
     
      return objID
         
   def locomotiveEmergencyStop(self, objID):
      """Issues an emergency stop command to a locomotive handle that has been previously acquired with locomotiveObjectGet()."""
      self.rxtx(objID['addr'], "TX\n")

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

      self.rxtx(objID['addr'], "TV%d\n" % (speed))
      # Direction is 0=REV, 1=FWD on WiThrottle
      self.rxtx(objID['addr'], "TR%d\n" % ([1,0][direction]))

      print "Set speed on locomotive ID %d to %d, %s" % (objID['locoNum'], speed, ["FWD","REV"][direction])
   
   def locomotiveFunctionSet(self, objID, funcNum, funcVal):
      """Sets or clears a function on a locomotive via a handle that has been previously acquired with locomotiveObjectGet().  
         funcNum is 0-28 for DCC, funcVal is 0 or 1."""
      funcNum = int(funcNum)
      funcVal = int(funcVal)
      self.rxtx(objID['addr'], "Tf%d%d\n" % ( funcVal, funcNum))

      print "Set function %d on locomotive ID %d to %d" % (funcNum, objID['locoNum'],  funcVal)

   def update(self):
      """This should be called frequently within the main program loop.  This implements the keepalive heartbeat
         within the WiThrottle protocol... badly.  Right now it's hard-wired to 10 seconds."""
      for addr,lastUpdate in self.lastUpdates.iteritems():
         if time.time() > lastUpdate + 10:
            self.rxtx(addr, "*\n")



   
   
