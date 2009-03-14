import twitter
from ConfigParser import SafeConfigParser, NoOptionError
from pickle import load,dump
from urllib2 import urlopen, HTTPError
from sys import stdout

config = SafeConfigParser()
config.read("settings.ini")

username = config.get("twitter","username")

pname = "friends-%s.pickle"%username
try:
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
		dump(friends,file(pname,"wb"))
	
	if friends[f]:
		config.set("mapping",f,f)
	else:
		config.set("mapping",f,"")

config.write(open("settings.ini","w"))
