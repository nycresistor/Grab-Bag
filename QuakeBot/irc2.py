#!/usr/bin/python

import subprocess
from multiprocessing import Process, Queue, Manager
import time
import os, socket, sys

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

logFile = "/Users/max/Dropbox/Projects/QuakeBot/test.log"

players = {}

HOST="irc.freenode.net"
PORT=6667
NICK="NYCRQuakeBot"
IDENT="NYCRQuakeBot"
REALNAME="NYCRQuakeBot"

#s=socket.socket()
#s.settimeout(1)
#s.connect((HOST, PORT))
#s.send("NICK %s\r\n" % NICK)
#s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
#s.send("JOIN #nycrtest\r\n")


class QuakeBot(irc.IRCClient):
    """A logging IRC bot."""

    nickname = "NYCRQuakeBot"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        #self.logger = MessageLogger(open(self.factory.filename, "a"))
        #self.logger.log("[connected at %s]" % time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        #self.logger.log("[disconnected at %s]" % time.asctime(time.localtime(time.time())))
        #self.logger.close()


    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        #self.logger.log("[I have joined %s]" % channel)
        print "[I have joined %s]" % channel

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        #self.logger.log("<%s> %s" % (user, msg))
        print "<%s> %s" % (user, msg)

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: I am a log bot" % user
            #self.msg(channel, msg)
            #self.logger.log("<%s> %s" % (self.nickname, msg))
            "<%s> %s" % (self.nickname, msg)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        #self.logger.log("* %s %s" % (user, msg))
        print "* %s %s" % (user, msg)

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        #self.logger.log("%s is now known as %s" % (old_nick, new_nick))
        print "%s is now known as %s" % (old_nick, new_nick)


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'

class QuakeBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = QuakeBot

    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()





def parseLine(line):
    if "ClientUserinfoChanged" in line:
        split = line.replace("\n", "").split(" ")
        clientNum = split[2]
        string = split[3]
        stringSplit = string.split("\\")
        clientName = stringSplit[1]
        players[clientNum] = clientName
        
        print "Quake: Connected: %s %s" % (clientNum, clientName)
        return "%s Connected"%(clientName)
        
        
    elif "ClientDisconnect" in line:
        split = line.replace("\n", "").split(" ")
        clientNum = split[2]
    
        print "Quake: Disconnected: %s %s" % (clientNum, players[clientNum])
        return "%s Disconnected"%(players[clientNum])
        players[clientNum] = None
    else:
        print "Could not parse line: %s"%(line)
        return None

def logListener(queue):
    lineNum = 0
    p = os.popen("tail -f /Users/max/Dropbox/Projects/QuakeBot/test.log", "r")
    
    while True:
        line = p.readline()
        if not line: break
        if lineNum > 9:
            message = parseLine(line)
            if message: 
                print message
                queue.put(message)
        lineNum += 1

#def ircSender(queue, socket):
#   while True:
#       message = queue.get()
#       if message:
#           socket.send("PRIVMSG #nycrtest :%s\r\n" % (message))

#def ircListener(queue, socket):
#   while True:
#       try: data = s.recv ( 4096 )
#       except: continue
        
 #       if data:
  #         print data


def ircClient(queue, bot):
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = QuakeBotFactory("nycrtest")
    
    bot[0] = f.protocol
    
    
    
    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
        
if __name__ == "__main__":
    sendQueue = Queue()
    
    manager = Manager()
    botDict = manager.dict()
    
    logListener = Process(target=logListener, args=(sendQueue,))
    logListener.start()
    
    ircClient = Process(target=ircClient, args=(sendQueue,botDict))
    ircClient.start()
    
    

    
    while True:
        print "test"
        message = sendQueue.get()
        if message:
            print "SENDING: " + message
            botDict[0].sendLine(botDict[0], message)
    
    
    