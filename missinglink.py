#!/usr/bin/env python
#
#       missinglink.py
#       
#       
#       Copyright (C) 2009 detcader <>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       

import os, sys
from mainwindow import MainWindow

def valid_aurl(a): #TODO: replace with regex
    """Checks validity of tracker URLs """
    return a.startswith('http://') and \
            a.endswith('/announce') and a.count('/') == 4

def main():
    if not os.path.exists('announce'):
        print 'ERROR: missing announce url file'
        print 'creating one... please edit with your announce URL on the first line'
        announcefile = open('announce', 'w')
        return 0
    f = open('announce')
    lines = f.readlines()
    a = lines[0]
    f.close()
    if not a:
        print 'ERROR: announce file empty'
    elif not valid_aurl(a.strip()):
        print 'ERROR: invalid announe url: ' + a
    else:
        un = None
        pw = None
        excludes = None
        if len(lines) == 3: # gets user/pass if present
            un = lines[1].strip()
            pw = lines[2].strip()
        if len(lines) == 4:
            un = lines[1].strip()
            pw = lines[2].strip()
            excludes = [e.strip() for e in lines[3].split(',')]
        print 'starting with trasnfer-excluded filetypes: ' + str(excludes)
        newwindow = MainWindow(a, un, pw, excludes)
    return 0

if __name__ == '__main__': main()
