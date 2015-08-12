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

import os

from buspy.controller import Controller
from buspy.controller import load_controller_from_json

from buspy.controller.eventqueue import ControllerSimulator
from buspy.controller.eventqueue import EmptyQueue

if __name__ == '__main__':
    #input files
    os.chdir('C:\\Research\\Code\\Git\\buspy-public\\bin\\test_data\\')
    bus_json = 'dist_cont_bus.json'
    control_json = 'DDESResultsIGMS.json'
    
    #load controller
    controller = load_controller_from_json(bus_json)
    
    #get simulation times
    start_time = controller.bus.sim_time.start_time
    end_time = controller.bus.sim_time.end_time
    
    #create a discrete event simulator
    sim = ControllerSimulator(start_time)
    
    #!!!!!!!!!obtain set points from DDES here!!!!!!!!!!!!!!
    controller.set_gld_from_json_file(control_json,sim.current_time)
    
    #add the set points to the simulator
    controller.add_events(sim)
    
    #MAIN CONTROL LOOP
    while not controller.bus.finished:
        sim.print_statement('New time step. Current gld time: %s' % str(controller.bus.sim_time.current_time))
        try:
            #perform setpoints with time <= current time
            while True:
                time,_ = sim.peek_event()
                
                if time <= sim.get_seconds_from_start(controller.bus.sim_time.current_time):
                    sim.step()
                else:
                    break
        except EmptyQueue:
            #no more setpoints, continue the gridlabd simulation
            sim.print_statement('Event queue is empty, continuing with GridLAB-D')
        
        #step gridlabd
        output = controller.bus.transaction()
        
        #NOTE: can pass GLD outputs back to DDES here if we want
        
    #perform any output wanted here
    
    #shutdown the bus
    controller.bus.stop_bus()
    
    
    