'''
Created on May 30, 2018

@author: RobinWeber
'''

from MSLibrary import MSLibrary
from MassSpectrum import MassSpectrum
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


class MSLibListBox(object):
    '''
    classdocs
    '''
#columns are: Name, d_RI, n_RI, Formula, MW 

    def __init__(self, app, widget):
        '''
        Constructor
        '''
        self.app = app
        self.widget = widget
        self.lib = None
        self.widget.itemSelectionChanged.connect(self.selection_changed)
        
    def scroll_to_ms(self,ms):
        if ms in self.lib:
            inx = self.lib.index(ms)
            if inx >= 0:
                self.widget.scrollToItem(self.widget.item(inx,0))
    
    def strike_selected_ms(self):
        for row in self.widget.selectionModel().selectedRows():
            ms = self.lib[row.row()]
            struck = ms.is_struck()
            ms.set_struck(not struck)
            if ms.is_struck():
                self.app.print_to_history('MS record '+ms.get_uid()+' struck.')
            else:
                self.app.print_to_history('MS record '+ms.get_uid()+' unstruck.')
        self.refresh()     
    
    def selection_changed(self):
        #rows = sorted(set(index.row() for index in
        #              self.widget.selectedIndexes()))
        selItems = self.widget.selectedIndexes()
        if selItems:
            msNum = selItems[0].row()
            item = self.widget.item(msNum,0)
            ms = item.data(QtCore.Qt.UserRole)
            if ms:
                self.app.display_ms(ms)
                #self.app.find_ms_in_matches(ms)
                pass
        
    def refresh(self):
        if self.lib:
            self.widget.setRowCount(self.lib.num_spectra())
            self.widget.setColumnCount(8)
            self.widget.setHorizontalHeaderLabels(['Name','file','UID','RI','RT2','Formula','MW','Maj. Ions'])
            row = 0
            for ms in self.lib:
                struck = ms.is_struck()
                item = QTableWidgetItem(ms.get_tag("Name"))
                item.setData(QtCore.Qt.UserRole,ms)
                self.widget.setItem(row,0, item)
                self.widget.setItem(row,1, QTableWidgetItem(ms.get_filename()))
                self.widget.setItem(row,2, QTableWidgetItem(str(ms.get_tag('UID'))))
                item = QTableWidgetItem()
                ri = ms.get_ri()
                if ri:
                    ri = int(ri)
                    item.setData(QtCore.Qt.DisplayRole,ri)
                self.widget.setItem(row,3, item)
                item = QTableWidgetItem()
                rt2 = ms.get_tag('RT2')
                if rt2:
                    rt2 = round(float(ms.get_tag('RT2')),4)
                    item.setData(QtCore.Qt.DisplayRole,rt2)
                self.widget.setItem(row,4, item)
                self.widget.setItem(row,5, QTableWidgetItem(ms.get_tag("Formula")))
                item = QTableWidgetItem()
                mw = ms.get_tag('MW')
                if mw:
                    if '.' in mw:
                        mw = float(mw)
                    else:
                        mw = int(mw)
                    item.setData(QtCore.Qt.DisplayRole,mw)
                self.widget.setItem(row,6, item)
                self.widget.setItem(row,7, QTableWidgetItem(str(ms.major_ions)))
                font = self.widget.item(row,0).font()
                font.setStrikeOut(struck)
                for col in range(0,self.widget.columnCount()):
                    self.widget.item(row,col).setFont(font)
                row += 1
            
            
    def link_lib(self,lib):
        self.lib = lib
        self.refresh()
    
    def get_lib(self):
        return self.lib
    
    def get_selected_ms(self):
        ixs = self.widget.selectionModel().selectedRows()
        if ixs:
            ix = ixs[0]
            return self.lib[ix.row()]
        else:
            return None
        