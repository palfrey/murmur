from pickle import load,dump
from urllib2 import urlopen
from ConfigParser import SafeConfigParser, NoOptionError
from xml.dom.minidom import parseString
from re import compile
from murmur import gen_thread, api, decide_password, yesterday_string
from os.path import getmtime,exists
from time import time

config = SafeConfigParser()
config.read("settings.ini")
username = config.get("twitter","username")
pname = "replies-%s.pickle"%username
try:
	if exists(pname) and time()-getmtime(pname)>60*60: # an hour
		raise IOError
	replies = load(file(pname))
except (OSError,IOError,EOFError):
	replies = urlopen("http://search.twitter.com/search.atom?lang=en&q=@%s&rpp=100"%username).read()
	dump(replies,file(pname,"wb"))

status = compile("http://twitter.com/([^\/]+)/statuses/(\d+)")

dom = parseString(replies)
links = dom.getElementsByTagName("link")
for l in links:
	if l.getAttribute("type")!="text/html": # images, other links, all ignorable
		continue
	href = l.getAttribute("href")
	if href.find("/statuses/")==-1: # not a status
		continue
	(otheruser, sid) = status.match(href).groups()
	sid = int(sid)
	#print "finding for %s"%otheruser,sid
	statuses = api.GetUserTimeline(otheruser,since=yesterday_string,count=200)
	#print [s.id for s in statuses]
	for s in statuses:
		if s.id == sid:
			th = gen_thread(s)
			if th!=None:
				for x in th:
					print x.text
				print
			#print "found",sid,s
