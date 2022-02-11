'''
Created on Jun 6, 2018

@author: RobinWeber
'''
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QApplication, QWidget 
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from MassSpectrum import MassSpectrum
from MSMatcher import MSMatcher
from MSLibMatchTreeItem import MSLibMatchTreeItem
#from builtins import False, True
import pandas as pd
#from pandas._libs.lib import item_from_zerodim
#from builtins import True

class MSLibMatchTree(object):
    '''
    classdocs
    '''


    def __init__(self, app, treeWidget, foundLabel, nextButton, reviewFilterEnable, reviewFilterSelector, reviewFilterValue, reviewFilterTolerance):
        '''
        Constructor
        '''
        self.app = app
        self.treeWidget = treeWidget
        self.foundLabel = foundLabel
        self.nextButton = nextButton
        self.foundMatches = []
        self.dimmedItems = []
        self.nextButton.clicked.connect(self.nextFound)
        self.reviewFilterEnable = reviewFilterEnable
        self.reviewFilterSelector = reviewFilterSelector
        self.reviewFilterSelector.addItems(['RI','RT2','Lib','RI margin','RT2 margin'])
        self.reviewFilterValue = reviewFilterValue
        self.reviewFilterTolerance = reviewFilterTolerance
        self.reviewFilterEnable.stateChanged.connect(self.filterEnableChanged)
        self.reviewFilterSelector.currentIndexChanged.connect(self.filterSelectorChanged)
        self.reviewFilterValue.textChanged.connect(self.filterValueChanged)
        #self.reviewFilterValue.editingFinished.connect(self.filterValueEditingFinished)
        self.reviewFilterTolerance.valueChanged.connect(self.filterToleranceChanged)
        self.someHidden = False
        self.filterMatchTree()
        self.matcher = None
        self.treeWidget.setColumnCount(8)
        self.treeWidget.setHeaderLabels(['# Confirm','FMatch','RMatch','RI','RT2','Lib','UID','Name'])
        self.treeWidget.setColumnWidth(0,70)
        self.treeWidget.setColumnWidth(1,50)
        self.treeWidget.setColumnWidth(2,50)
        self.treeWidget.setColumnWidth(3,50)
        self.treeWidget.setColumnWidth(4,50)
        self.treeWidget.itemSelectionChanged.connect(self.item_selected)
        self.treeWidget.doubleClicked.connect(self.onTreeDoubleClick)
        self.treeWidget.setStyleSheet("QTreeWidget:item:selected:active { color: white; background: blue }")
        self.color_white = QtGui.QBrush(QtGui.QColor(255,255,255,100))
        self.color_gray = QtGui.QBrush(QtGui.QColor(200,200,200,100))
        self.color_dkgray = QtGui.QBrush(QtGui.QColor(50,50,50,100))
        self.color_black = QtGui.QBrush(QtGui.QColor(0,0,0,100))
        self.color_ltgreen = QtGui.QBrush(QtGui.QColor(150,255,150,100))
        self.treeWidget.itemChanged.connect(self.item_changed)

        self.currentFind = None
        self.updateFound()
        self.finding = False

    def updateFound(self):
        if len(self.foundMatches) == 0:
            self.foundLabel.setText('')
            self.nextButton.setVisible(False)
        elif len(self.foundMatches) == 1:
            self.foundLabel.setText('1 found')
            self.nextButton.setVisible(False)
        elif len(self.foundMatches) > 1:
            self.foundLabel.setText(str(len(self.foundMatches))+' found')
            self.nextButton.setVisible(True)
    
    def clearFound(self):
        self.foundMatches = []
        self.currentFind = None
        self.updateFound()
                                        
    def nextFound(self):
        self.finding = True
        self.currentFind += 1
        if self.currentFind > (len(self.foundMatches)-1):
            self.currentFind = 0
        self.treeWidget.setCurrentItem(self.foundMatches[self.currentFind])
        self.foundMatches[self.currentFind].setSelected(True)
        self.finding = False
    
                
            
            
    def onTreeDoubleClick(self,index):
        item = self.treeWidget.currentItem()
        if item and not item.parent():
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            if index.column() != 7:
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
    
    def filterEnableChanged(self,value):
        self.filterMatchTree()
    
    def filterSelectorChanged(self,value):
        valText = self.reviewFilterSelector.currentText()
        if valText in ['RI','RT2']:
            if not self.reviewFilterValue.text().isnumeric():
                self.reviewFilterValue.setText('')
        self.filterMatchTree()

    def filterValueChanged(self,value):
        self.filterMatchTree()

    def filterValueEditingFinished(self):
        self.filterMatchTree()

    def filterToleranceChanged(self,value):
        self.filterMatchTree()
    
    def filterMatchTree(self):
        self.treeWidget.blockSignals(True)
        white = QtGui.QBrush(QtGui.QColor(255,255,255,100))
        gray = QtGui.QBrush(QtGui.QColor(200,200,200,100))
        dkgray = QtGui.QBrush(QtGui.QColor(50,50,50,100))
        black = QtGui.QBrush(QtGui.QColor(0,0,0,100))
        ltgreen = QtGui.QBrush(QtGui.QColor(150,255,150,100))
        self.refreshStripes()
        if self.someHidden:
            iterator = QtWidgets.QTreeWidgetItemIterator(self.treeWidget)
            while iterator.value():
                item = iterator.value()
                item.setHidden(False)
                iterator += 1
            self.someHidden = False 
        if not self.reviewFilterEnable.checkState():
            self.reviewFilterSelector.setEnabled(False)
            self.reviewFilterValue.setEnabled(False)
            self.reviewFilterTolerance.setEnabled(False)
            numfound = 0
        else:
            self.reviewFilterSelector.setEnabled(True)
            if self.reviewFilterSelector.currentText() in ['RI margin','RT2 margin']:
                self.reviewFilterValue.setEnabled(False)
            else:
                self.reviewFilterValue.setEnabled(True)
            if self.reviewFilterSelector.currentText() in ['RI','RT2','RI margin','RT2 margin']:
                self.reviewFilterTolerance.setEnabled(True)
            else:
                self.reviewFilterTolerance.setEnabled(False)
            if self.reviewFilterSelector.currentText() == 'RI':
                validator = QtGui.QIntValidator()
                self.reviewFilterValue.setValidator(validator)
            elif self.reviewFilterSelector.currentText() == 'RT2':
                validator = QtGui.QDoubleValidator ()
                self.reviewFilterValue.setValidator(validator)
            elif self.reviewFilterSelector.currentText() == 'Lib':
                self.reviewFilterValue.setValidator(None)
            else:
                self.reviewFilterValue.setValidator(None)
            # now do the actual filtering
            if (self.reviewFilterSelector.currentText() in ['RI','RT2','Lib'] and self.reviewFilterValue.text() != '') or ('margin' in self.reviewFilterSelector.currentText() and self.reviewFilterTolerance.value() != 0):
                top = None
                showTop = False
                numChildren = 0
                childNum = 0
                iterator = QtWidgets.QTreeWidgetItemIterator(self.treeWidget)
                while iterator.value():
                    item = iterator.value()
                    if item.childCount():
                        if top:
                            if not showTop:
                                top.setHidden(True)
                        top = item
                        showTop = False
                        numChildren = item.childCount()
                        childNum = 0
                    else:
                        childNum += 1
                        filtVal = self.reviewFilterValue.text()
                        filtTol = self.reviewFilterTolerance.value()
                        if self.reviewFilterSelector.currentText() == 'RI':
                            filtVal = int(filtVal)
                            val = item.getRI()
                            if (val <= filtVal+filtTol) and (val >= filtVal-filtTol):
                                showTop = True
                            else:
                                item.setHidden(True)
                                self.someHidden = True
                        elif self.reviewFilterSelector.currentText() == 'RT2':
                            filtVal = float(filtVal)
                            
                            val = float(item.getRT2())
                            if (val <= filtVal+filtTol) and (val >= filtVal-filtTol):
                                showTop = True
                            else:
                                item.setHidden(True)
                                self.someHidden = True
                        elif self.reviewFilterSelector.currentText() == 'Lib':
                            val = item.getLib()
                            if filtVal in val:
                                showTop = True
                            else:
                                item.setHidden(True)
                        elif self.reviewFilterSelector.currentText() == 'RI margin':
                            val = item.getRI()
                            topval = top.getRI()
                            margin = abs(val - topval)
                            showTop = True
                            if (margin <= filtTol):
                                color = self.color_ltgreen
                                self.dimmedItems.append(item)
                                self.someHidden = True
                                for i in range(0,item.columnCount()):
                                    #item.setForeground(i,color)
                                    item.setBackground(i,color)
                        elif self.reviewFilterSelector.currentText() == 'RT2 margin':
                            val = float(item.getRT2())
                            topval = float(top.getRT2())
                            margin = abs(val - topval)
                            showTop = True
                            if (margin <= filtTol):
                                color = self.color_ltgreen
                                self.dimmedItems.append(item)
                                self.someHidden = True
                                for i in range(0,item.columnCount()):
                                    #item.setForeground(i,color)
                                    item.setBackground(i,color)
                            
                        if childNum == numChildren:
                            if not showTop:
                                top.setHidden(True)
                                self.someHidden = True
                    iterator += 1
        self.treeWidget.blockSignals(False)
                                 
    def export_matches(self,filename):
        params = "Match Parameters: Match Threshold = "+str(self.matcher.likelyTh)+'   Use RI = '+str(self.matcher.useRI)+'   RI Margin = '+str(self.matcher.marginRI)+'    RI Tag = '+self.matcher.riTag
        rows = []
        for nm in range(0,self.matcher.get_num_matched()):
            for nt in range(0,self.matcher.get_num_matches(nm)):
                row_matchTreeNum = nm+1
                row_confirmStatus = int(self.matcher.get_match_confirmed_flag(nm,nt))
                row_fMatch = self.matcher.get_match_fm(nm,nt)
                row_rMatch = self.matcher.get_match_rm(nm,nt)
                n_ms = self.matcher.get_matched_ms(nm)
                row_leaderUID = n_ms.get_uid()
                row_leaderName = n_ms.get_name()
                row_leaderRI = n_ms.get_ri()
                row_leaderRT2 = n_ms.get_tag('RT2')
                row_leaderLib = n_ms.get_filename()
                m_ms = self.matcher.get_match_ms(nm,nt)
                row_cmUID = m_ms.get_uid()
                row_cmName = m_ms.get_name()
                row_cmRI = m_ms.get_ri()
                row_cmRT2 = m_ms.get_tag('RT2')
                row_cmLib = m_ms.get_filename()
                rows.append((row_matchTreeNum,row_confirmStatus,row_fMatch,row_rMatch,row_leaderUID,row_leaderName,row_leaderRI,row_leaderRT2,row_leaderLib,row_cmUID,row_cmName,row_cmRI,row_cmRT2,row_cmLib))
        rows.append((params,'','','','','','','','','','','','',''))
        df = pd.DataFrame(rows,columns = ['Match Tree #','Confirm Status','Fmatch','Rmatch','Leader UID','Leader Name','Leader RI','Leader RT2','Leader Lib','Candidate Match UID','Candidate Match Name','Candidate Match RI','Candidate Match RT2','Candidate Match Lib'])
        if filename[-5:].lower() == '.xlsx':
            df.to_excel(filename, engine='xlsxwriter')
        elif filename[-4:].lower() == '.csv':
            df.to_csv(filename)     
            
            
        
    def item_selected(self):
        if not self.finding:
            items = self.treeWidget.selectedItems()
            if items:
                item = items[0]
                if not item.get_to_ms():
                    self.app.display_ms(item.get_from_ms())
                else:
                    self.app.display_2_ms(item.get_from_ms(),item.get_to_ms())
                self.clearFound()
                #self.app.print_to_status("tree item selected")
    
    def item_changed(self,item,col):
        if not self.finding:
            if col == 0:
                fromID = item.get_from_ms().get_uid()
                toID = item.get_to_ms().get_uid()
                if item.checkState(col) == QtCore.Qt.Checked:
                    checked = True
                    self.app.print_to_history('CONFIRMED match between mass spec records UID '+fromID+' and '+toID)
                else:
                    checked = False
                    self.app.print_to_history('UNCONFIRMED match between mass spec records UID '+fromID+' and '+toID)
                self.matcher.set_match_confirmed_flag(item.get_matched_num(),item.get_match_num(),checked)
                self.app.touchProject()
            if col == 7:
                i=1    

    def item_name_changed(self,item,col):
        if item.getCheckState() == QtCore.Qt.Checked:
            checked = True
        else:
            checked = False
        self.matcher.set_match_confirmed_flag(item.get_matched_num(),item.get_match_num(),checked)    
        
                
    def make_tree_widget_item(self,stuff,num, fromMS, toMS, matched_num, match_num):
        white = QtGui.QBrush(QtGui.QColor(255,255,255,100))
        gray = QtGui.QBrush(QtGui.QColor(200,200,200,100))
        item =  MSLibMatchTreeItem(stuff, fromMS, toMS, matched_num, match_num)
        cols = len(stuff)
        if num % 2 == 0:
            clr = white
        else:
            clr = gray
        for i in range(0,cols):
            item.setBackground(i,clr)
        return item
        
    def clear(self):
        self.matcher = None
        self.treeWidget.clear()        
    
    def set_changed_signal(self):
        self.treeWidget.itemChanged.connect(self.item_changed)   
    
    def find_ms(self,ms):
        self.finding = True
        self.foundMatches = []
        self.currentFind = None
        iterator = QtWidgets.QTreeWidgetItemIterator(self.treeWidget)
        numfound = 0
        while iterator.value():
            item = iterator.value()
            if item.get_to_ms():
                #if (item.get_to_ms().get_uid() == ms.get_uid()) or (item.get_from_ms().get_uid() == ms.get_uid()):
                if item.get_to_ms().get_uid() == ms.get_uid():
                    self.foundMatches.append(item)
                    numfound += 1
            else:
                if item.get_from_ms().get_uid() == ms.get_uid():
                    self.foundMatches.append(item)
                    numfound += 1
            iterator += 1 
        if numfound > 0:
            self.currentFind = 0
            self.treeWidget.setCurrentItem(self.foundMatches[0])
            self.foundMatches[0].setSelected(True)
        self.updateFound()
        self.finding = False

        return numfound
        
    def update_matcher(self):
        for i in range(0,self.treeWidget.topLevelItemCount()):
            titem = self.treeWidget.topLevelItem(i)
            name = str(titem.text(7))
            self.matcher.set_matched_confirmed_name(i,name)
            for j in range(0,titem.childCount()):
                citem = titem.child(j)
                if citem.checkState(0) == QtCore.Qt.Checked:
                    checked = True
                else:
                    checked = False
                self.matcher.set_match_confirmed_flag(i,j,checked)    
    
    def get_num_matches(self):
        return self.treeWidget.topLevelItemCount()                    
                
    def refresh_strikeouts(self):
        it = QTreeWidgetItemIterator(self.treeWidget)
        while it.value():
            item = it.value()
            item.set_strikeout()
            it += 1
        self.treeWidget.update()

    def refreshStripes(self):
        topCount = 0
        it = QTreeWidgetItemIterator(self.treeWidget)
        top = None
        while it.value():
            item = it.value()
            if item.childCount() > 0:
                top = item
                topCount += 1
            if topCount % 2 == 0:
                bkColor = self.color_white
            else:
                bkColor = self.color_gray
            for i in range(0,item.columnCount()):
                item.setBackground(i,bkColor)
            it += 1    
        
    def display_matches(self,matcher):
        self.treeWidget.blockSignals(True)
                
        self.matcher = matcher
        self.treeWidget.clear()
        white = QtGui.QBrush(QtGui.QColor(255,255,255,100))
        gray = QtGui.QBrush(QtGui.QColor(200,200,200,100))
        dkgray = QtGui.QBrush(QtGui.QColor(50,50,50,100))
        
        if self.matcher:
            for i in range(0,self.matcher.get_num_matched()):
                if self.matcher.get_matched_confirmed_name(i):
                    topMSname = self.matcher.get_matched_confirmed_name(i)
                else:
                    topMSname =  self.matcher.get_matched_ms(i).get_name()
                n_ms = self.matcher.get_matched_ms(i)
                top = self.make_tree_widget_item([str(i+1),'','',n_ms.get_ri(),str(n_ms.get_tag('RT2')),n_ms.get_filename(),str(n_ms.get_tag('UID')),topMSname],i,self.matcher.get_matched_ms(i),None,i,None)
                topFwdMatch = 0
                topRevMatch = 0
                top.set_strikeout()
                #top.itemChanged.connect(self.item_name_changed)
                topFont = top.font(1)
                topFont.setItalic(True)
                top.setFont(1,topFont)
                topFont = top.font(2)
                topFont.setItalic(True)
                top.setFont(2,topFont)
                topFont = top.font(6)
                topFont.setBold(True)
                top.setFont(6,topFont)
                top.setForeground(1,dkgray)
                top.setForeground(2,dkgray)
                matches = []
                for j in range(0,self.matcher.get_num_matches(i)):
                    mFMatch = self.matcher.get_match_fm(i,j)
                    mRMatch = self.matcher.get_match_rm(i,j)
                    m_ms = self.matcher.get_match_ms(i,j)
                    m = self.make_tree_widget_item(['',str(mFMatch),str(mRMatch),m_ms.get_ri(),str(m_ms.get_tag('RT2')), m_ms.get_filename(),str(m_ms.get_tag('UID')),m_ms.get_name()],i,self.matcher.get_matched_ms(i),m_ms,i,j)
                    if mFMatch > topFwdMatch:
                        top.setData(1,QtCore.Qt.DisplayRole, mFMatch)
                        topFwdMatch = mFMatch
                    if mRMatch > topRevMatch:
                        top.setData(2,QtCore.Qt.DisplayRole, mRMatch)
                        topRevMatch = mRMatch
                    m.set_strikeout()
                    m.setFlags(m.flags() | QtCore.Qt.ItemIsUserCheckable)
                    #m.itemchanged.connect(self.item_checkbox_changed)
                    if self.matcher.get_match_confirmed_flag(i,j):
                        checkState = QtCore.Qt.Checked
                    else:
                        checkState = QtCore.Qt.Unchecked
                    m.setCheckState(0,checkState)
                    matches.append(m)
                if len(matches) > 1:
                    def sortFunc(match):
                        return min(int(match.data(1,0)),int(match.data(2,0)))
                    matches.sort(reverse=True,key=sortFunc)
                for m in matches: 
                    top.addChild(m)
                if  i % 2 == 0:
                    top.setBackground(0,white)
                else:
                    top.setBackground(0,gray)
                self.treeWidget.addTopLevelItem(top)
                self.treeWidget.expandAll()
        self.treeWidget.blockSignals(False)

                
        
        