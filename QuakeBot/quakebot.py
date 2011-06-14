#!/usr/bin/python

import subprocess
from multiprocessing import Process, Queue, Manager
import time
import os, socket, sys
import pyquake3
import json

#logFile = "/var/games/openarena-server/.q3a/osp/games.log"


class LogListener:
	
	players = {}
	game = True
	quake = None
	
	def __init__(self, quake):
		self.quake = quake
		
	def getPlayers(self):
		quake.rcon_update()
		newPlayers = q.players
		return newPlayers
		
	def parseLine(self, line):
		if "ClientConnect" in line:
			return self.clientConnect(line)
		elif "ClientDisconnect" in line:
			return self.clientDisconnect(line)
		elif "say:" in line:
			return self.said(line)
		elif "Game_End:" in line:
			return self.gameover(line)
		elif "score:" in line:
			return self.score(line)
	
	def clientConnect(self, line):
		newPlayers = getPlayers()	  
		diff = [player for player in newPlayers if player not in self.players]
		self.players = newPlayers
		
		player = diff[0].name
		print "Quake: " + player + " connected."
		return "[%s] joined the Quake server"%(player)
	
	def clientDisconnect(self, line):
		newPlayers = getPlayers()
		diff = [player for player in self.players if player not in newPlayers]
		self.players = newPlayers
		
		player = diff[0].name
		print "Quake: " + player + " disconnected."
		return "[%s] left the Quake server"%(player)
	
	def said(self, line):
		player = line.split(":")[1].lstrip()
		message = line[line.find(player) + len(player) + 2:]
		return "[%s] %s"%(player, message)
	
	def gameover(self, line):
		reason = line.split(":")[1].lstrip()
		#self.game = False
		
		print "Game Over: %s"%(reason)
		
		self.players = getPlayers()
		
		for player in self.players:
			print "[%s] score: %s"%(player.name, player.frags)
	
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
	
	def receive(self, messageQueue):
		while True:			
			try:
				data = socket.recv ( 4096 )
				#print "Data: " + data
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
		quake.command("say [%s] %s"%(sender, message))
		
	


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
	quake = pyquake3.PyQuake3(quakeserver, rconpass)
	
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
			print "Sending: %s"%(message)
			socket.send("PRIVMSG %s :%s\r\n"%(channel, message))