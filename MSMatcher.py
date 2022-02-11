'''
Created on May 31, 2018

@author: RobinWeber
'''
from MSMatchThread import MSMatchThread
from MassSpectrum import MassSpectrum 
import copy
from ctypes.test.test_funcptr import lib
import time
import datetime
from logging import _startTime
from datetime import datetime
import itertools
import configparser as cp
import os

class MSMatcher(object):
    '''
    classdocs
    '''


    def __init__(self, parent, fromLib, likelyTh, useRI, marginRI, riTag, nistTh, searchFlags):
        '''
        Constructor
                '''
        self.parent = parent
        self.fromLib = fromLib
        self.likelyTh = likelyTh
        self.nistTh = nistTh
        self.fromRecNum = 0
        self.toRecNum = 0
        self.useRI = useRI
        self.marginRI = marginRI
        self.riTag = riTag
        self.nativeSearch = searchFlags[0]
        self.nistSearch = searchFlags[1]
        self.clearFirst = searchFlags[2]
        self.matches = []
        self.matchPairs = []
        self.message = ''
        self.numCheckables = 0
        self.checkablesChecked = 0
        self.numMatchables = 0
        self.matchablesChecked = 0
        self.nistCheckables = 0
        self.nistCheckablesChecked = 0
        self.cancelled = False
        self.nistDirectory = self.getConfigItem('matchmaker.ini','NIST','directory')
        self.nistPrimLocatorFile = self.nistDirectory+'AUTOIMP.MSD'
        self.nistSecLocatorFile = self.getNISTSecondaryLocatorName()
        self.nistRecords = []
        self.nistMatchPairs = []
        #self.doMatchToSelf()
    
    def getConfigItem(self,filename,section,key):
        config = cp.ConfigParser()
        config.read(filename)
        return config[section][key]
        
    def getNISTSecondaryLocatorName(self):
        self.nistDirectory = self.getConfigItem('matchmaker.ini','NIST','directory')
        self.nistPrimLocatorFile = self.nistDirectory+'AUTOIMP.MSD'
        try:
            f = open(self.nistPrimLocatorFile,'r')
            l = f.readline()
            f.close()
            return l
        except:
            return self.nistDirectory+'secondLocator.fil'
        
    def doFullNISTsearch(self):
        # Create the spectra file to search against
        timeout =  self.getConfigItem('matchmaker.ini','NIST','timeoutmin')
        dolog = self.getConfigItem('matchmaker.ini','NIST','log')
        logdir = self.getConfigItem('matchmaker.ini','NIST','logdir')
        threshold = self.nistTh
        directory = os.path.dirname(__file__)
        searchFileName = directory+'\\NISTsearch.msp'
        chunkSize = 100
        recordsDone = 0
        self.nistRecords = []
        self.nistMatchPairs = []
        matchPairs = []
        self.nistCheckables = len(self.fromLib)
        self.nistCheckablesChecked = 0
        while recordsDone < len(self.fromLib):
            if len(self.fromLib)-recordsDone < chunkSize:
                chunkSize = len(self.fromLib)-recordsDone
            recs = self.fromLib[recordsDone:recordsDone+chunkSize]
            searchFile = open(searchFileName,'w')
            for ms in recs:
                msp = ms.to_msp_text_for_NIST_search()
                searchFile.write(msp+'\n')
            searchFile.close()
            secLocFileName = self.getNISTSecondaryLocatorName()
            secLocFile = open(secLocFileName.strip('\n'),'w')
            secLocFile.write(searchFileName+' OVERWRITE\n'+'0 0\n')
            secLocFile.close()
            os.system('"'+self.nistDirectory+'NISTMS$.EXE" /PAR=2')
            time.sleep(1)
            self.message = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' Starting NIST search, records '+str(recordsDone)+" to "+str(recordsDone+chunkSize-1)+" of "+str(len(self.fromLib)) 
            while not os.path.exists(self.nistDirectory+'SRCREADY.TXT'):
                if self.cancelled:
                    return None
                time.sleep(0.1)
            if os.path.exists(self.nistDirectory+'SRCRESLT.TXT'):
                if dolog:
                    if not os.path.exists(logdir):
                        os.makedirs(logdir)
                    f = open(self.nistDirectory+'SRCRESLT.TXT','r')
                    lines = f.readlines()
                    logfilename = logdir+'SRCRESLT_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.TXT'
                    f.close()
                    f = open(logfilename,'w')
                    f.writelines(lines)
                    f.close()
                matchPairs += self.parse_NIST_results(self.nistDirectory+'SRCRESLT.TXT', threshold)
            recordsDone += chunkSize
            self.nistCheckablesChecked += chunkSize
        self.nistMatchPairs = matchPairs
        self.nistCheckables = 0
    
    
    def parse_NIST_results(self,filename,matchThreshold):
        f = open(filename,'r')
        lines = f.readlines()
        f.close()
        pairs = []
        myMSrec = None
        nistRec = None
        for line in lines:
            if line[0:8].lower() == 'unknown:':
                ourUID = line[8:line.find('Compound in Library Factor')].strip()
                myMSrec = self.fromLib.get_ms_with_uid(ourUID)
                if not myMSrec:
                    print('cannot find UID '+ourUID)
            if line[0:3].lower() == 'hit':
                name = line[line.find('<<')+2:line.find('>>;')]
                line = line[line.find('>>;')+3:]
                fields = line.split(';')
                formula = fields[0][fields[0].find(':')+1:].strip().replace('<','').replace('>','')
                fmatch = int(fields[1][fields[1].find(':')+1:].strip())
                rmatch = int(fields[2][fields[2].find(':')+1:].strip())
                if (rmatch >= matchThreshold) and (fmatch >= matchThreshold): 
                    prob = float(fields[3][fields[3].find(':')+1:].strip())
                    casnum = fields[4][fields[4].find(':')+1:].strip()
                    molwt = fields[5][fields[5].find(':')+1:].strip()
                    lib = fields[6][fields[6].find(':')+1:].strip()
                    libid = fields[7][fields[7].find(':')+1:].strip()
                    ri=''
                    if len(fields) > 8:
                        ri= fields[8][fields[8].find(':')+1:].strip()
                    theirMSrec = self.fromLib.get_ms_with_uid(name)
                    if myMSrec.get_uid() != name:
                        theirMSrec = MassSpectrum(self.parent, libid, lib+libid, fromNIST=True)
                        theirMSrec.set_name(name)
                        theirMSrec.set_tag('Formula',formula)
                        theirMSrec.set_tag('CAS#',casnum)
                        theirMSrec.set_tag('MW',molwt)
                        theirMSrec.set_tag(self.parent.get_ri_tag(),ri)
                        self.nistRecords.append(theirMSrec)
                        pairs.append([[myMSrec,theirMSrec],fmatch,rmatch,prob])
        return pairs
                    
                    
                    
                
                
                
                
       
    def get_current_from_recnum(self):
        return self.fromRecNum

    def get_current_to_recnum(self):
        return self.toRecNum
    
    def set_all_thresholds(self, matchTh, useRi, riTh):
        self.likelyTh = matchTh
        self.useRi = useRi
        self.marginRI = riTh
        
            
    def get_saveable_copy(self):
        thecopy = MSMatcher(None,None,self.likelyTh,self.useRI,self.marginRI,self.riTag,self.nistTh,[True,True,False])
        thecopy.matches = []
        for match in self.matches:
            matchCopy = []
            for item in match:
                if type(item) == type([]):
                    matchCopy.append(copy.copy(item))
                else:
                    matchCopy.append(item)
            thecopy.matches.append(matchCopy)       
        for i in range(0,thecopy.get_num_matched()):
            ms = thecopy.get_matched_ms(i)
            thecopy.set_matched_ms(i, ms.get_uid())
            for j in range(0,thecopy.get_num_matches(i)):
                mms = thecopy.get_match_ms(i, j)
                thecopy.set_match_ms(i,j,mms.get_uid())
        if hasattr(self, 'matchPairs'):
            for pair in self.matchPairs:
                newPair = copy.copy(pair)
                newPair[0] = ([pair[0][0].get_uid(),pair[0][1].get_uid()])
                thecopy.matchPairs.append(newPair)
        if hasattr(self, 'nistRecords'):
            thecopy.nistRecords = []
            for ms in self.nistRecords:
                newMS = copy.copy(ms)
                newMS.setapp(None)
                thecopy.nistRecords.append(newMS)
        if hasattr(self, 'nistMatchPairs'):
            thecopy.nistMatchPairs = []
            for pair in self.nistMatchPairs:
                newPair = copy.copy(pair)
                newPair[0] = ([pair[0][0].get_uid(),pair[0][1].get_filename()])
                thecopy.nistMatchPairs.append(newPair)
        return thecopy 
    
    def restore_links_to_lib(self,parent,lib):
        self.parent = parent
        self.fromLib = lib
        for i in range(0,self.get_num_matched()):
            uid = self.get_matched_ms(i)
            ms = lib.get_ms_with_uid(uid)
            self.set_matched_ms(i, ms)
            for j in range(0,self.get_num_matches(i)):
                uid = self.get_match_ms(i, j)
                mms = lib.get_ms_with_uid(uid)
                self.set_match_ms(i,j,mms)
        if hasattr(self, 'matchPairs'):
            for pair in self.matchPairs:
                lpair = list(pair[0])
                pair[0] = ([lib.get_ms_with_uid(lpair[0]),lib.get_ms_with_uid(lpair[1])])
        if hasattr(self, 'nistRecords'):
            for ms in self.nistRecords:
                ms.setapp(parent)
        if hasattr(self, 'nistMatchPairs'):
            for pair in self.nistMatchPairs:
                pair[0][0] = lib.get_ms_with_uid(pair[0][0])
                nistid = pair[0][1]
                pair[0][1] = [rec for rec in self.nistRecords if rec.get_filename() == nistid][0]
        self.packageMatches()
        
    def set_thresholds(self, likelyTh):
        self.likelyTh = likelyTh
        self.doMatch()
    
    def set_progress_pct(self,pct):
        if self.parent:
            self.parent.set_progress(pct)
               
    '''
    def doMatch(self):
        self.matches = []
        flen = self.fromLib.num_spectra()
        tlen = self.toLib.num_spectra()
        f=0
        for fms in self.fromLib:
            match = False
            thisMatch = []
            t = 0
            for tms in self.toLib:
                # skip matching a record to itself
                if (tms.get_filename() != fms.get_filename()) and (tms.get_id() != fms.get_id()):
                    if self.useRI:
                        ri1 = int(tms.get_ri())
                        ri2 = int(fms.get_ri())
                        riGood = (max(ri1,ri2)-min(ri1,ri2) <= self.marginRI)
                    else:
                        riGood = True
                    if riGood:
                        try:
                            fMatchFact = fms.match_factor(tms)
                            rMatchFact = tms.match_factor(fms)
                        except:
                            print("match_factor blew up!")
                        if max(fMatchFact,rMatchFact) >= self.likelyTh:
                            if not match:
                                thisMatch = [f+1,fms]
                                match = True
                                tms.set_use_flag(True)
                            try:
                                thisMatch.append([t+1,fMatchFact,rMatchFact,tms])
                            except:
                                print("appending match blew up!")
                        
                prog_pct = (((f*tlen)+t)/(flen*tlen))*100
                print(str(f)+' '+str(t)+' '+str(prog_pct)+'% done')
                self.set_progress_pct(prog_pct)
                t += 1
            if match:
                try:
                    self.matches.append(thisMatch)
                except:
                    print("appending match set blew up!")
            f += 1
        self.set_progress_pct(100)
'''
    def doMatchToSelf2(self,thread):
        self.matches = []
        self.fromLib.set_use_ri()
        self.fromLib.set_major_ions()
        margin = self.marginRI
        checkables = []
        self.cancelled = False
        starttime = datetime.now()
        #self.print_to_history("starting list walk using itertools.combinations...\n")
        for f, t in itertools.combinations(self.lib, 2):
            if abs(f.use_ri - t.use_ri) <= margin:
                if f.major_ions == t.major_ions:
#            if self.compare(f,t,margin):
                    checkables.append((f,t))        
        endtime = datetime.now()
        interval = endtime - starttime
        secs = interval.total_seconds()
        #self.print_to_history(' Finished list walk using itertools.combinations in %d seconds, %d minutes, %d hours\n'%(secs, secs/60, secs/(60*60)))
        # now that we have filtered for pairs that are worth running the MS algorithm on, do the MS match
        matches = []
        for pair in checkables:
            fMatchFact = pair[0].match_factor(pair[1])
            rMatchFact = pair[1].match_factor(pair[0])
            if (fMatchFact >= self.likelyTh) and (rMatchFact >= self.likelyTh):
                # we have a match, add the record to matches
                matches.append([pair,fMatchFact,rMatchFact])
        # matching finished.  Add found matches to self in proper format
        matchnum = 0
        matches.sort(key = lambda x: x[0][0].get_id())
        currid = -1
        f=0
        t=0
        matchrec = []
        numMatches = len(matches)
        matchnum = 0
        for match in matches:
            if self.cancelled:
                return
            matchroot = match[0][0]
            matchnum += 1
            if currid != matchroot.get_id() or matchnum == numMatches:
                if len(matchrec) != 0:
                    self.matches.append(matchrec)
                    t=0
                    f+=1
                matchrec = [f+1,matchroot,'']
                currid = matchroot.get_id()
            matchrec.append([t+1,fMatchFact,rMatchFact,match[0][1],False])
            t+=1
        if not self.cancelled:
            thread.updateProgress(100)
        else:
            self.cleanUpMatches()
            
            
    def doOptimizedMatch(self,thread):        
        self.cancelled = False
        self.numCheckables = 0
        self.checkablesChecked = 0
        self.numMatchables = 0
        self.matchablesChecked = 0
        self.matchPairs = []        
        self.matches = []
        self.fromLib.set_use_ri()
        self.fromLib.set_major_ions()
        margin = self.marginRI
        libSize = len(self.fromLib)
        numPairs = ((libSize ** 2)-libSize)/2
        checkables = []
        self.cancelled = False
        starttime = datetime.now()
        print("starting list walk using itertools.combinations...")
        self.numCheckables = numPairs
        for f, t in itertools.combinations(self.fromLib, 2):
            if f.use_ri==0 or t.use_ri==0 or (abs(f.use_ri - t.use_ri) <= margin):
                # This passes on a complete match of the top three ions
                #if f.major_ions == t.major_ions:
                # This passes on there being any intersection between the top three ions of each MS
                if f.major_ions & t.major_ions:
#            if self.compare(f,t,margin):
                    checkables.append((f,t))
            self.checkablesChecked +=1        
        endtime = datetime.now()
        interval = endtime - starttime
        secs = interval.total_seconds()
        opTime = secs/numPairs
        opTimeStr = '{:.6f} secs per iteration'.format(opTime)
        mes = ' Finished list walk using itertools.combinations in %d seconds, %d minutes, %d hours'%(secs, secs/60, secs/(60*60))
        print(mes)
        mes = ' %d potential matches for matching algorithm, %s'%(self.numCheckables,opTimeStr)
        print(mes)
        # now that we have filtered for pairs that are worth running the MS algorithm on, do the MS match
        print("starting MS matching...")
        self.numMatchables = len(checkables)
        starttime = datetime.now()
        likelyTh = self.likelyTh
        for pair in checkables:
            if self.cancelled:
                return
            fMatchFact = pair[0].match_factor(pair[1])
            rMatchFact = pair[1].match_factor(pair[0])
            if (fMatchFact >= likelyTh) and (rMatchFact >= likelyTh):
                # we have a match, add the record to matches
                self.matchPairs.append([pair,fMatchFact,rMatchFact])
            self.matchablesChecked += 1            
        endtime = datetime.now()
        interval = endtime - starttime
        secs = interval.total_seconds()
        opTime = secs/len(checkables)
        opTimeStr = '{:.6f} secs per match operation'.format(opTime)
        mes = ' Finished MS matching in %d seconds, %d minutes, %d hours'%(secs, secs/60, secs/(60*60))
        print(mes)
        mes = ' %d matches found, %s'%(len(self.matchPairs),opTimeStr)
        print(mes)
        if not self.cancelled:
            thread.updateProgress(100)
        else:
            self.cleanUpMatches()

    def oldMatches(self):
        self.matchPairs.sort(key = lambda x: x[0][0].get_id())
        currid = -1
        f=0
        t=0
        matchrec = []
        numMatches = len(self.matchPairs)
        matchnum = 0
        for match in self.matchPairs:
            matchroot = match[0][0]
            #debugging here
            if match[0][0].get_uid() == 'LDYtest-15277' or match[0][1].get_uid() == 'LDYtest-15277':
                pass
            matchnum += 1
            if currid != matchroot.get_id() or matchnum == numMatches:
                if len(matchrec) != 0:
                    self.matches.append(matchrec)
                    t=0
                    f+=1
                matchrec = [f+1,matchroot,'']
                currid = matchroot.get_id()
            matchrec.append([t+1,match[1],match[2],match[0][1],False])
            if matchnum == numMatches:
                self.matches.append(matchrec)
            t+=1
    
    def packageMatches(self):
        matchGroups = []
        if hasattr(self, 'nistMatchPairs'):
            pairs = self.matchPairs+self.nistMatchPairs
        else:
            pairs = self.matchPairs+[]
        f = 1
        t = 1
        while len(pairs) > 0:
            leader = pairs[0]
            pairs.remove(leader)
            matchingPairs = [pair for pair in pairs if leader[0][0] in pair[0]]
            matchGroup = [f,leader[0][0],leader[0][0].get_name(),[t,leader[1],leader[2],leader[0][1],False,False]]
            leadMS = leader[0][0]
            for pair in matchingPairs:
                t += 1
                pairs.remove(pair)
                nms = [ms for ms in pair[0] if ms is not leadMS]
                ms=nms[0]
                matchGroup.append([t,pair[1],pair[2],ms,False,False])
            matchGroups.append(matchGroup)
            f += 1
            t = 1
        self.matches = matchGroups
                
                
                   
                    
    def doMatchToSelf(self,thread):
        self.matches = []
        flen = self.fromLib.num_spectra()
        tlen = self.fromLib.num_spectra()
        f=0
        cancelled = False
        for fms in self.fromLib:
            if cancelled:
                break
            match = False
            thisMatch = []
            t = f+1
            self.fromRecNum = f
            for i in range(f,tlen):
                #starttime = datetime.datetime.now()
                tms = self.fromLib[i]
                # skip matching a record to itself
                if tms.get_tag('UID') != fms.get_tag('UID'):
                    if self.useRI and tms.get_ri() and fms.get_ri():
                        ri1 = int(tms.get_ri())
                        ri2 = int(fms.get_ri())
                        riGood = (max(ri1,ri2)-min(ri1,ri2) <= self.marginRI)
                    else:
                        riGood = True
                    if riGood:
                        try:
                            print('getting match factors')
                            fMatchFact = fms.match_factor(tms)
                            rMatchFact = tms.match_factor(fms)
                        except:
                            print("match_factor blew up!")
                        #if max(fMatchFact,rMatchFact) >= self.likelyTh:
                        if (fMatchFact >= self.likelyTh) and (rMatchFact >= self.likelyTh):
                            if not match:
                                thisMatch = [f+1,fms,''] # empty string is a placeholder for new title
                                match = True
                                tms.set_use_flag(True)
                            try:
                                thisMatch.append([t+1,fMatchFact,rMatchFact,tms,False]) # False is a placeholder for 'confirmed' flag
                            except:
                                print("appending match blew up!")
                        
                    prog_pct = (((f*tlen)+t)/(flen*tlen))*100
                    cancelled = thread.updateProgress(prog_pct)
                self.toRecNum = t
                #endtime = datetime.datetime.now()
                #extime = endtime-starttime
                #print('match from '+str(f)+' to '+str(i)+' time(us)='+str(extime.microseconds))
                t += 1
                if cancelled:
                    break
            if match and not cancelled:
                try:
                    self.matches.append(thisMatch)
                except:
                    print("appending match set blew up!")
            f += 1
        if not cancelled:
            thread.updateProgress(100)
        else:
            self.cleanUpMatches()

    def cleanUpMatches(self):
        badMatches = []
        for match in self.matches:
            if len(match) < 5:
                badMatches.append(match)
        for match in badMatches:
            self.matches.remove(match)
            
# matches data structure is:
# [[num_match_0,matched_ms_0,matched_conf_name_0,[match_ms_num,fwd_md,rev_mf,match_ms,confirmed], [match_ms_num,fwd_md,rev_mf,match_ms,confirmed],...],...]
    def delete_matches_for_ms(self,ms):
        newmatches = []
        for match in self.matches:
            if match[1] == ms:
                continue
            newmatch = match[0:3]
            for i in range(0,len(match)-3):
                inx = 3+i
                if match[inx][3] != ms:
                     newmatch.append(match[inx])
            if len(newmatch) > 3:
                newmatches.append(newmatch)
        self.matches = newmatches
        
    def doMatchToMS(self,ms,app):
        tlen = self.fromLib.num_spectra()
        cancelled = False
        t=0
        match = False
        for tms in self.fromLib:
            if cancelled:
                break
            if tms.get_tag('UID') != ms.get_tag('UID'):
                if self.useRI and tms.get_ri() and ms.get_ri():
                    ri1 = int(tms.get_ri())
                    ri2 = int(ms.get_ri())
                    riGood = (max(ri1,ri2)-min(ri1,ri2) <= self.marginRI)
                else:
                    riGood = True
                if riGood:
                    try:
                        fMatchFact = ms.match_factor(tms)
                        rMatchFact = tms.match_factor(ms)
                    except:
                        print("match_factor blew up!")
                    #if max(fMatchFact,rMatchFact) >= self.likelyTh:
                    if fMatchFact >= self.likelyTh and rMatchFact >= self.likelyTh:
                        if not match:
                            thisMatch = [0,ms,''] # empty string is a placeholder for new title
                            match = True
                            tms.set_use_flag(True)
                        try:
                            thisMatch.append([0,fMatchFact,rMatchFact,tms,False]) # False is a placeholder for 'confirmed' flag
                        except:
                            print("appending match blew up!")
                    
                prog_pct = (t/tlen)*100
                print(str(t)+' '+"{0:.3f}".format(prog_pct)+'% done')
                if match:
                    numMatches = len(thisMatch)-3
                else:
                    numMatches = 0
                app.set_progress(prog_pct,numMatches)
                t += 1
        if match and not cancelled:
            try:
                self.matches.append(thisMatch)
            except:
                print("appending match set blew up!")
        if not cancelled:
            numMatches = len(self.matches)
            app.set_progress(100,numMatches)
                 
        
    def get_matches(self):
        return self.matches
    
    def get_num_matched(self):
        return len(self.matches)
    
    def get_matched_ms_num(self,nm):
        return self.matches[nm][0]
    
    def get_matched_ms(self,nm):
        return self.matches[nm][1]
    
    def set_matched_ms(self,nm,ms):
        self.matches[nm][1] = ms
        
    def get_matched_confirmed_name(self,nm):
        return self.matches[nm][2]
    
    def set_matched_confirmed_name(self,nm,name):
        self.matches[nm][2] = name
        
    def get_num_matches(self,nm):
        return len(self.matches[nm])-3
    
    def get_match_ms_num(self,nm,nt):
        retval = 0
        try:
            retval = self.matches[nm][nt+3][0]
        except:
            print("bad value ")
        return retval
    
    def find_match_for_ms(self,ms):
        nummatched = self.get_num_matched()
        for i in range(0,nummatched):
            if ms == self.get_matched_ms(i):
                return [i,-1]
            else:
                for j in range(0,self.get_num_matches(i)):
                    if ms == self.get_match_ms(i,j):
                        return [i,j]
        return []
        
    def get_match_fm(self,nm,nt):
        return self.matches[nm][nt+3][1]

    def get_match_rm(self,nm,nt):
        return self.matches[nm][nt+3][2]
    
    def get_match_ms(self,nm,nt):
        return self.matches[nm][nt+3][3]
    
    def set_match_ms(self,nm,nt,ms):
        self.matches[nm][nt+3][3] = ms
        
    def get_match_confirmed_flag(self,nm,nt):
        return self.matches[nm][nt+3][4]
    
    def set_match_confirmed_flag(self,nm,nt,value):
        try:
            self.matches[nm][nt+3][4] = value
        except IndexError as err:
            pass
    
    
            
                
                
        
         