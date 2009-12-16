import twitter
from ConfigParser import SafeConfigParser, NoOptionError
from pickle import load,dump
from urllib2 import urlopen, HTTPError, URLError
from sys import stdout
from os.path import exists, join, getmtime
from os import mkdir
from time import time

config = SafeConfigParser()
config.read("settings.ini")

username = config.get("twitter","username")

cache = "cache"
if not exists(cache):
	mkdir(cache)
pname = join(cache,"friends-%s.pickle"%username)
try:
	if exists(pname) and time()-getmtime(pname)>(24*60*60): # 1 day
		raise OSError
	friends = load(file(pname))
except (OSError,IOError,EOFError):
	password = config.get("twitter","password")

	api = twitter.Api(username=username,password=password)
	friends = [x.screen_name for x in api.GetFriends()]
	friends = dict(zip(friends, [None for x in friends]))
	dump(friends,file(pname,"wb"))
print friends

for f in friends:
	if config.has_option("mapping",f):
		continue
	if friends[f] == None:
		url = "http://%s.livejournal.com"%f.lower()
		print "url",url
		try:
			page = urlopen(url)
			print f,200
			friends[f] = True
		except HTTPError,e:
			print f,e.code
			friends[f] = False
		except URLError,e:
			print f,e.errno
			friends[f] = False
		dump(friends,file(pname,"wb"))
	
	if friends[f]:
		config.set("mapping",f,f)
	else:
		config.set("mapping",f,"")

config.write(open("settings.ini","w"))
