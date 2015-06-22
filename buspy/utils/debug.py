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
Created on August 11, 2014

@author: Tim Hansen

debug.py

A debug thread class for logging debug output to a queue and/or a file.

'''

from threading import Thread
# Queue renamed to queue for Python 3
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty
from datetime import datetime
from time import clock
import atexit


DEBUG_ENUM = ['dFile','dConsole','dNone']


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class DebugThread(Thread):
    
    STOP_KEY = 'stop'   #no value needed, will stop the thread
    LOG_KEY  = 'log'    #string of data to log
    SAVE_KEY = 'save'   #boolean of whether to save the stream and log data
    QUEUE_KEY= 'queue'  #boolean of whether to queue the stream and log data
    PRINT_KEY= 'print'  #boolean of whether to print the stream and log data
    FNAME_KEY= 'filename' #string of the new filename
    
    def __init__(self,out=None,queue_output=True,save_output=True,print_output=False,output_filename='debug.log'):
        '''
        Parameters:
            @type out: stream-like object that has a readline function
            @param out: stream-like object that has a readline function
            
            @type queue_output: boolean
            @param queue_output: boolean determining whether or not to queue out (and logs) into stream_queue
            
            @type save_output: boolean
            @param save_output: boolean determining whether or not to save out (and logs) to output_filename
            
            @type save_output: boolean
            @param save_output: boolean determining whether or not to print out (and logs)
            
            @type output_filename: string
            @param output_filename: name of output file
        '''
        super(DebugThread,self).__init__()
        self.daemon = True
        atexit.register(DebugThread.__on_shutdown,self)
        
        #create queues.  stream_queue will 
        self.stream_queue = Queue()
        self.msg_queue = Queue()
        
        self._msg_handler = {
                             
            self.STOP_KEY    :   self.__stop,
            self.LOG_KEY     :   self.__log,
            self.SAVE_KEY    :   self.__save,
            self.QUEUE_KEY   :   self.__queue
                             
        }
        
        self._open = False
        self._out = out
        self.__out_queue = Queue()
        self.__save_output = save_output
        self.__out_fname = output_filename
        self.__queue_output = queue_output
        self.__print_output = print_output
        self.__continue = True
        self._file = None
        self.__start_clock = clock()
        
        
    def run(self):
        #open output file if we are going to be saving
        self.__save(self.__save_output)
        
        if self._out != None:
            t_out = Thread(target=enqueue_output, args=(self._out, self.__out_queue))
            t_out.daemon = True
            t_out.start()
        
        #non-blocking loop
        try:
            while(self.__continue):
                _ts = self.__timestamp()
                _log = []
                
                ##handle messages
                msg_dict = {}
                try:
                    msg_dict = self.msg_queue.get_nowait()
                except Empty:
                    pass
    
                for key in msg_dict:
                    _ = self._msg_handler[key](msg_dict[key])
                    if key == self.LOG_KEY:
                        _log.append(_)
                
                ##get stream data
                if self._out != None:
                    try:
                        _log.append(self.__out_queue.get_nowait())
                    except Empty:
                        pass
                
                for line in _log:
                    ##if queue, queue
                    if self.__queue_output:
                        self.stream_queue.put(line)
                    
                    ##if save, save
                    if self.__save_output:
                        self._file.write(_ts + line)
                    
                    ##if print, print
                    if self.__print_output:
                        print _ts + line
                      
                if self._open:
                    self._file.flush()
        except:
            pass
        
        #call shutdown on exit
        DebugThread.__on_shutdown(self)
    
    
    def __stop(self,val):
        self.__continue = False
        
    def __log(self,val):
        return str(val)
        
    def __save(self,val):
        '''
        Update __save_output to val, attempt to close current file, if __save_output is true, open new file and write date.
        '''
        self.__save_output = val
        
        try:
            self._open = False
            self._file.close()
        except:
            #do nothing
            pass
        
        if self.__save_output:
            self._file = open(self.__out_fname,'w')
            self._file.write('\n\n----------------------------------------------------\nDEBUG LOG STARTING AT ' + str(datetime.now()) + '\n----------------------------------------------------\n')
            self._file.flush()
            self._open = True
        
    def __queue(self,val):
        self.__queue_output = val
        
    def __print(self,val):
        self.__print_output = val
        
    @staticmethod
    def __on_shutdown(debug_thread):
        try:
            debug_thread._open = False
            debug_thread._file.close()
        except:
            #do nothing
            pass
        
        try:
            debug_thread._out.close()
        except:
            #do nothing
            pass
    
    def __timestamp(self):
        return '[%5.3f] : ' % (clock()-self.__start_clock)
    
class DebugBase(object):
    def __init__(self,*args,**kwargs):
        self._start_clock = clock()
        atexit.register(DebugFileNonthread._on_shutdown,self)
    
    def open(self):
        pass
    
    def write(self,*args,**kwargs):
        pass
    
    def close(self):
        pass
    
    def _timestamp(self,item=''):
        i = item if item == '' else '\t' + item
        return '[%5.3f%s] : ' % ((clock()-self._start_clock), i)
    
    @staticmethod
    def _on_shutdown(debug):
        try:
            debug.close()
        except:
            pass
    
class DebugFileNonthread(DebugBase):
    
    def __init__(self,print_output=False,output_filename='debug.log'):
        super(DebugFileNonthread,self).__init__()

        self._out_fname = output_filename
        self._print_output = print_output
        self._file = None
        
    
    def open(self):
        self._file = open(self._out_fname,'w')
        self._file.write('----------------------------------------------------\nDEBUG LOG STARTING AT ' + str(datetime.now()) + '\n----------------------------------------------------\n')
        self._flush()
    
    def write(self,s,label=''):
        _out = self._timestamp(label) + s
        
        if self._print_output:
            print _out
            
        self._file.write(_out + '\n')
        self._flush()
    
    def close(self):
        try:
            self._file.close()
        except:
            #do nothing
            pass
        
    def _flush(self):
        try:
            self._file.flush()
        except:
            pass
    
    
class DebugEmpty(DebugBase):
    
    def __init__(self,*args,**kwargs):
        pass
    
    def open(self):
        pass
    
    def write(self,*args,**kwargs):
        pass
    
    def close(self):
        pass
    
class DebugConsole(DebugBase):
    
    def __init__(self,*args,**kwargs):
        super(DebugConsole,self).__init__(*args,**kwargs)
    
    def open(self):
        pass
    
    def write(self,s,label=''):
        print self._timestamp(label) + s
    
    def close(self):
        pass
    
DEBUG_MAP = {
             
        DEBUG_ENUM[0]: DebugFileNonthread,
        DEBUG_ENUM[1]: DebugConsole,
        DEBUG_ENUM[2]: DebugEmpty
             
}
    
    
if __name__ == '__main__':
    import time
#     test = DebugThread(queue_output=False,print_output=True)
#     
#     test.start()
#     
#     test.msg_queue.put({test.LOG_KEY:'test log'})
#     time.sleep(5)
#     test.msg_queue.put({test.LOG_KEY:'test log 2'})
#     test.msg_queue.put({test.STOP_KEY:'None'})
    test = DebugFileNonthread(print_output=True)
    test.open()
    test.write('gobble-dee-gook', label='label1')
    time.sleep(5)
    test.write('gobble-dee-gookie', label='label1')
    test.write('bark', label='label2')
    test.close()
    