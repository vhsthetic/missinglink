#!/usr/bin/env python
#
#       mainwindow.py
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

import urllib, os
from urlparse import urlparse
import gobject
import sys
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
from pywhat.pywhat import *

def notification(message): # from SoundConverter 1.4.4
	pass
try:
	import pynotify
	if pynotify.init("Basics"):
		def notification(message):
			n = pynotify.Notification(NAME, message)
			n.show()
except ImportError:
	pass

class MainWindow:
    """MainWindow GTK+ class"""
    
    pathlist = []
    logscores = []
    logchecker = None
    excludes = []
    
    def __init__(self, aurl, username=None, password=None, excludes=[]):
        self.aurl = aurl
        self.excludes = excludes
        self.wtree = gtk.glade.XML("main_window.glade")
        self.window = self.wtree.get_widget("main_window")
        dic = {
            "on_toolbutton_torrent_clicked" : self.make_torrent,
            "on_toolbutton_v0_clicked" : self.make_v0,
            "on_toolbutton_v2_clicked" : self.make_v2,
            "on_toolbutton_320_clicked" : self.make_320,
            "on_toolbutton_remove_clicked" : self.remove_selected,
            "on_menuitem_quit_activate" : self.quit,
            "on_menuitem_open_activate" : self.browse
        }
        self.wtree.signal_autoconnect(dic)
        
        # Liststore setup
        self.treeview = self.wtree.get_widget("treeview")
        self.liststore = gtk.ListStore(gobject.TYPE_STRING,
                                    gobject.TYPE_STRING)
        self.treeview.set_model(self.liststore)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Directory", renderer, text=0)
        self.treeview.get_selection().connect("changed",
                            self.on_selection_changed)
        self.treeview.append_column(column)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        # DnD
        self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL, [('text/uri-list', 0,
            80)], gtk.gdk.ACTION_COPY)
        self.window.connect("drag-data-received", self.on_drag_data_received_event)
        
        # Statusbar
        statusbar = self.wtree.get_widget('statusbar')
        self.context_id = statusbar.get_context_id('Statusbar')
        
        if username and password:
            self.logchecker = LogChecker(username, password)
        
        gtk.main()

    def on_drag_data_received_event(self, widget, drag_content, xcoord, ycoord, 
                                        selection_data, info, timestamp):
        """Handles drag-dropped files """
        for uri in selection_data.data.split():
            realpath = urllib.unquote(urlparse(uri).path)
            if not os.path.isdir(realpath):
                print 'ERROR: Not a directory!'
            else:
                self.add_row(realpath)
        
    def make_torrent(self, widget):
        """Handles activation of Make .torrent"""
        paths = self.get_selected_paths()
        if not paths: return
        for p in paths:
            self.status('Making .torrent for ' + p)
            mktorrent(p, self.aurl)
            self.status('Done.')

    def make_v0(self, widget):
        """Handles activation of Convert to v0"""
        self.make_encoding(['v0'])
    
    def make_v2(self, widget):
        """Handles activation of Convert to v2"""
        self.make_encoding(['v2'])
        
    def make_320(self, widget):
        """Handles activation of Convert to 320 """
        self.make_encoding(['320'])

    def remove_selected(self, widget):
        """Handles activation of Remove toolbutton """
        paths = self.get_selected_paths()
        if not paths: return
        for dir in paths:
            self.remove_row(dir)
    
    def browse(self, widget):
        """Handles activation of File > Open """
        selection = browser(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        if selection[1] == -5:
            self.add_row(selection[0])
    
    def on_selection_changed(self, widget):
        selected = self.treeview.get_selection().get_selected_rows()
        if selected[1]:
            lindex = selected[1][0][0]
            logreport = self.logscores[lindex]
            self.status(logreport)
    
    # UTILS    
    def make_encoding(self, encodings):
        """Uses pywhat to transcode and make torrents """
        paths = self.get_selected_paths()
        if not paths: return
        for p in paths:
            if not get_files_of_ext(p, '.flac'):
                print 'ERROR: No FLAC files in ' + p
                return
            self.status('Encoding ' + os.path.split(p)[1] + ' to ' + ', '.join(encodings) + ', please wait... ')
            pywhat(p, encodings, self.aurl, self.excludes)
            self.status('Done.')
            notification('Encoding finished')
            
    def status(self, s=''):
        """Changes statusbar """
        self.wtree.get_widget('statusbar').pop(self.context_id)
        self.wtree.get_widget('statusbar').push(self.context_id, s)
        update()
    #/UTILS
    
    # ROW UTILS
    def add_row(self, dir):
        """Adds a row and appends dir to pathlist """
        myiter = self.liststore.append()
        self.liststore.set_value(myiter, 0, dir)
        self.pathlist.append(dir)
        logs = get_files_of_ext(dir, '.log', True)
        if logs and self.logchecker and self.logchecker.USE:
            print 'Log files found.'
            self.status('Log files found. Log checking...')
            report = ''
            for log in logs:
                score = self.logchecker.check_log(log)[0]
                print 'Score: ' + score
                report += 'log score: ' + score + ' '
            self.logscores.append(report)
        else:
            self.logscores.append('')
                
        
    def remove_row(self, dir):
        """Removes a row and pops the folder from pathlist """
        datas = [row[0] for row in self.liststore]
        for rowdata in datas:
            if dir == rowdata:
                dataindex = datas.index(rowdata)
                self.liststore.remove(self.liststore.get_iter(dataindex))
                self.pathlist.pop(dataindex)
                break
    
    def get_selected_paths(self):
        """Returns a list of the selected paths in the treeview """
        selected = self.treeview.get_selection().get_selected_rows()
        if not selected[1]: 
            print 'Nothing selected!'
            return
        return [self.pathlist[row[0]] for row in selected[1]]

    def quit(self, widget):
        sys.exit(0)
    # /UTILS

def browser(browse_type, defaultdir = None):
    """ Browses for data, returns 2-tuple of path and response"""
    dialog = gtk.FileChooserDialog("Open..",
        None,
        browse_type,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    if defaultdir: dialog.set_current_folder(defaultdir)
    response = dialog.run()
    path = dialog.get_filename()
    dialog.destroy()
    return (path, response)

def update():
    """Refreshes GTK """
    while gtk.events_pending():
        gtk.main_iteration(False)

NAME = 'Missing Link'
