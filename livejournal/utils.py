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
# this file contains helper functions

import re

_version = re.compile (r'')

def valid_version (what):
    return _version.match (what) is not None

_spaces = re.compile (r'\s*,\s*')

def list2list (arg):
    return _spaces.split (arg)

l2m_specials = [ 'public', 'private', 'friends' ]

def list2mask (arg, groups):
    gg = map (lambda x : x.lower (), list2list (arg))

    for special in l2m_specials:
        if special in gg:
            gg = special
            break

    if gg in l2m_specials:
        security = gg
    else:
        mask = 0

        for group in groups:
            if group.name in gg:
                mask |= (1 << group.id)

        security = str (mask)

    return security

def mask2list (arg, groups):
    if arg in l2m_specials:
        result = [ arg ]        # actually, 'friends' does not exist
    else:
        try:
            mask = int (arg)
        except ValueError:
            mask = None
        
        if mask is None:
            result = None
        elif mask == 1:
            result = [ 'friends' ]
        else:
            pass

    return result
