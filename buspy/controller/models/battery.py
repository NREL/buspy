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

class Battery(Model):
    '''
    classdocs
    '''
    JSON_STRING = 'STORAGE DEVICES'
    
    
    JSON_MAXENERGY  = 'MaxEnergy'
    JSON_MINENERGY  = 'MinEnergy'
    JSON_MAXCHARGE  = 'MaxChargeSpeed'
    JSON_MAXDCHARGE = 'MaxDischargeSpeed'
    JSON_CHARGEFF   = 'ChargingEfficiency'
    JSON_DCHARGEFF  = 'DischargingEfficiency'
    
    JSON_SCHEDULE   = 'StorageSchedule'

    def __init__(self,name,bus_num,glm_bus_name,min_energy,max_energy,
                 max_charge_speed,max_discharge_speed,charging_eff,discharging_eff):
        '''
        Constructor
        '''
        super(Battery,self).__init__(name,bus_num,glm_bus_name)
        self.min_energy = float(min_energy)
        self.max_energy = float(max_energy)
        self.max_charge_speed = float(max_charge_speed)
        self.max_dcharge_speed = float(max_discharge_speed)
        self.charging_efficiency = float(charging_eff)
        self.discharging_efficiency = float(discharging_eff)
        
        
    @staticmethod
    def json_to_battery(json_obj):
        name,busnum,glmname = Model.json_common_model_params(json_obj)
        batt =  Battery(name,busnum,glmname,
                       json_obj[Battery.JSON_MAXENERGY],
                       json_obj[Battery.JSON_MINENERGY],
                       json_obj[Battery.JSON_MAXCHARGE],
                       json_obj[Battery.JSON_MAXDCHARGE],
                       float(json_obj[Battery.JSON_CHARGEFF])/100.0,
                       float(json_obj[Battery.JSON_DCHARGEFF])/100.0)
        
        batt.parse_schedule(json_obj[Battery.JSON_SCHEDULE])
        
        return batt

        
        
        