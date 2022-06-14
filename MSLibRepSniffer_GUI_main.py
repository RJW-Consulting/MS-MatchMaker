'''
Created on May 24, 2018

Main routine for MSLibrary code for detecting replicate mass spectra
@author: RobinWeber
'''
from logging import _startTime
#from builtins import True, False
#from builtins import True

if __name__ == '__main__':
    pass

import sys
import os
import time
import traceback
import argparse as ap
import numpy as np
import pickle
import itertools
from datetime import datetime
from MassSpectrum import MassSpectrum
from MSLibrary import MSLibrary
from MSLibListBox import MSLibListBox
from MSMatcher import MSMatcher
from MSLibMatchTree import MSLibMatchTree
from MSPlotView import MSPlotView
from MSTagView import MSTagView
from MSMatchThread import MSMatchThread
from MSRematchThread import MSRematchThread
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QInputDialog, QLineEdit, QFileDialog, qApp
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
import matplotlibwidget

#from MSLibRepMgrMainWindow_ui import Ui_MainWindow

Ui_MainWindow, QtBaseClass = uic.loadUiType("MSLibMatchmakerMainWindow.ui")


class MatchThread(QtCore.QThread):
    updateProg = QtCore.pyqtSignal(float)
    
    def __init__(self,parent,matcher):
        QtCore.QThread.__init__(self,parent)
        self.matcher = matcher
        self.updCount = 0
        
    def run(self):
        self.matcher.doMatchToSelf(self)
        
    def updateProgress(self,pct):
        self.updCount +=1
        if self.updCount > 100:
            time.sleep(0.1)
            self.updCount = 0
        self.updateProg.emit(pct)
            

class AppWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    
    def __init__(self):
        self.version = '0.95'
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.fromLibBox = MSLibListBox(self,self.fromTable)
        #self.toLibBox = MSLibListBox(self,self.toTable)
        self.matchBox = MSLibMatchTree(self,self.repTable,self.foundLabel, self.nextButton,self.reviewFilterEnable,self.reviewFilterSelector, self.reviewFilterValue, self.reviewFilterTolerance)
        self.tagView = MSTagView(self,self.compoundTags)
        self.msView = MSPlotView(self,self.compoundMS)
        self.navi_toolbar = NavigationToolbar(self.compoundMS,self)
        self.navBarLayout.addWidget(self.navi_toolbar)
        self.actionOpen_From_Library.triggered.connect(self.openFromLib)
        self.actionQuit.triggered.connect(qApp.quit)
        self.actionSave_Project_File.triggered.connect(self.save_project)
        self.actionSave_Project_File_As.triggered.connect(self.save_project_as)
        self.actionOpen_Project_File.triggered.connect(self.open_project)
        self.actionSave_Merged_Library.triggered.connect(self.save_merged_lib)
        self.actionSave_Library_for_NIST_Search.triggered.connect(self.save_merged_lib_for_NIST)
        self.actionShow_Record_Counts_3.triggered.connect(self.show_record_counts)
        self.actionExport_Matches_2.triggered.connect(self.export_matches)
        #self.actionCut.triggered.connect(self.cut)
        #self.actionCopy.triggered.connect(self.copy)
        #self.actionPaste.triggered.connect(self.paste)
        self.actionStrike.triggered.connect(self.strike_selected_record)
        self.UID_prefix.textChanged.connect(self.set_UIDs)
        self.UID_start.valueChanged.connect(self.set_UIDs)
        self.likelyThreshSB.valueChanged.connect(self.changedMatchThreshold)
        self.nistThreshSB.valueChanged.connect(self.changedNISTThreshold)
        self.use_ri_cb.stateChanged.connect(self.changedRIcb)
        self.ri_marginSB.valueChanged.connect(self.changedRImargin)
        self.RI_tag_cb.currentIndexChanged.connect(self.changedRItag)
        self.notesText.returnPressed.connect(self.fileNote)
        self.testButton.setVisible(False)
        self.clearOld_CB.setVisible(False)
        self.rescanButton.clicked.connect(self.do_rescan)
        #self.actionOpen_To_Library.triggered.connect(self.openToLib)
        self.scanButton.clicked.connect(self.doScan)
        self.testButton.clicked.connect(self.test4)
        self.testButton.setVisible(True)
        self.lastDirectory = ''
        self.nextID = 0
        self.matchCount = 0
        self.matcher = None
        self.matchTimeer = None
        self.lib = None
        self.cancelScan = False
        self.set_num_records(0)
        self.set_num_matches(0)
        self.setWindowTitle(self.windowTitle()+' - Version '+self.version)
        self.currentProjectName = ''
        self.currentProjectTouched = False
        self.history = ''
        #self.ui = Ui_MainWindow()
        #self.ui.setupUi(self)
        #self.statusBar()
        #self.mainmenu = self.menuBar()
        self.checkTouched()
    
    def changedMatchThreshold(self,val):
        self.touchProject()
    
    def changedNISTThreshold(self,val):
        self.touchProject()
        
    def changedRIcb(self,val):
        self.touchProject()
        
    def changedRImargin(self,val):
        self.touchProject()

    def changedRItag(self,val):
        self.touchProject()
        self.refresh_lib_box()
        
    def scan_in_progress(self):
        self.likelyThreshSB.setEnabled(False)
        self.nistThreshSB.setEnabled(False)
        self.use_ri_cb.setEnabled(False)
        self.RI_tag_cb.setEnabled(False)
        self.ri_marginSB.setEnabled(False)
        self.scanButton.setText('Cancel')
        self.scanButton.setEnabled(True)
        self.rescanButton.setEnabled(False)
        self.native_RB.setEnabled(False)
        self.nist_RB.setEnabled(False)
        self.both_RB.setEnabled(False)
        self.clearOld_CB.setEnabled(False)
        try:
            self.scanButton.clicked.disconnect(self.doScan)
        except:
            print('No connection')
        self.scanButton.clicked.connect(self.cancel_scan)
        self.checkTouched()
        
    def rescan_in_progress(self):
        self.likelyThreshSB.setEnabled(False)
        self.nistThreshSB.setEnabled(False)
        self.use_ri_cb.setEnabled(False)
        self.RI_tag_cb.setEnabled(False)
        self.ri_marginSB.setEnabled(False)
        self.rescanButton.setText('Cancel')
        self.rescanButton.setEnabled(True)
        self.scanButton.setEnabled(False)
        self.native_RB.setEnabled(False)
        self.nist_RB.setEnabled(False)
        self.both_RB.setEnabled(False)
        self.clearOld_CB.setEnabled(False)
        try:
            self.rescanButton.clicked.disconnect(self.do_rescan)
        except:
            print('No connection')
        self.rescanButton.clicked.connect(self.cancel_scan)
    
    def checkTouched(self):
        if self.currentProjectName != '' and self.currentProjectTouched:
            self.actionSave_Project_File.setDisabled(False)
        else:
            self.actionSave_Project_File.setDisabled(True)
    
    def touchProject(self):
        self.currentProjectTouched = True
        self.checkTouched()        
    
    def fileNote(self):
        if self.notesText.text().strip():
            self.print_to_history('NOTE> '+self.notesText.text().strip())  
            self.notesText.setText('')   
                  
    def scan_stopped(self):
        self.likelyThreshSB.setEnabled(True)
        self.nistThreshSB.setEnabled(True)
        self.use_ri_cb.setEnabled(True)
        self.RI_tag_cb.setEnabled(True)
        self.ri_marginSB.setEnabled(True)
        self.rescanButton.setEnabled(True)
        self.scanButton.setEnabled(True)
        self.native_RB.setEnabled(True)
        self.nist_RB.setEnabled(True)
        self.both_RB.setEnabled(True)
        self.clearOld_CB.setEnabled(True)
        self.scanButton.setText('Scan')
        try:
            self.scanButton.clicked.disconnect(self.cancel_scan)
        except:
            print('No connection')
        self.scanButton.clicked.connect(self.doScan)
        if self.matcher.cancelled:
            self.set_progress(0,0,0,0)
        
    def scan_cancelled_flag(self):
        return self.cancelScan
    
    def cancel_scan(self):
        self.cancelScan = True
        self.matcher.cancelled = True
        
    def compare(self,a,b,margin):
        if abs(a.use_ri - b.use_ri) <= margin:
            return a.major_ions == b.major_ions
        else:
            return False
 
    
    def doTest(self):
        pass

    def test3(self):
        self.matcher.newPackageMatches()
        self.refresh_match_box()

    def test4(self):
        self.print_to_history('Starting NIST search.')
        self.matcher.nistTh =  self.get_NIST_threshold()   
        self.matcher.doFullNISTsearch()
        self.matcher.packageMatches()

        
    def print_to_history(self,message):
        mes = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+message+'\n'
        self.history += mes
        self.statusText.setPlainText(self.history)
        self.scrollHistoryToBottom()
        time.sleep(0.001)
        self.touchProject()

    def print_to_status(self,message):
        #if message[0] == '\r':
        #    mes = '\n'.join(self.statusText.toPlainText().split('/n')[:-1])
        #else:
        #    mes = self.statusText.toPlainText()
        mes = self.statusText.toPlainText() + message
        self.statusText.setPlainText(mes)
        self.statusText.ensureCursorVisible()
        self.scrollHistoryToBottom()
    
    def scrollHistoryToBottom(self):
        self.statusText.verticalScrollBar().setValue(self.statusText.verticalScrollBar().maximum())

    def replace_status(self,message):
        mes = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+message
        self.statusText.setPlainText(mes + '\n')
    
    def set_num_records(self,num):
        if num > 0:
            self.numRecords.setText(str(num))
        else:
            self.numRecords.setText('')
    
    def set_num_matches(self,num):
        if num > 0:
            self.numMatches.setText(str(num)+' Matches')
        else:
            self.numMatches.setText('')
            
    def set_UIDs(self):
        if self.lib:
            prefix = self.UID_prefix.text()
            seq = self.UID_start.value()
            for ms in self.lib:
                ms.set_comment_tag('UID',prefix+'-'+str(seq))
                seq += 1
        self.fromLibBox.refresh()
        self.refresh_match_box()
        self.touchProject()        
    
    def refresh_lib_box(self):
        self.fromLibBox.refresh()
    
    def use_ri(self):
        return self.use_ri_cb.isChecked()
                
    def display_ms(self,ms):
        #self.print_to_status('selected '+ms.get_tag('Name'))
        #self.fromLibBox.scroll_to_ms(ms)
        self.tagView.show_tags(ms)
        self.msView.plot_one_ms(ms)
        
    def display_2_ms(self,fromMS,toMS):
        self.fromLibBox.scroll_to_ms(toMS)
        self.tagView.show_2_tags(fromMS,toMS)
        self.msView.plot_two_ms(fromMS,toMS)
        
    def find_ms_in_matches(self, ms):
        numfound = self.matchBox.find_ms(ms)
            
    def get_likely_threshold(self):
        return int(self.likelyThreshSB.value())

    def get_NIST_threshold(self):
        return int(self.nistThreshSB.value())

    def set_likely_threshold(self,val):
        self.likelyThreshSB.setValue(val)
    
    def set_NIST_threshold(self,val):
        self.nistThreshSB.setValue(val)
    
    def get_ri_margin(self):
        return int(self.ri_marginSB.value())
    
    def set_ri_margin(self,val):
        self.ri_marginSB.setValue(val)
        
    def get_use_ri_cb(self):
        return self.use_ri_cb.isChecked()

    def set_use_ri_cb(self,state):
        self.use_ri_cb.setChecked(state)
        
    def get_uid_prefix(self):
        return str(self.UID_prefix.text())
    
    def set_uid_prefix(self,txt):
        self.UID_prefix.setText(txt)
    
    def get_uid_seq(self):
        return int(self.UID_start.value())
    
    def set_uid_seq(self,val):
        self.UID_start.setValue(val)
        
    def get_params(self):
        params = [self.get_likely_threshold(), self.get_ri_margin(), self.get_use_ri_cb(), self.get_ri_index(),self.get_uid_prefix(),self.get_uid_seq(),self.history,self.get_NIST_threshold()]
        return params
    
    def set_params(self,p):
        self.set_likely_threshold(p[0])
        self.set_ri_margin(p[1])
        self.set_use_ri_cb(p[2])
        self.set_ri_index(p[3])
        self.set_uid_prefix(p[4])
        self.set_uid_seq(p[5])
        if len(p) > 6:
            self.history = p[6]
            self.statusText.setPlainText(self.history)
        if len(p) > 7:
            self.set_NIST_threshold(p[7])
        
            
            

    
    '''
    def get_ignore_above_threshold(self):
        return int(self.ignoreAboveSB.value()) 
    '''
    def reset(self):
        self.matcher = None
        self.fromLibBox.link_lib([])
        self.matchBox.clear()
        
        
        
    def check_matcher(self):
        if self.fromLibBox.get_lib():
            logFileName = ''
            if self.logMatches_cb.isChecked():
                name = QFileDialog.getSaveFileName(self, 'Save Matches to File', self.lastDirectory, 'csv(*.csv)', '')
                if name[0]:
                    logFileName = name[0]
                else:
                    return
            self.matchCount = 0
            self.matcher = None
            self.matchBox.clear()
            self.matchTimer = QtCore.QTimer()
            self.matchTimer.timeout.connect(self.showMatchProgress)
            searchFlags = [False,False,False]
            if self.native_RB.isChecked():
                searchFlags[0]=True
                searchFlags[1]=False
            elif self.nist_RB.isChecked():
                searchFlags[0]=False
                searchFlags[1]=True
            elif self.both_RB.isChecked():
                searchFlags[0]=True
                searchFlags[1]=True
            if self.clearOld_CB.isChecked():
                searchFlags[2]=True 
            self.matcher = MSMatcher(self,self.fromLibBox.get_lib(), self.get_likely_threshold(), self.use_ri(), self.get_ri_margin(), self.get_ri_tag(), self.get_NIST_threshold(),searchFlags)
            self.matcher.setLogFileName(logFileName)
            self.matchThread = MSMatchThread(self, self.matcher)
            self.matchThread.updateProg.connect(self.set_progress)
            self.matchThread.matchDone.connect(self.match_complete)
            self.matchThread.updateMatches.connect(self.refresh_match_box)
            mess = 'Beginning match scan: match threshold '+ str( self.get_likely_threshold())+', '
            if self.use_ri():
                mess += 'using '+ self.get_ri_tag() + ' margin ' + str(self.get_ri_margin()) + ', '
            else:
                mess += 'no RI used, '
            mess += str(len(self.fromLibBox.get_lib())) + ' records to be scanned.'
            self.print_to_history(mess)
 
            self.matchThread.start()
            self.matchTimer.start(1000)
            
            self.refresh_match_box()

    def begin_rescan(self):
        ms = self.fromLibBox.get_selected_ms()
        if ms and self.fromLibBox.get_lib():
            self.rematchThread = MSRematchThread(self, self.matcher, ms)
            self.rematchThread.updateProg.connect(self.set_progress)
            self.rematchThread.matchDone.connect(self.rematch_complete)
            self.rematchThread.updateMatches.connect(self.refresh_match_box)
            self.rematchThread.start()
            
            self.refresh_match_box()
    
    def rematch_complete(self):
        self.rescanButton.setEnabled(True)
        self.cancelScan = False
        self.scan_stopped()
        self.refresh_match_box()
  
    
    def match_complete(self):
        if self.cancelScan:
            self.print_to_history('Scan cancelled by user. '+str(self.matchCount)+' matches found.')
        else:
            self.print_to_history('Scan complete-- '+str(self.matchCount)+' matches found.')
            
        self.matchTimer.stop()
        self.matchTimer = None
        self.rescanButton.setEnabled(True)
        self.cancelScan = False
        self.scan_stopped()
        self.refresh_match_box()
        self.checkTouched()

        
    def set_progress(self, pct,numMatches,fromrec,torec):
        self.progressBar.setFormat('%.003f%%' % pct)
        self.progressBar.setValue(int(pct))
        self.set_num_matches(numMatches)
        self.matchCount = numMatches
        self.print_to_status('matching from rec #'+ str(fromrec)+' to rec # '+str(torec)+' '+"{0:.3f}".format(pct)+'% done                         ')
        self.checkTouched()

    def showMatchProgress(self):
        if hasattr(self.matcher,'message'):
            if self.matcher.message:
                self.print_to_status(self.matcher.message+'\n')
                self.matcher.message = ''
        if self.matcher.nistCheckables:
            self.progressBar.setStyleSheet("QProgressBar::chunk "
                          "{"
                          "background-color: yellow;"
                          "}")
            pct = (self.matcher.nistCheckablesChecked/self.matcher.nistCheckables) * 100
            self.progressBar.setFormat('%.003f%%' % pct)
            self.progressBar.setValue(int(pct))
        if self.matcher.numMatchables:
            self.progressBar.setStyleSheet("QProgressBar::chunk "
                          "{"
                          "background-color: #80c342;"
                          "}")
            pct = (self.matcher.matchablesChecked/self.matcher.numMatchables) * 100
            self.progressBar.setFormat('%.003f%%' % pct)
            self.progressBar.setValue(int(pct))
    
    def strike_selected_record(self):
        self.fromLibBox.strike_selected_ms()
        self.matchBox.refresh_strikeouts()
        self.checkTouched()

            
    def refresh_match_box(self):
        self.matchBox.display_matches(self.matcher)
        self.checkTouched()

        
    
    def get_ri_index(self):
        return str(self.RI_tag_cb.currentIndex())    

    def get_ri_tag(self):
        return str(self.RI_tag_cb.currentText())    

    def set_ri_index(self,index):
        self.RI_tag_cb.setCurrentIndex(int(index))    
    
    def save_project_as(self):
        name = QFileDialog.getSaveFileName(self, 'Save Project to File', self.lastDirectory, 'LMP(*.LMP)', '')
        if name[0]:
            pickle_file = open(name[0],'wb')
            mylib = self.lib.get_save_copy()
            self.matchBox.update_matcher()
            if self.matcher:
                mymatcher = self.matcher.get_saveable_copy()
            else:
                mymatcher = None
            self.print_to_history('Saved project as '+name[0])
            pickle.dump([mylib,mymatcher,self.get_params()],pickle_file)
            pickle_file.close()
            self.currentProjectName = name[0]
            self.currentProjectTouched = False
        self.checkTouched()

    def save_project(self):
        if self.currentProjectName:
            pickle_file = open(self.currentProjectName,'wb')
            mylib = self.lib.get_save_copy()
            self.matchBox.update_matcher()
            if self.matcher:
                mymatcher = self.matcher.get_saveable_copy()
            else:
                mymatcher = None
            self.print_to_history('Saved project to '+self.currentProjectName)
            pickle.dump([mylib,mymatcher,self.get_params()],pickle_file)
            pickle_file.close()
            self.currentProjectTouched = False
        self.checkTouched()
     
    def open_project(self):
        name = QFileDialog.getOpenFileName(self, 'Open Project File',self.lastDirectory,'LMP(*.LMP)')
        if name[0]:
            try:
                pickle_file = open(name[0],'rb')
                objs = pickle.load(pickle_file)
                pickle_file.close()
            except Exception as e:
                QMessageBox.about(self, "File Unreadable", 'Could not read file '+name[0])
                return
            mylib = objs[0]
            mylib.setapp(self)
            mymatcher = objs[1]
            self.set_params(objs[2])
            if mymatcher:
                mymatcher.restore_links_to_lib(self,mylib)
            self.lib = mylib
            self.set_num_records(len(mylib))
            self.lib.set_use_ri()
            self.lib.set_major_ions()
            self.fromLibBox.link_lib(mylib)
            self.matcher = mymatcher
            if mymatcher:
                self.matchBox.display_matches(mymatcher)
            else:
                self.matchBox.clear()
            self.set_num_matches(self.matchBox.get_num_matches())
            self.currentProjectName = name[0]
            self.print_to_history('Loaded project '+name[0])
            self.currentProjectTouched = False
        self.checkTouched()

    def export_matches(self):
        name = QFileDialog.getSaveFileName(self, 'Export Matches to File', self.lastDirectory, 'xlsx(*.xlsx);;csv(*.csv)', '')
        if name[0]:
            self.matchBox.export_matches(name[0])
            
    def save_merged_lib(self):
        self.save_lib_to_MSP(False)
        
    def save_merged_lib_for_NIST(self):
        self.save_lib_to_MSP(True)
        
    def save_lib_to_MSP(self, forNIST=False):
        name = QFileDialog.getSaveFileName(self, 'Save Merged Library', self.lastDirectory, 'MSP(*.MSP)', '')
        if name[0]:
            msp_file = open(name[0],'w')
            lib = self.lib
            matcher = self.matcher
            self.matchBox.update_matcher()
            for ms in lib:
                if matcher:
                    if not ms.is_struck():
                        matchinx = matcher.find_match_for_ms(ms)
                        confirmed = False
                        matches = []
                        if matchinx:
                            i = matchinx[0]
                            j = matchinx[1]
                            matches.append(matcher.get_matched_ms(i).get_uid())
                            hasConfirmed = False
                            for k in range(0,matcher.get_num_matches(i)):
                                confirmed = matcher.get_match_confirmed_flag(i,k)
                                hasConfirmed |= confirmed
                                if confirmed:
                                    matches.append(matcher.get_match_ms(i,k).get_uid())
                            if (j<0 and hasConfirmed) or (j>=0 and matcher.get_match_confirmed_flag(i,j)):
                                newname = matcher.get_matched_confirmed_name(i)
                                ms.set_name(newname)
                                if len(matches) > 1:
                                    if ms.get_uid() in matches:
                                        try:
                                            matches.remove(ms.get_uid())
                                        except ValueError:
                                            pass
                                    match_tag_val = ''
                                    for uid in matches:
                                        match_tag_val += uid + ","
                                    match_tag_val = match_tag_val[:-1]
                                    ms.set_comment_tag('Confirmed_matches', match_tag_val)
                if forNIST:
                    txt = ms.to_msp_text_for_NIST_search()
                else:
                    txt = ms.to_msp_text()
                msp_file.write(txt+'\n')
        msp_file.close()
                        
                    
    def show_record_counts(self):
        outText = ''
        totalRecs = 0
        if self.lib:
            files = []
            counts = []
            for ms in self.lib:
                name = ms.get_filename()
                if name in files:
                    counts[files.index(name)] += 1
                else:
                    files.append(name)
                    counts.append(1)
            outText = 'Record Counts:\n'
            for i in range(0,len(files)):
                outText += files[i] + ' \t' + str(counts[i]) + '\n'
                totalRecs += counts[i]
            outText += 'Total Records: \t' + str(totalRecs)
        else:
            outText = 'No Records\n'
        self.print_to_status(outText)
                
    def openFromLib(self):
        names = QFileDialog.getOpenFileNames(self, 'Open "From" MSP Library File',self.lastDirectory,'*.msp')
        if names[0]:
            self.reset()
            lib = MSLibrary(self)
            for name in names[0]:
                self.nextID = 1
                self.lastDirectory = '\\'.join(name.split('\\')[0:-1])
                self.nextID = lib.read_from_MSP(name,self.nextID)
            self.lib = lib
            self.set_UIDs()
            self.set_num_records(len(lib))
            self.lib.set_use_ri()
            self.lib.set_major_ions()
            self.fromLibBox.link_lib(lib)
            #self.print_to_status(name[0] + ' opened as "from" library.')
            #self.check_matcher()

    
    def doScan(self):
        self.scan_in_progress()
        self.check_matcher()

    def do_rescan(self):
        ms = self.fromLibBox.get_selected_ms()
        self.matcher.set_all_thresholds(self.get_likely_threshold(), self.use_ri(), self.get_ri_margin())
        if ms and self.fromLibBox.get_lib():
            self.matcher.delete_matches_for_ms(ms)
            self.matcher.doMatchToMS(ms,self)
            self.refresh_match_box()
            self.display_ms(ms)
            self.find_ms_in_matches(ms)


# This block is meant to enavble exception tracebacks that otherwise dont work under PyQT5 with Eclipse
if QtCore.QT_VERSION >= 0x50501:
    def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')
sys.excepthook = excepthook
        
app = QtWidgets.QApplication(sys.argv)
window = AppWindow()
window.show()
#ms_lib = MSLibrary()
#ms_lib.read_from_MSP("C:\\Users\\RobinWeber\\Box Sync\\Documents\\Goldstein Lab\\MS Library Project\\Testing\\Haofei-SOAS-EI_test.msp")
#window.fromLibBox.link_lib(ms_lib)
sys.exit(app.exec_())

'''    
argparser = ap.ArgumentParser()
argparser.add_argument("infile")
args = argparser.parse_args()

ms_lib = MSLibrary()
ms_lib.read_from_MSP(args.infile)
if not ms_lib:
    print("could not read file "+args.infile)
else:
    for n in range(1,len(ms_lib)):
        mf_f = ms_lib[0].match_factor(ms_lib[n])
        mf_r = ms_lib[n].match_factor(ms_lib[0])
        print(ms_lib[n].tags["Name"] + 'forward = ' + str(mf_f) + '   reverse = ' + str(mf_r))
    i=1
    
'''    
    




