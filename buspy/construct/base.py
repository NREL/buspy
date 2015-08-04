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
'''

import buspy.construct

from abc import abstractmethod
import argparse
from collections import OrderedDict
import copy
import datetime as dt
import json
import marshal
import numpy
import os
import pandas as pds
import re
    
class ParamDescriptor(object):
    """
    Information describing a paramter.
    """
    def __init__(self, 
                 name, 
                 description, 
                 required=True, 
                 default_value=None, 
                 parser=None,
                 suggested_values=None,
                 n=None,
                 template_value=None):
        """
        Create a new ParamDescriptor
        
        @type name: string
        @param name: The parameter's name.
        
        @type description: string
        @param description: The parameter's description.
        
        @type required: boolean
        @param required: Whether or not the user is required to provide this parameter.
        
        @type default_value: the parameter's type, or convertible by parser
        @param default_value: A default value for this parameter.
        
        @type parser: functor
        @param parser: Function for processing parameter values into standard form.
        
        @type suggested_values: list or functor
        @param suggested_values: List or function for generating list of suggested values.
        
        @type n: None, int, or string
        @param n: List size if not None. Passed to the nargs option of add_argument in 
                  argparse. 
        """
        self.name = name
        self.description = description
        self.required = required
        self.default_value = default_value
        if (default_value is not None) and (parser is not None):
            self.default_value = parser(default_value)
        self.parser = parser
        self.suggested_values = suggested_values # used for generating templates
        self.n = n
        
        #template value is a little different than default value
        self.template_value = default_value
        if template_value != None:
            self.template_value = template_value                @property    def parser(self):        return self.__parser            @parser.setter    def parser(self, value):        self.__parser = ExtendedParser(value) if value is not None else None
        
    def __str__(self): 
        return '{:s} - {:s}\n    {:s}{:s}'.format(self.name,
                                                  self.__required_str(),
                                                  self.description,
                                                  self.__default_value_str())
        
    def desc_str(self):
        """
        @rtype: string
        @return: descriptor like str(), but without name listed
        """
        return '{:s} - {:s}{:s}'.format(self.__required_str(),
                                        self.description,
                                        self.__default_value_str())
    
    def __required_str(self):
        return ('required' if self.required else 'optional')
        
    def __default_value_str(self):
        return ("\n    default_value: {:s}".format(str(self.default_value)) if self.default_value is not None else "")      

def to_datetime(value):
    """
    Tries to convert dt to a real datetime.datetime.
    """
    result = None
    
    if isinstance(value,dt.datetime) or isinstance(value, numpy.datetime64):
        result = value
        
    if result is None:
        try:
            result = pds.to_datetime(value)
        except:
            result = None
            
    if result is None:
        try:
            result = dt.datetime.strptime(value,'%Y-%m-%d %H:%M:%S')
        except:
            result = None
            
    if result is None:
        raise RuntimeError("Could not convert {:s} to datetime.datetime.".format(value))
        
    return result
        
def to_timedelta(td): 
    """
    Tries to convert td to a real datetime.timedelta, rounded to the 
    nearest second. Raises a RuntimeError if not successful.
    """
    result = None
    
    if type(td) in [type(dt.timedelta()), type(numpy.timedelta64())]:
        result = td
        
    if result is None:
        try:
            result = pds.to_timedelta(td)
        except:
            result = None
            
    if result is None:
        m = re.match('([0-9]{2}):([0-9]{2}):([0-9]{2}):([0-9]{2})',td)
        if m is not None:
            result = dt.timedelta(days=int(m.group(1)),
                                  hours=int(m.group(2)),
                                  minutes=int(m.group(3)),
                                  seconds=int(m.group(4)))
                                  
    if result is None:
        values = { 'd': None, 'h': None, 'm': None, 's': None }
        ok = True
        for piece in re.split(' ',td):
            m = re.match('([0-9]+)(d|h|m|s)',piece)
            if (m is None) or (m.group(2) not in values) or (values[m.group(2)] is not None):
                ok = False
                break
            values[m.group(2)] = int(m.group(1))
        if ok:
            for key, val in values.items():
                if val is None:
                    values[key] = 0
            result = dt.timedelta(days = values['d'],
                                  hours = values['h'],
                                  minutes = values['m'],
                                  seconds = values['s'])
            
    if result is None:
        raise RuntimeError("Could not convert {:s} to datetime.timedelta.".format(td))
        
    # round to nearest second
    if type(result) == type(dt.timedelta()):
        result = dt.timedelta(seconds=round(result.total_seconds()))
    if type(result) == type(numpy.timedelta64()):
        result = dt.timedelta(seconds=round(result/numpy.timedelta64(1,'s')))
    
    return result            
    
def to_boolean(value):
    return value in [True,'True','true','T','t','Yes','yes','Y','y']
        
def create_choice_descriptor(name,
                             choices,
                             description_prefix,
                             required=True,
                             default_value=None,
                             parser=None):
    """
    Helper method for describing parameters whose values should be chosen from a list.
    
    @type name: string
    @param name: The parameter's name.
    
    @type choices: list
    @param choices: List of valid choices for the parameter value.
    
    @type description_prefix: string
    @param description_prefix: String to be pre-pended to the choice list. Composite 
        string will be the parameter's description.
        
    @type required: boolean
    @param required: Whether or not the user is required to provide this parameter.
    
    @type default_value: the parameter's type
    @param default_value: A default value for this parameter, must be in choices.
    
    @type parser: functor
    @param parser: Function for processing individual parameter values into standard form.
    
    @rtype: ParamDescriptor
    """
    if parser is None:
        return  ParamDescriptor(name,
                                "{:s} {:s}.".format(description_prefix,print_choice_list(choices)),
                                required,
                                default_value,
                                lambda x: x if x in choices else None,
                                choices)
    else:
        return  ParamDescriptor(name,
                                "{:s} {:s}.".format(description_prefix,print_choice_list(choices)),
                                required,
                                default_value,
                                lambda x, *args, **kwargs: parser(x, *args, **kwargs) if parser(x, *args, **kwargs) in choices else None,
                                choices)
        
class ParamsEncoder(json.JSONEncoder):
    """
    Json encoding for all possible Params types. May need to be extended when
    a new class is derived from Params.
    """
    def default(self, obj):
        if isinstance(obj, dt.timedelta):
            # serialize dt.timedelta as string that can be parsed
            return to_walltime(obj)
        if isinstance(obj, dt.datetime):
            # serialize dt.datetime as string that can be parsed
            return str(obj)
        return json.JSONEncoder.default(self,obj)        class ExtendedParser(object):    def __init__(self, parser):        self.__parser = parser        self.clear_args()            @property    def bare(self):        return self.__parser        def set_args(self, *args, **kwargs):        self.__args = args        self.__kwargs = kwargs            def clear_args(self):        self.__args = ()        self.__kwargs = {}        def __call__(self, value):        return self.__parser(value, *self.__args, **self.__kwargs)class Params(dict):
    """
    Base class for dictionary-based params with json serialization.
    """
    
    @abstractmethod
    def get_class_name(self): pass    
   
    def __init__(self, schema, *arg, **kw):
        """
        Initialize a Params object with values.
        
        @type values: dict of param_name, param_value
        @param values: User's parameter values.
        """
        assert isinstance(schema,OrderedDict)
        self.__schema = schema
        
        self.__encoder = kw.pop('encoder',ParamsEncoder)
        assert isinstance(self.__encoder(),json.JSONEncoder)
        
        super(Params, self).__init__(*arg, **kw)
        
    def __str__(self):
        result = 'Values:\n\n'
        for pair in self.sorted_items(): 
            result += "{:s}: {:s}\n".format(pair[0],str(pair[1]))
        result += '\nDescriptors:\n\n'
        for descriptor in self.__schema.values():
            result += "{:s}\n\n".format(str(descriptor))
        return result
        
    def schema(self):
        """
        Returns a deep copy of the schema. (A Params schema cannot be modified, but others 
        may need to inspect it.)
        
        @rtype: dict of ParamDescriptors
        @return: Deep copy of this Params object's schema.
        """
        return copy.deepcopy(self.__schema)
    
    def __getitem__(self, param_name):        """Returns the set value if it exists. Otherwise, if param_name is in the schema,        returns the schema default value (which may be None). Otherwise returns None."""        if param_name in self:            return super(Params, self).__getitem__(param_name)        elif param_name in self.__schema:            descriptor = self.__schema[param_name]            return descriptor.default_value        return None     

    def get(self, param_name):
        # do not use derived method -- use code in __getitem__
        return self.__getitem__(param_name)    
              
    def __setitem__(self, param_name, param_value):        if param_name in self.__schema:            descriptor = self.__schema[param_name]            if descriptor.parser is not None:                super(Params, self).__setitem__(param_name, descriptor.parser(param_value))            else:                super(Params, self).__setitem__(param_name, param_value)            self.__refresh_schema(param_name)        else:            raise RuntimeError("{:s} is not a valid parameter.".format(param_name))                def set_parse_args(self, param_name, *parse_args, **parse_kwargs):        if param_name in self.__schema:            self.__schema[param_name].parser.set_args(*parse_args, **parse_kwargs)        else:            raise RuntimeError("{:s} is not a valid parameter.".format(param_name))        def clear_parse_args(self, param_name):        if param_name in self.__schema:            self.__schema[param_name].parser.clear_args()     def to_json_dict(self):
        """
        @rtype: collections.OrderedDict
        @return: 'class_name' and all items in schema-specified order
        """
        d = OrderedDict()
        d["class_name"] = self.get_class_name()
        for key, value in self.sorted_items():
            d[key] = value
        return d    
 
    def to_json(self): 
        """
        @rtype: string
        @return: JSON representation of this Params object
        """
        return json.dumps(self.to_json_dict(), 
                          cls=self.__encoder,
                          indent=4,
                          separators=(',', ': '))
  
    def save(self, path): 
        """
        Save these Params to json format.
        
        @type path: string
        @param path: path to save to, should end in file name with json extension
        """
        f = open(path,'w')
        f.write(self.to_json())
        f.close()
  
    def json_template(self): 
        """
        Create a json template that can be hand-edited and then used with the 
        command-line interface.
        
        @rtype: string
        @return: JSON file template
        """
        t = OrderedDict()
        
        t["class_name"] = self.get_class_name()
        t["file_desc"] = "This is a JSON template for {:s}. All items whose keys end in '_desc', including this one, are for information only and will be ignored upon import.".format(self.get_class_name())
        
        for description in self.__schema.values():
            t["{:s}_desc".format(description.name)] = description.desc_str()            value = None            if description.default_value is not None:                value = description.default_value            elif description.template_value is not None:                value = description.template_value            t[description.name] = value
            
        return json.dumps(t,
                          cls=self.__encoder,
                          indent=4,
                          separators=(',', ': '))
  
    def save_template(self, path): 
        """
        Save the json_template to path.
        
        @type path: string
        @param path: path to save the template to, should end in file name with json extension.
        """
        f = open(path,'w')
        f.write(self.json_template())
        f.close()
  
    def valid(self): 
        for param_name, descriptor in self.__schema.items():
            if descriptor.required:
                if self.get(param_name) is None:
                    return False
        return True
    
    def sorted_items(self): 
        return sorted(self.items(), key=lambda pair: list(self.__schema.keys()).index(pair[0]))
    
    def __nonzero__(self): 
        return self.valid()
               
    def __refresh_schema(self,param_name):
        return
        
    @staticmethod
    def __is_desc(key):
        """
        Returns true if x is a string ending in '_desc'.
        
        @type x: string
        
        @rtype: bool
        @return: True if x ends in '_desc', False otherwise.
        """
        if re.match('.+_desc',key):
            return True
        return False        
        
class Creator:
    """
    Base class for classes that create one or more simulations in separate run folders.
    """
    @abstractmethod
    def get_class_name(self): pass    
    
    def __init__(self, out_dir, params, resources_dir = None):
        self.out_dir = os.path.realpath(out_dir)
        self.params = params
        self.resources_dir = resources_dir
        
    def create(self): 
        """
        Base class create method to be called by derived class create method to 
        conduct runtime checks on parameters.
        """
        if not self.params.valid():
            raise RuntimeError("Cannot create with invalid parameters:\n{:s}".format(self.params))
    
    def to_json_dict(self): 
        return OrderedDict({"class_name": self.get_class_name(),
                            "out_dir": self.out_dir,
                            "params": self.params.to_json_dict(),
                            "resources_dir": self.resources_dir})

########################################
# Internal Helper Functions and Classes
########################################
    
def load_json_file(p):
    """
    Load json file into a dict from path p.
    
    @type p: string path
    @param p: path to json file to be loaded
    
    @rtype: dict
    @return: loaded json file
    """
    f = open(p,'r')
    obj = json.load(f)
    f.close()
    assert(isinstance(obj,dict))
    return obj
    
def print_choice_list(choices):
    """
    @type choices: list
    @param choices: List of choices. Each must be printable using "{:s}".format(x).
    
    @rtype: string
    @return: parenthetical list of choices, with each choice in single quotes 
             and separated by '|'
    """
    result = "({:s}".format(str(choices[0]))
    for x in choices[1:]:
        result = "{:s}|{:s}".format(result,str(x))
    result = "{:s})".format(result)
    return result
    
def find_file(filename, expected_dir = None, ext = None, none_ok = False, additional_dirs = []):
    """
    Function for finding a file generally expected to be in a certain directory.
    
    Parameters:
        - filename (string) - full path or just the filename
        - expected_dir (string) - path to the directory we expect to find the file in
        
    Returns the full path to the file (string).
    
    Throws RuntimeError if the file cannot be located.
    """
    if filename is None:        if none_ok:            return None        else:            raise RuntimeError("Filename is None, but that is not allowed.")    # fix-up filename    result = os.path.realpath(filename)    if ext is not None and not os.path.splitext(filename)[1] == ext:        filename += ext    # look for filename    if not os.path.exists(result):        dirs_to_search = additional_dirs        if expected_dir is not None:            dirs_to_search.append(expected_dir)        for dir in dirs_to_search:            result = os.path.join(dir, os.path.basename(filename))            if os.path.exists(result):                break    if not os.path.exists(result):        raise RuntimeError("Cannot locate file '{}' in '{}'. Tried '{}'.".format(filename, expected_dir, result))    return result
    
def installed_files(dir, ext = None):
    result = []
    for subdir, dirs, files in os.walk(dir):
        for file in files:
            if ext is not None and os.path.splitext(file)[1] != ext:
                continue
            result.append(file)
    return result
    
def installed_sub_templates():    return installed_files(os.path.realpath(igms.construct.data_dir() + "/Templates/"))
def to_walltime(dt):
    """
    Method to convert a timedelta object into a walltime string for use by submit scripts.
    
    @type dt: timedelta
    @param dt: Walltime parameter in timedelta format.
    @rtype: string
    @return: dt converted to "DD:HH:MM:SS"
    """
    n_days = dt.days
    n_hours = dt.seconds // 3600
    n_mins = (dt.seconds // 60 ) % 60
    n_secs = dt.seconds % 60
    return "{:02d}:{:02d}:{:02d}:{:02d}".format(n_days,n_hours,n_mins,n_secs)    def to_simple_duration(td,spaces=False):    """    Method to convert a timedelta object into a simple (e.g. '1d12h') string.        Parameters:        - td: timedelta object to print        - spaces: boolean for whether to include spaces            Returns string.    """    sep = " " if spaces else ""    def add_to_result(result, num, sym, sep):        if num > 0:            if len(result) > 0:                result += sep            result = "{}{}{}".format(result,num,sym)        return result        result = ""    result = add_to_result(result, td.days, 'd', sep)    result = add_to_result(result, td.seconds // 3600, 'h', sep)    result = add_to_result(result, (td.seconds // 60 ) % 60, 'm', sep)    result = add_to_result(result, td.seconds % 60, 's', sep)    return result            def assert_bounds(x,lb=None,ub=None):
    if lb is not None and x < lb:
        raise RuntimeError("Value {} is smaller than lower bound {}.".format(x,lb))
    if ub is not None and x > ub:
        raise RuntimeError("Value {} is greater than upper bound {}.".format(x,ub))
    return x
    
def assert_path(x):
    x = os.path.realpath(x)
    if not os.path.exists(x):
        raise RuntimeError("'{}' does not exist as a path on this system.".format(x))
    return x        
    
def assert_list_of_strings(x):
    assert isinstance(x, (list, tuple))
    assert sum([isinstance(xx,basestring) for xx in x]) == len(x)
    return x
    
def assert_file_list(x,list_len):
    """
    Throws if x does not check out as having len(x) == list_len, and if elements (0, 1, 2) are
    not accessible or do not exist as files.
    
    @type x: list
    @param x: expected to be a list of filenames of length list_len
    
    @rtype: list
    @return: x
    """
    if not len(x) == list_len:        raise RuntimeError("Value does not have len == {:d}".format(list_len))    x = [os.path.realpath(xx) if xx is not None else None for xx in x]    assert(len(x) == list_len)    for xx in x:        if (xx is not None) and (not os.path.exists(xx)):            raise RuntimeError("'{:s}' does not exist as a path on this system.".format(xx))    return x

# ---------------------------------------        
# at the command line:
#  1. drop a json template
#  2. put all params on the command line
#  3. load params from a json file (and possibly augment with params on the command line)  
class CommandLineTool:
    def __init__(self,parser,creator):
        """
        Populates an ArgumentParser, parses the command line arguments, and saves the 
        non-Params user arguments in easily accessible places. After calling this 
        constructor, the calling script should either save a template file to disk, or
        start the process of populating the creator with user data. 
        
        @type parser: argparse.ArgumentParser
        @type creator: class derived from Creator
        @param creator: default creator of the given class, that is, no non-default, 
            non-empty arguments
        """
        
        self.parser = parser
        self.creator = creator
        
        # populate with arguments
        self.parser.add_argument("-t", "--template", help="""output a config.json template 
            for {:s}""".format(self.creator.params.get_class_name()), action='store_true')
        self.parser.add_argument("-o", "--out_dir", help="""parent folder for config.json 
            (if --template), or out_dir for {:} (otherwise)""".format(
            self.creator.get_class_name()), default='.')
        self.parser.add_argument("-r", "--resources_dir", help="""directory for storing 
            resources (typically to be shared between multiple simulations)""")
        self.parser.add_argument("-c", "--config_file", help="""json file describing a 
            {:s} object (will be loaded and then any individual command-line parameters 
            will overwrite its values)""".format(self.creator.params.get_class_name()))
        for description in self.creator.params.schema().values():
            self.parser.add_argument("--{:s}".format(description.name), 
                                     help=description.desc_str(),
                                     nargs=description.n)
        
        # parse arguments
        self.__args = self.parser.parse_args()
        
        # populate creator paths and config_file path
        self.creator.out_dir = self.__args.out_dir        
        self.creator.resources_dir = self.__args.resources_dir
        self.config_file = self.__args.config_file        
        
    def save_template(self):
        """
        @rtype: boolean
        @return: returns true if the user requested a template config.json
        """
        return self.__args.template
        
    def finalize_params(self):
        """
        Overwrites self.creator.params values set by command-line arguments.
        """
        args_dict = vars(self.__args)
        for name, description in self.creator.params.schema().items():
            if (name in args_dict) and (args_dict[name] is not None):
                self.creator.params[name] = args_dict[name]
        

     
