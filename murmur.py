import twitter
from ConfigParser import SafeConfigParser, NoOptionError
from pickle import load,dump
from os.path import getmtime,exists
from time import time,strptime,strftime
from datetime import date, timedelta
from optparse import OptionParser

from re import compile
from xml.dom.minidom import parseString
from urllib2 import urlopen

yesterday = date.today()-timedelta(1)
yesterday_string = strftime("%a, %d-%b-%Y %H:%M:%S GMT",yesterday.timetuple())
two_days = date.today()-timedelta(2)
two_days_string = strftime("%a, %d-%b-%Y %H:%M:%S GMT",two_days.timetuple())

class CachedApi(twitter.Api):
	def __init__(self,*args,**kwargs):
		if "username" in kwargs:
			self.username = kwargs["username"]
		else:
			self.username = None
		if "password" in kwargs:
			self.password = kwargs["password"]
			self.logged_in = False
		else: # no password means unprotected updates only
			self.password = None
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

	def GetStatus(self, id):
		pname ="status-%d.pickle"%id
		try:
			data = load(file(pname))
			if isinstance(data,twitter.TwitterAuthError):
				raise data
			else:
				return data
		except (OSError,IOError,EOFError):
			self._doLogin()
			try:
				data = twitter.Api.GetStatus(self,id)
				dump(data,file(pname,"wb"))
			except twitter.TwitterAuthError,e:
				dump(e,file(pname,"wb"))
				raise
		return data
	def GetUserTimeline(self, user=None, count=None, since=None, page=1):
		pname ="timeline-%s-%d.pickle"%(user,page)
		try:
			if self.max_age==-1 or time()-getmtime(pname)<self.max_age:
				data = load(file(pname))
				if isinstance(data,twitter.TwitterAuthError):
					raise data
				else:
					return data
			else:
				raise IOError
		except (OSError,IOError,EOFError):
			self._doLogin()
			try:
				data = twitter.Api.GetUserTimeline(self,user,count=count,since=since, page=page)
				dump(data,file(pname,"wb"))
			except twitter.TwitterAuthError,e:
				dump(e,file(pname,"wb"))
				raise
		return data
used = []

def strip_front(raw):
	while True:
		x = raw[0]
		raw = raw[1:]
		if x in (" ","\t"):
			break
	return raw

def get_create_time(s):
	return strptime(s.created_at,"%a %b %d %H:%M:%S +0000 %Y")

def gen_thread(s, existing=[]): # generates a thread of "stuff" based on an initial status
	global used
	when = get_create_time(s)
	if date(*when[:3]) != yesterday:
		return None
	s.when = when
	top = s
	sequence = [s]
	used.append(s.id)
	while True:
		if top.in_reply_to_status_id!=None: # reply
			othername = top.in_reply_to_screen_name
			#print "other",othername,sequence
			try:
				otherstatus = []
				page = 1
				while True:
					print "Getting page %d for %s"%(page,othername)
					extra = api.GetUserTimeline(othername,count=200,since=two_days_string, page=page)
					if extra == []:
						break
					otherstatus.extend(extra)
					when = get_create_time(extra[-1])
					print "yesterday",yesterday,"last",date(*when[:3])
					if date(*when[:3]) < yesterday:
						break
					page+=1
			except twitter.TwitterAuthError: # assume protected updates
				break
			found = False
			for o in otherstatus:
				if o.id == top.in_reply_to_status_id:
					if o.id in used:
						break
					o.when = get_create_time(o)
					top.text = strip_front(top.text)
					used.append(o.id)
					sequence = [o] + sequence
					top = o
					found = True
					break
			if not found:
				print "can't find reply for %d"%top.in_reply_to_status_id,top.text
				for item in existing:
					if item[-1].id == top.in_reply_to_status_id:
						print "found in existing!",[(x.id,x.text) for x in item]
						top.text = strip_front(top.text)
						item.extend(sequence)
						return None
				print sorted([x.id for x in otherstatus])
				break
		else:
			break
	return sequence

def build_replies(username, existing):
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
		if sid in used:
			continue
		#print "finding for %s"%otheruser,sid
		statuses = api.GetUserTimeline(otheruser,since=two_days_string,count=200)
		#print [s.id for s in statuses]
		for s in statuses:
			if s.id == sid:
				th = gen_thread(s, existing)
				if th!=None:
					yield th
					break
				#print "found",sid,s
		#else:
			#print "not found",sid,s

def decide_password(config):
	try:
		password = config.get("twitter","password")
	except NoOptionError: # no password = unprotected updates only
		password = None

	if password!=None:
		try:
			auth = config.get("twitter","authenticated")
			if not eval(auth): # assume some value that resolves to False
				print "Clearing password due to auth = False"
				password = None
		except NoOptionError: # no authenticated field = work from password
			pass
	
	return password

config = SafeConfigParser()
config.read("settings.ini")

username = config.get("twitter","username")
password = decide_password(config)

api = CachedApi(username=username,password=password,max_age=60*60)

if __name__  == "__main__":

	parser = OptionParser()
	parser.add_option("-n","--no-post",help="Don't post, just work out what we would have posted",dest="post",action="store_false",default=True)
	(opts,args) = parser.parse_args()

	statuses = api.GetUserTimeline(username,since=yesterday_string,count=200)
	todo = []
	for s in statuses:
		if s.id in used:
			continue
		th = gen_thread(s, todo)
		if th!=None:
			todo.append(th)

	for th in build_replies(username, todo):
		todo.append(th)

	todo.sort(lambda x,y:cmp(x[0].when,y[0].when))

	output = "<lj-cut text=\"tweets\"><ul>"
	for sequence in todo:
		output += "<li>"
		for item in sequence:
			when = strptime(item.created_at,"%a %b %d %H:%M:%S +0000 %Y")
			name = None
			try:
				name = config.get("mapping",item.user.screen_name)
				if name == "":
					name = None
				else:
					name = "<lj user=\"%s\">"%name
			except NoOptionError:
				pass
			if name == None:
				name = "<img src=\"https://assets1.twitter.com/images/favicon.ico\" width=\"17\" height=\"17\"/><a href=\"http://twitter.com/%s\"><b>%s</b></a>"%(item.user.screen_name,item.user.screen_name)
			if item.text[0] == item.text[0].upper():
				between = ": "
			else:
				between = ""
			text = "<em>%s</em> %s %s%s <a href=\"http://twitter.com/%s/statuses/%d\">#</a>"%(strftime("%d/%m %I:%M %p",when), name, between, item.text, item.user.screen_name, item.id)
			output+=text
			if len(sequence)>1 and item!=sequence[-1]:
				output +="<br />"
		output += "</li>\n"
	output += "</ul><small>Automagically shipped by <a href=\"http://github.com/palfrey/murmur/\">Murmur</a></small></lj-cut>"
	try:
		print output
	except UnicodeEncodeError:
		print "Can't print output due to unicode issues"

	if opts.post:
		from livejournal import LiveJournal, list2list, list2mask

		subject = u"Daily mutterings"
		body = output

		username = config.get("livejournal","username")
		password = config.get("livejournal","password")
		usejournal = username

		lj = LiveJournal (0)
		info = lj.login (username, password)
		security = list2mask (config.get("livejournal","security"), info.friendgroups)

		entry = lj.postevent (unicode(body),
						subject = subject,
						security = security,
						props = {"taglist":"twitter"})

		print 'Posted'
