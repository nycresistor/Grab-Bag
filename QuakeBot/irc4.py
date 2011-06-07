#!/usr/bin/env python
 
import os, sys
import socket, asyncore, asynchat
import time

class Bot( asynchat.async_chat ):
    def __init__( self ):
        asynchat.async_chat.__init__( self )   
        self.buffer = ''
        self.set_terminator( '\r\n' )
        self.nick = "NYCRQuakeBot"
        self.ident = "NYCRQuakeBot"
        self.realname = "NYCRQuakeBot"
        self.debug = 1
 
        # load all our modules
 
    def write( self, text ):
        if self.debug == 1:
            print '<< DEBUG >> WRITING "%s" TO SOCKET!' % text
        self.push( text + '\r\n' )
 
 
    def handle_connect( self ):
        self.write( 'NICK %s' % self.nick )
        self.write( 'USER %s iw 0 :%s' % ( self.ident, self.realname ) )
 
    def collect_incoming_data( self, data ):
        self.buffer += data
 
    def found_terminator( self ):
        line = self.buffer
        self.buffer = ''
        if self.debug == 1:
            print '<< DEBUG >> %s' % line
 
    def run( self, host, port ):
        self.create_socket( socket.AF_INET, socket.SOCK_STREAM )
        self.connect( ( host, port ) )
        
        mypybot.write("test msg")
        time.sleep(1000)
    
        asyncore.loop()
 
# attemptfork is thanks to phenny irc bot ( http://inamidst.com/phenny/ )
def attemptfork(): 
    try: 
        pid = os.fork()
        if pid > 0:
            sys.exit( 0 )
    except OSError, e: 
        raise OSError( 'Could not daemonize process: %d ( %s )' % ( e.errno, e.strerror ) )
    os.setsid()
    os.umask( 0 )
    try: 
        pid = os.fork()
        if pid > 0: 
            sys.exit( 0 )
    except OSError, e: 
        raise OSError( 'Could not daemonize process: %d ( %s )' % ( e.errno, e.strerror ) )
 
 

 
# initialize
mypybot = Bot()
 
# and run
mypybot.run("irc.freenode.net", 6667)

