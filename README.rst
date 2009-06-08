Murmur
------
By Tom Parker <murmur@tevp.net>
http://github.com/palfrey/murmur

Murmur is a Twitter->Livejournal crossposting tool with support for threaded
conversations, automagic username cross-service mapping and variable security
choices. Primarly, it's used to generate an LJ post summarising your Twitter
conversations of the previous day for people who are on LJ, but not on Twitter.

Motivation
==========

One of the major issues with earlier tools of this type is that they only show
your tweets and @replies, which gives a distinct impression of only hearing half
the conversation, especially to people unfamiliar with or unwilling to navigate
through a collection of interlinked tweets. Murmur utilises the "in reply to"
data to track back the earlier sequence of tweets related to a set of initial
tweets (typically your last day's worth) as well as performing forwards
searching (using Twitter's search function) to find the tweets that are
themselves in reply to the initial tweet set. This combines to give the complete
picture of each day's twittering. (This relies on Twitter clients setting the
in_reply_to value, but this is becoming more the case as time goes on).

Setup
=====

To start using Murmur, we need a settings .ini file (by default called
"settings.ini"!). settings.ini.example contains an example of this. There are
three sections: twitter, livejournal and mapping.

twitter
*******

username: Your twitter username. Required.
password: Your twitter password. Required if you have a protected feed, or want 
to show tweets from other people's protected feeds.

livejournal
***********

username: Your livejournal username. Required.
password: Your livejournal password. Required (we can't post without it).
security: public, friends, private. Optional (defaults to public). Security 
level to post to livejournal at. Defaults to 'public'.

mapping
*******

The mapping section is special, in that it contains a series of values whose 
name is a Twitter name, and whose value is a Livejournal name. By default, 
tweets posted by Murmur have a Twitter icon, and link to the relevant person's 
Twitter account. If however, a mapping entry is specified for that Twitter 
account, then a Livejournal account link and icon is shown instead.

Because of the potential namespace clashes, Murmur can't assume that a person 
with a given Twitter account also owns the relevant Livejournal account (if one 
even exists), and so no automagic assumptions about what Twitter name maps to 
what Livejournal name. We do however supply the "build_mapping.py" script, which 
attempts to fill in the mapping section with mappings for every Twitter account 
in your friends where there exists a Livejournal account of the same name. To 
allow for multiple runs of build_mapping.py over time, it will never overwrite 
an existing mapping, the special case of a mapping with no value (only a twitter 
account as the 'name' part) is written for Twitter friends without a 
corresponding Livejournal account, and that is assumed by Murmur to mean that no 
mapping should be applied (i.e. like there was no mapping entry).

Usage
=====

Usage of Murmur is very simple, and often "python murmur.py" will be sufficient.  
This should be added to a cron job or equivalent so that Murmur can post each 
day's worth of Tweets, and as it only looks for Tweets from the previous day, 
running it just after midnight (ideally randomly between 12pm and 1am to avoid 
the load issues Twitter suffers from more severly from at the beginning and end 
of each hour due to misconfigured automated programs like this).

"python murmur.py --help" supplies more details, but the only option that will 
be of use to most users is the "-s" option, which allows changing of the 
specified settings file away from settings.ini.

# vim:textwidth=80:formatoptions=taw
