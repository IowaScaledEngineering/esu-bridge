# *************************************************************************
# Title:    Client driver for MRBus Throttle (mainly the ProtoThrottle)
# Authors:  Michael D. Petersen <railfan@drgw.net>
#           Nathan D. Holmes <maverick@drgw.net>
# File:     MRBusThrottle.py
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
#   This class provides a way parse incoming MRBus throttle packets (primarily
#   from the ProtoThrottle ( http://www.protothrottle.com/ ) and send them
#   on to a variety of command stations as a form of protocol translator.
# 
# *************************************************************************

import mrbus
import sys
import time

class MRBusThrottle:
   
   def __init__(self, addr):
      self.locAddr = 0
      self.locAddrShort = 0
      self.locSpeed = 0
      self.locDirection = 0
      self.locObjID = 0
      self.locEStop = 0
      self.locFunctions = [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]
      self.throttleAddr = addr
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
         self.locObjID = cmdStn.locomotiveObjectGet(addr, self.throttleAddr)
         self.locAddr = addr
         print "Acquiring new locomotive %d - objID = %s" % (self.locAddr, self.locObjID)
      
      # Only send ESTOP if we just moved into that state
      if estop != self.locEStop and estop == 1:
         print "Sending ESTOP locomotive %d" % (self.locAddr)
         cmdStn.locomotiveEmergencyStop(self.locObjID)

      self.locEStop = estop

      if self.locEStop != 1 and (speed != self.locSpeed or direction != self.locDirection):
         print "Updating speed/dir to %d/%d for locomotive %d" % (speed, direction, self.locAddr)
         cmdStn.locomotiveSpeedSet(self.locObjID, speed, direction)

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
            cmdStn.locomotiveFunctionSet(self.locObjID, i, functions[i])

      self.locFunctions = functions
      
      return
      
