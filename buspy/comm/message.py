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
Created on Jul 10, 2014

@author: thansen

comm.py

Base communication interface.

Classes:
    CommBase - base interface for bus.py IO
    MessageBase - base class for packet messages (packet.message) to inherit

    
To-Do List:

'''

######################################################################
# IMPORTS
######################################################################
import pandas as pd
from datetime import timedelta

######################################################################
# UTILITY FUNCTIONS
######################################################################


######################################################################
# CLASSES
######################################################################

###############################################################
# GRIDLAB PARAMETERS
###############################################################
    
#####################################################
# CommonParamFormat
#####################################################

class CommonParamFormat(object):
    REAL            =   0
    INT             =   1
    STRING          =   2
    COMPLEX         =   3
    
    STR_REAL        = 'real'
    STR_INT         = 'int' 
    STR_STRING      = 'str'   
    STR_COMPLEX     = 'complex'
    
    conversion_dict = {
            STR_REAL        : REAL,
            STR_INT         : INT,
            STR_STRING      : STRING,  
            STR_COMPLEX     : COMPLEX              
    }
    
    unconversion_dict = {
            REAL          : STR_REAL,
            INT           : STR_INT,
            STRING        : STR_STRING,  
            COMPLEX       : STR_COMPLEX  
    }
    
#####################################################
# CommonParam
#####################################################

class CommonParam(object):
    #fmt property
    __format = None
    def __format_getter(self):
        return self.__format
    def __format_setter(self,value):
        if value not in CommonParamFormat.unconversion_dict.keys():
            self.__format = CommonParamFormat.conversion_dict.setdefault(value,None)
        else:
            self.__format = value
    fmt = property(__format_getter,__format_setter)
    
    def __init__(self, name=None, param=None, fmt=None, unit=None, value=None):
        '''
        Initializes a GridlabParam object that can be sent to/received from gridlab comm.
        
        Attributes:
            name     - name of the object (e.g., 'node1')
            param    - name of the parameter within the object.  Note: if the parameter is global (e.g., 'clock') then this can be set to None
            fmt   - fmt of the parameter (e.g., 'polar')
            unit     - unit of the parameter (in formats accepted by GridLAB-D).  If None, gridlab will assume this is the same as the unit they have for the variable
            value    - value of the parameter
            
        TODO: implement CommonParamFormat behavior here (currently only complex strings are handled in gridlabcomm)

        Formats:
            'real'    - real float
            'int'     - integer
            'string'  - string
            'complex' - complex float in rectangular fmt
        '''
        self.name   = name
        self.param  = param
        self.__format = CommonParamFormat.conversion_dict.setdefault(fmt,None)
        self.unit   = unit
        self.value  = value
        
    def copy(self):
        ret = CommonParam()
        ret.name   = self.name
        ret.param  = self.param
        ret.format = self.__format
        ret.unit   = self.unit
        ret.value  = self.value
        return ret
    
    def __eq__(self,other):
        '''
        NOTE: This is a check on the name and param only.  The value is not considered.
        '''
        if not isinstance(other,CommonParam):
            return NotImplemented
        
        return ((self.name == other.name) and (self.param == other.param))
    
    def __ne__(self,other):
        ret = self == other
        if ret is NotImplemented:
            return 
        else:
            return not ret

        
#####################################################
# CommonTimeInfo
#####################################################
        
class CommonTimeInfo(object):
    #start_time property.  when set, always call pd.to_datetime
    __start_time = None
    def __start_time_getter(self):
        return self.__start_time
    def __start_time_setter(self,value):
        self.__start_time = pd.to_datetime(value)
        if self.__current_time == None:
            self.__current_time = self.__start_time
    start_time = property(__start_time_getter,__start_time_setter)
        
    #end_time property.  when set, always call pd.to_datetime
    __end_time = None
    def __end_time_getter(self):
        return self.__end_time
    def __end_time_setter(self,value):
        self.__end_time = pd.to_datetime(value)
    end_time = property(__end_time_getter,__end_time_setter)
        
    #delta property.  when set, always call timedelta(seconds=value)
    __delta = None
    def __delta_getter(self):
        return self.__delta
    def __delta_setter(self,value):
        self.__delta = timedelta(seconds=value)
    delta = property(__delta_getter,__delta_setter)
    
    #current time property.  Read only
    __current_time = None
    def __current_time_getter(self):
        return self.__current_time
    def __current_time_setter(self,value):
        self.__current_time = pd.to_datetime(value)
    current_time = property(__current_time_getter,__current_time_setter)
    
    def __init__(self,start_time=None, end_time=None, timezone=None,delta=None):
        '''
        Initializes a GridlabTimeInfo object that will be used to keep track of the simulation time
        
        Attributes:
            start_time    - start time of the simulation. pandas.to_datetime compatible object (i.e., datetime string or pd.datetime)
            end_time      - end time of the simulation. pandas.to_datetime compatible object (i.e., datetime string or pd.datetime)
            timezone      - optional timezone string (e.g., 'EST')
            delta         - timestep of the simulation in seconds
        '''
        if start_time != None:
            self.__start_time = pd.to_datetime(start_time)
            self.__current_time = self.__start_time
            
        if end_time != None:
            self.__end_time = pd.to_datetime(end_time)
            
        self.timezone = timezone
        
        if delta != None:
            self.__delta = timedelta(seconds=delta)
            
    def advance_time(self):
        '''
        advances the current time by delta.
        
        Returns True if current time is less than end time, else false
        '''
        
        #is this the best way to set the current time? (also added to the start_time getter method)
        if self.__current_time == None:
            self.__current_time = self.__start_time
        self.__current_time += self.__delta
        
        if self.__current_time >= self.__end_time:
            if self.__current_time > self.__end_time:
                self.__current_time = self.__end_time
            return False
        else:
            return True
        
    def __str__(self):
        '''
        Returns a string representation of the current time and the time zone
        '''
        ret = str(self.__current_time)
        
        if self.timezone != None:
            ret += ' ' + self.timezone
            
        return ret

###############################################################
# MESSAGES
###############################################################

#####################################################
# MessageBase
#####################################################

class MessageBase(object):
    '''
    Base class for message encodings for bus.py
    '''
    
    def __init__(self):
        pass
    
class MessageCommonBase(MessageBase):
    pass
    
class MessageCommonGridlabInit(MessageCommonBase):
    def __init__(self):
        '''
        Initialize a default CFF init packet
        
        Attributes:
            filename    - .glm filename
            host        - gridlabd hostname
            port        - gridlabd port
            time_info   - CommonTimeInfo object describing the simulation timesteps
            gld_in      - list of CommonParam objects describing the parameters that the master sends to gridlabd at each timestep
            gld_out     - list of CommonParam objects describing the parameters that the master receives from gridlabd at each timestep
            gld_args    - dict of additional gridlabd command line arguments in the form of {flag : value} pairs (e.g., {'-P':'6267','--server':None})
        '''
        self.filename = None
        self.folder = None
        self.host = None
        self.port = None
        self.time_info = CommonTimeInfo()
        self.gld_out = {}
        self.gld_args = {}
        
class MessageCommonData(MessageCommonBase):
    def __init__(self):
        '''
        gld_io - list of CommonParam objects
        time - time to run to.  If None, will use the current time from the initialization packet
        '''
        self.gld_io = {}
        self.time = None
        
    def add_param(self,common_param):
        self.gld_io.setdefault(common_param.name,{})[common_param.param] = common_param
        
    def get_param(self,name,param):
        return self.gld_io[name][param]
    
    def itervalues(self):
        for params in self.gld_io.itervalues():
            for param_obj in params.itervalues():
                yield param_obj
        
    def __getitem__(self,key):
        return self.gld_io[key]