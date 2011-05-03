#! /bin/python
import shlex, sys, os, time, subprocess, serial, sqlite3, random, json, multiprocessing, subprocess, math, socket, twitter

#Database
conn = sqlite3.connect('/var/www/barbot.sqlite')
c = conn.cursor()

#Initial MPlayer Command
#cmd = "mplayer -idle -fixed-vo -framedrop -quiet -slave -autosync 0 -fs -zoom -x 760 -y 600 /home/nycr/Video/main.mov"
#args = shlex.split(cmd)

#Sayings for twitter and LCD
#LCD says include formatting
twitterSayings = {0:"THIS IS #BATCOUNTRY", 1:"THIS IS #BATCOUNTRY", 2:"YOUR TURN TO DRIVE", 3:"I THINK I'M GETTING #THEFEAR", 4:"COME ON YOU #FIEND", 5:"PLEASE, TELL ME YOU BROUGHT THE FUCKING #GOLFSHOES", 6:"AS YOUR ATTORNEY I ADVISE YOU TO #SPIN", 7:"DOG'S FUCKED THE #POPE ? NO FAULT OF MINE", 8:"JUST ADMIRING THE SHAPE OF YOUR SKULL", 9:"DID THEY PAY YOU TO #SCREWTHATBEAR ?"}
lcdSayings = {0:"\n      THIS IS\n    BAT COUNTRY!", 1:"\n      SPIN IT\n     TO WIN IT", 2:"\n     YOUR TURN\n      TO DRIVE", 3:"\n     I THINK I'M\n  GETTING THE FEAR", 4:"\n   COME ON\n        YOU FIEND", 5:"PLEASE, TELL ME\n     YOU BROUGHT THE\nFUCKING GOLF SHOES", 6:"AS YOUR ATTORNEY\n        I ADVISE YOU\n      TO SPIN", 7:"DOG'S FUCKED\n          THE POPE?\nNO FAULT OF MINE", 8:"\n   JUST ADMIRING\n  THE SHAPE\n     OF YOUR SKULL", 9:"\nDID THEY PAY YOU\n TO SCREW THAT BEAR?"}

#Serial Interfaces
slotMachine = '/dev/serial/by-id/usb-FTDI_TTL232R_FTE3G3MI-if00-port0'
barBot = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A900acNt-if00-port0'
screen = '/dev/serial/by-id/usb-FTDI_TTL232R_FTDXPLJO-if00-port0'

#Possible replay wheel combinations
replay1 = [0, 4, 7, 11, 14, 18]
replay2 = [1, 6, 10, 14, 18]
replay3 = [0, 4, 8, 12, 16]

try:
    api = twitter.Api(consumer_key='', consumer_secret='', access_token_key='', access_token_secret='')
except:
    print "no twitter"

def killThreads():
    for thread in threads:
        if not thread.is_alive():
            threads.remove(thread)
            
def makeDrink(args=None):
#Make a random drink!
    drinkString = "DRINK ORDER "
    
    mult = c.execute("SELECT * FROM drinkmultiplier")
    mult = c.fetchone()
    mult = mult[1]
    print "DRINK MULTIPLIER: " + str(mult)
    
##########################    
    # EXECUTE CUSTOM ORDER
    custom = c.execute("SELECT * FROM custom WHERE custom.done is NULL ORDER BY id")
    custom = c.fetchone()
    print "CUSTOM RESULT: " + str(custom)
    
    if custom is not None:
        print "CUSTOM ORDER: %s" % (custom[1])
        drinknum = custom[1]
        result = c.execute("UPDATE custom SET done='True' WHERE id = %s" % (custom[0]))
        
    else:
        #print "RANDOM DRINK" 
        count = c.execute("SELECT COUNT (*) from drinks")
        count = c.fetchone()
        
        #RANDOM DRINK
        drinknum = random.randint(1,count[0])
##########################
    
    result = c.execute("SELECT name FROM drinks WHERE id = %s" % (drinknum))
    drinkname = c.fetchone()[0]
    print "Making #" + str(drinknum) + " " + drinkname
    
    results = c.execute("SELECT * FROM drinkcommands LEFT OUTER JOIN ingrediants ON drinkcommands.ingrediant=ingrediants.id WHERE drinknum = %s ORDER BY id" % (drinknum))
    commands = c.fetchall()
    
    #print commands

##########################
#            SEND COMMANDS
    oob = []
    for command in commands:
        if command[9] != "True":
            #print str(command[3]) + " " + command[4] + " " + command[7]
            drinkString += (str(command[2]) + ":" + str(int(command[3])*mult) + " ")
        else:
            oob.append(str(command[3]) + " " + command[4] + " " + command[7])
            
    print drinkString
    try:
        serBot.write(drinkString + "\n")
    except:
        print "! ! ! ! ! ! ! ! COULD NOT WRITE TO BARBOT ! ! ! ! ! ! ! !"
        
    clearLCD()
    writeSpecials(str(drinkname), oob)    
    
    log("Mixing drink: " + drinkname + " (%s)"%(str(drinknum)))
    
    x = random.randint(0, len(twitterSayings)-1)
    try:
        api.PostUpdate("I just mixed a '%s'! %s" % (drinkname, twitterSayings[x]))
    except:
        pass

def writeSpecials(drink, oob):
    x = 0
    
    try:
        lcd.write(chr(0xFE)+chr(0x48))
        lcd.write(drink)
        lcd.write(chr(10))
        time.sleep(2)
        
        if len(oob) > 2:
            lcd.write("\nADD:")
            time.sleep(1)
            
            clearLCD()
            #time.sleep(.5)
            lcd.write(drink)
            lcd.write(chr(10))
            lcd.write("\n     ADD:")
            time.sleep(.5)
            clearLCD()
            #time.sleep(.5)
            
            lcd.write(drink)
            lcd.write(chr(10))
            lcd.write("\n          ADD:")
            time.sleep(.5)
            clearLCD()
            #time.sleep(.5)
            
            #clearLCD()
            
            for inst in oob:
                lcd.write(str(inst))
                if x < len(oob)-1 and len(str(inst)) < 20:
                    lcd.write(chr(10))
                x += 1
        elif len(oob) > 0:
            lcd.write("ADD: \n")
            for inst in oob:
                lcd.write(str(inst))
                lcd.write(chr(10))
    except:
        print "! ! ! ! ! ! ! ! COULD NOT CONNECT TO LCD ! ! ! ! ! ! ! !"
    time.sleep(5)

def writeSpecials2(drink, oob)
    if len(oob) > 3:
        #need the whole screen
        
        lcd.write(chr(0xFE) + chr(0x48))
        lcd.write(drink.center(20))
        lcd.write(chr(10))
        lcd.write("ADD:".center(20))
        lcd.write(chr(10))
        time.sleep(4)

        clearLCD()

        for inst in oob:
            lcd.write(str(inst))
            if x < len(oob)-1 and len(str(inst)) < 20:
                lcd.write(Chr(10))
                x+=1
        
    elif len(oob) > 2:
        #can display name + 'add'
        
        drinkLine = ""  
        if len(drink) <= 15:
            for x in range(0, 20):
                if x > 16:
                    drinkLine[x] = "ADD:"[x-17]
                else: 
                    drinkLine[x] = drink.ljust(20)[x]
        
    elif len(oob) <= 2:
        #can display name, 'add', and instructions

        lcd.write(chr(0xFE) + chr(0x48))
        lcd.write(drink)
        lcd.write(chr(10))

        lcd.write(chr(0xFE) + chr(0x48))
        lcd.write("Please Add:")
        lcd.write(chr(10)) 
        
        for inst in oob:
            lcd.write(str(inst))
            lcd.write(chr(10))
    
    time.sleep(5)
    
def log(text):
    sql = "insert into logs values (NULL, %s, '%s')" % (time.time(), text)
    c.execute(sql)
    conn.commit()
    c.close()

def randomLCD():
    #Print a predefined message on the LCD
    x = random.randint(0, len(lcdSayings)-1)
    
    try:
        clearLCD()
        lcd.write(lcdSayings[x])
    except:
        print "! ! ! ! ! ! ! ! COULD NOT CONNECT TO LCD ! ! ! ! ! ! ! !"
    
def clearLCD():
    lcd.write(chr(0xFE)+chr(0x58))       

def play():
    global last_received
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

    print ip
    lcd.write(ip)
    
    time.sleep(3)
    print " = = = = = Waiting for Serialz = = = = =" 
    
    #Print a random LCD message
    randomLCD()
    
    while True:
        try:
            buffer = buffer + slotBot.read(slotBot.inWaiting())
        except:
            print "! ! ! ! ! ! ! ! COULD NOT READ FROM SLOT MACHINE ! ! ! ! ! ! ! !"
        
        try:
            lcdbuffer = lcdbuffer + lcd.read(lcd.inWaiting())
        except:
            print "! ! ! ! ! ! ! ! COULD NOT READ FROM LCD ! ! ! ! ! ! ! !"
        
        if "A" in lcdbuffer:
            lcdbuffer = ''
            clearLCD()
            lcd.write("IP ADDRESS:\n")
            lcd.write(ip + "\n\n")
            lcd.write("Enter Start Number")
            time.sleep(4)
            
            lcdbuffer = lcd.read(lcd.inWaiting())
            startNum = len(lcdbuffer)
            if (startNum == 0):
                startNum = 1
            print startNum
            lcdbuffer = ''
            
            for num in range(startNum, 13):
                serBot.write("DRINK ORDER ")
                serBot.write(str(num) + ":6000\n")
                
                print "Priming Solenoid " + str(num)
                clearLCD()
                lcd.write("Priming Solenoid " + str(num))
                
                time.sleep(12)
                lcdbuffer = lcdbuffer + lcd.read(lcd.inWaiting())
                
                if "A" in lcdbuffer:
                    lcdbuffer = ''
                    print "End Priming"
                    clearLCD()
                    lcd.write("End Priming")
                    time.sleep(1)
                    randomLCD()
                    break
                
            
        if '\n' in buffer:
            lines = buffer.split('\n')
            received = lines[-2]
            if (received == last_received):
                continue
            else:
                last_received = received
            buffer = lines[-1]
            print " = = = = = CMD Received: " + last_received + " = = = = ="
            
            if "COIN" in last_received: #Someone put a coin in!
                print "COIN RECEIVED!"
                try:
                    slotBot.write("C\n")
                    time.sleep(.2)
                    slotBot.write("C\n")
                    time.sleep(.2)
                    slotBot.write("C\n")
                except:
                    print "! ! ! ! ! ! ! ! COULD NOT CONNECT TO SLOT MACHINE ! ! ! ! ! ! ! !"
                    
            if "SPIN RESULT" in last_received: #Someone spun!
                spinArgs = last_received.split(" ")
                
                if replay(spinArgs) is True:
                    print "GOT A REPLAY!"
                else:
                    print "NOT A REPLAY"
                    #startVideo()
                    makeDrink()
                    time.sleep(3)
                    clearLCD()
                    randomLCD()
            
        time.sleep(.1)

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

if __name__ == '__main__':
    print " = = = = = Starting up... = = = = ="
    
    #Don't start until everything is connected
    
    while(q==0):
        #Check the LCD serial connection
        try:
            lcd = serial.Serial(screen, 19200)
            lcd.open()
            
            clearLCD()
            lcd.write("\n BarBot Operational")
            
            q=1
    
        except:
            print "Could not open LCD on " + screen
            log("Could not open LCD on " + screen)
    
            time.sleep(3)
    
    while(r==0):
       #Check the BarBot serial connection
        try:
            serBot = serial.Serial(barBot, 9600, timeout=.1)
            serBot.open()
            
            r=1
            
        except:
            print "Could not open BarBot on " + barBot
            log("Could not open BarBot on " + barBot)
            
            time.sleep(3)
            
    while(s==0):
        #Check the Slot Machine serial connection
        try:
            slotBot = serial.Serial(slotMachine, 9600, timeout=.1)
            slotBot.open()
            
            s=1
            
        except:
            print "Could not open SlotMachine on " + slotMachine
            log("Could not open Slot Machine on " + slotMachine)
            
            time.sleep(3)

    #p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    slotBot.flushInput()
    log("Starting up...")
    play()










        
def startVideo():
    #Play a random video
    print "= = = = = Playing new Video = = = = ="    
    video = c.execute("SELECT * FROM videos ORDER BY played asc")
    video = c.fetchone()
    
    print "Video Results: " + str(video)
    
    vidtime = video[3]
    vidname = video[1]
    
    #Update video playcount
    result = c.execute("UPDATE videos SET played = %s WHERE id = %s" % (video[2]+1, video[0]))
       
    print " = = = = = Playing Video %s = = = = =" % (vidname)
    spawnVideo(vidname, vidtime)
    
def spawnVideo(vidname, vidtime):
    #Spawn a video process, so that serial events can be read in the background
    p = multiprocessing.Process(target=playVideo,args=[vidname, vidtime])
    p.start()
    print p, "Is Activated: ", p.is_alive()
    threads.append(p)
    killThreads()
    
def playVideo(video, vidtime):
    #Play a video, wait until done, return to main.mov
    
    print "PLAYING " + video + " WITH TIME " + str(vidtime)
    cmd = "loadfile /home/nycr/Video/vids/%s\n" % (video)
    p.stdin.write(cmd)
    
    sleepTime = int(math.floor(vidtime))
    
    print "Sleeping for " + str(sleepTime) + " seconds, fool."
    
    time.sleep(sleepTime)
            
    print "Returning to Main Loop, sucker."
    p.stdin.write("loadfile /home/nycr/Video/main.mov\n")
    
    clearLCD()
    randomLCD()