'''
Created on May 24, 2018

@author: RobinWeber
'''
import sys
import os
import time
import copy
import ntpath
import numpy as np
from MassSpectrum import MassSpectrum
#from MSLibRepSniffer_GUI_main import app

class MSLibrary(list):
    '''
    classdocs
    '''


    def __init__(self,app):
        '''
        Constructor
        '''
        list.__init__(self)
        self.app = app
        self = []
    
    def setapp(self,app):
        self.app = app
        for ms in self:
            ms.setapp(app)
        
    def getapp(self):
        return self.app
        
    def get_save_copy(self):
        saveapp = self.app
        self.setapp(None)
        for ms in self:
            ms.setapp(None)
        mycopy = copy.deepcopy(self)
        self.setapp(saveapp)
        for ms in self:
            ms.setapp(saveapp)
        return mycopy
        
    def get_ms_with_uid(self,uid):
        retval = None
        for ms in self:
            if ms.get_uid() == uid:
                retval = ms
                break
        return retval
                
    def num_spectra(self):
        return len(self)
    
    def split_msp_into_records(self, filelines):
        records = []
        thisrec = []
        for line in filelines:
            sline = line.rstrip()
            if sline == '':
                if thisrec:
                    records.append(thisrec)
                    thisrec = []
            else:
                thisrec.append(sline)
        if thisrec:
            records.append(thisrec)
        return records
            
            
    def read_from_MSP(self, filename, startID):
        try:
            msp_f = open(filename,'r')
        except IOError as e:
            print('File I/O error({0}): {1}', e.errno, e.strerror)
            return None
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None
            
        msp_text = msp_f.readlines()
        msp_f.close()
        msp_recs = self.split_msp_into_records(msp_text)
        
        next_id = startID
        fnOnly = ntpath.basename(filename)
        for rec in msp_recs:
            ms = MassSpectrum(self.app,next_id,fnOnly)
            next_id += 1
            ms.fill_from_msp_rec(rec)
            self.append(ms)
        self.app.print_to_history('Opened library file '+filename+', '+str(len(msp_recs))+' records added.')
        return next_id    
        
    def get_ms_by_id(self,msid):
        for ms in self:
            if ms.get_id() == msid:
                return ms 
    
    def doSort(self, skey,sreverse):
        if skey == 'Name':
            def keyFunc(e):
                return e.get_name()
        elif skey == 'UID':
            def keyFunc(e):
                return e.get_key('UID')
        self.sort(key=keyFunc,reverse=sreverse) 
        
    def set_use_ri(self):
        for ms in self:
            ms.set_use_ri()
            
    def set_major_ions(self):
        for ms in self:
            ms.set_major_ions()
        
                   
            
        
            
        
        
        
        