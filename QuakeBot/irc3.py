#!/usr/bin/python

import subprocess
from multiprocessing import Process, Queue, Manager
import time
import os, socket, sys
from pyircalib import Server,__version__


logFile = "/Users/max/Dropbox/Projects/QuakeBot/test.log"

players = {}

HOST="irc.freenode.net"
PORT=6667
NICK="NYCRQuakeBot"
IDENT="NYCRQuakeBot"
REALNAME="NYCRQuakeBot"


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

if __name__ == "__main__":
    sendQueue = Queue()
    
    manager = Manager()
    botDict = manager.dict()
    
    logListener = Process(target=logListener, args=(sendQueue,))
    logListener.start()
    
    #ircClient = Process(target=ircClient, args=(sendQueue,botDict))
    #ircClient.start()
    


    def CallbackFunction(sock, event, d):
        if event != 'TICK':
            print event, d
            print "Channel info", pprint.pformat(sock.info['channels'])
            print "User info", pprint.pformat(sock.info['users'])
        if event == 'PRIVMSG':
            sock.privmsg(d['channel'], "%s %s %s"%(str(sock), event, str(d)))
            pprint.pprint(sock.info)
    
    conf = {'host':['irc.freenode.net', ],
            'channels':['#pyircalib'],
            'port':6667,
            'callback':CallbackFunction}
    
    server = Server(conf)
    server.instance({'nick':'NYCRQuakeBot'})
    server.process()
    
    while True:
        print "test"
        message = sendQueue.get()
        if message:
            print "SENDING: " + message    
    
    