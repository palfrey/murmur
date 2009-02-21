import twitter
from ConfigParser import SafeConfigParser
from pickle import load,dump
from os.path import getmtime,exists
from time import time

config = SafeConfigParser()
config.read("settings.ini")

username = config.get("twitter","username")

class CachedApi(twitter.Api):
	def __init__(self,*args,**kwargs):
		if "username" in kwargs:
			self.username = kwargs["username"]
		else:
			self.username = None
		if "password" in kwargs:
			self.password = kwargs["password"]
		else:
			self.password = None
		self.logged_in = False
		self.logged_in = True
		twitter.Api.__init__(self)
		self.max_age = kwargs['max_age']
	
	def _doLogin(self):
		if self.logged_in:
			return
		if self.username == None:
			return
		twitter.Api.__init__(self,username=self.username,password=self.password)
		self.logged_in = True
		print "logged in"

	def GetUserTimeline(self, user=None, count=None, since=None):
		pname ="timeline-%s.pickle"%user
		try:
			if self.max_age==-1 or time()-getmtime(pname)<self.max_age:
				return load(file(pname))
			else:
				raise IOError
		except (OSError,IOError,EOFError):
			self._doLogin()
			data = twitter.Api.GetUserTimeline(self,user)
			dump(data,file(pname,"wb"))
			return data

api = CachedApi(username=username,password=config.get("twitter","password"),max_age=60*60)
statuses = api.GetUserTimeline(username)
used = []
for s in statuses:
	if s in used:
		continue
	top = s
	sequence = [s]
	used.append(s)
	while True:
		if top.in_reply_to_status_id!=None: # reply
			othername = top.in_reply_to_screen_name
			#print "other",othername,sequence
			try:
				otherstatus = api.GetUserTimeline(othername)
			except twitter.TwitterAuthError: # assume protected updates
				break
			for o in otherstatus:
				if o.id == top.in_reply_to_status_id:
					if o in used:
						break
					used.append(o)
					sequence = [o] + sequence
					top = o
					break
			else:
				print "nothing earlier"
				break
			if top not in otherstatus:
				break
		else:
			break
	for item in sequence:
		print item.created_at,item.user.screen_name,item.text
	print

