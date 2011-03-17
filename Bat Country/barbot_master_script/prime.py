#! /bin/python
import serial, time

#Serial Interfaces
barBot = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A900acNt-if00-port0'
serBot = serial.Serial(barBot, 9600, timeout=.1)
serBot.open()

time.sleep(4)

primeString = "DRINK ORDER "

for f in range(1, 13):
	primeString += str(f) + ":12000 "
print primeString
serBot.write(primeString + "\n")