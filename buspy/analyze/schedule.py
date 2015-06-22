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

timeseries.py

Contains a GridLAB-D schedule datatype.


Requirements:

    
To-Do List:
    TODO: implement the schedule (copy functionality from core/schedule.c or tape/schedule.cpp)
    TODO: load schedule from a schedule .glm file
    TODO: implement __getitem__ from a pd.datetime index
'''

######################################################################
# IMPORTS
######################################################################

import pandas as pd


######################################################################
# CLASSES
######################################################################

class Schedule(object):
    
    def __getitem__(self,index):
        #make sure the index is a pd.datetime or a string that can be converted to a pd.datetime
        _i = index
        if not (isinstance(index,pd.datetime) or isinstance(index,pd.DatetimeIndex)):
            try:
                _i = pd.to_datetime(index)
            except:
                raise Exception('invalid index to Schedule.  Schedule[index] takes a pd.datetime, pd.DateTimeIndex, or a string that can be converted to a pd.datetime')
            
        #TODO: get the correct value from the time specified by _i
        
    def __init__(self):
        #TODO: how to instantiate
        pass

if __name__ == '__main__':
    test = Schedule()
    
    