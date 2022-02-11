'''
Created on Jun 7, 2018

@author: RobinWeber
'''
from MassSpectrum import MassSpectrum
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QTextEdit

class MSTagView(object):
    '''
    classdocs
    '''


    def __init__(self, app, edBox):
        '''
        Constructor
        '''
        self.app = app
        self.edBox = edBox
        self.ms = None
        
    def show_tags(self,ms):
        self.ms = ms
        txt = ''
        if ms:
            tags = ms.get_all_tag_names()
            for tag in tags:
                txt += tag + ': ' + ms.get_tag(tag) + '\n'
            txt += 'Library: '+ms.get_filename() + '\n'
        self.edBox.setText(txt)
    
    
    def show_2_tags(self,fromMS,toMS):
        txt = ''
        if toMS:
            txt += '*** TO MS ***\n'
            txt += '--------------------------------\n'
            tags = toMS.get_all_tag_names()
            for tag in tags:
                txt += tag + ': ' + toMS.get_tag(tag) + '\n'
            txt += 'Library: '+toMS.get_filename() + '\n'
        if fromMS:
            txt += '--------------------------------\n'
            txt += '*** FROM MS ***\n'
            txt += '--------------------------------\n'
            tags = fromMS.get_all_tag_names()
            for tag in tags:
                txt += tag + ': ' + fromMS.get_tag(tag) + '\n'
            txt += 'Library: '+fromMS.get_filename() + '\n'
        self.edBox.setText(txt)
            
               