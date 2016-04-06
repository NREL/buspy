'''
[LICENSE]
Copyright (c) 2008-2015, Alliance for Sustainable Energy.
All rights reserved.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

If you use this work or its derivatives for research publications, please cite:
Timothy M. Hansen, Bryan Palmintier, Siddharth Suryanarayanan, 
Anthony A. Maciejewski, and Howard Jay Siegel, "Bus.py: A GridLAB-D 
Communication Interface for Smart Distribution Grid Simulations," 
in IEEE PES General Meeting 2015, July 2015, 5 pages.
[/LICENSE]
@author Tim Hansen

Creation date: 3/16/3015

Summary: Example use cases for buspy.  

Usage:
    nosetests bus_nosetest.py:TestBus.<test_case>
    
Test cases:
    testConstantBus
    testConstantBusManualOpen - uses manual start, stop of the bus (instead of 'with' statement)
    testConstantBusTranslator - constant bus with a BusTranslator object attached
    testFileBus
    testFileBusTranslator - file bus with a BusTranslator object attached
'''

#######################################################################################
# Imports
#######################################################################################

from unittest import TestCase

from buspy.bus import open_bus
from buspy.bus import load_bus
from buspy.comm.message import CommonParam
from buspy.comm.message import MessageCommonData
from buspy.bus import AggregatorBusTranslator

from numpy import random

#######################################################################################
# Utility Functions
#######################################################################################

def translator_out_to_string(o):
    '''
    Takes the output from a bus.transaction and returns a formatted string.
    
    o should be from AggregatorBusTranslator.translate_output
    '''
    NAME = 'summed_power'
    PARAM = None
    return '[%s] %s.%s=%f + j%f' % (str(o[AggregatorBusTranslator.IN_TIME_KEY]),NAME,PARAM,o[AggregatorBusTranslator.OUT_P_RE_KEY],o[AggregatorBusTranslator.OUT_P_IM_KEY]) 

def out_to_string(o):
    '''
    Takes the output from a bus.transaction and returns a formatted string.
    '''
    NAME = 'house_test'
    PARAM = 'air_temperature'
    return '[%s] %s.%s=%s' % (str(o.time),NAME,PARAM,str(o.get_param(NAME,PARAM).value))


def translator_multinode_input():
    __dict = {}
    __dict[AggregatorBusTranslator.IN_V_RE_KEY] = random.normal(1.0,0.05)
    __dict[AggregatorBusTranslator.IN_V_IM_KEY] = random.normal(0,0.1)
    return __dict

def message_gld_input():
    '''
    Randomly assigns a kW power rating to the GridLAB-D house load.
    '''
    NAME = 'example_climate'
    PARAM = 'temperature'
    
    transfer = MessageCommonData()
    
    transfer.add_param(CommonParam(name=NAME,param=PARAM,value=abs(random.normal(80.0,10.0))))
    
    return transfer

#######################################################################################
# Unit Test Class
#######################################################################################

class TestBus( TestCase ):
    '''
    Python unit test to be used with nosetests.
    
    Usage:
    
        nosetests bus_nosetest.py:TestBus.<test_case>
        
        where <test_case> is:
            testConstantBus
            testConstantBusManualOpen
            testConstantBusTranslator
            testFileBus
            testFileBusTranslator
            
    '''
    
    def testConstantBus(self):
        '''
        Example using a ConstantBus.
        '''
        FILENAME = 'constant_bus.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=None)
                print out_to_string(__out)
    
        print 'bus finished'
        
    def testConstantBusManualOpen(self):
        '''
        Example using a ConstantBus.  Manually load, start, 
        and stop bus (instead of using 'with' statement)
        '''
        FILENAME = 'constant_bus.json'
        
        bus = load_bus('.',FILENAME)
        bus.start_bus()
        while not bus.finished:
            __out = bus.transaction(inputs=None)
            print out_to_string(__out)
        bus.stop_bus()
        print 'bus finished'
        
    def testConstantBusTranslator(self):
        '''
        Example using a ConstantBus with an AggregatorBusTranslator.
        '''
        FILENAME = 'constant_bus_translator.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=None)
                print translator_out_to_string(__out)
    
        print 'bus finished'
        
    
    def testFileBus(self):
        '''
        Example using a FileBus.
        '''
        FILENAME = 'file_bus.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=None)
                print out_to_string(__out)
    
        print 'bus finished'
        
    def testFileBusTranslator(self):
        '''
        Example using a FileBus with an AggregatorBusTranslator.
        '''
        FILENAME = 'file_bus_translator.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=None)
                print translator_out_to_string(__out)
    
        print 'bus finished'
        
    def testGridlabBus(self):
        '''
        Example using a GridlabBus.  Will change the base_power for the load
        house0_agg_R4-25-00-1_tm_1_R4-25-00-1_tn_141 at each timestep. Will
        then query the network_node power.
        '''
        FILENAME = 'gridlabd_bus.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=message_gld_input())
                print out_to_string(__out)
    
        print 'bus finished'
        
    def testGridlabBusWithPath(self):
        '''
        Example using a GridlabBus.  Will change the base_power for the load
        house0_agg_R4-25-00-1_tm_1_R4-25-00-1_tn_141 at each timestep. Will
        then query the network_node power.
        '''
        FILENAME = 'gridlabd_bus.json'
        PATHNAME = 'C:\\Program Files (x86)\\GridLAB-D\\bin'
        
        bus = load_bus('.',FILENAME)
        bus.set_path(PATHNAME)
        bus.start_bus()
        while not bus.finished:
            __out = bus.transaction(inputs=message_gld_input())
            print out_to_string(__out)
        bus.stop_bus()
    
        print 'bus finished'
        
    def testGridlabBusExternal(self):
        '''
        Example using a GridlabBus with an external GLD.  Will change the base_power for the load
        house0_agg_R4-25-00-1_tm_1_R4-25-00-1_tn_141 at each timestep. Will
        then query the network_node power.
        '''
        FILENAME = 'gridlabd_bus_external_gld.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=message_gld_input())
                print out_to_string(__out)
    
        print 'bus finished'
        
    def testMultiNodeBusTranslator(self):
        '''
        Example using a MultiNodeBus with Translator object.
        '''
        FILENAME = 'multi_bus_translator.json'
        
        with open_bus(FILENAME) as bus:
            while not bus.finished:
                __out = bus.transaction(inputs=translator_multinode_input())
                print translator_out_to_string(__out)
    
        print 'bus finished'
        
    
        