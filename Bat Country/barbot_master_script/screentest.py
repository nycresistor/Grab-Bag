import serial, time
screen = '/dev/serial/by-id/usb-FTDI_TTL232R_FTDXPLJO-if00-port0'

def clearLCD():
    lcd.write(chr(0xFE)+chr(0x58))
    
lcd = serial.Serial(screen, 19200)
lcd.open()

clearLCD()
lcd.write("\n Screen Operational!")
time.sleep(1)
buffer = ''

while True:
	buffer = buffer + lcd.read(lcd.inWaiting())
	print "BUFFER: " + buffer
	time.sleep(1)