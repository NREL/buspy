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
Created on Aug 10, 2015

@author: thansen

This is derived from an (currently) unlicensed discrete event simulator used for

Timothy M. Hansen, Edwin K. P. Chong, Siddharth Suryanarayanan, Anthony A. Maciejewski,
and Howard Jay Siegel, "A Partially Observable Markov Decision Process Approach to 
Residential Home Energy Management Systems," submitted to journal, 2015.
'''

###########################################################################
# EXCEPTIONS
###########################################################################
class EmptyQueue(Exception):
    pass

###########################################################################
# IMPORTS
###########################################################################
from heapq import heappush, heappop
from itertools import count
import numpy as np
import pandas as pd

###########################################################################
# CONSTANTS
###########################################################################
#priority levels
CRITICAL    =   0
URGENT      =   1
NORMAL      =   2
LOW         =   3
MINIMUM     =   4

###########################################################################
# UTILITY FUNCTIONS
###########################################################################

def diff_seconds_from_dates(date1,date2):
    '''
    Subtract date1 from date2, result in seconds
    '''
    return np.timedelta64(pd.to_datetime(date2) - pd.to_datetime(date1)).astype(float) / 1.0e6

def add_seconds_to_date(date, secs):
    return pd.to_datetime(date) + pd.to_timedelta('%f s' % secs)

###########################################################################
# EVENTS
###########################################################################

class Event(object):
    def __init__(self,simulator,priority=NORMAL):
        #common code and functionality here
        self.simulator = simulator
        self.priority = priority
        
    def execute(self):
        raise NotImplemented('Subclasses of Event must implement execute')
    
    def schedule(self,time,abs_time=False):
        self.env.schedule(self,time=time,abs_time=abs_time)


###########################################################################
# ControllerSimulator - discrete event simulator
###########################################################################

class ControllerSimulator(object):
    
    @property
    def current_time(self):
        '''Current datetime of the simulation'''
        return add_seconds_to_date(self.start_time,self.now)
    
    def __init__(self,start_time):
        self.now = 0
        self.eid = count()
        self.event_queue = []
        self.start_time = pd.to_datetime(start_time)
        
    def __schedule(self,event,time=0,abs_time=False):
        sch_time = time if abs_time else self.now + time
        if sch_time < self.now:
            raise Exception('Event must be scheduled at a time >= current simulation time')
        heappush(self.event_queue,(sch_time, event.priority, next(self.eid), event))
        
        
    def schedule(self,event,time=0,abs_time=False):
        if isinstance(time,int) or isinstance(time,float):
            self.__schedule(event,time,abs_time)
        else:
            #determine the time compared to the start time
            seconds = diff_seconds_from_dates(self.start_time,time)
            self.__schedule(event,time=seconds,abs_time=True)

    
    def step(self):
        """
        Process the next event in event_queue

        Raise EmptyQueue if no further events are available
        """
        event = self.pop_event()

        # Process callbacks of the event.
        event.execute()
        
    def pop_event(self):
        try:
            self.now, _1, _2, event = heappop(self.event_queue)
        except IndexError:
            raise EmptyQueue()

        return event
    
    def peek_event(self):
        try:
            event_time, _1, _2, event = self.event_queue[0]
        except IndexError:
            raise EmptyQueue()

        return event_time,event
    
    def get_seconds_from_start(self,date):
        return diff_seconds_from_dates(self.start_time,date)
    
    def print_statement(self,s):
        print '[%s]: %s' % (self.current_time,s)
        