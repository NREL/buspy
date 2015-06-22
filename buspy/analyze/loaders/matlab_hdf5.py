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

hdf5 functions.  Will load the files into the data-holder classes.  

Functions:
    Hdf5Festiv(filename) - takes a hdf5 filename and returns a filled FestivData class
    Hdf5Matpower(filename) - takes a hdf5 filename and returns a filled MatpowerData class

Requirements:
    h5py
    numpy
    pandas
    
To-Do List:
    TODO: only load a specific range of dates/times
'''

################################################################################################
#### IMPORTS
################################################################################################

import h5py
import numpy as np
import pandas as pd
from buspy.analyze import _structs
from buspy.analyze import festiv
from buspy.analyze import matpower


############################
# CONSTANTS
############################
#MATPOWER and FESTIV bus type constants
__MP_BUS_PQ = 1 #load bus
__MP_BUS_PV = 2 #generator bus
__MP_BUS_SLACK = 3 #slack bus


#############################################################################################################################
# UTILITY FUNCTIONS
#############################################################################################################################
def __readHdf5(filename):
    '''
    __readHdf5 - initializes the specified .hdf5 file
    
    Keyword arguments:
    filename -- name of the .hdf5 file to load (required)
    
    Returns:
    h5py root directory file
    '''
    
    #read only
    return h5py.File(filename,'r')

#takes market directory, returns filled market data
def __load_market_data(h5_dir,bus_names):
    ret = _structs._FESTIV_MARKET()
    
    ret.time = np.array(h5_dir['time'])
    
    ret.lmp = pd.DataFrame(np.array(h5_dir['market']['lmp']), columns=bus_names, index=ret.time)
    
    #TODO: hack because RTSCUC.market.rp is missing 2 values.  change back to the line below once the .hdf5 file is correct
    #ret.rcp = pd.DataFrame(np.array(h5_dir['market']['rcp']), columns=self.bus.names, index=ret.time)
    
    _temp_rp = np.array(h5_dir['market']['rcp'])
    ret.rcp = pd.DataFrame(_temp_rp, columns=bus_names, index=ret.time[np.arange(np.size(_temp_rp[:,0]))])
    
    return ret
        
#############################################################################################################################
# FESTIV
#############################################################################################################################    
def Hdf5Festiv(filename):
    '''
    TODO: define Hdf5Festiv
    '''
    _base_dir =  __readHdf5(filename)
    _ret = festiv.FestivData()
    
    ######bus data########################
    _bus_dir = _base_dir['SYSTEM']['bus']
    
    _types = np.array(_bus_dir['type'])
    
    _ret.bus.number = _types.size
    _ret.bus.names = np.arange(_ret.bus.number) #TODO: update this when there are bus names in the Festiv hdf5 file
    _ret.bus.PQ_mask = np.array(_bus_dir['load_idx'])-1 #load_idx is one indexed
    
    #need the masks as bus names to properly index into the panda dataframes
    _ret.bus.PQ_mask    = _ret.bus.names[_ret.bus.PQ_mask]
    _ret.bus.PV_mask    = _ret.bus.names[(np.array(_bus_dir['type']) == __MP_BUS_PV).reshape((_ret.bus.number,))]
    _ret.bus.slack_mask = _ret.bus.names[(np.array(_bus_dir['type']) == __MP_BUS_SLACK).reshape((_ret.bus.number,))]
    
    ######AGC DATA########################
    _agc_dir = _base_dir['AGC']
    
    _ret.AGC.time = np.array(_agc_dir['time'])
    _ret.AGC.time = _ret.AGC.time.reshape((_ret.AGC.time.size,))
    _ret.AGC.Pd = pd.DataFrame(np.array(_agc_dir['bus']['Pd']), columns=_ret.bus.names, index=_ret.AGC.time)
    _ret.AGC.Pg = pd.DataFrame(np.array(_agc_dir['gen']['Pg']), columns=_ret.bus.names, index=_ret.AGC.time)
    
    ######MARKET DATA#####################
    _ret.DASCUC = __load_market_data(_base_dir['DASCUC'],_ret.bus.names)
    _ret.RTSCED = __load_market_data(_base_dir['RTSCED'],_ret.bus.names)
    _ret.RTSCUC = __load_market_data(_base_dir['RTSCUC'],_ret.bus.names)
    
    #close file
    _base_dir.close()
    
    return _ret

#############################################################################################################################
# MATPOWER
#############################################################################################################################
#if memory requirements become a problem, can load data on an as-needed basis.  keep the names/times in memory for accessing specific portions of the tables.  would need to create some abstract wrapper class that the *Data classes would hold to access the data.
#TODO: make helper functions for some of the loading pieces as they are very similar
#TODO: what if there is load on a generator bus?
def Hdf5Matpower(filename):
    '''
    TODO: define Hdf5Matpower
    '''
    _ret = matpower.MatpowerData()
    
    _base_dir =  __readHdf5(filename)
    
    #load base MVA
    _ret.baseMVA = int(_base_dir['baseMVA'][0])
    
    #load time indeces
    _ret.time = np.array(_base_dir['time'][:]).reshape((np.shape(_base_dir['time'])[0],))
     
    ##########################
    #INITIALIZE BUS DATA
    ##########################
    #get bus directory (i.e., /bus/)
    _bus_dir = _base_dir['bus']
     
    #get the number of buses in the system
    _ret.bus.number = np.shape(_bus_dir['type'])[0] #can get this number elsewhere if necessary
     
    #get a mask for the three bus types (boolean array)
    _ret.bus.PQ_mask    = np.squeeze(np.array(_bus_dir['type'][:] == __MP_BUS_PQ))
    _ret.bus.PV_mask    = np.squeeze(np.array(_bus_dir['type'][:] == __MP_BUS_PV))
    _ret.bus.slack_mask = np.squeeze(np.array(_bus_dir['type'][:] == __MP_BUS_SLACK))
     
    #load bus names
    _ret.bus.names      = np.array(_bus_dir['bus_id']).reshape((_ret.bus.number,))
     
    #load real power
    _ret.bus.P    = pd.DataFrame(np.array(_bus_dir['Pd']), columns=_ret.bus.names, index=_ret.time)
    
    #load reactive power
    _ret.bus.Q    = pd.DataFrame(np.array(_bus_dir['Qd']), columns=_ret.bus.names, index=_ret.time)
      
    #load voltage magnitude (in p.u.)
    _ret.bus.Vm   = pd.DataFrame(np.array(_bus_dir['Vm']), columns=_ret.bus.names, index=_ret.time)

    #load voltage angle
    _ret.bus.Va   = pd.DataFrame(np.array(_bus_dir['Va']), columns=_ret.bus.names, index=_ret.time)

    #voltage base/voltage magnitude in kV
    _ret.bus.baseKV = np.array(_bus_dir['baseKV']).reshape((_ret.bus.number,))
       
    ###########################
    #INITIALIZE GEN/SLACK DATA
    ###########################
    #new directory in the h5 file for gens
    _gen_dir = _base_dir['gen']
    
    _ret.gen.names  = np.squeeze(np.array(_gen_dir['bus']))
    _ret.gen.number = np.shape(_ret.gen.names)[0]
       
    #need new masks because the indeces may be different. sort of a hack to get this to work, probably a cleaner/faster/easier way.
    _ret.gen.PV_mask = np.zeros((np.array(_gen_dir['bus']).shape[0],))
    _ret.gen.slack_mask = np.zeros(_ret.gen.PV_mask.shape)
       
    #iterates through and checks whether the bus id is a slack bus or generator bus
    for i, bus in enumerate(np.array(_gen_dir['bus'][:])): #.reshape((self.NUM_BUS_PV+self.NUM_BUS_SLACK,))
        if np.size(np.where(_ret.bus.names[_ret.bus.PV_mask] == bus)[0]) > 0:
            #generator bus
            _ret.gen.PV_mask[i] = 1
        else:
            #slack bus
            _ret.gen.slack_mask[i] = 1
            
    #turn array into boolean array for masking purposes        
    _ret.gen.PV_mask = _ret.gen.PV_mask == 1
    _ret.gen.slack_mask = _ret.gen.slack_mask == 1
   
        
    #real power (in MW)
    _ret.gen.P    = pd.DataFrame(np.array(_gen_dir['Pg']), columns=np.squeeze(np.array(_gen_dir['bus'])), index=_ret.time)

    #reactive power (in MVAR)
    _ret.gen.Q    = pd.DataFrame(np.array(_gen_dir['Qg']), columns=np.squeeze(np.array(_gen_dir['bus'])), index=_ret.time)

    ###########################
    #INITIALIZE BRANCH DATA
    ###########################
    _brn_dir = _base_dir['branch']
          
    #Temp arrays
    _pf = np.array(_brn_dir['Pf'])
    _pt = np.array(_brn_dir['Pt'])
    _qf = np.array(_brn_dir['Qf'])
    _qt = np.array(_brn_dir['Qt'])
    _from = np.squeeze(np.array(_brn_dir['fbus']))
    _to = np.squeeze(np.array(_brn_dir['tbus']))
          
    #get the number of branches
    _ret.branch.number = np.shape(_pf)[1]
      
    _temp_names = []
    #names - str(from,to)
    for i in range(_ret.branch.number):
        _temp_names.append(str(_from[i]) + ',' + str(_to[i]))
          
    _ret.branch.names = np.squeeze(np.array(_temp_names, dtype=np.str))
          
    #temp arrays for calculating before placing in pd.DataFrame
    _sf = np.sqrt(np.square(_pf) + np.square(_qf))
    _st = np.sqrt(np.square(_pt) + np.square(_qt))
    _powff = np.abs(_pf) / _sf
    _powft = np.abs(_pt) / _st
          
    #complex power (MVA)
    _ret.branch.Sf   = pd.DataFrame(_sf, columns=_ret.branch.names, index=_ret.time)
    _ret.branch.St   = pd.DataFrame(_st, columns=_ret.branch.names, index=_ret.time)
          
    #power factor
    _ret.branch.powff  = pd.DataFrame(_powff, columns=_ret.branch.names, index=_ret.time)
    _ret.branch.powft  = pd.DataFrame(_powft, columns=_ret.branch.names, index=_ret.time)
    
    #real power (MW)
    _ret.branch.Pf   = pd.DataFrame(_pf, columns=_ret.branch.names, index=_ret.time)
    _ret.branch.Pt   = pd.DataFrame(_pt, columns=_ret.branch.names, index=_ret.time)
    
    #reactive power (MVAr)
    _ret.branch.Qf   = pd.DataFrame(_qf, columns=_ret.branch.names, index=_ret.time)
    _ret.branch.Qt   = pd.DataFrame(_qt, columns=_ret.branch.names, index=_ret.time)
          
    #close file
    _base_dir.close()
    
    return _ret