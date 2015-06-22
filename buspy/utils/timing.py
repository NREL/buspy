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
Created on Apr 6, 2015

@author: thansen
'''

import time
import h5py

class TimerError(Exception):
    pass

class Timer(object):
    def __init__(self,timing_func=time.time,multiplier=1.0):
        self.timing_func = timing_func
        self.multiplier = multiplier
        self.times = []
        self.is_timing = False
    
    def start(self,restart=False):
        #throw error if the timer is already timing and restart is not specified.
        if self.is_timing and not restart:
            raise TimerError('timer is already running and restart was not specified.')
        
        self._start_time = self.timing_func()
        self.is_timing = True
        
    def stop(self):
        #get time now, do error checking after to be more accurate
        temp_time = self.timing_func()
        if not self.is_timing:
            raise TimerError('timer is not running, stop is undefined in this case.')
        
        self.times.append((temp_time - self._start_time) * self.multiplier)
        self.is_timing = False
        
    
    

class TimerCollection(object):
    '''
    Timer is used to hold a collection of timers associated with a key.  
    Each key points to a list of times for that timer.
    '''
    def __init__(self):
        self.timers = {}
    
    def add_timer(self,key,timing_func=time.time,multiplier=1.0):
        if key not in self.timers:
            self.timers[key] = Timer(timing_func,multiplier)
        else:
            raise KeyError('%s is already a timer' % key)
    
    def start_timer(self,key,restart=False):
        if key not in self.timers:
            raise KeyError('%s is not a timer' % key)
        
        try:
            self.timers[key].start(restart)
        except TimerError as e:
            raise TimerError('Error starting %s: %s' % (key,str(e)))
    
    def stop_timer(self,key):
        if key not in self.timers:
            raise KeyError('%s is not a timer' % key)
        
        try:
            self.timers[key].stop()
        except TimerError as e:
            raise TimerError('Error stopping %s: %s' % (key,str(e)))
    
    
    def to_hdf5(self,fname,access_flag='w'):
        with h5py.File(fname,access_flag) as f:
            for key,timer in self.timers.iteritems():
                f.create_dataset(key,data=timer.times)
    

class BlankTimerCollection(TimerCollection):
    '''
    Blank interface for a timer class
    '''
    def __init__(self):
        pass
    
    def add_timer(self,key):
        pass
    
    def start_timer(self,key):
        pass
    
    def stop_timer(self,key):
        pass
    
    def to_hdf5(self,fname):
        pass


if __name__ == '__main__':
    coll = TimerCollection()
    coll.add_timer('test1')
    coll.add_timer('test1_mult',multiplier=1e-6)
    coll.add_timer('test2')
    
    coll.start_timer('test2')
    for i in range(50):
        coll.start_timer('test1')
        coll.start_timer('test1_mult')
        total = 0.0
        for j in range(10000):
            total += j
        total /= 10000.0
        coll.stop_timer('test1')
        coll.stop_timer('test1_mult')
        
    coll.stop_timer('test2')
    
    coll.to_hdf5('test_time.h5')
    

