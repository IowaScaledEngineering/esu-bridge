#!/usr/bin/python
# ESU Cab Control Python Bridge

import socket
import re

ESU_PORT = 15471
ESU_RCV_SZ = 1024


# <REPLY set (1007, name ["Big Boy"])>
# 1007 name ["Big Boy"]
# <END 0 (OK)>


class ESUConnection:
   conn = socket.socket()
   REglobalList = re.compile("(?P<objID>\d+)\s+addr\[(?P<locAddr>\d+)\].*")
   RElocAdd = re.compile("10\s+id\[(?P<objID>\d+)\].*")
   
   def __init__(self):
      self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     
   def connect(self, ip):
      print "Trying to connect to %s" % (ip)
      try:
         self.conn.connect((ip, ESU_PORT))
         print "ESU command station connection succeeded"
      except:
         print "ESU command station connection failed"
      
   def disconnent(self):
      print "Disconnecting"
      conn.close()
      
   def esuTXRX(self, cmdStr, parseRE=None, resultKey=''):
      self.conn.send(cmdStr)
      resp = self.conn.recv(ESU_RCV_SZ)
      # Find the response
      lines = resp.splitlines()
      numDataElements = len(lines)
      if (lines[0] != "<REPLY %s>" % (cmdStr)):
         print "YIKES!  Reply malformed!"
      if (lines[numDataElements-1] != "<END 0 (OK)>"):
         print "Got an error back, parsing..."
      
      if parseRE is None:
         return {}
      
      results = { }
      for idx in range(1, numDataElements-1):
         try:
            parsed = parseRE.match(lines[idx])

            if resultKey == "":
               results[len(results)] = parsed.groupdict()
            else:
               results[parsed.group(resultKey)] = parsed.groupdict()
         except:
            print "Line %d does not match regex\n  Line %d: '%s'" % (idx, idx, lines[idx])

      return results

   def esuLocomotiveAdd(self, locoNum, locoName=""):
      cmdStr = "create(10, addr[%d], append)" % ( int(locoNum))
      result = self.esuTXRX(cmdStr, self.RElocAdd)
      return int(result[0]['objID'])

   def esuLocomotiveAcquire(self, objID):
      objID = int(objID)
      cmdStr = "request (%d, control, force)" % (objID)
      self.esuTXRX(cmdStr)

          
   def esuLocomotiveObjectGet(self, locoNum):
      cmdStr = "queryObjects(10,addr)"
      locoList = self.esuTXRX(cmdStr, self.REglobalList, 'locAddr')
      
      locAddr = "%d" % (int(locoNum))
      
      if locAddr in locoList.keys():
         objID = int(locoList[locAddr]['objID'])
         print "Found locomotive %s at object %d" % (locAddr, objID)
         return objID
      else:
         print "Need to add this locomotive"
         objID = self.esuLocomotiveAdd(locoNum)
         print "Added locomotive %s at object %d" % (locAddr, objID)
         return objID
         
   def esuLocomotiveEmergencyStop(self, objID):
      objID = int(objID)
      cmdStr = "set (%d, stop)" % (objID)
      self.esuTXRX(cmdStr)
      

   # For the purposes of this function, direction of 0=forward, 1=reverse
   def esuLocomotiveSpeedSet(self, objID, speed, direction=0):
      objID = int(objID)
      speed = int(speed)
      direction = int(direction)
      
      if direction != 0 and direction != 1:
         speed = 0
         direction = 0
      
      if speed >= 127 or speed < 0:
         speed = 0

      cmdStr = "set(%d, speed[%d], dir[%d])" % (objID, speed, direction)
      self.esuTXRX(cmdStr)
      
      print "Set speed on locomotive ID %d to %d, %s" % (objID, speed, ["FWD","REV"][direction])
   
   def esuLocomotiveFunctionSet(self, objID, funcNum, funcVal):
      objID = int(objID)
      funcNum = int(funcNum)
      funcVal = int(funcVal)
     
      cmdStr = "set(%d, func[%d,%d])" % (objID, funcNum, funcVal)
      self.esuTXRX(cmdStr)   

   def esuLocomotiveFunctionDictSet(self, objID, funcDict):
      objID = int(objID)
      
      funcStr = ""
      
      for funcNum in funcDict:
         funcNum = int(funcNum)
         funcVal = int(funcDict[funcNum])
         
         funcStr = funcStr + ", func[%d,%d]" % (funcNum, funcVal)
     
      cmdStr = "set(%d%s])" % (objID, funcStr)
      self.esuTXRX(cmdStr)   


   def disconnect(self):
      self.conn.close()
      print "Disconnected"
   
   
   
