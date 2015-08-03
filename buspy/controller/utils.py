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
Created on Aug 3, 2015

@author: thansen

Utility functions for the controller.
'''

#########################################################
# GridLAB-D Parameters from GLM File
#########################################################

def get_glm_objects_by_type(glm_obj,type_str):
    '''
    Returns a list of glm objects by type.
    '''
    return glm_obj.get_objects_by_type(type_str)

def get_glm_property_by_type(glm_obj,type_str,prop):
    '''
    Returns a list of a specific property of glm objects by type.
    '''
    ret = []
    for obj in get_glm_objects_by_type(glm_obj,type_str):
        ret.append(obj[prop])
    return ret

def get_glm_names_by_type(glm_obj,type_str):
    '''
    Returns a list of names of objects of a given type.
    '''
    return get_glm_property_by_type(glm_obj,type_str,'name')


##########################################################
# GridLAB-D Parameters from Active GridlabBus Object
##########################################################

import buspy.comm.message as message
import buspy.bus as bus

def get_gld_properties_from_list(in_bus,names,prop):
    '''
    Returns a list of properties in the same order as the list of specified names.
    '''
    ret = {}
    inputs = message.MessageCommonData()
    
    for name in names:
        inputs.add_param(message.CommonParam(name=name, param=prop))
        
    temp_out = in_bus.transaction(outputs=inputs,overwrite_output=True,trans_state=bus.Bus.TRANSACTION_OUTPUTS)
    
    for name in names:
        ret[name] = temp_out.get_param(name,prop).value
        
    return ret


