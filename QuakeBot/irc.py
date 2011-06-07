import sys
import socket
import string
import time, os
import subprocess
import pexpect
import fcntl

HOST="irc.freenode.net"
PORT=6667
NICK="NYCRQuakeBot"
IDENT="NYCRQuakeBot"
REALNAME="NYCRQuakeBot"
readbuffer=""
data = ""

PIPE = subprocess.PIPE

s=socket.socket( )

s.connect((HOST, PORT))
s.setblocking(0)

s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
s.send("JOIN #nycrtest\r\n")

#p = os.popen('tail -f /var/games/openarena-server/.q3a/osp/games.log',"r")
filename = "/var/games/openarena-server/.q3a/osp/games.log"

players = {}



def parseLine(line):
    if "ClientUserinfoChanged" in line:
        split = line.replace("\n", "").split(" ")
        clientNum = split[2]
        string = split[3]
        stringSplit = string.split("\\")
        clientName = stringSplit[1]
        players[clientNum] = clientName
        
        print "Quake: Connected: %s %s" % (clientNum, clientName)
        s.send("PRIVMSG #nycrtest :%s connected.\r\n" % (clientName))
        
        
    elif "ClientDisconnect" in line:
        split = line.replace("\n", "").split(" ")
        clientNum = split[2]
    
        print "Quake: Disconnected: %s %s" % (clientNum, players[clientNum])
        s.send("PRIVMSG #nycrtest :%s disconnected.\r\n" % (players[clientNum]))
        
        players[clientNum] = None

if __name__ == "__main__":
    

    p = subprocess.Popen(['tail', '-f', '/var/games/openarena-server/.q3a/osp/games.log'], stdout=PIPE)
   
    #p = pexpect.spawn("tail -f /var/games/openarena-server/.q3a/osp/games.log")
    flags = fcntl.fcntl(PIPE, fcntl.F_GETFL)
	fcntl.fcntl(PIPE, fcntl.F_SETFL, flags | os.O_NONBLOCK)
	
    while 1:
        
        try: data = s.recv ( 4096 )
        except: continue
        
        if data.find ( 'PING' ) != -1:
           s.send ( 'PONG ' + data.split() [ 1 ] + '\r\n' )
        print data
        
        