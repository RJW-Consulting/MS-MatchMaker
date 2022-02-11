'''
Created on Jun 6, 2018

@author: RobinWeber
'''
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QWidget 
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from MassSpectrum import MassSpectrum
from MSMatcher import MSMatcher


class MSLibMatchTreeItem(QTreeWidgetItem):
    '''
    classdocs
    '''

    def __init__(self, stuff, fromMS, toMS, matched_num, match_num):
        '''
        Constructor
        '''
        QTreeWidgetItem.__init__(self)
        col = 0
        for thing in stuff:
            if thing.isnumeric():
                if '.' in thing:
                    thing = float(thing)
                else:
                    thing = int(thing)
                self.setData(col,QtCore.Qt.DisplayRole,thing)
            else:
                self.setText(col,thing)
            col += 1
        self.fromMS = fromMS
        self.toMS = toMS
        self.matched_num = matched_num
        self.match_num = match_num
        
    def getRI(self):
        return self.data(3,QtCore.Qt.DisplayRole)
    
    def getRT2(self):
        return self.data(4,QtCore.Qt.DisplayRole)
    
    def getLib(self):
        return self.text(5)
        
    def get_from_ms(self):
        return self.fromMS
    
    def get_to_ms(self):
        return self.toMS
    
    def get_matched_num(self):
        return self.matched_num
    
    def get_match_num(self):
        return self.match_num
    
    def set_strikeout(self):
        if self.toMS:
            struck = self.toMS.is_struck()
        else:
            struck = self.fromMS.is_struck()
        for col in range(self.columnCount()):
            font = self.font(col)
            font.setStrikeOut(struck)
            self.setFont(col,font)
            
    
    
    
        