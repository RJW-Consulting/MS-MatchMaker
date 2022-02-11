'''
Created on May 24, 2018

@author: RobinWeber
'''
import re
import math
#from MSLibRepSniffer_GUI_main import app

class MassSpectrum(object):
    '''
    classdocs
    '''


    def __init__(self, app, msid, filename, fromNIST=False):
        '''
        Constructor
        '''
        self.msid = msid
        self.fromNIST = fromNIST
        self.tags = {}
        self.comment_tags = {}
        self.ms = {}
        self.masses = None
        self.num_masses = 0
        self.filtered_masses = None
        self.num_filtered_masses = 0
        self.major_ions = None
        self.tic = 0
        self.use_ri = 0
        self.use = False
        self.struck = False
        self.filename = filename
        self.app = app
    
    def is_from_NIST(self):
        return self.fromNIST
        
    def getapp(self):
        return self.app
    
    def setapp(self, app):
        self.app = app
    
    def set_struck(self,struck: bool):
        self.struck = struck
    
    def has_struck(self):
        return hasattr(self,'struck')
    
    def is_struck(self):
        if self.has_struck():
            return self.struck
        else:
            return False
        
             
    def get_id(self):
        return self.msid
    
    def get_filename(self):
        return self.filename
    
    def set_use_flag(self, use):
        self.use = use
        
    def use_flag(self):
        return self.use 
    
    def set_use_ri(self):
        try: 
            self.use_ri = int(self.get_ri())
        except:
            self.use_ri = 0
        
    def set_major_ions(self):
        pctOfTIC = 1
        self.masses = set(self.ms.keys())
        self.num_masses = len(self.masses)
        ions = list(self.ms.items())
        ions.sort(key = lambda x: x[1], reverse=True)
        self.tic = sum([item[1] for item in ions])
        # filter to remove 'noise' masses: anything below 0.5% TIC
        m = list(self.ms.keys())
        m.sort()
        self.filtered_masses = set([key for key in m if self.ms[key]/self.tic > 0.005])
        self.num_filtered_masses = len(self.filtered_masses)
        majList = []
        for x in range(0,3):
            if x < len(ions):
                if (ions[x][1]/self.tic)*100 > pctOfTIC:
                    majList.append(ions[x][0])
                else:
                    i=1
            else:
                i=1  
        self.major_ions = set(majList)
    
    def get_ri(self):
        tag = self.app.get_ri_tag()
        value = self.get_tag(tag)
        if '=' in value:
            pos = value.find('=')
            value = value[pos+1:]
            if '/' in value:
                pos = value.find('/')
                value = value[:pos-1]
            retval = value.strip()
        else:
            retval = value.strip() 
        
        return retval
        
            
    def get_tag(self,tag_name):
        retVal = ""
        if tag_name in self.tags.keys():
            retVal = self.tags[tag_name]
        elif tag_name in self.comment_tags.keys():
            retVal = self.comment_tags[tag_name]
        return retVal
    
    def set_tag(self,key,val):
        self.tags[key]=val

    def set_comment_tag(self,key,val):
        self.comment_tags[key]=val
        
    def get_uid(self):
        return self.get_tag('UID')   

    def get_all_tag_names(self):
        return list(self.tags.keys())+list(self.comment_tags.keys())
    
    def get_name(self):
        return self.get_tag('Name')
    
    def set_name(self,name):
        self.set_tag('Name',name)
    
    def get_masses(self):
        return list(self.ms.keys())
    
    def get_values(self):
        return list(self.ms.values())
                
    def add_tag_from_msp_line(self,line):
        pos = line.find(':')
        key = line[0:pos].strip()
        rest = line[pos+1:]
        if key.lower() != 'comments':
            self.tags[key] = rest.strip()
        else:
            eqs = [a.start() for a in list(re.finditer('=', rest))] 
            if eqs:
                for x in eqs:
                    eq = rest.find('=')
                    # the word before the equals is the comment tag key
                    key_begin = rest.rfind(' ',0,eq)+1
                    ckey = rest[key_begin:eq]
                    # check if there is a " immdidiately after the =
                    qrest = rest[eq+1:]
                    if qrest[0] == '"':
                        key_end = qrest[1:].find('"')+1
                        cvalue = qrest[1:key_end]
                    else:
                        key_end = qrest.find(' ')
                        cvalue = qrest[0:key_end]
                    key_end += eq+1
                    rest = rest[0:key_begin]+rest[key_end+1:]                    
                    self.comment_tags[ckey] = cvalue
            self.tags[key] = rest.strip()
             
    def to_msp_text(self):
        msp=''
        if "Comments" not in self.tags.keys():
            self.set_tag('Comments', '')
        for key in self.tags.keys():
            val = self.tags[key]
            msp += key+': '+val
            if key.lower() == 'comments':
                for ckey in self.comment_tags.keys():
                    cval = self.comment_tags[ckey]
                    msp += ' '+ckey+'="'+cval+'" '
            msp += '\n'
        msp += "Num Peaks: " + str(len(self.ms)) + '\n'
        for key in self.ms:
            msp += str(key)+' '+str(self.ms[key]) + ' ; '
        msp += '\n'
        return msp    

    def to_msp_text_for_NIST_search(self):
        msp=''
        msp += 'NAME: '+ self.get_uid()+"\n"
        if "Comments" not in self.tags.keys():
            self.set_tag('Comments', '')
        msp += 'COMMENT:' + self.get_tag('Comments')+"\n"
        msp += 'FORMULA:' + self.get_tag('Formula')+"\n"
        msp += 'MW:' + self.get_tag('MW')+"\n"
        msp += 'CAS#:' + self.get_tag('CAS#')+"\n"
        msp += "Num Peaks: " + str(len(self.ms)) + '\n'
        for key in self.ms:
            msp += str(key)+' '+str(self.ms[key]) + ' ; '
        msp += '\n\n'
        return msp    
              
      
    def add_mass_spec_from_msp_line(self,line):
        masses = line.split(';')
        for pair in masses:
            if pair:
                if ' ' in pair:
                    nums = pair.strip().split(' ')
                elif ',' in pair:
                    nums = pair.strip().split(',')
                if len(nums) < 2:
                    print('Bad mass spec line')
                if float(nums[1]) > 0:
                    self.ms[int(float(nums[0]))] = float(nums[1])
                
        
    
    def fill_from_msp_rec(self,rec):
        for line in rec:
            if 'Num Peaks:' not in line:
                if ':' in line:
                    self.add_tag_from_msp_line(line)
                elif ';' in line:
                    self.add_mass_spec_from_msp_line(line)
                    
    def num_masses(self):
        return len(self.ms)
    
    def mass_value(self,mass):
        value = 0
        try:
            value = self.ms[mass]
        except:
            pass
        return value
    
    def common_masses(self,other_ms):
        masses = []
        for m in self.ms:
            if other_ms.mass_value(m) > 0:
                masses.append(m)
        return masses
    
    def f_1(self,other_ms):
        num = 0
        sum_self = 0
        sum_other = 0
        for mass_self, abund_self in self.ms.items():
            abund_other = other_ms.mass_value(mass_self)
            num += mass_self*math.sqrt(abund_self*abund_other)
            sum_self += mass_self*abund_self
            sum_other += mass_self*abund_other
        return num/math.sqrt(sum_self*sum_other)
    
    def f_2(self,other_ms):
        # Determine the mass peaks present in both spectra
        peaks=self.common_masses(other_ms)
        num_common_peaks = len(peaks)
        term_1 = 0
        for i in range(1,num_common_peaks):
            x=self.mass_value(peaks[i-1])
            if x==0:
                print("problem!")
            rat1 = (self.mass_value(peaks[i])/self.mass_value(peaks[i-1]))
            rat2 = (other_ms.mass_value(peaks[i])/other_ms.mass_value(peaks[i-1]))
            n=1
            if rat2 < rat1:
                n=-1
            term_1 += (rat1**n)*(rat2**(-n))
        return (1/num_common_peaks)*term_1
    
    def match_factor(self,other_ms):
        common_masses = self.common_masses(other_ms)
        num_common_masses = len(common_masses)
        num_other_masses = other_ms.num_masses
        try:
            f1 = self.f_1(other_ms)
            f2 = self.f_2(other_ms)
            retval = int(1000/(num_common_masses+num_other_masses)*((num_other_masses*f1)+(num_common_masses*f2)))
        except:
            print('match failure- probable divide by zero')
            retval = 0
        return retval 

#  This is all stuff to be played with

''' 
    def common_masses(self,other_ms):
        return sorted(list(self.filtered_masses & other_ms.filtered_masses))
        
    def f_1(self,other_ms):
        num = 0
        sum_self = 0
        sum_other = 0
        for mass_self, abund_self in self.ms.items():
            abund_other = other_ms.mass_value(mass_self)
            num += mass_self*math.sqrt(abund_self*abund_other)
            sum_self += mass_self*abund_self
            sum_other += mass_self*abund_other
        return num/math.sqrt(sum_self*sum_other)
    
    def f_1_new(self,other_ms):
        num = 0
        sum_self = 0
        sum_other = 0
        for mass_self in self.filtered_masses:
            abund_self = self.mass_value(mass_self)
            abund_other = other_ms.mass_value(mass_self)
            num += mass_self*math.sqrt(abund_self*abund_other)
            sum_self += mass_self*abund_self
            sum_other += mass_self*abund_other
        return num/math.sqrt(sum_self*sum_other)
    
    def f_2(self,other_ms):
        # Determine the mass peaks present in both spectra
        peaks=self.common_masses(other_ms)
        num_common_peaks = len(peaks)
        term_1 = 0
        for i in range(1,num_common_peaks):
            x=self.mass_value(peaks[i-1])
            if x==0:
                print("problem!")
            rat1 = (self.mass_value(peaks[i])/self.mass_value(peaks[i-1]))
            rat2 = (other_ms.mass_value(peaks[i])/other_ms.mass_value(peaks[i-1]))
            n=1
            if rat2 < rat1:
                n=-1
            term_1 += (rat1**n)*(rat2**(-n))
        return (1/num_common_peaks)*term_1
    
    def match_factor(self,other_ms):
        common_masses = self.common_masses(other_ms)
        num_common_masses = len(common_masses)
        num_other_masses = other_ms.num_filtered_masses
        try:
            f1 = self.f_1(other_ms)
            f2 = self.f_2(other_ms)
            retval = int(1000/(num_common_masses+num_other_masses)*((num_other_masses*f1)+(num_common_masses*f2)))
        except:
            print('match failure- probable divide by zero')
            retval = 0
        return retval 


    def match_factor(self,other_ms):
        common_masses = self.common_masses(other_ms)
        num_common_masses = len(common_masses)
        num_other_masses = other_ms.num_filtered_masses
        try:
            f1 = self.f_1(other_ms)
            f2 = self.f_2(other_ms)
            retval = int(1000/(num_common_masses+num_other_masses)*((num_other_masses*f1)+(num_common_masses*f2)))
        except:
            print('match failure- probable divide by zero')
            retval = 0
        return retval 
'''        
            
         
        
                    
    
        
        

         