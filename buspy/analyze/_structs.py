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

structures for the data classes.  internal use only.
'''

##############################################################
#### FESTIV
##############################################################
class _FESTIV_AGC(object):
    Pd = None
    Pg = None
    time = None
    
class _FESTIV_BUS(object):
    number = None
    names = None
    PQ_mask = None
    PV_mask = None
    slack_mask = None
    
class _FESTIV_MARKET(object):
    lmp = None
    rcp = None
    time = None
    
##############################################################
#### MATPOWER
##############################################################
class _MATPOWER_BRANCH(object):
    Pf = None
    Pt = None
    Qf = None
    Qt = None
    Sf = None
    St = None
    powff = None
    powft = None
    names = None
    number = None
    
class _MATPOWER_BUS(object):
    P = None
    Q = None
    Va = None
    Vm = None
    baseKV = None
    names = None
    number = None
    PQ_mask = None
    PV_mask = None
    slack_mask = None
    
class _MATPOWER_GEN(object):
    P = None
    Q = None
    PV_mask = None
    slack_mask = None
    names = None
    number = None