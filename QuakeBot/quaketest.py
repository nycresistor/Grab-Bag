#!/usr/bin/python

from pyquake3 import PyQuake3, test_connection, Server
q = PyQuake3('net.nycr.us:27960', rcon_password='password2')
#print q.rcon_command("say test")
s = Server(q)
print s.__str__()