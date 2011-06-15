#!/usr/bin/python

import subprocess
from multiprocessing import Process, Queue, Manager
import time
import os, socket, sys
from pyq3 import q as quake
import json
import re

class LogListener:
    
    players = {}
    game = False
    gameStarting = False
    
    def __init__(self, quake):
        self.quake = quake
        
    def getPlayers(self):
        quake.rcon_update()
        newPlayers = quake.players
        return newPlayers
        
    def parseLine(self, line):
        if "HEALTH_MAX" in line:
            self.gameStarting = False
        elif "ClientBegin" in line:
            return self.clientBegin(line)
        elif "ClientDisconnect" in line:
            return self.clientDisconnect(line)
        elif "say:" in line:
            return self.said(line)
        elif "InitGame:" in line:
            return self.gamestart(line)
        elif "Game_End:" in line:
            return self.gameover(line)
        elif "ClientUserinfoChanged" in line:
            return self.clientUserinfoChanged(line)
        
    
    def gamestart(self, line):
        self.game = True
        self.gameStarting = True
        
        split = line.split("\\")
        timelimit = split[split.index("timelimit") + 1]
        fraglimit = split[split.index("fraglimit") + 1]
        mapname = split[split.index("mapname") + 1]
        
        return "A game has started on %s with Time Limit: %s and Frag Limit: %s"%(mapname.upper(), timelimit, fraglimit)
    
    def clientUserinfoChanged(self, line):
        search = re.search("\s\d+\s", line)
        num = int(search.group(0))
        print "Client Num: " + str(num)
        
        playerName = line.split("\\")[1]
        print "Player Name: " + playerName
        
        self.players[num] = playerName
    
    def clientBegin(self, line):
        
        if not self.gameStarting: #only care if connecting during or after a game
        
            #newPlayers = self.getPlayers()    
            #diff = [player for player in newPlayers if player not in self.players]
            #self.players = newPlayers
            
            #player = diff[0].name
            
            #self.players = self.getPlayers()
            num = int(line.split(":")[1])
            playerName = self.players[num]
            
            print "Quake: " + playerName + " connected."
            return "[%s] joined the Quake server"%(playerName)
    
    def clientDisconnect(self, line):
        #newPlayers = self.getPlayers()
        #diff = [player for player in self.players if player not in newPlayers]
        #self.players = newPlayers
        
        #player = diff[0].name
        
        num = int(line.split(":")[1])
        
        try:
        	playerName = self.players[num]
        
        	print "Quake: " + playerName + " disconnected."
        	return "[%s] left the Quake server"%(playerName)
        except:
        	print "Error: Don't know who just disconnected."
        	return None
    
    def said(self, line):
        player = line.split(":")[1].lstrip()
        message = line[line.find(player) + len(player) + 2:]
        return "[%s] %s"%(player, message)
    
    def gameover(self, line):
        reason = line.split(":")[1].lstrip()
        self.game = False
        
        print "Game Over: %s"%(reason)
        
        self.players = sorted(self.getPlayers(), key=lambda player: player.frags)
        
        output = "Game Over! "
        
        for player in self.players:
            
            output += "[%s] score: %s "%(player.name, player.frags)
        
        print output
        return output
    
    def watchLog(self, logFile, messageQueue):
        
        print "Watching Log %s"%(logFile)
        
        lineNum = 0
        p = os.popen("tail -f %s"%(logFile), "r")
        
        while True:
            line = p.readline()
            if not line: continue
            if lineNum > 9: #only get new lines
                quakemessage = self.parseLine(line)
                if quakemessage:
                    messageQueue.put(quakemessage)
            lineNum += 1
    
class IRCListener:
    def __init__(self, quake, socket, channel):
        self.quake = quake
        self.socket = socket
        self.channel = channel
    
    def receive(self, messageQueue):
        while True:         
            try:
                data = socket.recv ( 4096 )
                #print "Data: " + data
                
                if data == "":
                    print "Broken socket"
                    sys.exit(0)
                
                self.parseLine(data)

            except:
                continue
                
    def parseLine(self, data):
        print "Parsing: " + data
        if "PING" in data:
            try:
                socket.send("PONG %s\r\n"%(data.split(":")[1]))
                print "PONG %s"%(data.split(":")[1])
            except:
                socket.send("PONG\r\n")
                print "PONG"
        
        if "PRIVMSG %s"%channel in data:
            sender = data.split("!")[0][1:]
            message = data.split(":")[2]
            self.echoToQuake(sender, message)
    
    def echoToQuake(self, sender, message):
        print "Echoing to quake: [%s] %s" % (sender, message)
        quake.rcon("say [%s] %s"%(sender, message))
    
    def send(self, message):
        
        messages = message.split("\n")
        for message in messages:
            print "Sending: %s"%(message)
            socket.send("PRIVMSG %s :%s\r\n"%(self.channel, message))
        
    


if __name__ == "__main__":
    
    configFile = os.path.join(sys.path[0], "config.json")   
    configContents = open(configFile).read()
    config = json.loads(configContents)
    
    
    irc = config['irc']
    ircserver = irc['server']
    port = int(irc['port'])
    nick = irc['nick']
    ident = irc['ident']
    realname = irc['realname']
    channel = irc['channel']
    
    q = config['quake']
    quakeserver = q['server'] + ":" + q['port']
    rconpass = q['password']
    logFile = q['logfile']
    
    print "Opening connection to %s:%s as %s - %s - %s on channel %s"%(ircserver, port, nick, ident, realname, channel)
    
    socket=socket.socket( )
    socket.connect((ircserver, port))
    socket.settimeout(0.1)
    
    socket.send("NICK %s\r\n" % nick)
    socket.send("USER %s %s bla :%s\r\n" % (ident, ircserver, realname))
    socket.send("JOIN %s\r\n"%channel)
    
    print "Opening connection to Quake 3 server at %s"%(quakeserver)
    #quake = pyquake3.PyQuake3(quakeserver, rconpass)
    quake.rcon("say QuakeBot Connected.")
    
    sendQueue = Queue()
    
    print "Loading Quake log file at %s"%(logFile)
    
    logListener = LogListener(quake)
    ircListener = IRCListener(quake, socket, channel)
    
    logListener = Process(target=logListener.watchLog, args=(logFile, sendQueue,))
    logListener.start()
    
    ircClient = Process(target=ircListener.receive, args=(sendQueue,))
    ircClient.start()
    


    while True:
        message = sendQueue.get()
        if message:
           ircListener.send(message)