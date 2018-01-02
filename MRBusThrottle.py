import esu
import mrbus
import sys
import time

class MRBusThrottle:

   
   def __init__(self):
      self.locAddr = 0
      self.locAddrShort = 0
      self.locSpeed = 0
      self.locDirection = 0
      self.locObjID = 0
      self.locEStop = 0
      self.locFunctions = [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]
      return
   
   def update(self, cmdStn, pkt):
      if pkt.cmd != 0x53 or len(pkt.data) != 10:  # Not a status update, bump out
         return
         
      addr = pkt.data[0] * 256 + pkt.data[1]
      if (addr & 0x8000):
         locAddrShort = 1
         addr = addr & 0x007F
         
      speed = pkt.data[2] & 0x7F
      if 1 == speed:
         speed = 0
         estop = 1
      elif speed > 1:
         estop = 0
         speed = speed - 1
      elif speed == 0:
         estop = 0
      
      if pkt.data[2] & 0x80:
         direction = 0
      else:
         direction = 1

      if (addr != self.locAddr):
         self.locObjID = cmdStn.esuLocomotiveObjectGet(addr)
         self.locAddr = addr
         print "Acquiring new locomotive %d - objID = %d" % (self.locAddr, self.locObjID)
         
      if estop != self.locEStop and estop != 1:
         esuLocomotiveEmergencyStop(self.locObjID)

      self.locEStop = estop

      if speed != self.locSpeed or direction != self.locDirection:
         print "Updating speed/dir to %d/%d for locomotive %d" % (speed, direction, self.locAddr)
         cmdStn.esuLocomotiveSpeedSet(self.locObjID, speed, direction)

      self.locSpeed = speed
      self.locDirection = direction
      
      functions = [ 0,0,0,0,0,0,0,0,0,0,
                       0,0,0,0,0,0,0,0,0,0,
                       0,0,0,0,0,0,0,0 ]
      
      for i in range(28):
#         print "i=%d, shifter = %08X" % (i, 1<<(i))
         if i >= 0 and i < 8:
            if pkt.data[6] & (1<<i):
               functions[i] = 1
         elif i >= 8 and i < 16:
            if pkt.data[5] & (1<<(i-8)):
               functions[i] = 1
         elif i >= 16 and i < 24:
            if pkt.data[4] & (1<<(i-16)):
               functions[i] = 1
         elif i >= 24 and i < 28:
            if pkt.data[3] & (1<<(i-24)):
               functions[i] = 1
         
      funcsChanged = { }
      for i in range(28):
         if functions[i] != self.locFunctions[i]:
            print "Sending update for function %d to state %d" % (i, functions[i])
            cmdStn.esuLocomotiveFunctionSet(self.locObjID, i, functions[i])

      self.locFunctions = functions
      
      return
      
