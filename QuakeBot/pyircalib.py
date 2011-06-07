# Python Asynchronous IRC Libary
# Copyright 2008 RickRollington ( Rollington.Rick@gmail.com )
#
# ==============================================================================
# License 
# ==============================================================================
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
# ==============================================================================
# Change log
# ==============================================================================
#
# [18/06/2008] Version 0.1.2
#       - Renamed the _Client class to _Instance to more appropriately represent
#         the classes purpose/action/role.
#
# [25/05/2008] Version 0.1.1
#       - Added the ability to define "address:port"'s in the host
#         configuration key
#       - Added SSL support
#       - Documented basic python sessions showing pyircalib usage
#       - Renamed Server() to _SocketManager() and made Server() a wrapper
#         object that will disalow users to initialise more than one instance of
#         the main _SocketManager()
#       - Changed the type of 'tickinterval' to float
#       - Changed the name of he config key 'consolelogging' to 'verbose'
#
# [15/05/2008] Version 0.1
#       - Original version released

__version__ = "0.1.2"

import re
import time
import socket
import select
import sys
import random
import pprint

def _overlaydict(original, overlay):
        d = dict(original)
        for key in overlay.keys():
                if key in d.keys() and type(overlay[key]) == type({}):
                        d[key] = _overlaydict(d[key], overlay[key])
                else:
                        d[key] = overlay[key]
        return d

_retypeint = re.compile("[0-9]+")

def _isint(s):
        if _retypeint.match(str(s)):
                return True
        return False
        
class _Instance:
        def __init__(self, parent, confoverlay={}):
                self.connected, self.initiated = False, False
                self.parent = parent
                self.messagedelays = []
                self.connectdelays = []
                self.lasttick = time.time()
                self.sendq = []
                self.rawsocket = None
                self.sslsocket = None
                self.readbuffer = ""
                self.conf = _overlaydict(self.parent.conf, confoverlay)
                self.info = {'users':{}, 'channels':{}, 'server':{}}

                self.pong = lambda msg: self.send("PONG %s" % msg)
                self.ping = lambda msg: self.send("PING %s" % msg)
                
                self.queue = lambda raw: self.sendq.append(raw)
                
                # Normal commands/actions.
                self.nick = lambda nick: self.queue("NICK %s" % nick)
                self.privmsg = lambda chan, msg: self.queue("PRIVMSG %s :%s" % (chan, msg))
                self.notice = lambda chan, msg: self.queue("NOTICE %s :%s" % (chan, msg))
                self.join = lambda chan: self.queue("JOIN %s" % chan)
                self.part = lambda chan, msg: self.queue("PART %s :%s" % (chan, msg))
                self.kick = lambda chan, nick, msg: self.queue("KICK %s %s :%s" % (chan, nick, msg))
                self.who = lambda pattern: self.queue("WHO %s" % pattern)
                self.topic = lambda chan, topic: self.queue("TOPIC %s :%s" % (chan, topic))
                self.whois = lambda nick: self.queue("WHOIS %s" % nick)
                self.mode = lambda chan, mode, nicklist: self.queue("MODE %s %s %s" % (chan, mode, ' '.join(nicklist)))
                self.chanmode = lambda chan: self.queue("MODE %s" % chan)
                
                # Popular IRC operator actions.
                self.sajoin = lambda nick, chan: self.queue("SAJOIN %s %s" % (nick, chan))
                self.sapart = lambda nick, chan: self.queue("SAPART %s %s" % (nick, chan))
                self.oper = lambda nick, passwd: self.queue("OPER %s %s" % (nick, passwd))
                self.sendraw = lambda chan, raw: self.queue("SENDRAW %s :%s" % (chan, raw))
                self.chghost = lambda nick, host: self.queue("CHGHOST %s %s" % (nick, host))
                
        def select_host(self):
                hosttype = type(self.conf['host'])
                if hosttype == type([]):
                        host = self.conf['host'][int(random.random()*len(self.conf['host']))]                   
                elif hosttype == type(''):
                        host = self.conf['host']
                else:
                        raise Exception('Invalid host configuration value %r' % self.conf['host'])
                        
                if ":" in host:
                        host, port = host.split(":")
                        port = int(port)
                else:
                        if self.conf['ssl']:
                                port = self.conf['sslport']
                        else:
                                port = self.conf['port']
                
                return host, port
        
        def connect_delaying(self): 
                return bool(self.parent._calcdelay(self.connectdelays, self.conf['connectdelay']))
                
        def connect_delaytime(self): 
                return self.parent._calcdelay(self.connectdelays, self.conf['connectdelay'])
                
        def message_delaying(self): 
                return bool(self.parent._calcdelay(self.messagedelays, self.conf['messagedelay']))
                
        def message_delaytime(self): 
                return self.parent._calcdelay(self.messagedelays, self.conf['messagedelay'])

        def sslcheck(self):
                if self.conf['ssl']:
                        self.sslsocket = socket.ssl(self.rawsocket)
                        self.readfunction = self.sslsocket.read
                        self.sendfunction = self.sslsocket.write
                else:
                        self.readfunction = self.rawsocket.recv
                        self.sendfunction = self.rawsocket.send

        def readlines(self, bytes=1024):
                self.readbuffer += self.readfunction(bytes)
                temp = self.readbuffer.split("\n")
                self.readbuffer = temp.pop()
                lines = self.clean_input(temp)
                return lines
        
        def clean_input(self, lines):
                clean = []
                for line in lines:
                        line = line.rstrip()
                        line = line.split(" ")
                        clean.append(line)
                return clean
        
        def send(self, raw):
                if self.conf['verbose']:
                        print ">>> %s" % raw
                raw += "\r\n"
                self.sendfunction(raw)
                self.messagedelays.append(time.time())
        
class _SocketManager:   
        def __init__(self, confoverlay={}):
                self.online = False
                self.socks = []

                self.conf = {'messagedelay':(100, 60),
                                'connectdelay':(5, 100),
                                'nick':'pyircalib',
                                'user':'pyircalib',
                                'ident':'pyircalib',
                                'host':'irc.freenode.net',
                                'channels':['#pyircalib'],
                                'port':6667,
                                'ssl':False,
                                'sslport':6697,
                                'logging':False,
                                'logfile':'bot.log',
                                'verbose':True,
                                'tickinterval':1.0,
                                'quitmessage':'pyircalib v%s'%str(__version__),
                                'callback':self.dummycallback}
                        
                self.imax = 0
                self.conf = _overlaydict(self.conf, confoverlay)
        
        def instance(self, confoverlay={}):
                self.socks.append(_Instance(self, confoverlay))
                
        def quit(self, sock, msg="Ooops! you found my self destruct button"):
                sock.quit("QUIT :%s" % msg)
                sock.connected = False
        
        def process(self):
                if not len(self.socks): 
                        raise Exception("No irc connections defined.")
                try:
                        self.sockets_listen()
                except:
                        raise

        def _calcdelay(self, delaylist, delaysetting):
                actions, period = delaysetting
                if len(delaylist) == 0:
                        return 0
                if actions == period == None:
                        if self.imax > 1000:
                                self.imax = 0
                                return 0.05
                        self.imax += 1
                        return 0
                actions, period = float(actions), float(period)
                while len(delaylist) and (delaylist[0]+period) < time.time():
                        del delaylist[0]
                # Settled with a linear delay function. My quadratic attempt was
                # too jumpy
                delay = delaylist[-1] + (period/actions) - time.time()
                if delay < 0.001: return 0
                return delay

# Multiple sockets actions/functions:

        def sockets_onlinelist(self):
                l = []
                for sock in self.socks:
                        if sock.initiated and sock.connected:
                                l.append(sock.rawsocket)
                return l        

        def sockets_listen(self):
                self.online = True
                while self.online:
                        self.connect_idlesockets()
                        input = self.sockets_onlinelist()
                        if not len(input):
                                # At this point no irc instance has successfully connected
                                # to its designated server. The socket manager now sleeps
                                # until the next instance is ready to attempt reconnection.
                                time.sleep(self.connect_mintime())
                                continue

                        self.messages_sendqprocess()
                        locktime = self.messages_queuelocktime()
                        readyforread = select.select(input, [], [], locktime)[0]

                        for rawsocket in readyforread:
                                sock = self.socket_belongsto(rawsocket)
                                try:
                                        lines = self.socket_read(sock)
                                except:
                                        raise
                                
                                for line in lines: 
                                        try:
                                                self.parse_rawmessage(sock, line)
                                        except:
                                                print "Error parsing line %r" % line
                                                raise
                        
# Singular socket actions/functions:
        
        def socket_read(self, sock):
                lines = sock.readlines()
                if "" in lines:
                        # Socket returned NULL byte.
                        sock.quit(sock)
                        raise Exception("Socket returned NULL byte")
                return lines
        
        def socket_belongsto(self, rawsocket):
                for sock in self.socks:
                        if rawsocket == sock.rawsocket:
                                return sock
                        
# Socket Connection actions/functions:

        def connect_idlesockets(self):
                for sock in self.socks:
                        if sock.connected: continue
                        if sock.initiated:
                                if sock.connect_delaying(): 
                                        print "socket is delaying, skipping"
                                        continue
                                else:
                                        print "socket isnt delaying, not skipping"
                                        
                        self.connect_socket(sock)
        
        def connect_mintime(self):
                l = [1, ]
                for sock in self.socks:
                        l.append(sock.connect_delaytime())
                return min(l)

        def connect_socket(self, sock):
                sock.initiated, sock.connected = True, False
                try:
                        sock.info = {'users':{}, 'channels':{}, 'server':{}}
                        sock.connectdelays.append(time.time())
                        sock.rawsocket, sock.sslsocket = socket.socket(), None
                        host, port = sock.select_host()

                        print "Establishing a connection with %s:%d" % (host, port)
                        sock.rawsocket.connect((host, port))
                        sock.sslcheck()
                        nick = self.callback(sock, "NICK_ENGINE")
                        if not nick:
                                nick = sock.conf['nick']
                        else:
                                sock.conf['nick'] = nick
        
                        user, ident = sock.conf['ident'], sock.conf['user']                     
                        sock.send("NICK %s" % nick)
                        sock.send("USER %s %s bla :%s" % (ident, host, user))
                        sock.connected = True
                except:
                        sock.connected = False
                        raise
                        
# Mutliple Messages actions/functions:
                
        def messages_sendqprocess(self):
                for sock in self.socks:
                        if not sock.connected: continue
                        while len(sock.sendq) and not sock.message_delaying():
                                try:
                                        #if sock.conf['verbose']:
                                        #       print ">>>",sock.sendq[0].strip()
                                        sock.send(sock.sendq[0])
                                        del sock.sendq[0]
                                except:
                                        raise   
                        
        def messages_queuelocktime(self):
                l = [1, ]
                for sock in self.socks:
                        if not len(sock.sendq): continue
                        l.append(sock.message_delaytime())
                return min(l)

# Singular Parsing functions:
        
        def parse_rawmessage(self, sock, line):
                if sock.conf['verbose']:
                        print "<<<", " ".join(line).strip()
                if line[0] == "PING":
                        sock.pong(line[1])
        
                elif line[0] == "ERROR":
                        self.err_error(sock, line)
                        
                elif line[1] == "JOIN":
                        self.chan_userjoin(sock, line)
                
                elif line[1] == "PART":
                        self.user_part(sock, line)
                        
                elif line[1] == "QUIT":
                        self.user_quit(sock, line)

                elif line[1] == "NICK":
                        self.user_changednick(sock, line)
                
                elif line[1] == "TOPIC":
                        self.chan_topicchanged(sock, line)
                                
                elif line[1] == "KICK":
                        self.chan_userkicked(sock, line)
                        
                elif line[1] == "PRIVMSG":
                        self.parse_privmsg(sock, line)

                elif line[1] == "NOTICE":
                        self.parse_notice(sock, line)
                        
                elif line[1] == "INVITE":
                        self.chan_userinvite(sock, line)        

                elif line[1] == "315":
                        #RPL_ENDOFWHO
                        self.callback(sock, 'RPL_ENDOFWHO')

                elif line[1] == "324":
                        self.rpl_channelmodeis(sock, line)      

                elif line[1] == "332":
                        #RPL_TOPIC
                        self.rpl_topic(sock, line)

                elif line[1] == "352":
                        #RPL_WHOREPLY
                        self.rpl_whoreply(sock, line)           

                elif line[1] == "353":
                        # RPL_NAMREPLY
                        self.rpl_namreply(sock, line)

                elif line[1] == "366":
                        #RPL_ENDOFNAMES
                        self.rpl_endofnames(sock, line)
                        
                elif line[1] == "376":
                        #RPL_ENDOFMOTD
                        self.callback(sock, "RPL_ENDOFMOTD")
                        self.act_startupcmds(sock)

                elif line[1] == "381":
                        #RPL_YOUREOPER
                        self.callback(sock, "RPL_YOUREOPER")

                elif line[1] == "422":
                        #ERR_NOMOTD
                        self.callback(sock, "ERR_NOMOTD")
                        self.act_startupcmds(sock)              

                elif line[1] == "433":
                        #ERR_NICKNAMEINUSE
                        self.err_nicknameinuse(sock, line)
                        
                elif line[1] == "473":
                        #ERR_INVITEONLYCHAN
                        self.err_inviteonlychan(sock, line)
                                
                elif line[1] == "474":
                        #ERR_BANNEDFROMCHAN
                        self.err_bannedfromchan(sock, line)

                elif line[1] == "005":
                        #RPL_SERVEROPTIONS?
                        self.rpl_serveroptions(sock, line)
        
        def parse_privmsg(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                d['msg'] = ' '.join(line[3:])[1:].split(" ")
                self.user_updateident(sock, d['ident'])
                self.callback(sock, 'PRIVMSG', d)

        def parse_notice(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                d['msg'] = ' '.join(line[3:])[1:].split(" ")
                self.user_updateident(sock, d['ident'])
                self.callback(sock, 'NOTICE', d)

# Action/callback functions

        def act_startupcmds(self, sock):
                # Cue to run user startup commands
                self.callback(sock, "RUNSTARTUPCMDS")
                # Running irclib startup commands
                for channel in sock.conf['channels']:
                        sock.join(channel)

# Reply parsing functions       
        
        def rpl_topic(self, sock, line):
                channel = line[3]
                topic = ' '.join(line[3:])[1:]
                self.chan_updatetopic(sock, channel, topic)

        def rpl_namreply(self, sock, line):
                channel = line[4]
                users = self.user_namesreplyuserlist(sock, line)
                if channel in sock.info['channels'].keys():
                        for user in users:
                                nick, mode = user
                                self.chan_namesreplyuser(sock, channel, nick, mode)
                                self.user_namesreplyaddnick(sock, nick)
                
        def rpl_channelmodeis(self, sock, line):
                channel = line[3]
                mode = ' '.join(line[4:])
                self.chan_modeis(sock, channel, mode)
                
        def rpl_endofnames(self, sock, line):
                d = {'channel':line[3]}
                sock.who(d['channel'])
                self.callback(sock, "RPL_ENDOFNAMES", d)
        
        def rpl_whoreply(self, sock, line):
                #RPL_WHOREPLY
                nick, user, host, server, channel, mode = line[7], line[4], line[5], line[6], line[3], line[8]
                ident = "%s!%s@%s" % (nick, user, host)
                self.user_updateident(sock, ident)
                self.user_updatemode(sock, nick, mode)
                d = {   'nick':nick,
                        'channel':channel,
                        'server':server,
                        'host':host,
                        'user':user,
                        'ident':ident }         
                self.callback(sock, 'RPL_WHOREPLY', d)
        
        def rpl_serveroptions(self, sock, line):
                # Parses server options strings and loads them into
                # sock.info['server']
                s = ' '.join(line[3:]).split(" :")[0]
                s = s.split(" ")
                for option in s:
                        self.server_addoption(sock, option)
        
# Error reply parsing functions 
        
        def err_error(self, sock, line):
                d = {'msg':" ".join(line[1:])[1:]}
                sock.connected = False
                #self.log("Error: %r" % d['msg'])
                self.callback(sock, "ERROR", d)

        def err_bannedfromchan(self, sock, line):
                #ERR_BANNEDFROMCHAN
                channel = line[3]
                #self.log("Error: Banned from channel %r."%channel)
                self.callback(sock, "ERR_BANNEDFROMCHAN", {'channel':channel})                  
        
        def err_inviteonlychan(self, sock, line):
                #ERR_INVITEONLYCHAN
                channel = line[3]
                #self.log("Error: Channel %r is invite only."%channel)
                self.callback(sock, "ERR_INVITEONLYCHAN", {'channel':channel})
        
        def err_nicknameinuse(self, sock, line):
                #ERR_NICKNAMEINUSE
                newnick = self.callback(sock, "ERR_NICKNAMEINUSE")
                if not newnick:
                        newnick = sock.conf['nick']+str(int(time.time()))[-4:]
                sock.conf['nick'] = newnick
                sock.nick(newnick)

# user & sock.info['user'] functions

        def user_part(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                del d['pm']
                d['reason'] = ' '.join(line[4:])[1:]
                if d['nick'] == sock.conf['nick']:
                        #self.log("Parted from channel %r reason %r"%(d['channel'],d['reason']))
                        self.chan_partedfrom(sock, d['channel'])
                        self.callback(sock, 'PARTED', d)
                else:
                        self.chan_userparted(sock, d['nick'], d['channel'])                     
                        self.callback(sock, 'PART', d)
                
        def user_quit(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                del d['pm']
                d['reason'] = ' '.join(line[4:])[1:]
                if d['nick'] == sock.conf['nick']:
                        sock.info = {'users':{}, 'channels':{}, 'server':{}}
                        sock.connected = False
                else:
                        self.chan_userquit(sock, d['nick'])
                        self.user_delorphaned(sock)
                self.callback(sock, 'QUIT', d)
        
        def user_namesreplyaddnick(self, sock, nick):
                if len(self.chan_userchanlist(sock, nick)):
                        if nick not in sock.info['users'].keys():
                                sock.info['users'][nick] = {'ident':None, 'mode':""}
                        
        def user_namesreplyuserlist(self, sock, line):
                users = " ".join(line[5:])[1:].split(" ")
                charmode, symmode = sock.info['server']['PREFIX']
                userlist = []           
                for user in users:
                        mode = ''.join([charmode[symmode.find(s)] for s in user if s in symmode])
                        nick = user[len(mode):]
                        userlist.append([nick, mode])
                return userlist

        def user_changednick(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                for key in ['pm', 'channel']:
                        del d[key]
                d['newnick'] = line[2][1:]
                if d['nick'] == sock.conf['nick']:
                        sock.conf['nick'] = d['newnick']
                self.user_updatenick(sock, d['nick'], d['newnick'])
                ident = "%s!%s@%s" % (d['newnick'], d['user'], d['host'])
                self.user_updateident(sock, ident)
                self.callback(sock, "NICK", d)
        
        def user_updatenick(self, sock, nick, newnick):
                if nick in sock.info['users'].keys():
                        sock.info['users'][nick]['mode'] = ""
                        sock.info['users'][newnick] = dict(sock.info['users'][nick])
                        del sock.info['users'][nick]
                        
        def user_updatemode(self, sock, nick, mode):
                if nick in sock.info['users'].keys():
                        sock.info['users'][nick]['mode'] = mode
        
        def user_delorphaned(self, sock):
                for user in sock.info['users'].keys():
                        if not len(self.chan_userchanlist(sock, user)):
                                del sock.info['users'][user]
                                        
        def user_updateident(self, sock, ident):
                nick = ident[:ident.find("!")]
                if nick in sock.info['users'].keys():
                        sock.info['users'][nick]['ident'] = ident

        def user_joinedchannel(self, sock, nick, ident):
                if nick not in sock.info['users'].keys():
                        sock.info['users'][nick] = {'ident':ident}

        def user_msginfo(self, sock, line):
                d = {   'nick':line[0][1:line[0].find("!")],
                        'user':line[0][line[0].find("!")+1:line[0].find("@")],
                        'host':line[0][line[0].find("@")+1:],
                        'ident':line[0][1:],
                        'channel':line[2],
                        'pm':False }
                if d['channel'] == sock.conf['nick']:
                        d['pm'] = True
                        d['channel'] = d['nick']
                self.user_updateident(sock, d['ident'])
                return(d)

# channel & sock.info['channel'] functions

        def chan_userjoin(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                d['channel'] = d['channel'][1:]
                del d['pm']
                if d['nick'] == sock.conf['nick']:
                        sock.chanmode(d['channel'])
                        sock.info['channels'][d['channel']] = {'users':{}, 'mode':"", 'topic':None}
                        self.callback(sock, 'JOINED', d)
                else:
                        self.chan_userjoinedchannel(sock, d['nick'], d['channel'])
                        self.user_joinedchannel(sock, d['nick'], d['ident'])
                        self.callback(sock, 'JOIN', d)

        def chan_userinvite(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                del d['pm']
                d['channel'] = line[3][1:]
                self.callback(sock, 'INVITE', d)
        
        def chan_modeis(self, sock, channel, mode):
                if channel in sock.info['channels'].keys():
                        sock.info['channels'][channel]['mode'] = mode
        
        def chan_userjoinedchannel(self, sock, nick, channel):
                if channel in sock.info['channels'].keys():
                        sock.info['channels'][channel]['users'][nick] = {'mode':""}

        def chan_userquit(self, sock, nick):
                for channel in self.chan_userchanlist(sock, nick):
                        del sock.info['channels'][channel]['users'][nick]

        def chan_updatenick(self, sock, nick, newnick):         
                for channel in self.chan_userchanlist(sock, nick):
                        sock.info['channels'][channel]['users'][newnick] = dict(sock.info['channels'][channel]['users'][nick])
                        if nick != newnick:
                                del sock.info['channels'][channel]['users'][nick]
        
        def chan_namesreplyuser(self, sock, channel, nick, mode):
                if channel in sock.info['channels'].keys():
                        sock.info['channels'][channel]['users'][nick] = {'mode': mode}  

        def chan_partedfrom(self, sock, channel):
                if channel in sock.info['channels'].keys():
                        del sock.info['channels'][channel]
                        self.user_delorphaned(sock)

        def chan_userparted(self, sock, user, channel):
                if channel in sock.info['channels'].keys():
                        if user in sock.info['channels'][channel]['users'].keys():
                                del sock.info['channels'][channel]['users'][user]
                                self.user_delorphaned(sock)
        
        def chan_userkicked(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                del d['pm']
                d['reason'] = ' '.join(line[4:])[1:]
                nick = line[3]
                if nick == sock.conf['nick']:
                        #self.log("Kicked from channel %r reason %r"%(d['channel'],d['reason']))
                        self.chan_partedfrom(sock, d['channel'])
                        self.callback(sock, "KICKED", d)
                else:
                        d['kicked'] = nick
                        self.chan_userparted(sock, d['kicked'], d['channel'])
                        self.callback(sock, "KICK", d)

        def chan_updatetopic(self, sock, channel, topic):
                if channel in sock.info['channels'].keys():
                        sock.info['channels'][channel]['topic'] = topic
                                
        def chan_topicchanged(self, sock, line):
                d = self.user_msginfo(sock, line[:3])
                del d['pm']
                d['topic'] = ' '.join(line[3:])[1:]
                if d['channel'] in sock.info['channels'].keys():
                        d['oldtopic'] = sock.info['channels'][d['channel']]['topic']
                        sock.info['channels'][d['channel']]['topic'] = d['topic']
                        self.callback(sock, "TOPIC", d)
        
        def chan_userchanlist(self, sock, nick):
                channels = []
                for channel in sock.info['channels'].keys():
                        if nick in sock.info['channels'][channel]['users'].keys():
                                channels.append(channel)
                return channels
                                        
# sock.info['server'] functions 
        
        def server_addoption(self, sock, option):
                if "=" in option:
                        key, value = option.split("=", 1)
                        if key == "PREFIX":
                                value = value[1:].split(")")
                        if _isint(value):
                                value = int(value)
                        sock.info['server'][key] = value
                else:
                        sock.info['server'][option] = None

        def callback(self, sock, event, d={}):
                return self.conf['callback'](sock, event, d)
        
        def dummycallback(self, sock, event, d):
                if event != 'TICK':
                        print event, d
                if event == 'PRIVMSG':
                        sock.privmsg(d['channel'], "Configure me correctly: remember to assign {'callback':myparsefunction}.")
                        sock.privmsg(d['channel'], "%s %s %s"%(str(sock), event, str(d)))

class Server(object):
        instance = None
        def __new__(cls, *args, **kargs):
                if cls.instance is None:
                        cls.instance = _SocketManager(*args, **kargs)
                        return cls.instance
                raise Exception("You are only allowed one instance of the Server() class.")
                
if __name__ == "__main__":
        
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
        server.instance({'nick':'pyircalib'})
        server.process()