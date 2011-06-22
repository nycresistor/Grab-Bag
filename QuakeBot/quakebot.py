#!/usr/bin/python

import subprocess
from multiprocessing import Process
import time
import os, socket, sys
from pyq3 import q as quake
import json
import re
import traceback

def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)

class Player:
    def __init__(self, num, name, announced=False):
        self.name = name
        self.announced = announced
        self.num = num
    def announce(self):
        if self.announced:
            print "Quake: player %s already announced"%(self.name)
        else:
            self.announced = True
            print "Quake: Begin client %s %s - announced: %s"%(self.num, self.name, self.announced)
            return "[%s] joined the Quake server"%(self.name)
            
class Game:

    props = {}
    
    def __init__(self, inProps, isStarting=True, announced=False):
        self.parseProps(inProps)
        self.isStarting = isStarting
        self.announced = announced
    def parseProps(self, inProps):
        split = inProps.split("\\")
        self.props['timelimit'] = split[split.index("timelimit") + 1]
        self.props['fraglimit'] = split[split.index("fraglimit") + 1]
        self.props['mapname'] = split[split.index("mapname") + 1].upper()
    
    def end(self, players, line):
        """Game has ended, print why and scores"""
        reason = line.split(":")[1].lstrip()
        
        print "Game Over: %s"%(reason)
        
        endPlayers = sorted(players, key=lambda player: player.frags)
        
        output = "Game Over: %s"%(reason)
        
        for player in endPlayers:
            output += "[%s] score: %s "%(player.name, player.frags)
        return output
        
    def announce(self):
        self.announced = True
        return "A game has started on %s with Time Limit: %s and Frag Limit: %s"%(self.props['mapname'], self.props['timelimit'], self.props['fraglimit'])
                
class LogListener:
    
    players = {}
    currentGame = None
    
    def __init__(self, quake):
        self.quake = quake
        
    def getPlayers(self):
        """Get an updated list of current players"""
        quake.rcon_update()
        newPlayers = quake.players
        return newPlayers
        
    def parseLine(self, line):
        """Parse the incoming log line for specified events"""
        if "Resetting back" in line or "Warmup:" in line:
            self.currentGame = None
        elif "ClientBegin" in line:
            return self.clientBegin(line)
        elif "ClientDisconnect" in line:
            return self.clientDisconnect(line)
        elif "say:" in line:
            return self.said(line)
        elif "InitGame:" in line:
            self.currentGame = Game(line)
        elif "Game_End:" in line:
            return self.currentGame.end(self.getPlayers(), line)
        elif "Game_Start:" in line:
            return self.currentGame.announce()
        elif "ClientUserinfoChanged" in line:
            self.clientUserinfoChanged(line)

    def clientUserinfoChanged(self, line):
        """User has connected/changed name"""
        search = re.search("\s\d+\s", line)
        num = int(search.group(0))
        playerName = line.split("\\")[1]
        
        if not num in self.players:
            self.players[num] = Player(num, playerName, False)
            print "Quake: new player: %s %s"%(num, playerName)
        else:
            self.players[num] = Player(num, playerName, self.players[num].announced)
            print "Quake: updating player %s %s"%(num, playerName)
            
    def clientBegin(self, line):
        """User has connected and name has been updated, 
        only here is it safe to display their name"""
                
        num = int(line.split(":")[1])
        player = self.players[num]
        
        return player.announce()
        
    
    def clientDisconnect(self, line):
        """Client has disconnected"""
        num = int(line.split(":")[1])
        
        try:
            player = self.players[num]
            del self.players[num]
                    
            return "[%s] has left the Quake server"%(player.name)
        except:
            print "Error: Don't know who just disconnected."
            return None
    
    def said(self, line):
        """Client has said something in the Quake console"""
        player = line.split(":")[1].lstrip()
        message = line[line.find(player) + len(player) + 2:]
        return "[%s] %s"%(player, message)
    
    def reopenLog(self, logFile, process=None):
        if process: process.close()
        return os.popen("tail -f %s"%(logFile), "r")
        
    def watchLog(self, logFile, ircClient):
        """Loop for watching the log file"""
        print "Watching Log %s"%(logFile)
        
        p = self.reopenLog(logFile)
        
        lineNum = 0

        while True:
            line = p.readline()
            if not line: continue
            if lineNum > 9: #only get new lines
                quakemessage = self.parseLine(line)
                if quakemessage:
                    #messageQueue.put(quakemessage)
                    ircClient.send(quakemessage)
            lineNum += 1
            #except:
            #    print "Error reading log file: "
            #    print formatExceptionInfo()
            #    p = self.reopenLog(logFile, p)
                
    
class IRCListener:
    def __init__(self, quake, socket, channel):
        self.quake = quake
        self.socket = socket
        self.channel = channel
    
    def receive(self):
        """Loop for watching for IRC data"""
        while True:         
            try:
                data = socket.recv ( 4096 )                
                if data == "":
                    print "Broken socket"
                    sys.exit(0)
                
                self.parseLine(data)
            except:
                continue
                
    def parseLine(self, data):
        """Function for parsing incoming IRC data,
        only supports PING and echoing of content
        into the Quke console"""
        
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
            message = data.split(self.channel)[1][2:] #fuck ipv6
            self.echoToQuake(sender, message)
    
    def echoToQuake(self, sender, message):
        """Echo IRC traffic into the Quake console"""
        cmd = "say [%s] %s"%(str(sender), str(message))
        print "RCON: %s"%(cmd)
        quake.rcon(cmd)
        
    def send(self, message):
        """Split message by lines and send to the IRC socket"""
        messages = message.split("\n")
        for message in messages:
            if message != "":
                print "Sending: %s"%(message)
                socket.send("PRIVMSG %s :%s\r\n"%(self.channel, message))

if __name__ == "__main__":
    
    #config file
    configFile = os.path.join(sys.path[0], "config.json")   
    configContents = open(configFile).read()
    config = json.loads(configContents)
    
    #IRC properties
    irc = config['irc']
    ircserver = irc['server']
    port = int(irc['port'])
    nick = irc['nick']
    ident = irc['ident']
    realname = irc['realname']
    channel = irc['channel']
    
    #Quake properties (currently unused)
    q = config['quake']
    quakeserver = q['server'] + ":" + q['port']
    rconpass = q['password']
    logFile = q['logfile']
    
    #Open the socket connection to IRC
    print "Opening connection to %s:%s as %s - %s - %s on channel %s"%(ircserver, port, nick, ident, realname, channel)
    
    socket=socket.socket( )
    socket.connect((ircserver, port))
    socket.settimeout(0.1) #Blocking mode doesn't work very well
    socket.send("NICK %s\r\n" % nick)
    socket.send("USER %s %s bla :%s\r\n" % (ident, ircserver, realname))
    socket.send("JOIN %s\r\n"%channel)
    
    #Open the Quake connection
    #Currently unused as the pyq3 __init__.py does it for us
    print "Opening connection to Quake 3 server at %s"%(quakeserver)
    quake.rcon("say QuakeBot Connected.")

    #Start the IRC listener
    ircClient = IRCListener(quake, socket, channel)
    ircClientProcess = Process(target=ircClient.receive, args=())
    ircClientProcess.start()
    
    #Start the log listener
    print "Loading Quake log file at %s"%(logFile)
    logListener = LogListener(quake)
    logListenerProcess = Process(target=logListener.watchLog, args=(logFile, ircClient,))
    logListenerProcess.start()