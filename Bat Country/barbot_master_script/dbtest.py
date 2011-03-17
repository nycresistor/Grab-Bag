import shlex, sys, os, time, subprocess, serial, sqlite3, random

conn = sqlite3.connect('/Users/max/Dropbox/Fear\ and\ Loathing/barbot.sqlite')
c = conn.cursor()