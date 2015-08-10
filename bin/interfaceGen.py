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

@author Muhammad Umer Tariq

interfaceGen.py
Generates a json file (DDESResults.json) that represents an example output of the DDES module.

The output file also contains certain elements that are actually inputs to the DDES module. These elements are included in the output file for the sake of providing comprehensive information to the user in a single place. 

Edited by Tim Hansen for development of the controller module.
'''


import json
import collections
 
filename = "DDESResults.json"

data = collections.OrderedDict()

#Lets deal with GENERATORS:

genList = []

#gen1 = {}
gen1 = collections.OrderedDict()

gen1['Name'] = 'Generator1'
gen1['BusNum'] = 1
gen1['GLMBusName'] = 'Node632'
gen1['GenCost'] = 1000
gen1['MaxPower'] = 100
gen1['MinPower'] = 50

pScheduleList1 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

gen1['PSchedule'] = pScheduleList1 

qScheduleList1 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

gen1['QSchedule'] = qScheduleList1 

genList.append(gen1)

#gen2 = {}
gen2 = collections.OrderedDict()

gen2['Name'] = 'Generator2'
gen2['BusNum'] = 2
gen2['GLMBusName'] = 'Node634'
gen2['GenCost'] = 1500
gen2['MaxPower'] = 100
gen2['MinPower'] = 80

pScheduleList2 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]


gen2['PSchedule'] = pScheduleList2 

qScheduleList2 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]


gen2['QSchedule'] = qScheduleList2 
genList.append(gen2)


data['GENERATORS'] = genList


#Lets deal with STORAGE DEVICES:

storageList = []

storage1 = collections.OrderedDict()

storage1['Name'] = 'Storage1'
storage1['BusNum'] = 1
storage1['GLMBusName'] = 'Node632'
storage1['MaxEnergy'] = 1000
storage1['MinEnergy'] = 100
storage1['MaxChargeSpeed'] = 50
storage1['MaxDischargeSpeed'] = 40
storage1['ChargingEfficiency'] = 90
storage1['DischargingEfficiency'] = 90

storageScheduleList1 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

storage1['StorageSchedule'] = storageScheduleList1 

storageList.append(storage1)

storage2 = collections.OrderedDict()

storage2['Name'] = 'Storage2'
storage2['BusNum'] = 3
storage2['GLMBusName'] = 'Load635'
storage2['MaxEnergy'] = 1000
storage2['MinEnergy'] = 100
storage2['MaxChargeSpeed'] = 50
storage2['MaxDischargeSpeed'] = 40
storage2['ChargingEfficiency'] = 90
storage2['DischargingEfficiency'] = 90

storageScheduleList2 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

storage2['StorageSchedule'] = storageScheduleList2 

storageList.append(storage2)


data['STORAGE DEVICES'] = storageList

# Let's deal with RENEWABLES

renewableList = []

renewable1 = collections.OrderedDict()

renewable1['Name'] = 'Renewable1'
renewable1['BusNum'] = 5
renewable1['GLMBusName'] = 'Node642'

renewableForecastList1 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

renewable1['Forecast'] = renewableForecastList1 

curtailmentScheduleList1 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

renewable1['CurtailmentSchedule'] = curtailmentScheduleList1


renewableList.append(renewable1)

data['RENEWABLES'] = renewableList

# Let's deal with (Aggregated) LOADS

loadList = []

load1 = collections.OrderedDict()

load1['Name'] = 'Load1'
load1['BusNum'] = 7
load1['GLMBusName'] = 'Load647'

demandForecastList1 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

load1['DemandForecast'] = demandForecastList1

loadList.append(load1)

load2 = collections.OrderedDict()

load2['Name'] = 'Load1'
load2['BusNum'] = 9
load2['GLMBusName'] = 'Load649'

demandForecastList2 = [(1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5), (6,6,6), (7,7,7), (8,8,8), (9,9,9), (10,10,10), (11,11,11), (12,12,12), (13,13,13), (14,14,14), (15,15,15), (16,16,16), (17,17,17), (18,18,18), (19,19,19), (20,20,20), (21,21,21), (22,22,22), (23,23,23), (24,24,24)]

load2['DemandForecast'] = demandForecastList2

loadList.append(load2)

data['LOADS'] = loadList


# Let's write the data to JSON file

f1 = open(filename, 'w')

json.dump(data, f1, indent=2)
