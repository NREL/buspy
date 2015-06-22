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

cpest.construct.bus.py

Params implementations for each of the cpest.run.bus.bus.Bus interface implementations. 

Params Implementations:
    GridlabBusParams     - initialization parameters (Params) for the GridLAB-D bus interface
    FileBusParams        - initialization parameters (Params) for the file-based bus interface
    ConstantBusParams    - initialization parameters (Params) for the constant bus interface (NOT YET IMPLEMENTED)
    ResistorBusParams    - initialization parameters (Params) for the resistance-based bus interface (NOT YET IMPLEMENTED)
    MultiNodeBusParams   - initialization parameters (Params) for the substation-like bus interface


Requirements:
    
    
To-Do List:
    TODO: implement Params for the resistance-based version of the interface
'''

######################################################################
# IMPORTS
######################################################################
import logging

from buspy.construct.base import Params
from buspy.construct.base import ParamDescriptor
from buspy.construct.base import create_choice_descriptor
from buspy.construct.base import load_json_file
from buspy.utils.debug import DEBUG_ENUM
from collections import OrderedDict

from buspy.comm.gridlabcomm import GLD_DEFAULT_PORT

######################################################################
# CONSTANTS
######################################################################


######################################################################
# UTILITY FUNCTIONS
######################################################################



######################################################################
# CLASSES
######################################################################

###############################################################
# Decoders
###############################################################
'''
Custom JSONDecoder classes
'''



###############################################################
# Encoders
###############################################################
'''
Custom JSONEncoder classes
'''



###############################################################
# Params
###############################################################
'''
Custom Params classes
'''

##########################################################
# BusParams
##########################################################

class BusParams(Params):
    #common BusParams keys
    CLASS_KEY   = 'class_name'
    BUS_KEY     = 'bus_type'
    FOLDER_KEY  = 'folder'
    OUTPUT_KEY  = 'output'
    TIME_KEY    = 'time_info'
    BUS_TRANSLATOR_KEY = 'io_translator'
    DEBUG_KEY   = 'debug'
    DEBUG_TYPE_KEY = 'debug_type'
    DEBUG_ARGS_KEY = 'debug_args'
    
    #time keys
    TIME_START_KEY  = 'start'
    TIME_END_KEY    = 'end'
    TIME_ZONE_KEY   = 'timezone'
    TIME_DELTA_KEY  = 'delta'
    
    #I/O keys
    IO_NAME_KEY    = 'name'
    IO_PARAM_KEY   = 'param'
    IO_UNIT_KEY    = 'unit'
    IO_VALUE_KEY   = 'value'
    
    _param_descriptions = {
                            
            BUS_KEY         :   {'description'      : 'Name of the Bus type',
                                 'parser'           : str,
                                 'template_value'   : 'GridlabBus'},
                           
            FOLDER_KEY      :   {'description'      : 'Folder where all Bus input/output will take place.',
                                 'required'         : False,
                                 'parser'           : str,
                                 'default_value'    : '.'},
                           
            OUTPUT_KEY      :   {'description'      : 'Parameters that will be OUTPUT FROM the bus.  In the form of a list of JSON-objects with the following keys: name, param, unit. Unit is optional.',
                                 'required'         : False,
                                 'template_value'   : [{'name':'network_node','param':'measured_current_A'},
                                                       {'name':'network_node','param':'measured_current_B'},
                                                       {'name':'network_node','param':'measured_current_C'}]},
                                                       
            TIME_KEY        :   {'description'      : 'Time information for the simulation.  Takes a JSON-object with the following keys: start, end, timezone, delta.  Delta is in seconds.',
                                 'required'         : True,
                                 'template_value'   : {'start':'2020-06-01 00:00:00','end':'2020-06-01 00:15:00','timezone':'EST','delta':60}},

        
            BUS_TRANSLATOR_KEY :{'description'      : 'Name of the BusTranslator object to use to translate the inputs and outputs of the MultiNodeBus',
                                 'required'         : False,
                                 'default_value'    : 'BusTranslator'},
                           
            DEBUG_KEY       :   {'description'      : 'Tells the bus to output any debug information',
                                 'required'         : False,
                                 'default_value'    : True},
                           
            DEBUG_ARGS_KEY  :   {'description'      : 'Additional arguments to the debug_type constructor',
                                 'required'         : False,
                                 'default_value'    : {}}    
                                             
    }

    def get_class_name(self):
        return self.__class__.__name__ 
    
    def __init__(self,*arg, **kw):
        '''
        Sets the schema based-on the inherited _param_descriptions and calls Params constructor
        '''

        schema = OrderedDict()
        
        #add the arguments from __param_descriptions into the BusParams schema
        for key in self._param_descriptions.keys():
            schema[key] = ParamDescriptor(key, **self._param_descriptions[key])
            
        schema[self.DEBUG_TYPE_KEY] =        create_choice_descriptor(self.DEBUG_TYPE_KEY,
                                             DEBUG_ENUM,
                                             'Type of debug to use. NOTE: debug must also be set to true.',
                                             required=False,
                                             default_value=DEBUG_ENUM[2],
                                             parser=None)
            
        super(BusParams,self).__init__(schema, *arg, **kw)

    @staticmethod
    def load(filename):
        '''
        Loads the JSON file into the BusParams class specified by the value at key='class_name'
        '''
        _json = None
        try: 
            # load the json into a dict
            _json = load_json_file(filename)
        except Exception as e:
            raise Exception('Could not load {} as a json file, because {}.'.format(filename, e))
        
        #get the name of the class we are interested in
        _bus_type = _json.pop(BusParams.CLASS_KEY,None)
        
        _bus_params = None
        try:
            #call its constructor
            _bus_params = globals()[_bus_type]()
        except:
            raise Exception('Invalid class_name provided in JSON file: ' + str(_bus_type))
        
        #input the rest of the non-description keys (including None).  class_name is no longer in dict, do not need to search for it
        for key, item in _json.items():
            if not (Params._Params__is_desc(key)):
                try:
                    _bus_params[key] = item
                except Exception as e:
                    logging.warning('Could not set parameter {} on the {}, because {}.'.format(key, _bus_type, e))

        
        return _bus_params

##########################################################
# GridlabBusParams
##########################################################

class GridlabBusParams(BusParams):
    '''
    The initialization parameters for the GridLAB-D bus implementation.
    '''
    
    FILE_KEY    = 'filename'
    HOST_KEY    = 'host'
    PORT_KEY    = 'port'
    ARGS_KEY    = 'gld_args'
    POLL_KEY    = 'poll'
    
    #gld parameter keys
    GLD_FORMAT_KEY  = 'format'
    

    def __init__(self, *arg, **kw):
        
        #add additional ParamDescriptor inputs for the GridlabBusParams class to the json_template
        self._param_descriptions[self.FILE_KEY]         = {'description'      : 'Name of the GridLAB-D .glm case file',
                                                           'parser'           : str,
                                                           'template_value'   : '*.glm'}
        
        self._param_descriptions[self.HOST_KEY]         = {'description'      : 'Communication hostname of GridLAB-D',
                                                           'required'         : False,
                                                           'parser'           : str,
                                                           'default_value'    : 'localhost'}
        
        self._param_descriptions[self.PORT_KEY]         = {'description'      : 'Communication port of GridLAB-D.  Set to -1 to automatically find a port.',
                                                           'required'         : False,
                                                           'parser'           : int,
                                                           'default_value'    : GLD_DEFAULT_PORT}
        
        self._param_descriptions[self.ARGS_KEY]         = {'description'      : 'Additional GridLAB-D command line arguments to be passed to the command line upon instantiation.  These will overwrite any parameters (e.g., port) defined in the JSON input.  dict in the form of {flag : value} pairs (e.g., {"-P":"6267","--server":null})',
                                                           'required'         : False,
                                                           'template_value'   : {'-P':'6267','--server':None}}
        
        self._param_descriptions[self.POLL_KEY]         = {'description'      : 'Polling time for the GridLAB-D instance (in seconds).',
                                                           'required'         : False,
                                                           'default_value'    : 0.05}
        
        
        #Change GridLAB-D specific default ParamDescriptors
        self._param_descriptions[self.FOLDER_KEY]['description'] = 'Folder where the GridLAB-D *.glm is located.'
        self._param_descriptions[self.OUTPUT_KEY]['description'] = 'GridLAB-D parameters that will be OUTPUT_FROM GridLAB-D.  In the form of a list of JSON-objects with the following keys: name, param, format, unit.  Format and unit are optional.  If it is a global variable, set param to null'
        
        super(GridlabBusParams,self).__init__(*arg, **kw)
    
    '''
    BusParams interface implementation
    '''
    
    
    '''
    Local functions
    '''


##########################################################
# FileBusParams
##########################################################

class FileBusParams(BusParams):
    '''
    The initialization parameters for the file-based bus implementation.
    '''
    
    #CONSTANTS###############
    SAVE_INPUT_KEY = 'save_input'
    
    IO_FILE_KEY = 'filename'

    def __init__(self, *arg, **kw):
        schema = OrderedDict()
        
        #Change file specific default ParamDescriptors
        self._param_descriptions[self.BUS_KEY]['default_value'] = 'FileBus'
        
        self._param_descriptions[self.OUTPUT_KEY]['template_value'] = [{'name':'network_node','param':'measured_power',self.IO_FILE_KEY:'power.player'}]
        self._param_descriptions[self.OUTPUT_KEY]['description'] = 'Parameters that will be OUTPUT FROM the bus using the specified file.  In the form of a list of JSON-objects with the following keys: name, param, filename.'
        
        #Add FileBus unique descriptors
        self._param_descriptions[self.SAVE_INPUT_KEY] = {'description'      : 'Flag determining whether the FileBus will save the provided inputs to transaction.',
                                                         'required'         : False,
                                                         'default_value'    : False} 
        
        super(FileBusParams,self).__init__(schema, *arg, **kw)
    
    '''
    Params interface implementation
    '''
    
    
    '''
    Local functions
    '''
    

##########################################################
# ConstantBusParams
##########################################################

class ConstantBusParams(BusParams):
    '''
    The initialization parameters for the constant bus implementation.
    '''
    
    def __init__(self, *arg, **kw):
        schema = OrderedDict()
        
        self._param_descriptions[self.BUS_KEY]['default_value']    = 'ConstantBus'
        self._param_descriptions[self.OUTPUT_KEY]['template_value'] =  [{'name':'network_node','param':'measured_current_A','value':25.5},
                                                                        {'name':'network_node','param':'measured_current_B','value':27.9},
                                                                        {'name':'network_node','param':'measured_current_C','value':35.5}]
        
        super(ConstantBusParams,self).__init__(schema, *arg, **kw)
    
    '''
    Params interface implementation
    '''
    
    
    '''
    Local functions
    '''


##########################################################
# ResistorBusParams
##########################################################

class ResistorBusParams(BusParams):
    '''
    The initialization parameters for the resistance-based bus implementation.
    '''
    
    MAPPING_KEY = 'io_map'
    
    def __init__(self, *arg, **kw):
        schema = OrderedDict()
        
        self._param_descriptions[self.BUS_KEY]['default_value']    = 'ResistorBus'
        #TODO: FINISH RESISTORBUS
        self._param_descriptions[self.OUTPUT_KEY]['template_value'] =  [{'name':'network_node','param':'measured_current_A'},
                                                                        {'name':'network_node','param':'measured_power'}]
        
        
        self._param_descriptions[self.MAPPING_KEY] = {'description'      : 'Map of inputs to outputs.',
                                                      'required'         : True,
                                                      'template_value'   : [{'in_name':''}]} 
        
        super(ResistorBusParams,self).__init__(schema, *arg, **kw)
    
    '''
    Params interface implementation
    '''
    
    
    '''
    Local functions
    '''


##########################################################
# MultiNodeBusParams
##########################################################

class MultiNodeBusParams(BusParams):
    '''
    The initialization parameters for the multi-node bus implementation.
    '''
    
    NODE_KEY    = 'nodes'
    ACTION_KEY  = 'actions'
    BUS_FILE_KEY= '__bus_file'
    
    def __init__(self, *arg, **kw):
        schema = OrderedDict()

        '''
        class_key - MultiNodeBusParams
        bus_key - MultiNodeBus
        node_key - array of Bus descriptions
        action_key - array of actions to take on the outputs from the contained Bus objects
        '''
        
        #Change multi-node specific default ParamDescriptors
        self._param_descriptions[self.FOLDER_KEY]['description'] = 'Folder where the multiple Bus object JSON-files are located.'
        self._param_descriptions[self.OUTPUT_KEY]['description'] = 'Bus parameters that will be OUTPUT FROM the buses.  These will be appended to all outputs of all sub-Bus objects.  In the form of a list of JSON-objects with the following keys: name, param, unit. Unit is optional.'
        self._param_descriptions[self.BUS_KEY]['default_value'] = 'MultiNodeBus'
        
        #add class specific ParamDescriptors
        self._param_descriptions[self.NODE_KEY]     =       {'description'      : 'Array of either (a) filenames that contain Bus JSON objects or (b) Bus JSON objects.',
                                                             'required'         : True,
                                                             'template_value'   : [{self.BUS_FILE_KEY   :   'other_bus.json'},
                                                                                   {self.BUS_FILE_KEY   :   'other_bus2.json'},
                                                                                   {
                                                                                        self.CLASS_KEY  :   'GridlabBusParams',
                                                                                        self.BUS_KEY    :   'GridlabBus',
                                                                                        self.FOLDER_KEY :   'GridlabFolder/glms',
                                                                                        'other_stuff'   :   '...'
                                                                                    }]} #,{GridlabBusParams().to_json()}
        
        self._param_descriptions[self.ACTION_KEY]   =       {'description'      : 'Array of actions to take on specified outputs (e.g., sum currents) in the form: name, action, output-list.  The actions are taken in order and outputs from prior actions are passed to future actions (as well as inputs).',
                                                             'required'         : True,
                                                             'template_value'   : [
                                                                                       {'name'      : 'summed_current_A',
                                                                                        'action'    : 'sum',
                                                                                        'action-list'   : [{'name':'network_node','param':'measured_current_A'}]},
                                                                                       
                                                                                       {'name'      : 'summed_currents',
                                                                                        'action'    : 'sum',
                                                                                        'action-list'   : [{'name':'network_node','param':'measured_current_A'},
                                                                                                           {'name':'network_node','param':'measured_current_B'},
                                                                                                           {'name':'network_node','param':'measured_current_C'}]}
                                                                                   ]}

        
        super(MultiNodeBusParams,self).__init__(schema, *arg, **kw)
    
    '''
    Params interface implementation
    '''
    
    
    '''
    Local functions
    '''



#####################################################################################################################
# TEST MAIN
#####################################################################################################################

if __name__ == "__main__":
    t = MultiNodeBusParams()
    
    t.save_template('test.json')
    
#     t2 = BusParams.load('test.json')
#     t2['port'] = 6300
#     t2.save('test2.json')
    
    