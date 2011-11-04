#! /bin/python
import sys, os, time, serial, sqlite3, random, json, math, socket

#Database
conn = sqlite3.connect('/var/www/barbot.sqlite')
c = conn.cursor()

#Sayings for twitter and LCD
#LCD says include formatting
twitterSayings = {0:"THIS IS #BATCOUNTRY", 1:"THIS IS #BATCOUNTRY", 2:"YOUR TURN TO DRIVE", 3:"I THINK I'M GETTING #THEFEAR", 4:"COME ON YOU #FIEND", 5:"PLEASE, TELL ME YOU BROUGHT THE FUCKING #GOLFSHOES", 6:"AS YOUR ATTORNEY I ADVISE YOU TO #SPIN", 7:"DOG'S FUCKED THE #POPE ? NO FAULT OF MINE", 8:"JUST ADMIRING THE SHAPE OF YOUR SKULL", 9:"DID THEY PAY YOU TO #SCREWTHATBEAR ?"}
lcdSayings = {0:"\n		 THIS IS\n	  BAT COUNTRY!", 1:"\n		SPIN IT\n	  TO WIN IT", 2:"\n		YOUR TURN\n		 TO DRIVE", 3:"\n	  I THINK I'M\n	 GETTING THE FEAR", 4:"\n	COME ON\n		 YOU FIEND", 5:"PLEASE, TELL ME\n	  YOU BROUGHT THE\nFUCKING GOLF SHOES", 6:"AS YOUR ATTORNEY\n		 I ADVISE YOU\n		 TO SPIN", 7:"DOG'S FUCKED\n		  THE POPE?\nNO FAULT OF MINE", 8:"\n	JUST ADMIRING\n	 THE SHAPE\n	 OF YOUR SKULL", 9:"\nDID THEY PAY YOU\n TO SCREW THAT BEAR?"}

#Serial Interfaces
slotMachine = '/dev/serial/by-id/usb-FTDI_TTL232R_FTE3G3MI-if00-port0'
barBot = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A900acNt-if00-port0'
screen = '/dev/serial/by-id/usb-FTDI_TTL232R_FTE55VLS-if00-port0'

#Possible replay wheel combinations
replay1 = [0, 4, 7, 11, 14, 18]
replay2 = [1, 6, 10, 14, 18]
replay3 = [0, 4, 8, 12, 16]
	   
def writeSpecials(drink, mixers):
	x = 0
	
	lcd.write(chr(0xFE)+chr(0x48))
	lcd.write(drink)
	lcd.write(chr(10))
	time.sleep(2)
	
	if len(mixers) > 2:

		clearLCD()
		lcd.write(drink)
		lcd.write(chr(10))
		lcd.write("\n	  ADD:")
		time.sleep(.5)
		clearLCD()

		for mixer in mixers:
			lcd.write(str(mixer))
			if x < len(mixers)-1 and len(str(mixer)) < 20:
				lcd.write(chr(10))
			x += 1
			
	elif len(mixers) > 0:
		lcd.write("ADD: \n")
		for mixer in mixers:
			lcd.write(str(mixer))
			lcd.write(chr(10))

	time.sleep(5)

def getDrinkCommands(drinknum):
	c.execute("SELECT * FROM drinkcommands LEFT OUTER JOIN ingrediants ON drinkcommands.ingrediant=ingrediants.id WHERE drinknum = %s ORDER BY id" % (drinknum))
	commands = c.fetchall()
	
def getRandomOrder():
	c.execute("SELECT COUNT (*) from drinks")
	count = c.fetchone()
	
	drinknum = random.randint(1,count[0])
	result = c.execute("SELECT name FROM drinks WHERE id = %s" % (drinknum))
	drinkname = c.fetchone()[0]
	
	return drinknum, drinkname
	
def getCustomOrder():
	c.execute("SELECT * FROM custom WHERE custom.done is NULL ORDER BY id")
	custom = c.fetchone()
	if custom is None: return None, None
	
	drinknum = custom[1]
	drinkname = c.execute("SELECT name FROM drinks WHERE id = %s" % (drinknum))
	
	print "Custom Drink Order Found: [%s] #%s - %s" % (str(custom[0]), str(drinknum), drinkname)
	
	return drinknum, drinkname
	
def getDrinkMultiplier():
	mult = c.execute("SELECT * FROM drinkmultiplier")
	mult = c.fetchone()
	mult = mult[1]
	print "Drink Multiplier: " + str(mult)
	return mult
	
def makeDrink(args=None):
#Make a random drink!
	drinkString = "DRINK ORDER "
	
	drinkMultiplier = getDrinkMultiplier()
	
	drinknum, drinkname = getCustomOrder()
	if drinkNum:
		result = c.execute("UPDATE custom SET done='True' WHERE id = %s" % (custom[0]))
	else:
		drinknum, drinkname = getRandomOrder()

	print "Making #%s - %s"%(str(drinknum), drinkname)
	
	commands = getDrinkCommands(drinknum)

	mixers = []
	for command in commands:
		# Alcohol? Add it to the drink order
		if command[9] != "True":
			drinkString += (str(command[2]) + ":" + str(int(command[3])*mult) + " ")
		else: # Mixer? Add it to the LCD screen
			mixers.append(str(command[3]) + " " + command[4] + " " + command[7])
			
	print drinkstring
	serBot.write(drinkString + "\n")

	clearLCD()
	writeSpecials(str(drinkname), mixers)	 
		
def printLCDMessage(x = random.randint(0, len(lcdSayings)-1)):
	#Print a predefined message on the LCD
	try:
		clearLCD()
		lcd.write(lcdSayings[x])
	except:
		print "Error: Could not connect to the LCD screen."
	
def clearLCD():
	lcd.write(chr(0xFE)+chr(0x58))		 

def replay(spinArgs):
	#Check for possible replay combinations
	
	for x in range(2,len(spinArgs)):
		spinArgs[x] = int(spinArgs[x])
		
	if spinArgs[3] in replay2: #is center wheel a replay?
		if (spinArgs[2] in replay1) and (spinArgs[4] in replay3):
			return True
		if (spinArgs[2]-1 in replay1) and (spinArgs[4]+1 in replay3):
			return True
		if (spinArgs[2]+1 in replay1) and (spinArgs[4]-1 in replay3):
			return True
		
	elif spinArgs[3]-1 in replay2:
		if (spinArgs[2]-1 in replay1) and (spinArgs[4]-1 in replay3):
			return True
	elif spinArgs[3]+1 in replay2:
		if (spinArgs[2]+1 in replay1) and (spinArgs[4]+1 in replay3):
			return True
	else:
		return False

def play():
	#global last_received
	last_received = ""
	buffer = ''
	lcdbuffer = ''
	clearLCD()
	lcd.write("IP ADDRESS:\n")
	
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("google.com",80))
		ip = str(s.getsockname()[0])
	except:
		ip = "0.0.0.0"

	lcd.write(ip)
	
	time.sleep(3)
	print "Waiting for Serial Input..." 
	
	printLCDMessage()
	
	while True:

		buffer += slotBot.read(slotBot.inWaiting())

		if '\n' in buffer:
			lines = buffer.split('\n')
			received = lines[-2]
			if (received == last_received):
				continue
			else:
				last_received = received
			buffer = lines[-1]
			print "Slot machine command: %s"%(last_received)
			
			if "COIN" in last_received: #Someone put a coin in!
				print "Coin received."
				
				slotBot.write("C\n")
				time.sleep(.2)
				slotBot.write("C\n")
				time.sleep(.2)
				slotBot.write("C\n")
					
			if "SPIN RESULT" in last_received: #Someone spun!
				spinArgs = last_received.split(" ")
				
				if replay(spinArgs) is True:
					print "Got a replay!"
				else:
					print "Not a replay."
					makeDrink()
					time.sleep(3)
					clearLCD()
					printLCDMessage()
			
		time.sleep(.1)

if __name__ == '__main__':
	print "NYC Resistor BarBot Initializing."
	
	try:
		serBot = serial.Serial(barBot, 9600, timeout=.1)
		serBot.open()
	except:
		print "Error: Could not connect to the robot bartender."
		sys.exit(1)
	
	try:
		slotBot = serial.Serial(slotMachine, 9600, timeout=.1)
		slotBot.open()
		slotBot.flushInput()
	except:
		print "Error: Could not connect to the slot machine interface."
		sys.exit(1)
		
	try:
		lcd = serial.Serial(screen, 19200)
		lcd.open()	   
		clearLCD()
		lcd.write("\n BarBot Operational")
	except:
		print "Error: Could not connect to the LCD Screen."
		sys.exit(1)
		
	play()