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
Created on August 18, 2014

@author: Tim Hansen

action.py

An abstract 'action' to take on a set of outputs from a Bus.

Classes:
    Action            - base class
    SumAction         - sum the given parameters
    DifferenceAction  - subtract the given parameters.  The first input is assumed to be the minuend 
    ProductAction     - multiply the given parameters.
    QuotientAction    - divide the given parameters. The first input is assumed to be the dividend.

Requirements:
    
    
To-Do List:
    TODO: use numpy ufuncs and numpy arrays instead for performance
'''

######################################################################
# IMPORTS
######################################################################

import buspy.comm.message as message

######################################################################
# CONSTANTS
######################################################################

SUM_KEY     = 'sum'
DIFF_KEY    = 'difference'
PROD_KEY    = 'product'
QUOT_KEY    = 'quotient'

ACTION_KEY          = 'action'
NAME_KEY            = 'name'
ACTION_LIST_KEY     = 'action-list'
PARAM_KEY           = 'param'

######################################################################
# UTILITY FUNCTIONS
######################################################################

def json_to_action(action_item):
    action_type = action_item[ACTION_KEY]
    
    action = {
                   
        SUM_KEY     :   SumAction,
        DIFF_KEY    :   DifferenceAction,
        PROD_KEY    :   ProductAction,
        QUOT_KEY    :   QuotientAction
                   
    }.setdefault(action_type,None)
    
    if action == None:
        raise Exception('Unknown action type: ' + str(action_type))
    
    return action(action_item[NAME_KEY], action_item[ACTION_LIST_KEY])

######################################################################
# CLASSES
######################################################################

##########################################################
# Action
##########################################################

class Action(object):
    def __init__(self,name,action_list):
        self.name = name
        
        #loop through the list of inputs and put them into a data structure
        self.action_names = []
        
        for a in action_list:
            self.action_names.append((a[NAME_KEY],a[PARAM_KEY]))

        
    def execute(self,input_list):
        '''
        Takes a list of inputs, executes the action, and returns a single output.
        
        Parameters:
            input_list - array (or list) of message.CommonParam arrays (or lists).  I.e., [[CommonParams,...],[CommonParams,...]].  There should be one element for each node under the MultiNodeBus.
            
        Outputs:
            single output of actioned-items
            
        TODO: should this be more general than just for MultiNodeBus?  Could be useful for decoding formats, etc.
        '''
        ordered_input = []
        
        #in order, add values to input list
        for a in self.action_names:
            for node in input_list:
                if (a[0] in node) and (a[1] in node[a[0]]):
                    ordered_input.append(node[a[0]][a[1]].value)
                
        #perform action on ordered_input        
        if len(ordered_input) == 1:
            output = self._none_handler(ordered_input[0])
        elif len(ordered_input) == 0:
            output = None
        else:
            output = self._local_action(ordered_input[0], ordered_input[1])
            index = 2
            
            while(index < len(ordered_input)):
                output = self._local_action(output, ordered_input[index])
                index += 1
            
        #return the output as a CommonParam
        param_output = message.CommonParam()
        param_output.name = self.name
        param_output.value = output
        return param_output
        
    
    def _local_action(self,a,b):
        '''
        Performs a-action-b, returns one number.
        '''
        raise Exception('Action objects should implement _local_action(a,b)')
    
    def _none_handler(self,a):
        '''
        If the list is only one element long, what should be returned?  Defaults to return a
        '''
        return a
    
    
    def __find_value_from_input_list(self,name,param,in_list):
        for _in in in_list:
            if _in.name == name and _in.param == param:
                return _in.value
            
        return None
    
##########################################################
# SumAction
##########################################################

class SumAction(Action):
    def __init__(self,name,action_list):
        super(SumAction,self).__init__(name,action_list)
        
    def _local_action(self,a,b):
        '''
        Returns a + b
        '''
        return a+b
    
##########################################################
# ProductAction
##########################################################

class ProductAction(Action):
    def __init__(self,name,action_list):
        super(ProductAction,self).__init__(name,action_list)
        
    def _local_action(self,a,b):
        '''
        Returns a * b
        '''
        return a*b
    
##########################################################
# DifferenceAction
##########################################################

class DifferenceAction(Action):
    def __init__(self,name,action_list):
        print 'WARNING: DifferenceAction may produce unintended output based on the ordering of actions.'
        super(DifferenceAction,self).__init__(name,action_list)
        
    def _local_action(self,a,b):
        '''
        Returns a - b
        '''
        return a-b
    
##########################################################
# QuotientAction
##########################################################

class QuotientAction(Action):
    def __init__(self,name,action_list):
        print 'WARNING: QuotientAction may produce unintended output based on the ordering of actions.'
        super(QuotientAction,self).__init__(name,action_list)
        
    def _local_action(self,a,b):
        '''
        Returns a / b
        '''
        return a/b

