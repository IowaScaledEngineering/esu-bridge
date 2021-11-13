# Title:    Client for JMRI Clock
# Authors:  Thomas Pfarr
# File:     JMRIClock.py
# License: BSD 3-Clause license for the lomond module
#
# LICENSE for lomond websocket module:
# Copyright (c) 2017, WildFoundry Ltd (UK Company No: 08045924) All rights reserved.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
#  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT #NOT LIMITED TO, THE IMPLIED WARRANTIES
#  OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
#  SHALL THE #COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#  TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
#  OR BUSINESS INTERRUPTION) #HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
#  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
#  POSSIBILITY OF SUCH DAMAGE.
#
# DESCRIPTION:
#   This class provides a client to connect to a JMRI websocket time source

import socket
import time
from lomond import WebSocket
import thread

class JMRIClock():
   """class provides for JMRI clock retrieval via websocket interface for transmission to the protothrottle"""
   def __init__(self, timeZoneOffset):
      """Constructor for the object.  Any internal initialization should occur here."""
      self.timetext = ""
      self.offset = int(timeZoneOffset)

   def monitorTime(self, threadname, websocket):
        for event in websocket.connect(ping_rate=7):
            #print "event received->%s [%s]" % (event, event.name)
            if event.name == "ready":
               websocket.send_json(type='time', data='')
            elif event.name == "text":
               timedict = event.json
#               print "json received: %s\n" % (event.json)
               if timedict.get("type","none") == "time":
                  self.timetext = timedict.get("data", "nodata").get("time", "nodata")
                  print "JMRI sent time = [%s]" % (self.timetext)
            elif event.name == "connect_fail":
               try:
                  raise ValueError("JMRI Websocket connection failure, check that it is running on the right port") 
               except ValueError as e:
                  print e
               
   def connect(self, ipaddr, port):
      self.jmriwebsocket = WebSocket("ws://%s:%d/json/time" % (ipaddr, port))
      print "Starting websocket thread for JMRI time retrieval"
      thread.start_new_thread(self.monitorTime, ("timeMon", self.jmriwebsocket))

   def disconnect(self):
      self.jmriwebsocket.close()

   def getHours(self):      
      index = self.timetext.find("T")
      if index == -1:
         return 99
      else:
         return int((int(self.timetext[index+1:index+3]) + self.offset) % 24)

   def getMinutes(self):
      index = self.timetext.find("T")
      if index == -1:
         return 99
      else:
         return int(self.timetext[index+4:index+6])
