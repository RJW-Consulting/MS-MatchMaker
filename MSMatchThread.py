'''
Created on Jun 13, 2018

@author: RobinWeber
'''
from PyQt5 import uic, QtCore, QtGui, QtWidgets
import time


class MSMatchThread(QtCore.QThread):
    updateProg = QtCore.pyqtSignal(float,int,int,int)
    updateMatches = QtCore.pyqtSignal()
    matchDone = QtCore.pyqtSignal()
    
    def __init__(self,parent,matcher):
        QtCore.QThread.__init__(self,parent)
        self.matcher = matcher
        self.numMatches = 0
        self.app = parent
        self.updateCounter = 0
        self.updateEvery = 2
        self.debug = False
        
    def run(self):
        if self.debug:
            import pydevd
            import threading
            pydevd.settrace(suspend=False)
            threading.settrace(pydevd.GetGlobalDebugger().trace_dispatch)
        self.app.touchProject()
        #self.matcher.doMatchToSelf(self)
        if self.matcher.nistSearch:
            self.matcher.doFullNISTsearch()
        if not self.matcher.cancelled:                
            if self.matcher.nativeSearch:
                self.matcher.doOptimizedMatch(self)
            self.matcher.packageMatches()
        self.matchDone.emit()
        
    def updateProgress(self,pct):
        y = self.matcher.get_num_matched()
        frrec = self.matcher.get_current_from_recnum()+1
        torec = self.matcher.get_current_to_recnum()+1
        self.updateProg.emit(pct,y,frrec,torec)
        #self.updateCounter += 1
        #if self.updateCounter >= self.updateEvery:
        time.sleep(0.001)
        #    self.updateCounter = 0
        if y > self.numMatches:
            self.numMatches = y
            self.updateMatches.emit()
        return self.app.scan_cancelled_flag()
            
