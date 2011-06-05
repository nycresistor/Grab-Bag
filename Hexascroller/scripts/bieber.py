#!/usr/bin/python

import serial
import re
import time
import sys
import simplejson
import popen2

class Monitor:
    def __init__(self):
        self.serialPort = None

    def open(self,portName,baud=9600):
        self.serialPort = serial.Serial(portName, baud, timeout=10)
        try:
            self.serialPort.open()
        except serial.SerialException, e:
            sys.stderr.write("Could not open serial port %s: %s\n" % (self.serialPort.portstr, e)
)
        time.sleep(1.1);
        self.serialPort.write("+++");
        time.sleep(1.1);
        self.serialPort.write("ATPL2\r");
        time.sleep(0.03);
        self.serialPort.write("ATMY2\r");
        time.sleep(0.03);
        self.serialPort.write("ATDL1\r");
        time.sleep(0.03);
        self.serialPort.write("ATSM0\r");
        time.sleep(0.03);
        self.serialPort.write("ATCN\r");
        time.sleep(0.03);
        data = self.serialPort.read(1)  # read one, blocking
        n = self.serialPort.inWaiting() # look if there is more
        if n:
            data = data + self.serialPort.read(n)
        print "DATA: ", data

mon = Monitor()
mon.open("/dev/ttyUSB0")
last_id = "foo"

req_str=r"wget --quiet -O - 'http://search.twitter.com/search.json?q=%23bieber&rpp=1&page=1'"

def twitter():
    global last_id
    while 1:
        try:
            (so,si) = popen2.popen2(req_str)
            d = so.read().encode('ascii')
            o = simplejson.loads(d)
            r = o['results'][0]
            t_id = r['id']
            t_text = r['text']
            if (t_id != last_id):
                last_id = t_id
                print "Writing",t_id,t_text
                m = str(t_text)
                while (len(m)+len(t_text)+5) < 70:
                    m = m + "          "+t_text
                mon.serialPort.write(str(m+"\n"))
        except Exception, e:
            print "except", e
            pass
        time.sleep(2)

if len(sys.argv) > 1:
    s = " ".join(sys.argv[1:])
    mon.serialPort.write(s+"\n")
else:
    twitter()




