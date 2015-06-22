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
Created on August 6, 2014

@author: Tim Hansen

player.py

Load a GridLAB-D player file into Python memory.

Functions:
    player_to_timeseries(filename) - takes a .player file and returns a cpest.analyze.data.timeseries.TimeSeries

Requirements:
    pandas
    
To-Do List:

'''

######################################################################
# IMPORTS
######################################################################

import pandas as pd
from datetime import timedelta
from buspy.analyze.timeseries import TimeSeries


######################################################################
# CONSTANTS
######################################################################


######################################################################
# UTILITY FUNCTIONS
######################################################################

def _get_delta(t):
    '''
    Turns a delta string into a timedelta object
    '''
    
    #remove the + sign
    t = t.lstrip('+ ')
    
    #get the unit
    unit = t[len(t)-1]
    
    #remove the unit
    t = t.rstrip(unit)
    
    if unit == 's':
        return timedelta(seconds=int(t))
    elif unit == 'm': 
        return timedelta(minutes=int(t))
    elif unit == 'h': 
        return timedelta(hours=int(t))
    elif unit == 'd':
        return timedelta(days=int(t))
    else:
        raise Exception('Unknown unit: ' + unit)

def _is_delta(t):
    '''
    Checks if the time string is a delta or absolute
    '''
    return t[0] == '+'

def _get_time(t,cur_time):
    '''
    Returns the time from the given time object and current time
    '''
    t = t.strip()
    if _is_delta(t):
        return cur_time + _get_delta(t)
    else:
        return pd.to_datetime(t)
        
def _split_line(line):
    '''
    Splits the line at the comma.  Index 0 will have the time and 1 will have the value
    '''
    return line.rstrip('\r\n;,').split(',')

def _player_line_to_key_value(line,cur_time):
    '''
    Returns the time and value for the current line
    '''
    t, v = _split_line(line)
    
    return _get_time(t, cur_time), v

def player_to_timeseries(filename):
    '''
    Takes a .player file and returns a cpest.analyze.data.timeseries.TimeSeries
    '''
    #the list of time:value pairs to be converted to a time series
    times = []
    values = []
    
    #open the file
    with open(filename, 'r') as f:
        cur_time = None
        for line in f:
            cur_time, _v = _player_line_to_key_value(line,cur_time)
            times.append(cur_time)
            values.append(complex(_v))
    
    #convert the list of times into a datetime index for faster access
    return TimeSeries(values, index=pd.DatetimeIndex(times))

