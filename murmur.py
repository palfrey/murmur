import twitter
from ConfigParser import SafeConfigParser, NoOptionError
from pickle import load,dump
from os.path import getmtime,exists,join
from time import time,strptime,strftime
from datetime import date, timedelta
from optparse import OptionParser
from sys import stdout

from re import compile
from xml.dom.minidom import parseString
from urllib2 import urlopen,URLError

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

		if "cache" in kwargs:
			self.cache = kwargs["cache"]
		else:
			self.cache = "cache"
	
	def _doLogin(self):
		if self.logged_in:
			return
		if self.username == None:
			return
		twitter.Api.__init__(self,username=self.username,password=self.password)
		self.logged_in = True

	def GetStatus(self, id):
		pname = join(self.cache,"status-%d.pickle"%id)
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

	def GetUserTimeline(self, user=None, page=1):
		pname = join(self.cache, "timeline-%s-%d.pickle"%(user,page))
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
				data = twitter.Api.GetUserTimeline(self,user, page=page)
				dump(data,file(pname,"wb"))
			except twitter.TwitterAuthError,e:
				if not exists(pname):
					dump(e,file(pname,"wb"))
				raise
			except URLError:
				if not exists(pname):
					dump(None,file(pname,"wb"))
				return None
		return data

	def GetReplies(self, username = None):
		if username == None:
			assert self.username!=None
			username = self.username
		pname = join(self.cache, "replies-%s.pickle"%username)
		try:
			if exists(pname) and time()-getmtime(pname)>self.max_age:
				raise IOError
			replies = load(file(pname))
		except (OSError,IOError,EOFError):
			replies = urlopen("http://search.twitter.com/search.atom?lang=en&q=@%s&rpp=100"%username).read()
			dump(replies,file(pname,"wb"))
		return replies

def strip_front(raw):
	while True:
		x = raw[0]
		raw = raw[1:]
		if x in (" ","\t"):
			break
	return raw

def get_create_time(s):
	return strptime(s.created_at,"%a %b %d %H:%M:%S +0000 %Y")

class Murmur:
	used = []

	def __init__(self, day=-1, local_only=False, settings="settings.ini"):
		self.config = SafeConfigParser()
		self.config.read(settings)

		self.username = self.config.get("twitter","username")
		self.password = self._decide_password()

		if local_only:
			max_age = -1
		else:
			max_age = 60*60
		self.api = CachedApi(username=self.username,password=self.password,max_age=max_age)

		self.day = date.today()+timedelta(day)

	def gen_thread(self, s, existing=[]): # generates a thread of "stuff" based on an initial status
		when = get_create_time(s)
		if date(*when[:3]) != self.day:
			return None
		s.when = when
		s.children = []
		tree = s
		self.used.append(s.id)
		while True:
			if tree.in_reply_to_status_id!=None: # reply
				othername = tree.in_reply_to_screen_name
				#print "other",othername,tree
				try:
					otherstatus = []
					page = 1
					while True:
						print "Getting page %d for %s"%(page,othername)
						extra = self.api.GetUserTimeline(othername, page=page)
						if extra == []:
							break
						otherstatus.extend(extra)
						when = get_create_time(extra[-1])
						print "self.day",self.day,"last",date(*when[:3])
						if date(*when[:3]) < self.day:
							break
						page+=1
				except twitter.TwitterAuthError: # assume protected updates
					break
				found = False
				for o in otherstatus:
					if o.id == tree.in_reply_to_status_id:
						if o.id in self.used:
							break
						o.when = get_create_time(o)
						tree.text = strip_front(tree.text)
						self.used.append(o.id)
						o.children = [tree]
						tree = o
						print "found",o.id,tree.children,o.text
						found = True
						break
				if not found:
					print "can't find reply for %d"%tree.in_reply_to_status_id,tree.text
					for item in existing:
						if item.id == tree.in_reply_to_status_id:
							print "found in existing!",(item.id,item.text)
							tree.text = strip_front(tree.text)
							item.children.append(tree)
							return None
					print "Using direct methods"
					o = self.api.GetStatus(tree.in_reply_to_status_id)
					if o.id in self.used:
						break
					tree.text = strip_front(tree.text)
					o.when = get_create_time(o)
					self.used.append(o.id)
					o.children = [tree]
					tree = o
			else:
				#print "not reply",tree
				break
		print "returned",tree.text,[x.text for x in tree.children]
		return tree

	def build_replies(self, username=None, existing=[]):
		if username == None:
			username = self.username
		status = compile("http://twitter.com/([^\/]+)/statuses/(\d+)")
		replies = self.api.GetReplies(username = username)

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
			if sid in self.used:
				continue
			#print "finding for %s"%otheruser,sid
			statuses = self.api.GetUserTimeline(otheruser)
			if statuses == None: # couldn't find user
				continue
			#print [s.id for s in statuses]
			for s in statuses:
				if s.id == sid:
					th = self.gen_thread(s, existing)
					if th!=None:
						yield th
						break
					#print "found",sid,s
			#else:
				#print "not found",sid,s

	def _decide_password(self):
		try:
			password = self.config.get("twitter","password")
		except NoOptionError: # no password = unprotected updates only
			password = None

		if password!=None:
			try:
				auth = self.config.get("twitter","authenticated")
				if not eval(auth): # assume some value that resolves to False
					print "Clearing password due to auth = False"
					password = None
			except NoOptionError: # no authenticated field = work from password
				pass
		
		return password

	def build_trees(self):
		statuses = self.api.GetUserTimeline(self.username)
		todo = []
		for s in statuses:
			if s.id in self.used:
				continue
			th = self.gen_thread(s, todo)
			if th!=None:
				todo.append(th)

		for th in self.build_replies(existing=todo):
			todo.append(th)

		todo.sort(lambda x,y:cmp(x.when,y.when))
		return todo

if __name__  == "__main__":

	parser = OptionParser()
	parser.add_option("-n","--no-post",help="Don't post, just work out what we would have posted",dest="post",action="store_false",default=True)
	parser.add_option("-d","--days",help="Go N days back. Default is 1 (i.e. yesterday's posts)",dest="days",type="int",default=1)
	parser.add_option("-l","--local-only",help="Only use local data (which may be very old). Only of use for debugging in networkless environments", dest="local_only", default=False, action="store_true")
	parser.add_option("-s","--settings-file",help="Specify a name of the settings file. Defaults to settings.ini",default="settings.ini")
	(opts,args) = parser.parse_args()

	if len(args)!=0:
		parser.error("Murmur doesn't take any extra args after the options!")

	m = Murmur(-opts.days, opts.local_only, opts.settings_file)
	todo = m.build_trees()

	print
	output = "<lj-cut text=\"tweets\"><ul>"
	for tree in todo:
		print "tree",tree.children
		output += "<li>"
		for item in tree:
			when = strptime(item.created_at,"%a %b %d %H:%M:%S +0000 %Y")
			name = None
			try:
				name = m.config.get("mapping",item.user.screen_name)
				if name == "":
					name = None
				else:
					print name,
					name = "<lj user=\"%s\">"%name
			except NoOptionError:
				pass
			if item!=sequence[0] or (item.text[0].isalpha() and item.text[0] == item.text[0].upper()):
				between = ": "
			else:
				between = ""
				print "",
			if name == None:
				name = "<img src=\"https://assets1.twitter.com/images/favicon.ico\" width=\"17\" height=\"17\"/><a href=\"http://twitter.com/%s\"><b>%s</b></a>"%(item.user.screen_name,item.user.screen_name)
				stdout.write(item.user.screen_name)
				if between == "":
					print " ",
			stdout.write(between)
			text = "<em>%s</em> %s %s%s <a href=\"http://twitter.com/%s/statuses/%d\">#</a>"%(strftime("%d/%m %I:%M %p",when), name, between, item.text, item.user.screen_name, item.id)
			print "%s"%item.text,
			output+=text
			if len(tree)>1 and item!=tree[-1]:
				print ""
				output +="<br />"
		output += "</li>\n"
		print "\n"
	output += "</ul><small>Automagically shipped by <a href=\"http://github.com/palfrey/murmur/\">Murmur</a></small></lj-cut>"
	try:
		print output
	except UnicodeEncodeError:
		print "Can't print output due to unicode issues"

	if opts.post:
		from livejournal import LiveJournal, list2list, list2mask

		subject = u"Daily mutterings"
		body = output

		username = m.config.get("livejournal","username")
		password = m.config.get("livejournal","password")
		usejournal = username

		lj = LiveJournal (0)
		info = lj.login (username, password)
		security = list2mask (m.config.get("livejournal","security"), info.friendgroups)

		entry = lj.postevent (unicode(body),
						subject = subject,
						security = security,
						props = {"taglist":"twitter"})

		print 'Posted'
