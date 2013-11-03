#! /usr/bin/python
# -*- coding: utf-8 -*-
import sys
from bs4 import BeautifulSoup
import urllib2
import re

# This is our path to the BOM-EX database file
PARTSDB = "partsdb.txt"

mfgPartNo = None
desc = None
mfg = None
package = "None"

DIGIKEY_URL = 'http://www.digikey.com/product-detail/en/0/'
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.151 Safari/535.19"


with open(PARTSDB, 'a') as file:
	
	# Assume the digikey part number is the first argument
	partNo = sys.argv[1]

	# There's a more robust way to do this
	url = DIGIKEY_URL + partNo.replace("/", "%2F").replace("#", "%23")

	# Grab the data!
	request = urllib2.Request(url)
	request.add_header('User-Agent', USER_AGENT)
	opener = urllib2.build_opener()
	data = opener.open(request).read()
	soup = BeautifulSoup(data)

	# Parse out the Manufacturer Part Number
	for elem in soup(text=re.compile(r'Manufacturer Part Number')):
		try:
			parent = elem.parent.parent.td.meta.attrs
			mfgPartNo = parent['content']
		except:
			pass

	# Parse out the Description
	for elem in soup(text=re.compile(r'Description')):
		try:
			parent = elem.parent.parent.td
			desc = parent.contents[0]
		except:
			pass

	# Parse out the Manufacturer
	for elem in soup(text=re.compile(r'Manufacturer')):
		try:
			parent = elem.parent.parent
			mfg = parent.span.span.contents[0]
		except:
			pass

	# Parse out the Package
	for elem in soup(text=re.compile(r'Package / Case')):
		try:
			parent = elem.parent.parent.td
			package = parent.contents[0]
			if u"®" in package:
				package = package.replace(u"®" "")
		except:
			pass

	# We got everything we needed! Add the part to the database.
	if mfgPartNo is not None and mfg is not None and desc is not None and package is not None:

		entry = "%s\t%s\tDK\t%s\t%s\t%s\n" % (mfgPartNo, mfg, partNo, desc, package)
		print entry
		file.write(entry)

	# Something went wrong, the part was not found, DigiKey changed their site layout, etc.
	else:
		print mfgPartNo, mfg, partNo, desc, package
		print "Error adding entry"
		sys.exit(1)
