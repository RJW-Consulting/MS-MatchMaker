'''
Created on Jun 13, 2018

@author: RobinWeber
'''
from PyQt5 import uic, QtCore, QtGui, QtWidgets

class MSRematchThread(QtCore.QThread):
    updateProg = QtCore.pyqtSignal(float,int)
    updateMatches = QtCore.pyqtSignal()
    matchDone = QtCore.pyqtSignal()
    
    def __init__(self,parent,matcher,ms):
        QtCore.QThread.__init__(self,parent)
        self.matcher = matcher
        self.numMatches = 0
        self.app = parent
        self.ms = ms
        
    def run(self):
        self.matcher.doMatchToMS(self.ms,self)
        self.matchDone.emit()
        
    def updateProgress(self,pct):
        y = self.matcher.get_num_matched()
        self.updateProg.emit(pct,y)
        if y > self.numMatches:
            self.numMatches = y
            self.updateMatches.emit()
        return self.app.scan_cancelled_flag()
            
