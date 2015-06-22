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

bus.py

The interface between the GridLAB-D aggregator and an arbitrary feeder load.
bus.py will take time-series data from the aggregator, input the data to the
arbitrary feeder, and return the feeder output to the aggregator.   

bus.py will contain a set of implemented feeders/substations/etc. implementing 
an interface with the following functions and attributes:

Functions:
    open_bus - Context Manager for use in a 'with' statement.  Takes a JSON filename and returns a Bus object.  
               This will start and stop the bus object automatically in the course of the 'with' statement.
               

Bus Implementations:
    Bus            - base class that defines the interface
    GridlabBus     - GridLAB-D bus interface
    FileBus        - file-based bus interface 
    ConstantBus    - constant bus interface 
    ResistorBus    - resistance-based bus interface (NOT YET FULLY IMPLEMENTED)
    MultiNodeBus   - substation-like bus interface
    
Usage:
    #Option #1
    from bus import load_bus
    
    bus = load_bus($PATH_BUT_NOT_FILENAME_TO_bus.json)
    bus.start_bus() 
    
    
    #Option #2
    from bus import open_bus
    
    with open_bus(json_filename) as bus:
        # do stuff with bus
        # e.g., 
        out = bus.transaction(in_packet)


Requirements:
    
    
To-Do List:
    TODO: implement a resistance-based version of the interface
'''

######################################################################
# IMPORTS
######################################################################

from contextlib import contextmanager
from buspy.construct.bus_params import BusParams
from buspy.construct.bus_params import GridlabBusParams
from buspy.construct.bus_params import FileBusParams
from buspy.construct.bus_params import ConstantBusParams
from buspy.construct.bus_params import ResistorBusParams
from buspy.construct.bus_params import MultiNodeBusParams
import buspy.comm.message as message

from buspy.analyze.loaders.player import player_to_timeseries

import buspy.utils.action as action
import os
import numpy as np
import json
import shutil
import sys

import logging

from buspy.comm.gridlabcomm import GridlabCommHttp 
from time import sleep
from copy import deepcopy

from buspy.utils.debug import DebugEmpty
from buspy.utils.debug import DEBUG_MAP

import socket   #for hostname ID

######################################################################
# CONSTANTS
######################################################################

VOLTAGE_CONVERSION_A = np.cos(120.0 * np.pi/180.0) + np.sin(120.0 * np.pi/180.0) * 1j

VOLTAGE_CONVERSION_A_SQUARED = np.square(VOLTAGE_CONVERSION_A)

DEFAULT_BUS_FILENAME = 'bus.json'
DEFAULT_BUS_DEBUG    = 'bus.debug'

DEFAULT_DEBUG = DebugEmpty()


######################################################################
# CONSTANTS
######################################################################

GLOBAL_DEFAULT_BUS_TYPE = None
GLOBAL_DEFAULT_BUS_INIT = None

def set_default_bus(bus_type,json_init):
    global GLOBAL_DEFAULT_BUS_TYPE 
    global GLOBAL_DEFAULT_BUS_INIT
    
    GLOBAL_DEFAULT_BUS_TYPE = bus_type
    GLOBAL_DEFAULT_BUS_INIT = json_init

######################################################################
# UTILITY FUNCTIONS
######################################################################

def positive_sequence_to_phase(pos_seq_volt):
    #NOTE: only true if the phases are balanced
    return (pos_seq_volt,pos_seq_volt*VOLTAGE_CONVERSION_A_SQUARED,pos_seq_volt*VOLTAGE_CONVERSION_A)

def get_bus_from_classname(params):
    return globals()[params[BusParams.BUS_KEY]](params)

def load_bus(path,fname=DEFAULT_BUS_FILENAME,debug=DEFAULT_DEBUG):
    loader = BusLoader(path, fname, path_params_to_absolute = True)
    return loader.bus

@contextmanager
def open_bus(json_filename):
    '''
    For use in a 'with' statement.
    
    E.g.,:
        with open_bus(json_filename) as bus:
            bus.transaction( ... )
            ...
            
    Parameters:
        bus - an initialized Bus (constructor called with the proper initialization packet)
    '''
    loader = BusLoader(json_filename)
    bus = loader.bus
    bus.start_bus()
    try:
        yield bus
    finally:
        bus.stop_bus()

######################################################################
# CLASSES
######################################################################

class BusLoader(object):
    def __init__(self, 
                 bus_dir, 
                 bus_filename = DEFAULT_BUS_FILENAME, 
                 bus_params = None,
                 path_params_to_absolute = False):
        """
        Constructor is robust to bus_dir actually being the json file
        to load. Raises a RuntimeError in the even that the bus_dir or
        the json file do not actually exist.
        """
        self.__dir = None
        self.__filename = None
        self.__params = None
        self.__bus_type = None
        self.__bus = None        
        self.path_params_to_absolute = path_params_to_absolute
        
        # params already loaded
        if bus_params is not None:
            if isinstance(bus_params, BusParams):
                self.__params = bus_params
                return
        
        # will be loading from file
        if os.path.isdir(bus_dir):
            self.__dir = bus_dir
            self.__filename = bus_filename
        elif os.path.isfile(bus_dir):
            self.__dir = os.path.dirname(bus_dir)
            self.__filename = os.path.basename(bus_dir)
        else:
            logging.warning("""The bus location '{}' does not exist. 
                Will return a default bus.""".format(bus_dir))
            
        if self.json_path is not None and not os.path.exists(self.json_path):
            self.__dir = None; self.__filename = None
            logging.warning("""No file exists at '{}'. Will return a default
                bus""".format(self.json_path))
            
    @property
    def dir(self):
        return self.__dir
        
    @property
    def filename(self):
        return self.__filename
            
    @property
    def json_path(self):
        return os.path.join(self.dir, self.filename) if self.dir is not None else None
        
    @property
    def params(self):
        if self.__params is None:
            if self.json_path is None:
                self.__params = GLOBAL_DEFAULT_BUS_INIT
            else:
                try:
                    self.__params = BusParams.load(self.json_path)
                    new_bus_folder = self.__update_bus_folder() if self.path_params_to_absolute else None
                    msg = "Loaded bus from {}".format(self.json_path)
                    if new_bus_folder is not None:
                        msg += " and set its folder to {}.".format(new_bus_folder)
                    else:
                        msg += "."
                    logging.info(msg)
                except Exception as e:
                    logging.warning('WARNING: could not load bus (' + self.json_path + '). Exception message: ' + str(e))
                    self.__params = None
        return self.__params
    
    @property
    def bus_type(self):
        if self.__bus_type is None:
            if self.params is not None:
                self.__bus_type = self.params.get_class_name()
        return self.__bus_type
        
    @property
    def bus(self):
        if self.__bus is None:
            if self.params is None:
                self.__bus = self.__fallback_bus()
            else:
                self.__bus = globals()[self.params[BusParams.BUS_KEY]](self.params)
        return self.__bus
        
    def __fallback_bus(self):
        if GLOBAL_DEFAULT_BUS_TYPE is None:
            return None
        return GLOBAL_DEFAULT_BUS_TYPE(GLOBAL_DEFAULT_BUS_INIT)
        
    def __update_bus_folder(self):
        new_bus_folder = None
        if self.dir is not None:
            if self.__params[BusParams.FOLDER_KEY] == None or \
               self.__params[BusParams.FOLDER_KEY] == '' or \
               self.__params[BusParams.FOLDER_KEY] == '.':
                self.__params[BusParams.FOLDER_KEY] = self.dir
                new_bus_folder = self.__params[BusParams.FOLDER_KEY]
            else:
                if os.path.isdir(os.path.join(dir, self.__params[BusParams.FOLDER_KEY])):
                    self.__params[BusParams.FOLDER_KEY] = os.path.join(dir, self.__params[BusParams.FOLDER_KEY])
                    new_bus_folder = self.__params[BusParams.FOLDER_KEY]
        return new_bus_folder
    


###############################################################
# Bus Types
###############################################################

##########################################################
# Bus
##########################################################

class Bus(object):
    '''
    The interface between the GridLAB-D aggregator and an arbitrary feeder load.
    bus.py will take time-series data from the aggregator, input the data to the
    arbitrary feeder, and return the feeder output to the aggregator.
    
    Attributes:
        time        - simulation time information
        outputs     - representation of the requested parameters
    '''
    
    TRANSACTION_INPUTS      = 0
    TRANSACTION_RUNTO       = 1
    TRANSACTION_RUNTO_POLL  = 2
    TRANSACTION_OUTPUTS     = 3
    TRANSACTION_ALL         = 4
    
    def __init__(self,json_file):
        '''
        __init__()
        
        Bus constructor.
        
        Throws:
            Exception
        '''
        #check to make sure this is an inherited class
        if self.__class__.__name__ == 'Bus':
            raise Exception('Bus is an interface and should not be instantiated')
 
        #common initialization
        self.params   = json_file
        
        self.folder   = Bus._json_to_obj(json_file,BusParams.FOLDER_KEY)
        self.bus_out  = self._json_param_list_to_common_dict(Bus._json_to_arr(json_file,BusParams.OUTPUT_KEY))
        self.sim_time = self.json_timeinfo_to_common(Bus._json_to_obj(json_file,BusParams.TIME_KEY))
        self.debug    = Bus._json_to_bool(json_file,BusParams.DEBUG_KEY)
        
        if self.debug: 
            self.debug_instance = DEBUG_MAP.setdefault(Bus._json_to_obj(json_file,BusParams.DEBUG_TYPE_KEY),DebugEmpty)(**Bus._json_to_dict(json_file,BusParams.DEBUG_ARGS_KEY))
        else:
            self.debug_instance = DEFAULT_DEBUG
        
        #will be set to true after end_time is reached
        self.finished = False
        
        self.__cwd = '.'
        
        #get the BusTranslator object
        _ = self._json_to_obj(json_file, MultiNodeBusParams.BUS_TRANSLATOR_KEY)
        self.bus_translator = globals()[_](json_file) if _ != None else BusTranslator(json_file)
        
    def set_path(self,path):
        '''
        May be overloaded by children.
        '''
        pass
    
    def start_bus(self):
        '''
        start_bus()
        
        Starts the bus process.  All initialization of the Bus object should be compete before this is called.
        
        Throws:
            Exception
        '''
        #Add node name info to debug file
        raise Exception('Bus objects should implement start_bus()')
    
    def stop_bus(self):
        '''
        stop_bus()
        
        Stops the bus process.
        
        Throws:
            Exception
        '''
        raise Exception('Bus objects should implement stop_bus()')
    
    def transaction(self,inputs=None,outputs=None,overwrite_output=False,trans_state=TRANSACTION_ALL):
        '''
        transaction(input)
        
        Takes a MessageCommonData object with a list of inputs and returns
        a MessageCommonData with either the specified output OR the output
        specified in the initialization packet.
        
        Parameters:
            inputs - MessageCommonData object with .gld_io being a list of inputs (CommonParam) to the bus
                    and .time being an optional CommonTimeInfo that will specify the next simulation time.
            
            outputs - (optional) MessageCommonData object specifying additional outputs (CommonParam) other than what was 
                     requested in the initialization
            
            overwrite_output - if True, the output parameter will replace the initialization output, else it will be appended
                     
        Returns:
            MessageCommonData - returns current time step in .time and the requested outputs (CommonParam) in .gld_io
        '''

        
        '''
        Send input to Bus
        Run to new time
        Receive, return outputs
        '''
        self._enter_folder()
        _out = None
        
        if (trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_INPUTS):
            if inputs != None:
                _trans_inputs = self.bus_translator.translate_input(inputs)
                
                #check for special inputs
                additional_inputs = []
                for param in _trans_inputs.itervalues():
                    if param.name == 'special':
                        additional_inputs.append(param)
                        
                for param in additional_inputs:
                    _trans_inputs.gld_io[param.name].pop(param.param)
                    for new_param in Bus.param_dict_itervalues(self.check_special(param)):
                        _trans_inputs.add_param(new_param)
                del additional_inputs
                
                for param in _trans_inputs.itervalues():
                    self.debug_instance.write('[SEND]: ' + str(_trans_inputs.time) + '\t' + str(param.name) + '.' + str(param.param) + ' = ' + str(param.value), self.folder)
                
                #send the new inputs, advance to our sim_time to the next time step, and run to said time step
                self._local_bus_send(_trans_inputs)
                
                self._local_advance_time(_trans_inputs.time)
            else:
                self._local_advance_time(time=None)
        
        if (trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_RUNTO):
            self._local_bus_runto(self.sim_time)
            
        if (trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_RUNTO_POLL):
            self._local_bus_runto_poll(self.sim_time)
            
        if (trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_OUTPUTS):
            _out_params = self._get_outputs(outputs, overwrite_output)
            _out = self.bus_translator.translate_output(self._local_bus_recv(_out_params))
        
        self._leave_folder()
        
        return _out
    
    def get_time(self):
        return self.sim_time.current_time
    
    
    def _local_bus_send(self,inputs):
        '''
        _local_bus_send(inputs)
        
        Local send function.  Subclasses need to implement this.
        '''
        raise Exception('Bus objects should implement _local_bus_send()')  
      
    
    def _local_bus_runto(self,time=None):
        '''
        _local_bus_runto(time)
        
        Local 'run to' function.  Subclasses need to implement this.  returns (True if continue, False if finished)
        '''
        raise Exception('Bus objects should implement _local_bus_runto()')  
    
    def _local_bus_runto_poll(self,time=None):
        pass  
    
    def _local_bus_recv(self,outputs):
        '''
        _local_bus_recv(outputs)
        
        Local receive function.  Subclasses need to implement this.
        '''
        raise Exception('Bus objects should implement _local_bus_recv()')    
    
    def _local_advance_time(self,time):
        '''
        advance time in the simulation by either (a) using the provided timestep, or (b) advancing our current kept time
        '''
        if time != None: #check input for the .time, update our current time, and run to that time instead
            #do some error checking, such as new time > current time, new time <= end time

            if not (time.current_time > self.sim_time.current_time):
                self.debug_instance.write('WARNING: Provided time is not greater than the current time: ' + str(time) + ' <= ' + str(self.sim_time), self.folder)
                
            if time.current_time > self.sim_time.end_time:
                self.debug_instance.write('WARNING: Provided time is greater than the end time, setting next time step to simulation end.', self.folder)
                self.sim_time.current_time = self.sim_time.end_time
            else:
                self.sim_time.current_time = time.current_time
            self.finished = self.sim_time.current_time >= self.sim_time.end_time
        else:
            self.finished = not self.sim_time.advance_time()
    
     
    _TEMPLATE_CLASS_KEY = 'template'
    @staticmethod
    def generate_template(filename,**kwargs):
        '''
        generate_template(filename)
         
        Generates a JSON-initialization-file template for the current Bus.
        '''
        kwargs.pop(Bus._TEMPLATE_CLASS_KEY,BusParams)().save_template(filename)
        
    '''
    Local functions
    '''
    @staticmethod
    def _json_to_obj(json_obj,json_obj_name):
        if json_obj_name not in json_obj:
            return None
        else:
            return json_obj[json_obj_name]
        
    @staticmethod
    def _json_to_bool(json_obj,json_obj_name,default=False):
        if json_obj_name not in json_obj:
            return default
        else:
            return json_obj[json_obj_name]
       
    @staticmethod 
    def _json_to_arr(json_obj,json_obj_name):
        ret = Bus._json_to_obj(json_obj,json_obj_name)
        if ret == None:
            ret = []
        return ret
    
    @staticmethod 
    def _json_to_dict(json_obj,json_obj_name):
        ret = Bus._json_to_obj(json_obj,json_obj_name)
        if ret == None:
            ret = {}
        return ret
        
    @staticmethod
    def param_dict_itervalues(d):
        '''duplicated to avoid circular imports'''
        for params in d.itervalues():
            for param_obj in params.itervalues():
                yield param_obj
                
    def _json_param_list_to_common_dict(self,params):
        ret = {}
        
        for io_param in params:
            param = self.json_param_to_common(io_param)
            ret.setdefault(param.name,{})[param.param] = param
            
        return ret
    
    def json_param_to_common(self,in_param):
        param = message.CommonParam()
        param.name      = Bus._json_to_obj(in_param, BusParams.IO_NAME_KEY)
        param.param     = Bus._json_to_obj(in_param, BusParams.IO_PARAM_KEY)
        param.unit      = Bus._json_to_obj(in_param, BusParams.IO_UNIT_KEY)
        param.value     = Bus._json_to_obj(in_param, BusParams.IO_VALUE_KEY)
        return param
    
    def json_timeinfo_to_common(self,t_info):
        if t_info != None:
            time_info = message.CommonTimeInfo()
            
            time_info.start_time    = Bus._json_to_obj(t_info, BusParams.TIME_START_KEY)
            time_info.end_time      = Bus._json_to_obj(t_info, BusParams.TIME_END_KEY)
            time_info.timezone      = Bus._json_to_obj(t_info, BusParams.TIME_ZONE_KEY)
            time_info.delta         = float(Bus._json_to_obj(t_info, BusParams.TIME_DELTA_KEY))
            
            return time_info
        return None
    
    def _enter_folder(self):
        self.__cwd = os.path.abspath(os.path.curdir)
        if self.folder != None:
            os.chdir(self.folder)
        
    def _leave_folder(self):
        if self.__cwd != None:
            os.chdir(self.__cwd)
        
    def check_special(self,param):
        ret = {}
        if param.param == 'positive_sequence_voltage':
            a, b, c = positive_sequence_to_phase(param.value)
            ret['network_node'] = {}
            ret['network_node']['voltage_A'] = message.CommonParam(name='network_node', param='voltage_A', value=a)
            ret['network_node']['voltage_B'] = message.CommonParam(name='network_node', param='voltage_B', value=b)
            ret['network_node']['voltage_C'] = message.CommonParam(name='network_node', param='voltage_C', value=c)
            
        return ret
    
    def _get_outputs(self,outputs,overwrite_output):
        if overwrite_output:
            _out = outputs
        else:
            _out = message.MessageCommonData()
            
            _out.gld_io = deepcopy(self.bus_out)
            
            if outputs != None:
                for o in outputs.itervalues():
                    _out.add_param(o)
                    
        _out.time = self.sim_time
                    
        return _out
            
##########################################################
# GridlabBus
##########################################################

class GridlabBus(Bus):
    '''
    The interface between the GridLAB-D aggregator and GridLAB-D.
    '''
    
    
    def __init__(self, json_file):
        super(GridlabBus,self).__init__(json_file)
        
        self._comm = None
        self._gld_initialized = False
        self.poll_time = self.params[GridlabBusParams.POLL_KEY]
        self.gld_path = ''
        
    def set_path(self,path):
        '''
        Sets the path to gridlabd to arg path. Default: first gridlabd in system PATH.
        '''
        self.gld_path = path
    
    '''
    Bus interface implementation
    '''
    def start_bus(self):
        '''
        start_bus()
        
        Starts a GridLAB-D instance.
        
        Throws:
            Exception
        '''
        self.debug_instance.open()
        #Add node name info to debug file
        self.debug_instance.write('Running on host %s with python pid %s'%(socket.gethostname(),os.getpid()), self.folder)
        #TODO: some switch for the GridlabComm object.  currently assuming HTTP   
        self._comm = GridlabCommHttp(self._to_cff_init())
        #set the gridlabd path (new: 5/28/15 -TMH)
        self._comm.set_path(self.gld_path)
        self._comm.debug = DEFAULT_DEBUG if self.debug == False else self.debug_instance
        self._comm.debug_label = self.folder
        self._gld_initialized = self._comm.open()
         
        if not self._gld_initialized:
            no_init_err_str = "WARNING: GridLAB-D failed to initialize for %s"%(self.folder)
            print(no_init_err_str)
            self.debug_instance.write(no_init_err_str, self.folder)
#BP: possible source of hang            raise Exception('GridLAB-D failed to open.')
    
    
    def stop_bus(self):
        '''
        stop_bus()
        
        Stops the GridLAB-D instance.
        
        Throws:
            Exception
        '''
        try:
            self._comm.shutdown(resume=True)
        except:
            self.debug_instance.write('WARNING: GridLAB-D already shutdown.', self.folder)
        finally:
            self._comm.close()
            self.debug_instance.close()
        
    def _local_bus_send(self,inputs):
        '''
        _local_bus_send(inputs)
        
        Sends the inputs to GridLAB-D.
        '''
        assert isinstance(inputs,message.MessageCommonData)
        
        self._comm.send(inputs)
      
    
    def _local_bus_runto(self,time=None):
        '''
        _local_bus_runto(time)
        
        Runs the bus to the specified time.
        '''
        self._comm.run_to_time(time)
        
    def _local_bus_runto_poll(self,time=None):
        while(not self._comm.poll(time)):
            #check if connected, otherwise do not get into the infinite loop
            if not self._comm.connected:
                break
            sleep(self.poll_time)
     
    
    def _local_bus_recv(self,outputs):
        '''
        _local_bus_recv(outputs)
        
        Local receive function.  Subclasses need to implement this.
        '''
        assert isinstance(outputs,message.MessageCommonData)
        
        _out = self._comm.recv(outputs=outputs)
        
        #if it is not connected, send back 0s
        if not self._comm.connected:
            for o in _out.itervalues():
                o.value = 0.0 
                
        return _out
            
   
    @staticmethod
    def generate_template(filename):
        Bus.generate_template(filename, template=GridlabBusParams)
    
    def _to_cff_init(self):
        ret = message.MessageCommonGridlabInit()
        
        #transfer JSON packet contents to ret
        #file - required
        ret.filename = Bus._json_to_obj(self.params,GridlabBusParams.FILE_KEY)
        if ret.filename == None:
            raise Exception('No filename in the JSON init packet.')
        
        ret.host =      Bus._json_to_obj(self.params,GridlabBusParams.HOST_KEY)
        ret.port =      Bus._json_to_obj(self.params,GridlabBusParams.PORT_KEY)
        ret.gld_args =  Bus._json_to_obj(self.params,GridlabBusParams.ARGS_KEY)
        ret.folder =    Bus._json_to_obj(self.params,GridlabBusParams.FOLDER_KEY)
        
        #time_info parameters
        ret.time_info = self.sim_time
        
        #output parameters
        ret.gld_out = self.bus_out
        
        return ret
    
    '''
    Local functions
    '''


##########################################################
# FileBus
##########################################################

def _file_error(filename):
    raise Exception('ERROR: ' + str(filename) + ' not a supported file type')

class CommonFileParam(message.CommonParam):
    def __init__(self, name=None, param=None, fmt=None, unit=None, value=None, filename=None):
        super(CommonFileParam,self).__init__(name, param, fmt, unit, value)
        self.filename = filename
        self._val_data = None

class FileBus(Bus):
    '''
    The interface between the GridLAB-D aggregator and a load specified by the given file.
    
    TODO: schedule .glm support
    TODO: other (?) file support
    '''
    
    #CONSTANTS###############
    '''
    EXTENSION_HANDLER
    
    A python dictionary that takes a file extension as a key and a function name as a parameter.  
    The function should take a filename and return an object that takes time as an index.
    To add support for other filenames, add a new extension:function entry into the dict.
    '''
    EXTENSION_HANDLER = {'.glm'     : _file_error,
                         '.player'  : player_to_timeseries,
                         '.csv'     : _file_error}
    
    
    def __init__(self, json_file):
        super(FileBus,self).__init__(json_file)
        self._save = self._json_to_obj(json_file, FileBusParams.SAVE_INPUT_KEY)
        
    '''
    Bus interface implementation
    '''
    def start_bus(self):
        '''
        start_bus()
        
        Loads each output file into a data structure that takes a datetime as an input to __getitem__ (i.e., output[time]).
        '''
        self._enter_folder()
        self.debug_instance.open()
        #for each provided input file, load it using the functor provided in EXTENSION_HANDLER
        for output in FileBus.param_dict_itervalues(self.bus_out):
            output._val_data = self.EXTENSION_HANDLER.setdefault(FileBus._get_file_extension(output.filename),_file_error)(output.filename)
        self._leave_folder()
    
    
    def stop_bus(self):
        '''
        stop_bus()
        
        Stops the GridLAB-D instance.
        '''
        #free the memory after stopping as these might take a lot of memory
        self.debug_instance.close()
        
    def _local_bus_send(self,inputs):
        '''
        _local_bus_send(inputs)
        
        Saves the inputs if self._save is True.
        '''
        #TODO: save inputs
        if self._save:
            pass
        
        pass
      
    
    def _local_bus_runto(self,time=None):
        pass
     
    
    def _local_bus_recv(self,outputs):
        '''
        _local_bus_recv(outputs)
        
        Local receive function.  Sends back the value at the given time from the specified files.
        '''
        ret = message.MessageCommonData()
        for output in outputs.itervalues():
            _param = output.copy()
            #TODO: translate output into correct value (e.g., complex-string to complex float), strip unit, etc.
            _param.value = output._val_data[self.sim_time.current_time]
            ret.add_param(_param)
            
        ret.time = self.sim_time
        
        return ret
        
        
    def transaction(self,inputs,outputs=None,overwrite_output=False,trans_state=Bus.TRANSACTION_ALL):
        '''
        Do not allow additional outputs as we do not have an open file for them.
        '''
        if outputs != None and ((trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_OUTPUTS)):
            self.debug_instance.write('WARNING: additional outputs are ignored in FileBus.transaction', self.folder)
            
        return super(FileBus,self).transaction(inputs,trans_state=trans_state)
            
    def json_param_to_common(self,in_param):
        param = CommonFileParam()
        param.name      = Bus._json_to_obj(in_param, BusParams.IO_NAME_KEY)
        param.param     = Bus._json_to_obj(in_param, BusParams.IO_PARAM_KEY)
        param.unit      = Bus._json_to_obj(in_param, BusParams.IO_UNIT_KEY)
        param.value     = Bus._json_to_obj(in_param, BusParams.IO_VALUE_KEY)
        param.filename  = Bus._json_to_obj(in_param, FileBusParams.IO_FILE_KEY)
        return param
        
    @staticmethod
    def generate_template(filename):
        Bus.generate_template(filename, template=FileBusParams)
    
    '''
    Local functions
    '''
    @staticmethod
    def _get_file_extension(filename):
        #NOTE: this only returns the last extension in the file.  e.g., 'file.tar.gz' returns '.gz'
        return os.path.splitext(filename)[1]

##########################################################
# ConstantBus
##########################################################

class ConstantBus(Bus):
    '''
    The interface between the GridLAB-D aggregator and a constant load.
    '''
    
    
    def __init__(self,json_file):
        '''
        Load the BusParams.  Default Bus behavior will work for this type.
        '''
        super(ConstantBus,self).__init__(json_file)
    
    
    '''
    Bus interface implementation
    '''
    def _local_bus_send(self,inputs):
        pass
    
    def start_bus(self):
        self.debug_instance.open()
        #Add node name info to debug file
        self.debug_instance.write('Running on host %s with python pid %s'%(socket.gethostname(),os.getpid()), self.folder)

    def stop_bus(self):
        self.debug_instance.close()
    
    def transaction(self,inputs,outputs=None,overwrite_output=False,trans_state=Bus.TRANSACTION_ALL):
        ret = None
        
        if ((trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_INPUTS)):
            super(ConstantBus,self).transaction(inputs,trans_state=Bus.TRANSACTION_INPUTS)
        
        if (trans_state == Bus.TRANSACTION_ALL) or (trans_state == Bus.TRANSACTION_OUTPUTS):
            #return the constant output stored in memory
            ret = self.bus_translator.translate_output(self._get_outputs(None, False))
            
            if outputs != None:
                self.debug_instance.write('WARNING: additional outputs are ignored in ConstantBus.transaction', 
                                            self.folder)
        return ret
   
    @staticmethod
    def generate_template(filename):
        Bus.generate_template(filename, template=ConstantBusParams)
    
    '''
    Local functions
    '''


##########################################################
# ResistorBus
##########################################################

class ResistorBus(Bus):
    '''
    The interface between the GridLAB-D aggregator and a resistance-based load.
    '''
    
    
    def __init__(self,json_file):
        '''
        Initialize the resistor-like actions
        '''
        super(ResistorBus,self).__init__(json_file)
        
        '''
        TODO: create input-to-output function mapping
        '''
        #TODO: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    '''
    Bus interface implementation
    '''
    def start_bus(self):
        self.debug_instance.open()
        #Add node name info to debug file
        self.debug_instance.write('Running on host %s with python pid %s'%(socket.gethostname(),os.getpid()), self.folder)

    def stop_bus(self):
        self.debug_instance.close()
    
    def transaction(self,inputs,outputs=None,overwrite_output=False):
        '''
        Do not allow additional outputs as we do not have a correct mapping for them.
        '''
        if outputs != None:
            self.debug_instance.write('WARNING: additional outputs are ignored in ResistorBus.transaction', self.folder)
            
        super(ResistorBus,self).transaction(inputs,None,False)
        
    def _local_bus_send(self,inputs):
        '''
        _local_bus_send(inputs)
        
        Maps the inputs to outputs given the init.
        '''
        #TODO: map inputs to outputs.  overwrite bus_out.gld_io[].value
        raise Exception('ResistorBus transaction is not yet implemented. Do not Use ResistorBus.')
        pass
      
    
    def _local_bus_runto(self,time=None):
        pass
     
    
    def _local_bus_recv(self,outputs):
        '''
        _local_bus_recv(outputs)
        
        Local receive function.  Sends back the outputs as is as they should have already been set by _local_bus_send.
        '''
        return outputs
    
    @staticmethod
    def generate_template(filename):
        Bus.generate_template(filename, template=ResistorBusParams)
    
    '''
    Local functions
    '''


##########################################################
# MultiNodeBus
##########################################################

class MultiNodeBus(Bus):
    '''
    The interface between the GridLAB-D aggregator and a bus that takes and iterates through N Bus objects.
    '''
    
    
    def __init__(self,json_file):
        '''
        Initialize all sub-Bus objects, save the actions
        '''
        super(MultiNodeBus,self).__init__(json_file)
        
        #set the GLD outputs
        _ = self.bus_out
        self.bus_out = message.MessageCommonData()
        self.bus_out.gld_io = _
        
        self._enter_folder()
        
        #load the buses
        self._buses = []
        
        for node in json_file[MultiNodeBusParams.NODE_KEY]:
            #load Bus from JSON file
            if MultiNodeBusParams.BUS_FILE_KEY in node:
                self._buses.append(get_bus_from_classname(BusParams.load(node[MultiNodeBusParams.BUS_FILE_KEY])))
            
            #load Bus from this JSON object
            else:
                self._buses.append(get_bus_from_classname(node))
        
        #load action-list
        self._actions = []
        
        for a in json_file[MultiNodeBusParams.ACTION_KEY]:
            self._actions.append(action.json_to_action(a))
            
        self._leave_folder()
        
    def set_path(self,path):
        '''
        Call set_path for all sub-buses
        '''
        for bus in self._buses:
            try:
                bus.set_path(path)
            except Exception as e:
                self.debug_instance.write('failed to set_path for %s (%s)' % (str(bus),str(e)))
    
    '''
    Bus interface implementation
    '''
    
    def start_bus(self):
        self._enter_folder()
        self.debug_instance.open()
        #Add node name info to debug file
        self.debug_instance.write('Running on host %s with python pid %s'%(socket.gethostname(),os.getpid()), self.folder)
        for b_num in range(len(self._buses)):
            bus = self._buses[b_num]
            self.debug_instance.write("Starting child bus (%d/%d): %s"%(b_num+1, len(self._buses), bus.folder))
            bus.start_bus()
        self._leave_folder()
    
    def stop_bus(self):
        for bus in self._buses:
            bus.stop_bus()
        self.debug_instance.close()
    
    def transaction(self,inputs,run_serial=False,*args,**kwargs):
        '''
        run flow:
            put inputs as a list into output_list[0]
            for each bus
                output_list.append(bus.run)
            
            put empty list into output_list[-1]
            for each action
                output_list[-1].append(action(output_list))
                
            return output_list[-1] #only if there are actions, else return outputs some other way (throw exception for now)
        '''
        self._enter_folder()
        
        _trans_inputs = self.bus_translator.translate_input(inputs)
        output_list = [_trans_inputs.gld_io]
        
        #advance time in the simulation
        self._local_advance_time(_trans_inputs.time)
        
        for io in _trans_inputs.itervalues():
            self.debug_instance.write('[SEND]: ' + str(_trans_inputs.time) + '\t' + str(io.name) + '.' + str(io.param) + ' = ' + str(io.value), self.folder)
        
        #do the old method of serially running sub-Bus objects
        if run_serial:
            for bus in self._buses:
                output_list.append(bus.transaction(_trans_inputs,outputs=self.bus_out,overwrite_output=False).gld_io)
        else:
            #do the transaction for each of the sub-Bus objects ONE STEP AT A TIME
            #INPUTS
            for bus in self._buses:
                bus.transaction(_trans_inputs,outputs=self.bus_out,overwrite_output=False,trans_state=Bus.TRANSACTION_INPUTS)
                
            #RUN_START
            for bus in self._buses:
                bus.transaction(_trans_inputs,outputs=self.bus_out,overwrite_output=False,trans_state=Bus.TRANSACTION_RUNTO)
            
            #RUN_CHECK
            for bus in self._buses:
                bus.transaction(_trans_inputs,outputs=self.bus_out,overwrite_output=False,trans_state=Bus.TRANSACTION_RUNTO_POLL)
            
            #OUTPUTS
            for bus in self._buses:
                output_list.append(bus.transaction(_trans_inputs,outputs=self.bus_out,overwrite_output=False,trans_state=Bus.TRANSACTION_OUTPUTS).gld_io)
                
        #perform the actions on the outputs.  
        output_list.append({})
        for a in self._actions:
            param = a.execute(output_list)
            output_list[-1].setdefault(param.name,{})[param.param] = param
            
        ret = message.MessageCommonData()
        ret.gld_io = output_list[-1]
        ret.time = self.sim_time
        
        for io in ret.itervalues():
            self.debug_instance.write('[RECV]: ' + str(_trans_inputs.time) + '\t' + str(io.name) + '.' + str(io.param) + ' = ' + str(io.value), self.folder)
        
        self._leave_folder()
        return self.bus_translator.translate_output(ret)
    
    @staticmethod
    def generate_template(filename):
        Bus.generate_template(filename, template=MultiNodeBusParams)
    
    '''
    Local functions
    '''
        
        
###############################################################
# BusTranslator Types
###############################################################
'''
These translate init packets, transaction send/receive packets according to their needs.
'''
    
##########################################################
# BusTranslator
##########################################################
class BusTranslator(object):
    def __init__(self,*args,**kwargs):
        pass
    
    
    def translate_input(self,inputs):
        '''
        Translates the inputs to a Bus.transaction to the specific implementation needed.
        
        Default behavior is to do nothing.  Subclasses should change this if different behavior is required.
        '''
        return inputs

    def translate_output(self,outputs):
        '''
        Translates the outputs to a Bus.transaction to the specific implementation needed.
        
        Default behavior is to do nothing.  Subclasses should change this if different behavior is required.
        '''
        return outputs
    
    def translate_init(self,init):
        '''
        Translates the inputs to a Bus.__init__ to the specific implementation needed.
        
        Default behavior is to do nothing.  Subclasses should change this if different behavior is required.
        '''
        return init
    
    
##########################################################
# BusTranslator
##########################################################
class AggregatorBusTranslator(object):
    #these keys are shared with IGMS core, might want to point to same constants in both
    IN_TIME_KEY = 'next_time'
    IN_V_RE_KEY = 'voltage_real'
    IN_V_IM_KEY = 'voltage_imag'
    
    OUT_P_RE_KEY = 'load_real'
    OUT_P_IM_KEY = 'load_imag'
    
    BUS_VOLTAGE_NAME = 'special'
    BUS_VOLTAGE_PARAM = 'positive_sequence_voltage'
    
    BUS_POWER_NAME = 'summed_power'
    BASE_KV_KEY = 'base_kv'
    DEFAULT_BASE_KV = 138.0
    
    def __init__(self,*args,**kwargs):
        #assuming json_file is args[0], probably a poor assumption.  possibly make it a keyword
        self.BASE_KV = Bus._json_to_obj(args[0], AggregatorBusTranslator.BASE_KV_KEY) 
        if self.BASE_KV == None:
            self.BASE_KV = self.DEFAULT_BASE_KV
    
    def translate_input(self,inputs):
        '''
        Translates the inputs from a dictionary to a message.MessageCommonData
        '''
        _new_in = message.MessageCommonData()
        
        #if there is a new time-step, add to inputs
        if AggregatorBusTranslator.IN_TIME_KEY in inputs:
            #start_time will also set the current_time which is used in Bus
            _new_in.time = message.CommonTimeInfo(start_time=inputs[AggregatorBusTranslator.IN_TIME_KEY])
            
        _voltage = (inputs[AggregatorBusTranslator.IN_V_RE_KEY] + inputs[AggregatorBusTranslator.IN_V_IM_KEY] * 1.0j) * self.BASE_KV * 1000 / np.sqrt(3.0)
        _new_in.add_param(message.CommonParam(name=AggregatorBusTranslator.BUS_VOLTAGE_NAME, param=AggregatorBusTranslator.BUS_VOLTAGE_PARAM, value=_voltage))

        return _new_in
    
    def translate_output(self,outputs):
        '''
        Translates the outputs from a message.MessageCommonData to a dictionary
        '''
        _new_out = {}
        
        _val = outputs.get_param(AggregatorBusTranslator.BUS_POWER_NAME,None).value

        _new_out[AggregatorBusTranslator.OUT_P_RE_KEY] = _val.real/1e6 if _val != None else 0.0
        _new_out[AggregatorBusTranslator.OUT_P_IM_KEY] = _val.imag/1e6 if _val != None else 0.0
        _new_out[AggregatorBusTranslator.IN_TIME_KEY] = str(outputs.time.current_time)
        
        return _new_out
    
    def translate_init(self,init):
        '''
        Passes the init straight through
        '''
        return init
    
