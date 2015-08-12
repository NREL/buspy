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
Created on July 6, 2015

@author: thansen

The controller module will allow more fine control of
a gridlabd bus. This class may be used after a GridlabBus
has been opened, between transactions (i.e., GridLAB-D is
currently paused).
'''

from __future__ import print_function
import buspy.bus as bus
#from glmgen.feeder import GlmFile
import utils
import os
import json
import models
from buspy.controller.eventqueue import Event

class SetpointEvent(Event):
    def __init__(self,simulator,controller,model,setpoint):
        #TODO: setpoint, model
        super(SetpointEvent,self).__init__(simulator)
        self.controller = controller
        self.model = model
        self.setpoint = setpoint
        
    def execute(self):
        new_setpoint = self.model.update_state(self.simulator.current_time,self.setpoint)
        self.controller.send_setpoint(new_setpoint)
        self.simulator.print_statement(str(new_setpoint))

class Controller(object):
    def __init__(self,gridlab_bus):
        '''
        Keeps track of the gridlab bus and associated glm file.
        '''
        assert isinstance(gridlab_bus,bus.GridlabBus)
        
        self.bus = gridlab_bus
        #self.glm = GlmFile.load(self.bus._comm._info.filename)
        
    def set_gld_from_json_str(self,json_str,time=None):
        set_points = json.loads(json_str)
        self.models = {}
        
        cur_time = self.bus.sim_time.current_time if time == None else time

        for model_type,model_arr in set_points.iteritems():
            for json_obj in model_arr:
                model = models.json_to_model(model_type, json_obj,cur_time)
                self.models[model.name] = model
    
    
    def set_gld_from_json_file(self,json_file,time=None):
        with open(json_file) as f:
            s = f.read()
        self.set_gld_from_json_str(s,time)
        
    def send_setpoint(self,setpoint):
        utils.send_param(self.bus, setpoint)
        
    def add_events(self,simulator):
        #TODO: this only works if there is one setpoint per model per time. Fix this workflow!
        #iterate through model schedules and add events for each change in set point
        for m in self.models.itervalues(): 
            set_keys = m.setpoints.keys()
            for i_key in set_keys: #the key is also the time to change the setpoint
                setpoint = m.setpoints.pop(i_key)
                simulator.schedule(SetpointEvent(simulator,self,m,setpoint),time=i_key)
        
        
def load_controller_from_json(bus_json_file,path='.'):
    the_bus = bus.load_bus(path, fname=bus_json_file)
    
    the_bus.start_bus()
    
    return Controller(the_bus)
 
            
        