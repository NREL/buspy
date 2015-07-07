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
Created on July 10, 2014

@author: Tim Hansen

gridlabcomm.py

Conducts communication from bus.py to GridLAB-D instances.
Encodes bus.py common format to specific GridLAB-D format (e.g., http xml requests)
Decodes GridLAB-D specific format to bus.py common format

Classes:
    GridlabCommBase - contains all function definitions needed by bus.py (interface)
    GridlabCommHttp - implements GridlabCommBase using the http protocol
    GridlabCommFile - test class that writes in/out to files (DEPRECATED, DO NOT USE)
    GridlabCommMemory - test class that uses static IO from/to memory (DO NOT USE)

Functions:


Requirements:
    
To-Do List:

'''

######################################################################
# IMPORTS
######################################################################
from __future__ import print_function
import pandas as pd
import xml.etree.ElementTree as ET
import buspy.comm.message as message

#for GridLAB-D subprocess
import sys

#Use the new python3.2 version of subprocess that is better for multi-threaded. Only works on Linux
try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess
    print("WARNING Importing subprocess32 failed. Using subprocess which is known unstable for multi-threaded environments")

try:
    from Queue import Empty
except ImportError:
    from queue import Empty
from buspy.utils.debug import DebugThread

#for http connection to gridlab
import urllib
try:
    import httplib as http
    from httplib import CannotSendRequest
    from httplib import BadStatusLine
except ImportError:
    import http.client as http
    from http.client import CannotSendRequest
    from http.client import BadStatusLine

import os
import re
import cmath
import timeit
import time
import random

#socket stuff
from contextlib import contextmanager
import socket

#errors
from socket import error as socket_error
from xml.etree.ElementTree import ParseError as xml_parse_error

import atexit

from buspy.utils.debug import DebugEmpty

######################################################################
# CONSTANTS
######################################################################
GLD_DEFAULT_PORT = -1
GLD_DEFAULT_HOST = 'localhost'

ON_POSIX = 'posix' in sys.builtin_module_names
 
COMPLEX_REGEX_PATTERN = re.compile('([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)')        

######################################################################
# UTILITY FUNCTIONS
######################################################################
    
def complex_to_str(val):
    '''
    converts the complex number into either a complex-rectangular string
    '''
    return str(val.real) + ('+' if val.imag >= 0.0 else '') + str(val.imag) + 'j'

def str_to_complex(value_str):
    '''
    converts the rectangular or polar string into a complex number
    '''
    val_str = value_str.rstrip()
    
    #polar
    if val_str[-1]=='d':
        '''
        can probably find a better REGEX, but this works.  
        returns two two-tuples: first index has the whole number (including exponent), second is just exponent.  
        Second index is not needed in the tuple as the float cast parses it.  First tuple is the magnitude, second is the angle
        '''
        _mag, _ang = re.findall(COMPLEX_REGEX_PATTERN, val_str.rstrip('d'))
        
        _mag = float(_mag[0])
        _ang = float(_ang[0])
        
        return cmath.rect(_mag, _ang * (cmath.pi/180.0))
    
    #rectangular.  if it ends in 'i', replace with 'j' so casting to complex works
    elif val_str[-1]=='i':
        val_str = val_str.replace('i', 'j')
        
    return complex(val_str)
    
    
def find_open_tcp_port():
    '''
    Finds an open TCP port on the localhost.
    NOTE: this will not work if GridLAB-D is on another machine.
    '''
    @contextmanager
    def socketcontext(*args, **kw):
        s = socket.socket(*args, **kw)
        try:
            yield s
        finally:
            s.close()

    with socketcontext(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('',0))
        sock.listen(1)
        port = sock.getsockname()[1]
        
    return port

######################################################################
# CLASSES
######################################################################

###############################################################
# Comm Classes
###############################################################

#####################################################
# CommBase
#####################################################

class CommBase(object):
    '''
    CommBase - interface for all bus.py comm objects
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    def open(self):
        raise Exception('Subclasses of CommBase must implement open()')
    
    def close(self):
        raise Exception('Subclasses of CommBase must implement close()')
        
    
    def send(self,packet):
        '''
        Send packet over the comm
        '''
        raise Exception('Subclasses of CommBase must implement send(packet)')
    
    def recv(self):
        '''
        Blocking receive for a PacketBase object
        '''
        raise Exception('Subclasses of CommBase must implement recv()')
        
    @staticmethod
    def param_dict_itervalues(d):
        '''duplicated to avoid circular imports'''
        for params in d.itervalues():
            for param_obj in params.itervalues():
                yield param_obj


#####################################################
# GridlabCommBase
#####################################################

class GridlabCommBase(CommBase):
    '''
    '''
    
    #GLD command line arguments
    _GRIDLABD = 'gridlabd'
    PORT_FLAG = '-P'
    DEFINE_FLAG = '-D'
    VERBOSE_FLAG = '--verbose'
    SERVER_FLAG = '--server'
    QUIET_FLAG = '--quiet'
    
    def __init__(self,gld_init_pkt):
        '''
        Sets up the parameters for the GridlabCommBase object using the MessageCommonGridlabInit message received from the comm master
        '''
        if not isinstance(gld_init_pkt,message.MessageCommonGridlabInit):
            raise TypeError('GridlabCommBase objects must be initialized with a MessageCommInit object.')
        self._info = gld_init_pkt
        self.DEFAULT_PARAMS = {}
        
        self.debug = DebugEmpty()
        self.debug_label = ''
        self.gld_path = ''
        
        #TODO: if gld_init_pkt.folder != None, os.chdir(folder)
        
    def set_path(self,path):
        '''
        Sets the path to gridlabd. Useful if you do not want to use the default PATH.
        
        Default: first gridlabd in PATH
        '''
        self.gld_path = path
        
    def poll(self,time):
        '''
        returns true if GridLAB-D client is ready for next instructions
        '''
        raise Exception('Subclasses of GridlabCommBase need to implement poll(time)')
        
        
    '''------------------------------------------------------------------------
    GridLAB-D communication functions.
    ------------------------------------------------------------------------'''
    def send(self,params):
        '''
        Will set (CommonParam.name).(CommonParam.param) = CommonParam.value for each param in the MessageCommonData object.  If each is a list of length N, will set each obj[i].param[i] = val[i]
        
        If it is a global object, set CommonParam.param=None (i.e., CommonParam.name=CommonParam.value)
        '''
        raise Exception('Subclasses of GridlabCommBase need to implement send(params)')
        
    def recv(self):
        '''
        Will return the set of parameters from the input packet gld_out as a MessageCommonData object
        '''
        raise Exception('Subclasses of GridlabCommBase need to implement recv')
        
    def run_to_time(self,time):
        '''
        Will run the GridLAB-D instance to CommonGridlabTimeInfo.current_time
        '''
        raise Exception('Subclasses of GridlabCommBase need to implement run_to_time(time)')
        
    def shutdown(self,resume=False):
        '''
        Shuts down the instance of GridLAB-D.
        
        resume - True => resume the GridLAB-D instance (i.e., stop controlling execution) and let run to completion
               - False=> immediately shut down the GridLAB-D instance using the "shutdown" command.  WARNING: May not output to files properly.
        '''
        raise Exception('Subclasses of GridlabCommBase need to implement shutdown(resume)')
    
    #takes a dictionary in the form {arg:param} and converts it to a list (to be called by subprocess)
    def dict_to_args(self,d):
        ret = []
        
        for key in d:
            ret.append(key)
    
            val = d[key]
            if val != None:
                ret.append(str(val))
                
        return ret
    
    #creates the gridlab command line call with the specified model and arguments (*args takes a dict_to_args)
    def gridlabd_cmd_args(self,model,*args):
        #new: set gridlabd path (5/28/15) -TMH
        ret = [os.path.join(self.gld_path, self._GRIDLABD),str(model)]
        
        for arg in args:
            ret.append(arg)

        return ret
        
    
#####################################################
# GridlabCommHttp
#####################################################

class GridlabHttpControlStrings:
    #use the functions to get these encoded properly
    _GLOBAL = 'xml/'
    _CONTROL = '/control'
    _PAUSEAT = '/pauseat='
    _RESUME = '/resume'
    _SHUTDOWN = '/shutdown'
    _CLOCK = 'clock'
    _VERBOSE = 'verbose'
    _QUIET = 'quiet'
    
    SERVER_START_STR = 'starting server'
    SERVER_START_STR_PAUSE = 'Pausing the server at'
    
    def _time_str(self,time,timezone=None):
        tz = timezone
        if tz == None or tz == '':
            tz = ''
        else:
            tz = ' ' + tz
            
        return str(time)+ tz
    
    def pauseat(self,time,timezone=None):
        return urllib.quote(self._CONTROL+self._PAUSEAT+self._time_str(time, timezone),safe=':/=')
    
    def clock(self):
        return self._GLOBAL + self._CLOCK
    
    def resume(self):
        return self._CONTROL + self._RESUME
    
    def shutdown(self):
        return self._CONTROL + self._SHUTDOWN
    
    def verbose(self):
        return self._GLOBAL + self._VERBOSE
    
    def quiet(self):
        return self._GLOBAL + self._QUIET
    
    def obj_to_str(self,obj,param=None,val=None,unit=None):
        ret = '/' + obj 
        if param != None:
            ret += '/' + param
        if val != None:
            ret += '=' + val
        if unit != None:
            ret += ' ' + unit
        return urllib.quote(ret,safe=':/=+')
    
    def xml_to_valstr(self,txt):
        try:
            xml = ET.fromstring(txt).find('value').text
        except xml_parse_error:
            xml = ''  
        return xml
    
    def im_to_str(self,im):
        return str(im).lstrip('(').rstrip(')')

class GridlabCommHttp(GridlabCommBase):
    '''
    '''
    
    def __init__(self,gld_init_pkt):
        '''
        
        '''
        super(GridlabCommHttp,self).__init__(gld_init_pkt)
        self._control = GridlabHttpControlStrings()
        self.DEFAULT_PARAMS[self.SERVER_FLAG] = None
        self.DEFAULT_PARAMS[self.VERBOSE_FLAG] = None
        
        #connection to gridlab.  will be initialized in .open()
        self.connection = None
        self._gld_instance = None
        self.connected = False
        
        self.GLD_START_TIMEOUT = 60 #sec
        self.GLD_START_CHECK_DELAY = 0.1 #sec
        self.GLD_START_RETRYS = 10
        self.GLD_START_LOOP_PAUSE = 1 #sec
        
        atexit.register(GridlabCommHttp._cleanup,self)
    
    def get_clock(self, write_log=True):
        #gets the current GridLAB-D clock. 
        return pd.to_datetime(self._get_object(self._control.clock(), param=None, write_log=write_log))
    
    def poll(self,time):
        #check if the current gridlab clock is equal to the time
        return self.get_clock() >= time.current_time
    
    #TODO: gld open timeout?
    def open(self,gld_serv_pause=False,gld_path=''):
        '''
        Open a subprocess of gridlabd, wait for the server to start, and open a connection
        
        gld_serv_pause - True if using a version of GridLAB-D that pauses after starting the server (more robust)
        gld_path - path to the gridlabd instance. Defaults to first gridlabd in PATH
        '''
        self.connected = False
        
        '''
        create GridLAB-D argument list
        '''
        arg_list = self.DEFAULT_PARAMS
        
        #add a command to GLD command line to pause at the start time of the simulation
        arg_list[self.DEFINE_FLAG] = self._control._PAUSEAT.lstrip('/') + '\"' + self._control._time_str(self._info.time_info.start_time, self._info.time_info.timezone) + '\"'
        
        if self._info.host == None:
            self._info.host = GLD_DEFAULT_HOST
        
        if self._info.port == None:
            self._info.port = GLD_DEFAULT_PORT
        
        #add additional gridlab arguments from the initialization packet into the arg_list dict.  This will overwrite any defaults.
        if (self._info.gld_args is not None) and len(self._info.gld_args) != 0:
            for key in self._info.gld_args:
                arg_list[key] = self._info.gld_args[key]
        
        '''
        open GridLAB-D subprocess
        '''
        
        #change directory if one is provided
        _cwd = os.path.abspath(os.path.curdir)

        if self._info.folder != None:
            os.chdir(self._info.folder)
        
        #Loop until gridlab starts or max retrys is reached
        is_gld_started = False
        for gld_start_try in xrange(self.GLD_START_RETRYS):
            self.gld_stdout_file = open('stdout', 'w+')
            self.gld_stderr_file = open('stderr', 'w+')
        
            if (self._info.port == GLD_DEFAULT_PORT) or (gld_start_try > 0):
                #if the port is -1 or if we failed last time, try a random port
                self._info.port = random.randrange(25000,60000) #new range to not-overlap with global port option in IGMS tool
            arg_list[self.PORT_FLAG] = str(self._info.port)
        
            gld_open_str = self.gridlabd_cmd_args(self._info.filename,*self.dict_to_args(arg_list))

            start_string = 'starting GridLAB-D (try %d/%d): %s'%(gld_start_try+1,self.GLD_START_RETRYS, gld_open_str)
            self.debug.write(start_string, self.debug_label)
            
            try:    
                self._gld_instance = subprocess.Popen(gld_open_str,shell=False,stderr=self.gld_stderr_file,stdout=self.gld_stdout_file,bufsize=1,close_fds=ON_POSIX)
            except Exception as e:
                print("%s: Uh Oh, Gld Popen problem (try %d)"%(socket.gethostname(),gld_start_try+1))
                self.debug.write("  Uh Oh, there was a problem 'Popen'ing gridlabd: %s (%s)"%(sys.exc_info()[0],str(e)), self.debug_label)
                time.sleep(random.uniform(0.1,2.0))
                continue
            self.debug.write("  Popen complete", self.debug_label)
            
            #Give GridLAB-D a little time to start-up    
            time.sleep(self.GLD_START_CHECK_DELAY)
            
            #Make sure gridlabd is actually running
            self._gld_instance.poll()
            if self._gld_instance.returncode is not None:
                print("%s: Ack! Gld immediate exit wth code %d (try %d)"%(socket.gethostname(), self._gld_instance.returncode,gld_start_try+1))
                self.debug.write("  Ack, where did you go? Gridlab immediately exited with code %d"%(self._gld_instance.returncode), self.debug_label)
                time.sleep(random.uniform(0.1,2.0))
                continue
            self.debug.write("  Started", self.debug_label)
            self.debug.write('  Gridlab: pid=%s port=%d'%(self._gld_instance.pid,self._info.port), self.debug_label)
                
            '''
            Open TCP connection with GridLAB-D
            '''
            #open connection   
            self.debug.write('Opening HTTP connection to ' + str(self._info.host) + ':' + str(self._info.port), self.debug_label)
    
            #wait until gridlab responds over http. 
            end_time = timeit.default_timer() + self.GLD_START_TIMEOUT
            poll_count = 0
            self.debug.write('  Starting poll loop', self.debug_label)
            is_gld_started=False
        
            while(timeit.default_timer() < end_time):
                poll_count +=1
                #TODO: retries for the HTTP connection

                self.connection = http.HTTPConnection(self._info.host,self._info.port)
                gld_time=self.get_clock(write_log=True)
                self.debug.write('  Current GridLAB-D time is %s'%(gld_time), self.debug_label)                    
                if str(gld_time) != "NaT":                
                    is_gld_started = True
                    self.debug.write('  Success! GridLAB-D server started after ~%gsec (loop #%d)'%(
                        self.GLD_START_LOOP_PAUSE*poll_count,poll_count), self.debug_label)                    
                    self.debug.write('  Current GridLAB-D time is %s'%(gld_time), self.debug_label)                    
                    break
                
                time.sleep(self.GLD_START_LOOP_PAUSE)     #Pause in seconds

            if is_gld_started:
                break
            else:
                self.debug.write('  Shoot, GridLAB-D server not started after ~%gsec (loop #%d)'%(
                        self.GLD_START_LOOP_PAUSE*poll_count,poll_count), self.debug_label)                 
                #If not started, need to exit the process cleanly
                print("%s: Kill Gld and restart (try #%d)"%(socket.gethostname(), gld_start_try+1))
                self.debug.write('  Timeout: Killing Process', self.debug_label)
                self._gld_instance.kill()
                time.sleep(self.GLD_START_LOOP_PAUSE*random.uniform(5,10)) 
        #turn off verbosity
        self._set_object(self._control.verbose(), None, 'FALSE')
        if not self.debug:
            self._set_object(self._control.quiet(), None, 'TRUE')
        if is_gld_started:
            self.connected = True
        else:
            no_start_string = '%s: WARNING: Unable to start and communicate with GridLAB-D (folder=%s)'%(socket.gethostname(), self._info.folder)
            self.debug.write(no_start_string, self.debug_label)
            print(no_start_string)
        
        #change back to the original directory
        os.chdir(_cwd)
        
        return self.connected
        
    
    def close(self):
        '''
        Close the http connection
        '''
        try:
            self.connection.close()
            self.connected = False
        except:
            pass
    
    def send(self,params):
        '''
        Will set (CommonParam.name).(CommonParam.param) = CommonParam.value for each param in the MessageCommonData object.  If each is a list of length N, will set each obj[i].param[i] = val[i]
        
        If it is a global object, set CommonParam.param=None (i.e., CommonParam.name=CommonParam.value)
        '''
        
        for param in params.itervalues():
            #try to change from complex to a complex string
            _val = str(param.value).lstrip('(').rstrip(')')
            self._set_object(param.name, param.param, _val, param.unit)
        
    def recv(self,outputs=None):
        '''
        Will return the set of parameters from the input packet gld_out as a MessageCommonData object
        '''
        _out = self._info.gld_out if outputs == None else outputs.gld_io
        
        ret = message.MessageCommonData()
        
        #do not have to receive anything
        if _out != None:
            for param in self.param_dict_itervalues(_out):
                _p = message.CommonParam()
                _p.fmt = param.fmt
                _p.name = param.name
                _p.param = param.param
                
                #TODO: formats (e.g., complex)
                __val = self._get_object(param.name, param.param)
    
                #try to get the unit if there is one
                _p.value, _p.unit = GridlabCommHttp._split_val_and_unit(__val,self.debug,self.debug_label)
                
                ret.add_param(_p)
            ret.time = self._info.time_info
            
        return ret
        
    def run_to_time(self,time,timezone=''):
        '''
        Will run the GridLAB-D instance to CommonGridlabTimeInfo.current_time
        '''
        self._gridlab_comm(self._control.pauseat(time, timezone),xml=False)
        
    def shutdown(self,resume=False):
        '''
        Shuts down the instance of GridLAB-D.
        
        resume - True => resume the GridLAB-D instance (i.e., stop controlling execution) and let run to completion
               - False=> immediately shut down the GridLAB-D instance using the "shutdown" command.  WARNING: May not output to files properly.
        '''
        if resume:
            msg = self._control.resume()
        else:
            msg = self._control.shutdown()
        self._gridlab_comm(msg, xml=False)
        self._gld_instance.wait()
    
    def _gridlab_comm(self,msg,xml=True,write_log=True):
        try:
            if write_log:
                self.debug.write('[RAW SEND]: ' + str(msg), self.debug_label)
            self.connection.request('GET', msg)
            out = self.connection.getresponse().read()
            if write_log:
                self.debug.write('[RAW RECV]: ' + str(out), self.debug_label)
        except socket_error as e:
            if write_log:
                self.debug.write('WARNING: GridLAB-D Socket closed: ' + e.strerror, self.debug_label)
            out = ''
            self.connected = False
        except CannotSendRequest as err:
            if write_log:
                self.debug.write('WARNING: GridLAB-D Comm error: CannotSendRequest ' + str(err), self.debug_label)
            out = ''
            self.connected = False
        except BadStatusLine as err:
            if write_log:
                self.debug.write('WARNING: GridLAB-D Comm error: BadStatusLine (' + str(err.line) + ') ' + str(err), self.debug_label)
            out = ''
            self.connected = False
        except Exception as e:
            if write_log:
                self.debug.write('WARNING: GridLAB-D Comm error: exception type ' + e.__class__.__name__, self.debug_label)
            out = ''
            self.connected = False
        
        if xml:
            return self._control.xml_to_valstr(out)
        else:
            return out
    
    def _set_object(self,obj,param,val,unit=None):
        self._gridlab_comm(self._control.obj_to_str(obj,param,val,unit),xml=False)
    
    def _get_object(self,obj,param,write_log=True):
        return self._gridlab_comm(self._control.obj_to_str(obj,param),write_log=write_log)
    
    @staticmethod
    def _split_val_and_unit(s,debug=DebugEmpty(),debug_label=''):
        '''
        Split the value and unit of the gridlabd parameter.
        
        Note: Do not call this with the clock string as it will most likely ruin the clock format
        '''
        
        #only split on the last space
        _split = s.rsplit(' ',1)
        
        #if there was a space, assume index 0 is the value, index 1 is the unit
        if len(_split) == 2:
            _unit = _split[1]
            _value = _split[0]
        else:
            _value = s
            _unit = None
            
        try:
            _value = str_to_complex(_value)
        except:
            debug.write('Warning: unable to convert from a string to a complex value. (' + str(_value) + ')', debug_label)
        
        return (_value,_unit)
    
    def __check_connection(self):
        if self.connection == None or not self.connected:
            raise Exception('GridLAB-D connection not open.')
    
    @staticmethod
    def _cleanup(gld_comm_http):
        try:
            gld_comm_http._gld_instance.kill()
            gld_comm_http.debug.write('Killing GridLAB-D instance on exit.', gld_comm_http.debug_label)
        except:
            try:
                gld_comm_http.debug.write('GridLAB-D already closed', gld_comm_http.debug_label)
            except ValueError:
                pass

    
