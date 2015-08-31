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
'''
from unittest import TestCase
import os
import numpy as np
from buspy.bus import open_bus
from buspy.bus import AggregatorBusTranslator
import buspy.comm.message as message
from buspy.bus import load_bus
from buspy.bus import set_default_bus
from buspy.bus import ConstantBus
from buspy.construct.bus_params import BusParams

#in case mpi4py is not setup properly
try:
    from cpest.run.igms.bus_aggregator import DefaultBus
except ImportError:
    class DefaultBus(object):
        """Simple bus to use when a full gridlabd bus is not needed.
    
        Only implemented transaction and stop_bus for minimum to work with existing
        code
        """
        def __init__(self,*args,**kargs):
            pass
    
        def transaction(self,input):
            """Return voltage*voltage/2800 as load for real and imag
            """
            output = {}
            output['load_real'] = input['voltage_real']**2/2800.
            output['load_imag'] = input['voltage_imag']**2/2800.
            output['bid'] = input['price']*0.75
            return output
    
        def stop_bus(self):
            pass

fld_name = 'B109'
bus_name = 'bus.json'

THIS_DIR = os.path.dirname(__file__)

dir_name = os.path.normpath(os.path.join(THIS_DIR, '..','..','..','test_scenario','distribution'))

class TestBus( TestCase ):
    
    def _load_time(self):
        #NOTE: this can be changed up to one hour if a longer test is needed
        self._time = message.CommonTimeInfo(start_time="2020-06-01 00:00:00",end_time="2020-06-01 00:05:00",delta=4)
        
    def _check_time(self):
        return self._time.current_time >= self._time.end_time
        
    def _load_default_bus(self,custom=False):
        if custom:
            default_bus_init = os.path.join(dir_name,'default_bus.json')
            set_default_bus(ConstantBus,BusParams.load(default_bus_init))
        else:
            set_default_bus(DefaultBus,None)
    
    def _aggregator_dict(self):
        __dict = {}
        __dict[AggregatorBusTranslator.IN_TIME_KEY] = str(self._time)
        __dict[AggregatorBusTranslator.IN_V_RE_KEY] = np.random.normal(1.0,0.05)
        __dict[AggregatorBusTranslator.IN_V_IM_KEY] = np.random.normal(0,0.1)
        
        return __dict
    
    def testContextManager(self):
        self._load_time()
        
        os.chdir(os.path.join(dir_name,fld_name))
        print '-------------------------'
        print 'RUNNING BUS: ' + os.path.join(dir_name, bus_name)
        print '-------------------------'
        print
           
        with open_bus(bus_name) as bus:
            while(not (bus.finished or self._check_time())):
                self._time.advance_time()
                __out = bus.transaction(self._aggregator_dict())
                print str(self._time) + ':' + str(__out[AggregatorBusTranslator.OUT_P_RE_KEY]) + '+ ' + str(__out[AggregatorBusTranslator.OUT_P_IM_KEY]) + 'j'
        
        assert True
        
    def testDefaultBus(self):
        self._load_time()
        
        self._load_default_bus(custom=False)
        bus = load_bus('INCORRECT_FOLDER_NAME')
        self.assertTrue(isinstance(bus,DefaultBus), 'Incorrect instance of the default bus was returned')
        
        #bus.start_bus()
        
        print '-------------------------'
        print 'RUNNING DEFAULT BUS'
        print '-------------------------'
        print
        
        while(True):
            self._time.advance_time()
            _ = self._aggregator_dict()
            _['price'] = np.random.normal(20.0,3.0)
            __out = bus.transaction(_)
            print str(self._time) + ':' + str(__out[AggregatorBusTranslator.OUT_P_RE_KEY]) + '+ ' + str(__out[AggregatorBusTranslator.OUT_P_IM_KEY]) + 'j'
                
            if not self._time.advance_time():
                break
            
        bus.stop_bus()
        
    def testDefaultBusConstant(self):
        self._load_time()
        
        self._load_default_bus(custom=True)
        bus = load_bus('INCORRECT_FOLDER_NAME')
        self.assertTrue(isinstance(bus,ConstantBus), 'Incorrect instance of the default bus was returned')
        
        bus.start_bus()
        
        print '-------------------------'
        print 'RUNNING CUSTOM DEFAULT BUS'
        print '-------------------------'
        print
        
        while(not (bus.finished or self._check_time())):
            self._time.advance_time()
            __out = bus.transaction(self._aggregator_dict())
            p_re = __out[AggregatorBusTranslator.OUT_P_RE_KEY]
            p_im = __out[AggregatorBusTranslator.OUT_P_IM_KEY]
            print str(self._time) + ':' + str(p_re) + '+ ' + str(p_im) + 'j'
                
        bus.stop_bus()
                
    def test(self):
        self._load_time()
        
        bus = load_bus(os.path.join(dir_name,fld_name))
        
        print '-------------------------'
        print 'RUNNING BUS: ' + os.path.join(dir_name, fld_name, bus_name)
        print '-------------------------'
        print
        
        bus.start_bus()
        
        while(not (bus.finished or self._check_time())):
            self._time.advance_time()
            __out = bus.transaction(self._aggregator_dict())
            print str(self._time) + ':' + str(__out[AggregatorBusTranslator.OUT_P_RE_KEY]) + '+ ' + str(__out[AggregatorBusTranslator.OUT_P_IM_KEY]) + 'j'
                
        bus.stop_bus()
        
        assert True
        
    def testGldCrash(self):
        self._load_time()
        
        bus = load_bus(os.path.join(THIS_DIR,'gld_crash_test_bus'))
        
        print '-------------------------'
        print 'RUNNING BUS: ' + os.path.join(THIS_DIR,'gld_crash_test_bus', bus_name)
        print '-------------------------'
        print
        
        bus.start_bus()
        
        while(not (bus.finished or self._check_time())):
            self._time.advance_time()
            __out = bus.transaction(self._aggregator_dict())
            print str(self._time) + ':' + str(__out[AggregatorBusTranslator.OUT_P_RE_KEY]) + '+ ' + str(__out[AggregatorBusTranslator.OUT_P_IM_KEY]) + 'j'
                
        bus.stop_bus()
        
        