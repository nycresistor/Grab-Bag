#!/usr/bin/python

import serial
import re
import time
import sys

class Monitor:
    def __init__(self):
        self.serialPort = None

    def open(self,portName,baud=9600):
        self.serialPort = serial.Serial(portName, baud, timeout=10)
        try:
            self.serialPort.open()
        except serial.SerialException, e:
            sys.stderr.write("Could not open serial port %s: %s\n" % (self.serialPort.portstr, e))
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


if len(sys.argv) > 1:
    s = " ".join(sys.argv[1:])
    mon.serialPort.write(s+"\n")



