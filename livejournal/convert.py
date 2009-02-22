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
# this file some helpers to convert entries to and from different formats
#

from cStringIO import StringIO

def args2text (info, event, subject = None, usejournal = None, security = None, when = None, props = None):
    output = StringIO ()

    output.write ('Journal: ')

    if usejournal is not None:
        output.write (usejournal)

    output.write ('\t' * 3)
    print >> output, '# %s' % ' '.join (info.usejournals)

    sitems = [ 'private', 'friends' ]

    for group in info.friendgroups:
        sitems.append (group.name)

    print >> output, 'Security: public\t\t# %s' % ' '.join (sitems)

    output.write ('Mood: ')
    if props.has_key ('current_mood'):
        output.write (props['current_mood'])
    output.write ('\n')

    output.write ('Music: ')
    if props.has_key ('current_music'):
        output.write (props['current_music'])
    else:
        output.write ('\t\t\t# <detect>')
    output.write ('\n')

    if  subject is not None:
        print >> output, 'Subject:', subject

    output.write ('\n')

    output.write (event)

    return output.getvalue ()

def text2args (info, text):
    pass
