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

Created on Apr 27, 2015

@author: thansen

@summary: Python script that will take a GridLAB-D .glm file and create
          the proper .json input.
'''

import argparse
from collections import OrderedDict
import buspy.comm.message as message
import buspy.bus as bus
import os

CMD_ARGS = OrderedDict()

CMD_ARGS['glm_file']    = (
            [],
            {
                'type'  : str,
                'help'  : 'GridLAB-D glm input filename'
            }
)


def get_properties_from_list(in_bus,names,prop):
    ret = {}
    inputs = message.MessageCommonData()
    
    for name in names:
        inputs.add_param(message.CommonParam(name=name, param=prop))
        
    temp_out = in_bus.transaction(outputs=inputs,overwrite_output=True,trans_state=bus.Bus.TRANSACTION_OUTPUTS)
    
    for name in names:
        ret[name] = temp_out.get_param(name,prop).value
        
    return ret


if __name__ == '__main__':
    ####
    #ARGUMENT PARSER
    ###
    parser = argparse.ArgumentParser(description="""Script for adding
    generating a buspy input JSON file from a GLM.""")
    
    #add the arguments from ARGS
    for key in CMD_ARGS.keys():
        parser.add_argument(key, *CMD_ARGS[key][0], **CMD_ARGS[key][1])
     
    args = parser.parse_args()
        
    try: #use glmgen to dynamically find nodes
        from glmgen.feeder import GlmFile
         
        #load the GLM file
        glm = GlmFile.load(args.glm_file)
         
        #these are nodes in the powerflow
        network_nodes = []
        for obj in glm.get_objects_by_type('node'): #glm.itervalues():
            #print obj['name']
            network_nodes.append(obj['name'])
        for obj in glm.get_objects_by_type('load'): #workaround because of network issue from glmgen output
            #print obj['name']
            network_nodes.append(obj['name'])
    except: #hardcoded workaround so Umer can run this test code without the glmgen code
        network_nodes = ['Node633', 'Node630', 'Node632', 'Node680', 'Node684', 'Load646_strip_node', 'Load634', 'Load645', 'Load646', 'Load652', 'Load671', 'Load675', 'Load692', 'Load611', 'Load6711', 'Load6321']
        
    #set up the IEEE 13-Node bus to test get_properties_from_list
    ieee_bus = bus.load_bus(path=os.path.dirname(args.glm_file), fname='dist_cont_bus.json')
        
    ieee_bus.start_bus()
    
    #get voltage_A at each node at each point in time. 
    with open(os.path.join(os.path.dirname(args.glm_file),'test_output.txt'),'w') as f:
        while not ieee_bus.finished:
            volt_a = get_properties_from_list(ieee_bus,network_nodes,'voltage_A')
            print ieee_bus.sim_time
            f.write(str(ieee_bus.sim_time) + '\n')
            
            for name,val in volt_a.iteritems():
                out_str = '\t%s=%s' % (name,str(val))
                print out_str
                f.write(out_str + '\n')
                
            ieee_bus.transaction(outputs=message.MessageCommonData(),overwrite_output=True)
        
    ieee_bus.stop_bus()
    
    
#     print '\nLOADS'
#     #iterate through houses, find children loads
#     for obj in glm.get_objects_by_type('house'):
#         print obj['name']
#         for ch_key in glm.get_children_keys(glm.get_object_key_by_name(obj['name'])):
#             print '\t',glm[ch_key]['name']





