from time import time
import socket
import serial.tools.list_ports

def findXbeePort():
   ports = list(serial.tools.list_ports.grep("ttyUSB"))
   for p in ports:
      if "FTDI" == p.manufacturer:
         return p.device
   return None


def get_ip():
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

def testPort(ip, port, timeout=0.3):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            return 1
        except(socket.timeout,socket.error):
            return 0

def esuFind():
   defaultIP = get_ip()
   o1,o2,o3,o4 = defaultIP.split('.')
   print "Starting Scan"
   for i in range(0,254):
      scanIP = "%s.%s.%s.%d" % (o1, o2, o3, i)
      result = testPort(scanIP, 15471, 0.01)
      if result:
         print "IP %s has ESU port open" % (scanIP)
         return scanIP
   return None

