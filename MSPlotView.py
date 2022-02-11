'''
Created on Jun 7, 2018

@author: RobinWeber
'''
from MassSpectrum import MassSpectrum
#from MSLibRepSniffer_GUI_main import AppWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

class MSPlotView(object):
    '''
    classdocs
    '''


    def __init__(self, app, widget):
        '''
        Constructor
        '''
        self.app = app
        self.plotWid = widget
        self.ax = self.plotWid.axes
        #self.fig = widget.getFigure()
        #self.ax = self.fig.add_subplot(111)
        
    def plot_one_ms(self,ms):
        self.ax.clear()
        values = np.array(ms.get_values())
        values = (values/ms.tic)*100
        self.ax.bar(ms.get_masses(),values,1)
        self.plotWid.draw()
        
    def plot_two_ms(self,fromMS,toMS):
        self.ax.clear()
        self.ax.bar(toMS.get_masses(),toMS.get_values(),1)
        values = np.array(fromMS.get_values())
        values = values * -1
        self.ax.bar(fromMS.get_masses(),values,1)
        self.plotWid.draw()
        
        