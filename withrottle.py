#!/usr/bin/python
# WiThrottle Python Bridge

import socket
import re
import time

WITHROTTLE_RCV_SZ = 4096

class WiThrottleConnection:
   conn = socket.socket()
   recvBuffer = ""
   activeThrottles = { }
   lastUpdates = { }
   ip = None
   port = None
   
   def __init__(self):
      self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.conn.settimeout(0.01)
      
   def connect(self, ip, port):
      print "Trying to connect to %s" % (ip)
      self.ip = ip
      self.port = port
      
   def rxtx(self, addr, cmdStr):
      connection = self.activeThrottles[addr]
      self.lastUpdates[addr] = time.time()
      connection.sendall(cmdStr)
      try:
         recvBuffer = connection.recv(WITHROTTLE_RCV_SZ)
      except:
         pass
      
   def locomotiveObjectGet(self, locoNum, srcAddr):
      print "WiThrottle locomotiveObjectGet"
      objID = {'addr':srcAddr, 'locoNum':locoNum, 'isLong':True }

      if srcAddr in self.activeThrottles:
         self.rxtx(objID['addr'], "Tr\n")
      else:
         self.activeThrottles[srcAddr] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         self.activeThrottles[srcAddr].settimeout(0.01)
         self.activeThrottles[srcAddr].connect((self.ip, self.port))
         self.rxtx(objID['addr'], "NProtoThrottle 0x%02X\n" % (srcAddr))
         self.rxtx(objID['addr'], "*60\n")

      if objID['isLong']:
         self.rxtx(objID['addr'], "TL%d\n" % (objID['locoNum']))
      else:
         self.rxtx(objID['addr'], "TS%d\n" % (objID['locoNum']))
     
      return objID
         
   def locomotiveEmergencyStop(self, objID):
      self.rxtx(objID['addr'], "TX\n")

   # For the purposes of this function, direction of 0=forward, 1=reverse
   def locomotiveSpeedSet(self, objID, speed, direction=0):
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
      funcNum = int(funcNum)
      funcVal = int(funcVal)
      self.rxtx(objID['addr'], "Tf%d%d\n" % ( funcVal, funcNum))

      print "Set function %d on locomotive ID %d to %d" % (funcNum, objID['locoNum'],  funcVal)

   def update(self):
      for addr,lastUpdate in self.lastUpdates.iteritems():
         if time.time() > lastUpdate + 10:
            self.rxtx(addr, "*\n")

   def disconnect(self):
      for addr,connection in self.activeThrottles.iteritems():
         connection.close()
      self.conn.close()
      print "Disconnected"

   
   
