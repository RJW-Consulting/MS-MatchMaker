'''
Created on May 24, 2018

Main routine for MSLibrary code for detecting replicate mass spectra
@author: RobinWeber
'''

if __name__ == '__main__':
    pass

import argparse as ap
import numpy as np
import pandas as pd
from MassSpectrum import MassSpectrum
from MSLibrary import MSLibrary


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
    
    
    




