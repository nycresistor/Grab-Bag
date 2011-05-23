#!/usr/bin/python

try:
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
import gdata.calendar.data
import gdata.calendar.client
import gdata.calendar.service
import gdata.acl.data
import atom
import getopt
import sys, os
import string
import time
from BeautifulSoup import BeautifulStoneSoup
import urllib2
import re
import json
import time

appkey = ""
calendarURL = ""
ebRss = ""
venue = None

def retry(ExceptionToCheck, tries=10, delay=2, backoff=1):
    """Retry decorator
    original from http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    print "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry # true decorator
    return deco_retry

class EBConnector:

  def __init__(self, email, password):
  	#setup calendar client
	self.cal_client = gdata.calendar.client.CalendarClient(source='Google-Calendar_Python_Sample-1.0')
	self.cal_client.ClientLogin(email, password, self.cal_client.source);
	
	#setup calendar service
	self.cal_service = gdata.calendar.service.CalendarService()
	self.cal_service.email = email
	self.cal_service.password = password
	self.cal_service.source = 'Google-Calendar_Python_Sample-1.0'
	self.cal_service.ProgrammaticLogin()
  
  @retry(gdata.client.RedirectError, tries=10)
  def _InsertEvent(self, title, content, where, start_time, end_time):
	event = gdata.calendar.data.CalendarEventEntry()
	event.title = atom.data.Title(text=title)
	event.content = atom.data.Content(text=content)
	event.where.append(gdata.data.Where(value=where))
	
	start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', start_time)
	end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', end_time)
	event.when.append(gdata.data.When(start=start_time,end=end_time))
	
	new_event = self.cal_client.InsertEvent(event, calendarURL)

	return new_event
  
  @retry(gdata.client.RequestError, tries=10)
  def _GetCalEvents(self, calendarURL):
	query = self.cal_service.GetCalendarEventFeed(calendarURL)
	gcalEvents = {}
	
  	print "\nFound in gcal:"
	
	for i, an_event in enumerate(query.entry): 
  		
  		print "\t" + str(an_event.title.text)
  		for a_when in an_event.when:
  			print "\t\t" + a_when.start_time + " ::: " + a_when.end_time

  		#if an_event.extended_property != []:
  		#	print "\t\tEventBrite: " + an_event.extended_property[0].value
  		#	
  		#	if an_event.extended_property[0].value not in gcalEvents:
  		#		gcalEvents[an_event.extended_property[0].value] = an_event
  		#	else:
  		#		print "\t\t=== Deleting duplicate gcal event: %s ==="%(an_event.extended_property[0].value)
  		#		self.cal_service.DeleteEvent(an_event.GetEditLink().href)

  		m = re.search(r"(<a href=\")(\D+)(\d+)(\">)", str(an_event.content.text))

  		if m:
  			ebid = m.group(3)
  			print "\t\tEventBrite: " + ebid
  			
  			if ebid not in gcalEvents:
  				gcalEvents[ebid] = an_event
  			else:
  				print "\t\t=== Deleting duplicate gcal event: %s ==="%(ebid)
  				self.cal_service.DeleteEvent(an_event.GetEditLink().href)
  		else:
  			print "\t\tNO MATCH"
  				
  	return gcalEvents

  def _UpdateCalEvent(self, calendarURL, gcalEvent, ebEvent, eid): 	
  	ebStartTime = ebEvent['startdate']
  	gcalStartTime = time.gmtime(time.mktime(time.strptime(gcalEvent.when[0].start_time[:23], "%Y-%m-%dT%H:%M:%S.000")))  		
  
  	ebEndTime = ebEvent['enddate']
  	gcalEndTime = time.gmtime(time.mktime(time.strptime(gcalEvent.when[0].end_time[:23], "%Y-%m-%dT%H:%M:%S.000"))) 
  
  	if gcalEvent.title.text != ebEvent['title'] or gcalEvent.content.text != ebEvent['desc'] or ebStartTime != gcalStartTime or ebEndTime != gcalEndTime:
  		event = self._DeleteAndOrCreateEvent(ebEvent, eid, gcalEvent)
  		return event
  	return False
  
  @retry(gdata.service.RequestError, tries=10)
  def _DeleteAndOrCreateEvent(self, ebEvent, eid, gcalEvent=None):
  	if gcalEvent:
  		print "\tRecreating event %s"%(eid)
  		self.cal_service.DeleteEvent(gcalEvent.GetEditLink().href)
  	else:
  		print "\tCreating event %s"%(eid)
  		
  	event = self._InsertEvent(ebEvent['title'], ebEvent['desc'], venue, ebEvent['startdate'], ebEvent['enddate'])
	#event = self._AddExtendedProperty(event, name="EventBrite", value=eid)
	return event
  
  #@retry(gdata.service.RequestError, tries=10)
  #def _AddExtendedProperty(self, event, name, value):
  #  event.extended_property.append(
  #      gdata.calendar.data.CalendarExtendedProperty(name=name, value=value))
  #  print '\tAdding extended property to event: \'%s\'=\'%s\'' % (name, value,)
  #  return self.cal_client.Update(event)

  def _getCourseListing(self):
	xml = urllib2.urlopen(ebRss)
	soup = BeautifulStoneSoup(xml)
	tags = soup.findAll('link')
	
	eids = []
	
	courses = {}
	
	global venue
	
	for tag in tags:
		match = re.search(r"(event/)(\d+)(/rss)", str(tag))
		if match: 
			print "Found EventBrite ID %s : %s"%(match.group(2), str(tag))
			eids.append(match.group(2))
			
	for eid in eids:
		print "Querying EventBrite API for %s"%(eid)
		
		xml = urllib2.urlopen('https://www.eventbrite.com/xml/event_get?app_key=%s&id=%s'%(appkey, eid))
		soup = BeautifulStoneSoup(xml)
		startdate = self._fixText(soup.find('start_date'))
		enddate = self._fixText(soup.find('end_date'))
		title = self._fixText(soup.find('title'))
		#desc = self._fixText(soup.find('description'))
		
		if not venue:
			venueXML = soup.find('venue')
			name = str(venueXML.find('name'))
			address = str(venueXML.find('address'))
			address2 = str(venueXML.find('address_2'))
			city = str(venueXML.find('city'))
			region = str(venueXML.find('region'))
			zip = str(venueXML.find('postal_code'))
			list = [name, address, address2, city, region]
			venue = self._fixText(", ".join(list) + " " + zip)
			print "Setting Venue: " + venue
		
		urls = soup.findAll('url')
		url = ""
		for addr in urls:
			m = re.search(r"\d+", str(addr))
			if m:
				url = self._fixText(addr)
		
		startdate = time.gmtime(time.mktime(time.strptime(startdate, "%Y-%m-%d %H:%M:%S")))
		enddate = time.gmtime(time.mktime(time.strptime(enddate, "%Y-%m-%d %H:%M:%S")))
		
		desc = '<a href="%s">Click Here</a> for more info.'%(url)
		
		thisCourse = {'title':title, 'desc':desc, 'startdate':startdate, 'enddate':enddate, 'url':url}
		
		courses[eid] = thisCourse
	return courses

  def _fixText(self, data):
	p = re.compile(r'P?&.*?;')
	q = re.compile(r'&lt;.*?&gt;')
	r = re.compile(r'<.*?>')
	data = q.sub('', str(data))
	data = p.sub('', str(data))
	data = r.sub('', str(data))
	data = data.replace("\\xc2\\xa0", "").replace("\\n", "").replace("\n", " ").strip()
	return data
	
  def Run(self):
  		
	ebEvents = self._getCourseListing()
	calEvents = self._GetCalEvents(calendarURL)
	
	print "\n"
	
	for eid in ebEvents:
		if eid not in calEvents:	#new eb course not in calendar
			print "Adding new course %s to gcal"%(eid)	
			self._DeleteAndOrCreateEvent(ebEvents[eid], eid)
			
		else:
			print "Reconciling %s : %s"%(eid, ebEvents[eid]['title'])
			result = self._UpdateCalEvent(calendarURL, calEvents[eid], ebEvents[eid], eid)
			if not result:	print "\tNo changes."
	
	print "\n\nAll good in the neighborhood"

def main():

  # parse command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "pw=", "delete=", "url=", "key=", "rss="])
	except getopt.error, msg:
		print ('python calendarExample.py --user [username] --pw [password] --url [cal url] --key [eb key] --rss [eb rss url] ' + '--delete [true|false] ')
		sys.exit(2)

	user = ''
	pw = ''
	delete = 'false'
	
	global calendarURL
	global appkey
	global ebRss
	
  # Process options
	for o, a in opts:
		if o == "--user":
			user = a
		elif o == "--pw":
			pw = a
		elif o == "--delete":
			delete = a
		elif o == "--url":
			calendarURL = a
		elif o == "--key":
			appkey = a
		elif o == "--rss":
			ebRss = a

	if user == '' or pw == '' or calendarURL == '' or appkey == '' or ebRss == '':
		print ('python calendarExample.py --user [username] --pw [password] --url [cal url] --key [eb key] --rss [eb rss url] ' + '--delete [true|false] ')
		sys.exit(2)

	cal = EBConnector(user, pw)
	cal.Run()

if __name__ == '__main__':
	main()