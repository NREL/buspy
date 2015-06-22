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
Created on Feb 2, 2015

@author: thansen
'''

import os
import time
from contextlib import contextmanager

TIME_FORMAT = '%a %b %d %H:%M:%S %Y'

FILE_STR    =   '# file...... '
DATE_STR    =   '# date...... '
USER_STR    =   '# user...... '
HOST_STR    =   '# host...... '
TARG_STR    =   '# target.... '
TRIG_STR    =   '# trigger... '
INTR_STR    =   '# interval.. '
LIMT_STR    =   '# limit..... '

TIME_STR    =   '# timestamp'

def _header(filename,target,headers,interval='60',user='(null)',host='(null)',trigger='(none)',limit='(none)'):
    ret = []
    ret.append(FILE_STR + filename + '\n')
    ret.append(DATE_STR + time.strftime(TIME_FORMAT) + '\n')
    ret.append(USER_STR + user + '\n')
    ret.append(HOST_STR + host + '\n')
    ret.append(TARG_STR + target + '\n')
    ret.append(TRIG_STR + trigger + '\n')
    ret.append(INTR_STR + interval + '\n')
    ret.append(LIMT_STR + limit + '\n')
    h = TIME_STR
    for head in headers:
        h += (',%s' % head)
    ret.append(h + '\n')
    return ret

def _busmeter(name):
    return """
object triplex_meter {
    name %s;
}
    """ % name

class BusMeter(object):
    '''
    classdocs
    '''


    def __init__(self, filename, target, headings, folder='.', interval='60',user='(null)',host='(null)',trigger='(none)',limit='(none)'):
        '''
        Constructor
        
        headings - [list] strings of column headings
        '''

        #create folder
        if not os.path.exists(folder):
            os.mkdir(folder)
            
        #make glm file
        model_glm = os.path.join(folder, 'model.glm')
        with open(model_glm,'w') as output:
            output.write(_busmeter(filename.split('.')[0])) #remove extension, save meter
        
        #open meter
        self.file = open(os.path.join(folder,filename),'w')
        
        for header in _header(filename,target,headings,interval,user,host,trigger,limit):
            self.file.write(header)

            
        
    def write(self,time,values):
        '''
        time - time object that can be cast to a string
        values - list of values to write in the order of headings
        '''
        
        line = str(time)
        
        for v in values:
            line += (',%s' % str(v))
            
        self.file.write(line + '\n')
        self.file.flush() #write out content
            
            
    def close(self):
        self.file.close()
            

@contextmanager
def open_bus_meter(filename, target, headings, folder='.', interval='60',user='(null)',host='(null)',trigger='(none)',limit='(none)'):
    meter = BusMeter(filename, target, headings, folder, interval,user,host,trigger,limit)
    
    try:
        yield meter
    finally:
        meter.close()
    
    
    
    
        