#!/usr/bin/python

# By Adam Mayer 1/11/2014
# Usage: python send_hurco.py myFile.gcode
# On Hurco: upload file, serial port 1

import serial
import sys
import signal

#port = '/dev/tty.usbserial-A501E3GX' # Mac
port = '/dev/ttyUSB0' # Linux

ser = serial.Serial('/dev/tty.usbserial-A501E3GX',9600,parity=serial.PARITY_EVEN,
                bytesize=serial.SEVENBITS,stopbits=serial.STOPBITS_ONE,
                xonxoff=False)

def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        ser.close()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

f = open(sys.argv[1],'r')

while True:
    inb = ser.read(1)
    if inb == serial.XON:
        print "GOT XON"
        ser.write(f.read())
        ser.write('\x04')
        ser.flush()
        ser.read(1)
        break
    else:
        print "GOT JUNK"

ser.close()
