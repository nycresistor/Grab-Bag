#! /bin/python

import shlex, sys, os, time, subprocess, serial, sqlite3, random, json

conn = sqlite3.connect('/var/www/barbot.sqlite')
c = conn.cursor()

cmd = "mplayer -idle -fixed-vo -framedrop -quiet -slave -autosync 0 -fs -zoom -x 760 -y 600 /home/nycr/Video/main.mov"
args = shlex.split(cmd)

slotMachine = '/dev/serial/by-id/usb-FTDI_TTL232R_FTE3G3MI-if00-port0'
barBot = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A900acNt-if00-port0'

vids = {1:40.58, 2:19.43, 3:19.43, 4:38.66, 5:31.28, 6:27.81, 7:35.20, 8:30.28, 9:32.90}

x = 1

def playVid():
    print "= = = = = Playing new Video = = = = ="
    
    
    #video = random.randint(1,9)
    
    video = c.execute("SELECT * FROM videos ORDER BY played desc")
    video = c.fetchone()
    
    print video
    
    video = video[1]
    
    print " = = = = = Playing Video %s = = = = =" % (video)
    cmd = "loadfile /home/nycr/Video/vids/%s\n" % (video)
    p.stdin.write(cmd)

    log("Playing Video %s" % (video))

    #print "Sleeping for " + str("%.0d" % round(vids[video], -0)) + " seconds"
    
    #for i in range(int("%.0d" % round(vids[video], -0))):
    for i in range(video[3]):
        buffer=''
        buffer = buffer + ser.read(ser.inWaiting())
        if '\n' in buffer:
            break
        time.sleep(1)
    
    print "Returning to Main Loop"
    p.stdin.write("loadfile /home/nycr/Video/main.mov\n")
    
def makeDrink(args=None):
   
    drinkString = "DRINK ORDER "
    
    custom = c.execute("SELECT * FROM custom WHERE done is NULL ORDER BY id")
    custom = c.fetchone()
    
    if custom is not None:
    	print "CUSTOM ORDER: %s" % (custom[1])
    	drinknum = custom[1]
    	result = c.execute("UPDATE custom SET done='True' WHERE id = %s" % (custom[0]))
    	
    else:
    	count = c.execute("SELECT COUNT (*) from drinks")
    	count = c.fetchone()
    
    	drinknum = random.randint(1,count[0])
    	#print "DRINKNUM: " + str(drinknum)

    
    result = c.execute("SELECT name FROM drinks WHERE id = %s" % (drinknum))
    drinkname = c.fetchone()[0]
    print "Making #" + str(drinknum) + " " + drinkname
    
    results = c.execute("SELECT * FROM drinkcommands LEFT OUTER JOIN ingrediants ON drinkcommands.ingrediant=ingrediants.id WHERE drinknum = %s AND ingrediants.oob is not 'True' ORDER BY id" % (drinknum))
    #results = c.execute("SELECT * FROM drinkcommands AS dc JOIN ingrediants AS i ON dc.ingrediant=i.id JOIN special AS s ON dc.drinknum=s.drinknum WHERE dc.drinknum=%s" % (drinknum))
    commands = c.fetchall()
    
    results = c.execute("SELECT * FROM special WHERE id=%s" % (drinknum))
    specials = c.fetchall()
    

    for command in commands:
        print str(command[3]) + " " + command[4] + " " + command[7]
        drinkString += (str(command[2]) + ":" + str(command[3]) + " ")
    	
    print drinkString
    serBot.write(drinkString + "\n")
    
    if specials != []:
    	print specials[0][2]
    
    log("Mixing drink: " + drinkname + " (%s)"%(str(drinknum)))

def log(text):
    sql = "insert into logs values (NULL, %s, '%s')" % (time.time(), text)
    c.execute(sql)
    conn.commit()
    c.close()

def play():
    global last_received
    buffer = ''
    print " = = = = = Waiting for Serialz = = = = =" 
    
    while True:
        buffer = buffer + ser.read(ser.inWaiting())
        #print "BUFFER: ", buffer
        
        if '\n' in buffer:
            lines = buffer.split('\n')
            last_received = lines[-2]
            buffer = lines[-1]
            print " = = = = = CMD Received: " + last_received + " = = = = ="
            
            if "SPIN RESULT" in last_received:
                spinArgs = last_received.split(" ")
                print " = = WHEEL 1: " + spinArgs[2]
                print " = = WHEEL 2: " + spinArgs[3]
                print " = = WHEEL 3: " + spinArgs[4]
                drinkArgs = spinArgs[2:]
               
            
        time.sleep(.1)



if __name__ == '__main__':
    print " = = = = = Starting up... = = = = ="
    
    try:
    	serBot = serial.Serial(barBot, 9600, timeout=.1)
    	serBot.open()
    except:
    	print "Could not open BarBot on " + barBot
    	log("Could not open BarBot on " + barBot)
    	sys.exit(-1)
    
    
    try:
        ser = serial.Serial(slotMachine, 9600, timeout=.1)
        ser.open()
    except:
        print "Could not open SlotMachine on " + slotMachine
        log("Could not open Slot Machine on " + slotMachine)
        sys.exit(-1)
        
    if ser.isOpen() is True:    
        time.sleep(2)
        ser.flushInput()
        log("Starting up...")
        play()
        
    else:
        print "Could not open " + slotMachine
        log("Could not open" + slotMachine)
        sys.exit(-1)

