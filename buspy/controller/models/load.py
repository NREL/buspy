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
Created on Aug 10, 2015

@author: thansen
'''

from buspy.controller.models import Model

class Load(Model):
    '''
    TODO: initial setpoint?
    '''
    
    JSON_STRING = 'LOADS'
    
    JSON_SCHEDULE   = 'DemandSchedule'
    
    
    KEY_GLD_PARAM = 'base_power'

    def __init__(self,name,bus_num,glm_bus_name,start_time,initial_value=0.0):
        '''
        Constructor
        '''
        super(Load,self).__init__(name,bus_num,glm_bus_name,start_time)
        
        self.current_load = initial_value
        
        
    def parse_schedule(self,sch,param):
        super(Load,self).parse_schedule(sch,param)
        
    def _local_update(self,setpoint):
        self.current_load = setpoint.value
        return setpoint
        
    @staticmethod
    def json_to_load(json_obj,start_time):
        name,busnum,glmname = Model.json_common_model_params(json_obj)
        load =  Load(name,busnum,glmname,start_time)
        
        load.parse_schedule(json_obj[Load.JSON_SCHEDULE],Load.KEY_GLD_PARAM)
        
        return load
        
        
        
#TODO: 3-phase load. 'base_power_A', etc.
#TODO: imaginary load. 'base_power' = sqrt(P^2 + Q^2), 'power_pf' = cos(tan^-1(Q/P))
#TODO: 3-phase load with imaginary. 'base_power_A', 'power_pf_A', etc.

'''
try:
    pf = cos(tan^-1(Q/P))
except ZeroDivisionError:
    #if P=0, pf=0 (purely reactive power injection)
    pf = 0.0
'''
        
        
        
        