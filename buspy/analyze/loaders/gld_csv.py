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
Created on June 9, 2014

@author: Tim Hansen

csv functions.  Will load the files into the data-holder classes.  

Functions:
    CsvGridlab(filename) - takes a csv filename and returns a filled GridlabData class

Requirements:
    numpy
    pandas
    
To-Do List:
    TODO: only load a specific range of dates/times
'''

################################################################################################
#### IMPORTS
################################################################################################

from __future__ import print_function
import numpy as np
import linecache
import pandas as pd
from array import *

from buspy.analyze.gridlabd import _strip_prefix_asarray as _strip
import buspy.analyze.gridlabd as gridlabd

#for complex conversion
import re
from igms.run.bus_utils.comm.gridlabcomm import COMPLEX_REGEX_PATTERN
import cmath
from igms.run.bus_utils.comm.gridlabcomm import str_to_complex

############################
# CONSTANTS
############################

NUM_SKIP_ROWS = 9 #[file,date,user,host,group,property,limit,interval,col_label]
LABEL_ROW = 8
TYPE_ROW = 5 #contains information we can determine GRIDLAB filetype from
PROPERTY_ROW = 6 #contains the property measured for some filetypes

#identifiers that can be used to determine the filetype
_GRIDLAB_FILETYPE = {
    'target.... ':gridlabd._G_TARGET,
    'class=meter':gridlabd._G_GROUP_METER,
    'class=node':gridlabd._G_GROUP_NODE,
    'class=ZIPload':gridlabd._G_GROUP_ZIPLOAD
}

_GRIDLAB_DELIMITER = {
    gridlabd._G_TARGET:('.... ',1),
    gridlabd._G_GROUP_METER:('. ',1),
    gridlabd._G_GROUP_NODE:('. ',1),
    gridlabd._G_GROUP_ZIPLOAD:('groupid=',1)           
}

############################
# UTILITY FUNCTIONS
############################
def is_complex_str(value_str):
    '''
    converts the rectangular or polar string into a complex number
    '''
    is_complex = True
    
    try:
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
            _ = cmath.rect(_mag, _ang * (cmath.pi/180.0))
        #rectangular.  if it ends in 'i', replace with 'j' so casting to complex works
        elif val_str[-1]=='i':
            val_str = val_str.replace('i', 'j')
            _ = complex(val_str)
        else:
            is_complex = False
    except ValueError:
        is_complex = False

    return is_complex

#used to clean the input data of switches from CLOSED/OPEN to 1/0
def conv_data(x,comp_ind,cur_line,skip_rows=True):
    #replace switches
    ret = str(x).replace('CLOSED','1').replace('OPEN', '0')
    
    #fix complex values
    dat = ret.strip('\n').split(',')
    
    #for some reason gen_from_txt sends the skipped lines to conv_data, don't do anything with them
    if (not skip_rows or (skip_rows and (cur_line >= NUM_SKIP_ROWS))) and ('end of tape' not in dat[0]):
        ret = ''

        for i,s in enumerate(dat):
            if i in comp_ind:
                val = str_to_complex(s)
                ret += '%s,%s,' % (str(val.real),str(val.imag))
            else:
                ret += '%s,' % s
        
    return ret.rstrip(',')

def get_indeces_of_complex(test_line):
    ret = []
    for i,s in enumerate(test_line.strip('\n').split(',')):
        
        try:
            if is_complex_str(s):
                ret.append(i)
        except ValueError as e:
            pass
        
    return ret

def common_load(filename,prefix=None):
    _ret = gridlabd.GridlabData()
    
    #filetype
    _type_line = None
    _property_line = None
    
    #load column labels.  weird hacky stuff to remove '# timestamp' label and get all correct values
    with open(filename) as f:
        #attempt to check for complex values
        complex_indices = get_indeces_of_complex(linecache.getline(filename, LABEL_ROW+2))

        #lines are 1 indexed, hence LABEL_ROW+1.  split if complex name.
        _ret.names = linecache.getline(filename, LABEL_ROW+1).strip('\n').split(',')
        __add = 0
        for c_ind in complex_indices:
            _ret.names.insert(c_ind+__add+1,_ret.names[c_ind+__add] + '.imag')
            _ret.names[c_ind+__add] += '.real'
            __add+=1

        _ret.names = np.array(_ret.names, dtype=np.str)
        
        _type_line = linecache.getline(filename, TYPE_ROW)
        _property_line = linecache.getline(filename, PROPERTY_ROW)
        
    #determine filetype
    for key in _GRIDLAB_FILETYPE.keys():
        if key in _type_line:
            _ret._filetype = _GRIDLAB_FILETYPE[key]
     
    #check that the correct filetype is found       
    if _ret._filetype == None:

        raise IOError('unknown GridLAB-D filetype, please create issue on Github for @thansen with the file that failed')
    
    #switch off _ret._filetype to determine how to continue
    #_G_TARGET - get target name from _type_line, property names from LABEL_ROW+1, numpy loadtxt 'CLOSED' = 0, 'OPEN' = 1
    # _G_GROUP_METER - get property from PROPERTY_ROW, asset names from LABEL_ROW+1 (should already be in .names)
    # _G_GROUP_NODE - same as _G_GROUP_METER
    # _G_GROUP_ZIPLOAD - get groupid from _type_line, one column of data with name on LABEL_ROW+1
    
    #for METER and NODE, get the unit being measured.  for TARGET, get object name.  for ZIPLOAD, get groupid.
    if (_ret._filetype == gridlabd._G_GROUP_METER) or (_ret._filetype == gridlabd._G_GROUP_NODE):
        _ret.groupid = _property_line.split(_GRIDLAB_DELIMITER[_ret._filetype][0])[_GRIDLAB_DELIMITER[_ret._filetype][1]].rstrip('\n')
    else:
        _ret.groupid = _type_line.split(_GRIDLAB_DELIMITER[_ret._filetype][0])[_GRIDLAB_DELIMITER[_ret._filetype][1]].rstrip('\n')
    
    #calculate the number of columns in the dataset
    _ret.number = _ret.names.shape[0] - 1
    _ret.names = _ret.names[1:_ret.number+1]
    if prefix != None:
        _ret.names = _strip(_ret.names, prefix)
        
    return _ret, complex_indices

def get_line_offsets(filename,num_ranks,skip_lines=NUM_SKIP_ROWS):
    line_indices = []
    with open(filename) as f:
        curr_ind = 0
        for i,line in enumerate(f):
            if i >= skip_lines:
                line_indices.append(curr_ind)
            curr_ind += len(line)
        line_indices.append(curr_ind)
        
    read_indices = []
    index_offsets = []
    chunk_size = len(line_indices)/float(num_ranks)
    partition = 0
    for i in range(num_ranks):
        offs_min = int(round(partition))
        offs_max = int(round(partition+chunk_size))
        if i == num_ranks-1:
            offs_max -= 1
        read_indices.append( (line_indices[offs_min] , line_indices[offs_max]) )
        index_offsets.append( (offs_min, offs_max) )
        partition += chunk_size
        
    return read_indices, index_offsets, offs_max

#############################################################################################################################
# GRIDLAB-D
#############################################################################################################################   
def CsvGridlab(filename,prefix=None,dtype=np.float):
    '''
    Loads the gridlab output from a csv to GridlabData.
    
    Keyword Arguments:
        filename - csv file to load
        prefix - string to strip from the gridlabd names
    '''
    _ret, complex_indices = common_load(filename,prefix)
    
    _ret.time = pd.to_datetime(np.loadtxt(filename, delimiter=',', skiprows=NUM_SKIP_ROWS, dtype=np.str, usecols=(0,)))
    
    #iterate through the data lines and replace the string using conv_switch.
    _ret.data = pd.DataFrame(np.genfromtxt((conv_data(x,complex_indices,i) for i,x in enumerate(open(filename))),delimiter=',', 
                                           skip_header=NUM_SKIP_ROWS,usecols=np.arange(1,_ret.number+1),dtype=dtype), 
                                           columns=_ret.names, index=_ret.time)
    
    return _ret


def ParallelCsvGridlab(filename,prefix=None,dtype=np.float,root=0):
    try:
        from mpi4py import MPI
        rank = MPI.COMM_WORLD.rank
        size = MPI.COMM_WORLD.size
    except ImportError:
        print('ParallelCsvGridlab could not load MPI.  Defaulting to serial read.')
        return CsvGridlab(filename,prefix,dtype), None, None
    
    #get common items (column names, etc.)
    _ret, complex_indices = common_load(filename,prefix)
    
    #get the file offset for the parallel read
    line_indices = []
    offset_indices = []
    num_lines = -1
    if rank == root:
        line_indices,offset_indices, num_lines  = get_line_offsets(filename,size)
    file_offset_range = MPI.COMM_WORLD.scatter(line_indices, root=root)
    offset_indices = MPI.COMM_WORLD.scatter(offset_indices, root=root)
    num_lines = MPI.COMM_WORLD.bcast(num_lines,root=root)
    
    #parallel read.  each rank will get a chunk of the csv file.
    mpi_file = MPI.File.Open(MPI.COMM_WORLD, filename)
    mpi_file.Seek(file_offset_range[0])
    #character buffer
    buffer = array('c', '\0' * (file_offset_range[1]-file_offset_range[0]))
    mpi_file.Read([buffer,MPI.CHARACTER])
    
    #convert to pandas dataframe
    data = buffer.tostring()
    _ret.time = pd.to_datetime(np.loadtxt((x for x in data.split('\n')), delimiter=',', dtype=np.str, usecols=(0,)))
    
    _ret.data = pd.DataFrame(np.genfromtxt((conv_data(x,complex_indices,i,False) for i,x in enumerate(data.split('\n'))),delimiter=',', 
                                           usecols=np.arange(1,_ret.number+1),dtype=dtype), 
                                           columns=_ret.names, index=_ret.time)
    
    return _ret, offset_indices, num_lines



