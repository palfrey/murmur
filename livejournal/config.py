# -*- coding: utf-8 -*-
#
# Copyright (C) 2002, 2003, 2004, 2005 by Mikhail Sobolev <mss@mawhrin.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# this file contains all stuff related to configuration files

from ConfigParser import ConfigParser, NoOptionError
from os.path import expanduser
from cStringIO import StringIO

def evalue (*values):
    '''find an effective value'''

    result = values[0]

    for i in range (len (values) - 1, 0, -1):
        if values[i] is not None:
            result = values[i]
            break

    return result

class Config:
    def __init__ (self):
        pass

    def load (self, name):
        self._cp = ConfigParser ()
        self._cp.read (expanduser (name))

    def as_string (self):
        s = StringIO ()
        self._cp.write (s)
        return s.getvalue ()

    def __hasattr__ (self, name):
        return self._cp.has_section (name)

    def __getattr__ (self, name):
        return ConfigSection (self._cp, name)

    def __setattr__ (self, name, value):
        if name in [ '_cp' ]:
            self.__dict__[name] = value
        else:
            pass # do nothing

class ConfigSection:
    def __init__ (self, config, section):
        self._config = config
        self._section = section

    def __hasattr__ (self, name):
        return self._config.has_option (self._section, name)

    def __getattr__ (self, name):
        try:
            result = self._config.get (self._section, name)
        except NoOptionError:
            result = None

        return result

    def __setattr__ (self, name, value):
        if name in [ '_config', '_section' ]:
            self.__dict__[name] = value
        else:
            self._config.set (self._section, name, value)

def add_std_options (parser):
    '''adds to the specified parser "standard" options
    
unfortunately, this function has purely side effect (which I, personally, do not like'''

    parser.add_option ('-C', '--config', type='string', dest='config', default = None,
                    help = 'specify a config file',
                    metavar = 'CONFIG')
    parser.add_option ('-P', '--server', type='string', dest='server', default = 'server',
                    help = 'specify the server section within the configuration file',
                    metavar = 'SECTION')
    parser.add_option ('-u', '--username', type='string', dest='username', default = None,
                    help = 'specify username, otherwise the one from the configuration file is used',
                    metavar = 'USER')
    parser.add_option ('-p', '--password', type='string', dest='password', default = None,
                    help = 'specify password, otherwise the one from the configuration file is used',
                    metavar = 'PASSWORD')
    

def std_parser (usage = None):
    try:
        from optparse import OptionParser
    except ImportError:
        print >> sys.stderr, "optparse module is really required for this program to work"
        sys.exit (1)

    parser = OptionParser (usage)

    add_std_options (parser)

    return parser
