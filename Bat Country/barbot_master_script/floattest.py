#! /bin/python
import time

video = ['1', '2', '3', '4']
video[3] = 20.98

for i in range(int("%.0d" % round(float(video[3]), -0))):
	print "Working"
	time.sleep(1)