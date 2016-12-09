#!/usr/bin/env python
#
#       pywhat.py
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

import os, shutil, re
import gtk
import subprocess
try:
    from twill.commands import *
    NOTWILL = False
except:
    NOTWILL = True
from BeautifulSoup import BeautifulSoup

class LogChecker:
    
    def __init__(self, username, password):
        if NOTWILL: self.USE = False
        else: self.USE = True
        self.username = username
        self.password = password
        
    def login(self, username, password):
        go('http://what.cd/login.php')
        showforms()
        fv("1" , "username" , username)
        fv("1" , "password" , password)
        submit("login")
        
    def check_log(self, logpath):
        self.login(self.username, self.password)
        go('http://what.cd/logchecker.php')
        #showforms()
        formfile("7", "log", logpath)
        submit()
        soup = BeautifulSoup(show())
        score = soup.findAll(attrs = {'style' : 'color:#418B00'})[0].string
        report = soup.findAll('pre')[0].string
        return (score, report)

def get_files_of_ext(path, ext, fullpath=False):
    """Returns a list of raw filenames of all files in path ending with ext """
    extfiles = []
    for path, dirs, files in os.walk(path):
        for file in [os.path.abspath(os.path.join(path, fname)) for fname in files if fname.endswith(ext)]:
            if fullpath:
                extfiles.append(file)
            else:
                extfiles.append(os.path.split(file)[1])
    return extfiles

def whattheflac(file, tags, encoding, mp3dir):
    """Encodes and transfers tags using flac and lame """
    TAGLISTZ = [t for t in TAGLIST if not t == 'COMMENT']
    tag_args = []
    for pre, tag in zip(FLAC_PREFIXES, TAGLISTZ):
        tag_args.append(pre)
        tag_args.append(tags[tag])
    
    lame_args = ['lame'] + LAME_OPTIONS[encoding.upper()] + tag_args + ['--add-id3v2', '-', mp3dir]
    flacr = subprocess.Popen(['flac', '-dc', file], stdout=subprocess.PIPE)
    os.system('clear')
    update()
    lamer = subprocess.Popen(lame_args, stdin=flacr.stdout, stdout=subprocess.PIPE)
    update()
    lamer.wait()
    update()
    
def mktorrent(basepath, aurl, private=True):
    """Uses mktorrent to create a torrent """
    mktorrent_args = ['mktorrent', '-a', aurl, '-o', basepath + '.torrent']
    if private: mktorrent_args.append('-p')
    mktorrent_args.append(basepath)
    subprocess.call(mktorrent_args)
    os.system('clear')

def pywhat(dir, encodings, aurl, excludetypes=[]):
    for encoding in encodings:
        enddir = '%s [%s]' % (dir, encoding) # /foo/blah/albumname [encoding]
        enddir = ' '.join([i for i in enddir.split() if 'FLAC' not in i.upper() or '/' in i])
        flacfiles = get_files_of_ext(dir, '.flac')
        extrafiles = [os.path.join(dir, f) for f in os.listdir(dir) if not f in flacfiles]
        enddir = enddir.replace('//','/')
        if not os.path.exists(enddir): 
            os.mkdir(enddir)
        
        for f in extrafiles: # Move over any other files
            if excludetypes and any([f.endswith(ext) for ext in excludetypes]): # skips any files of specified type
                continue
            rawf = os.path.split(f)[1] # rawf rawf!
            if os.path.isdir(f):
                subdirend = os.path.join(enddir, rawf)
                if not os.path.exists(subdirend): 
                    shutil.copytree(f, subdirend)
            elif not os.path.exists(os.path.join(enddir, rawf)): 
                shutil.copy(f, enddir)
        
        flacfiles = sorted(flacfiles)
        tags = {}
        for file in [os.path.join(dir, f) for f in flacfiles]:
            print 'Getting tags for: ' + file
            for tag in TAGLIST:
                r = subprocess.Popen(['metaflac', '--show-tag=' + tag, file], stdout=subprocess.PIPE).communicate()
                t = re.sub(r'[:?/]', '_', r[0].strip())
                if '=' in t: tags[tag] = t[t.index('=') + 1:]
                else: tags[tag] = t
            if not tags['TRACKNUMBER'] and tags['TITLE']: # if none of those tags are found, keep the same name as FLAC track
                mp3filepath = file[:file.rindex('.')] + '.mp3'
            else:
                mp3filepath = os.path.join(enddir, '%s - %s.mp3' % (tags['TRACKNUMBER'], tags['TITLE']))
            whattheflac(file, tags, encoding, mp3filepath)
        
        # what's with these .ana files flac is making...
        for badfile in [os.path.join(enddir, file) for file in get_files_of_ext(enddir, '.ana')]:
            os.remove(badfile)
        
        basepath = os.path.split(mp3filepath)[0]
        mktorrent(basepath, aurl)
        
def update():
    """Refreshes GTK """
    while gtk.events_pending():
        gtk.main_iteration(False)

TAGLIST = ["TITLE", "ALBUM", "ARTIST", "TRACKNUMBER", "GENRE", "DATE", "COMMENT"]
FLAC_PREFIXES = ['--tt', '--tl', '--ta', '--tn', '--tg', '--ty']
LAME_OPTIONS = {
    "320" : ["-b", "320", "--ignore-tag-errors"],
    "V0"  : ["-V", "0", "--vbr-new", "--ignore-tag-errors"],
    "V2"  : ["-V", "2", "--vbr-new", "--ignore-tag-errors"]
}
