'''
[LICENSE]
Copyright (c) 2015, Alliance for Sustainable Energy.
All rights reserved.

Redistribution and use in source and binary forms, 
with or without modification, are permitted provided 
that the following conditions are met:

1. Redistributions of source code must retain the above 
copyright notice, this list of conditions and the 
following disclaimer.

2. Redistributions in binary form must reproduce the 
above copyright notice, this list of conditions and the 
following disclaimer in the documentation and/or other 
materials provided with the distribution.

3. Neither the name of the copyright holder nor the 
names of its contributors may be used to endorse or 
promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

If you use this work or its derivatives for research publications, please cite:
Timothy M. Hansen, Bryan Palmintier, Siddharth Suryanarayanan, 
Anthony A. Maciejewski, and Howard Jay Siegel, "Bus.py: A GridLAB-D 
Communication Interface for Smart Distribution Grid Simulations," 
in IEEE PES General Meeting 2015, Denver, CO, July 2015, 5 pages.
[/LICENSE]
Created on June 9, 2014

@author: Tim Hansen

NREL CPES GridLAB-D datafile.  Holds all relevant information from the GridLAB-D output.

Classes:
    GridlabData

Functions:
    TODO

Requirements:
    Numpy
    
To-Do List:

'''

################################################################################################
#### IMPORTS
################################################################################################

import numpy as np
import pandas as pd

#############################################################################################################################
# CONSTANTS
#############################################################################################################################

UNITS_DICTIONARY  = {#'Y':  'years',
                     #'M':  'months',
                     'W':  'weeks',
                     'D':  'days',
                     'h':  'hours',
                     'm':  'minutes',
                     's':  'seconds',
                     'ms': 'milliseconds',
                     'us': 'microseconds',
                     'ns': 'nanoseconds',
                     'ps': 'picoseconds',
                     'fs': 'femtoseconds',
                     'as': 'attoseconds'}

#Gridlab Filetypes
_G_TARGET = 0
_G_GROUP_METER = 1
_G_GROUP_NODE = 2
_G_GROUP_ZIPLOAD = 3

#############################################################################################################################
# UTILITY FUNCTIONS
#############################################################################################################################

#returns a time delta object of the difference between t1 and t0
def _get_time_delta(t1,t0,units='s'):
    #overtyped because of a bug with the new pandas and datetimes.  Otherwise the division will create an exception. -TMH (2/20/15)
    return pd.to_timedelta(pd.to_datetime(t1)-pd.to_datetime(t0)) / pd.to_timedelta('1 %s' %units)

#units = 'D' (days), 'h' (hours), 'm' (minutes), 's' (seconds), 'ms' (millisecond), 'us' (microsecond), 'ns', 'ps', 'fs', 'as'.  also, 'Y' (years), 'M' (months), 'W' (weeks)
#offset=n - will offset the start time by n units
def _get_time_delta_asarray(array,units='s',offset=0):
    _ret = np.zeros(array.shape[0])
    
    _cur_time = offset
    _prev_date = array[0]
    for i, date in enumerate(array):
        _delta = _get_time_delta(date,_prev_date,units=units)
        _cur_time += _delta
        _ret[i] = _cur_time
        _prev_date = date
        
    return _ret

def _strip_prefix(string,prefix):
    return string.replace(prefix,'') #.lstrip(prefix), lstrip will take off prefix, but replace will also grab prefix in the middle such as in prefix_meter_n_prefix_load_n_strip_node.  this is probably slower, however

def _strip_prefix_asarray(array,prefix):
    _ret = np.array(array)
    
    for i,string in enumerate(_ret):
        #can't just assign to string as it is not a reference
        _ret[i] = _strip_prefix(string,prefix)
        
    return _ret

################################################################################################
#### CLASSES
################################################################################################

class GridlabData(object):
    '''
    TODO
    '''
    
    def __init__(self):
        '''
        Empty GridLAB-D datatype constructor.  
        
        self._filetype:
            _G_TARGET = 0
            _G_GROUP_METER = 1
            _G_GROUP_NODE = 2
            _G_GROUP_ZIPLOAD = 3
        
        Attributes:
            names - data column labels
            time - data row labels
            number - number of data columns
            data - M x N matrix of data values where M is time steps and N is self.number
            units - units for the columns.  use get_asset_unit(index) for access.
            groupid - holds different values for the different filetypes.  use the get methods for proper access.
        '''
        
        #attributes
        self.names = None
        self.time = None
        self.number = None
        self.data = None
        self.units = None #an Nx1 array of units for the N data columns
        self.groupid = None #only for ZIPloads
        self._filetype = None
         
        
    def get_time(self,units=None):
        '''
        get_time
        
        returns an array of the time.  If units are specified, the DateTime format will be
        converted to a double array of the proper time units.  
        
        Keyword Arguments:
            units - use the keys from UNITS_DICTIONARY to select a time scale
        '''
        if units != None:
            return _get_time_delta_asarray(self.time,units=units)
        else:
            return self.time
        
    def get_asset_name(self,index):
        '''
        The different filetypes have a different number of asset names.
        This function abstracts the access.
        '''
        
        return { 
                _G_TARGET : self.groupid,
                _G_GROUP_METER : self.names[index],
                _G_GROUP_NODE : self.names[index],
                _G_GROUP_ZIPLOAD : self.groupid
        }.get(self._filetype,'null')
        
    def get_asset_unit(self,index):
        '''
        The different filetypes have a different number of units.
        This function abstracts the access.
        '''
        
        return { 
                _G_TARGET : self.names[index],
                _G_GROUP_METER : self.groupid,
                _G_GROUP_NODE : self.groupid,
                _G_GROUP_ZIPLOAD : self.names[index]
        }.get(self._filetype,'null')
        
    
        