# *************************************************************************
# Title:    Helper Functions for esu-bridge
# Authors:  Michael D. Petersen <railfan@drgw.net>
#           Nathan D. Holmes <maverick@drgw.net>
# File:     netUtils.py
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
#   This class provides various helper functions to discover networks and
#   serial ports for autoconfiguring the esu-bridge project.
# 
# *************************************************************************

from time import time
import socket

try:
   import serial.tools.list_ports
except ImportError:
   raise ImportError('serial.tools.list_ports is missing - you probably need to use pip to install serial and pySerial')

def findXbeePort():
   """This looks for the first USB serial port with an FTDI bridge chip.  In the RasPi embedded esu-bridge, this will always be the XBee."""
   ports = list(serial.tools.list_ports.grep("ttyUSB"))
   for p in ports:
      if "FTDI" == p.manufacturer:
         return p.device
   return None


def get_ip():
   """Tries to determine our local network IP address."""
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   try:
      # doesn't even have to be reachable
      s.connect(('10.255.255.255', 1))
      IP = s.getsockname()[0]
   except:
      IP = '127.0.0.1'
   finally:
      s.close()
   return IP

def testPort(ip, port, timeout=0.01):
   """Tests a given ip and port to see if there's something listening.  Returns True if there is."""
   try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.settimeout(timeout)
      s.connect((ip, port))
      return True
   except(socket.timeout,socket.error):
      return False

def serverFind(timeout, port):
   """Given a port, this searches the local class C subnet for anything with that port open."""
   defaultIP = get_ip()
   o1,o2,o3,o4 = defaultIP.split('.')
   print "Starting Scan"
   for i in range(0,254):
      scanIP = "%s.%s.%s.%d" % (o1, o2, o3, i)
      result = testPort(scanIP, port, timeout)
      if result:
         print "IP %s has port %d open" % (scanIP, port)
         return scanIP
   return None


