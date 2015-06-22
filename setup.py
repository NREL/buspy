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
'''
from distutils.core import setup
import buspy

setup(
    name='buspy',
    version=buspy.__version__,
    author='Timothy Hansen',
    author_email='timothy.hansen@colostate.edu',
    packages=['buspy',
              'buspy.analyze', 'buspy.analyze.loaders',
              'buspy.comm','buspy.utils',
              'buspy.construct'],
    scripts=['bin/add_header.py'],
    url='http://www.engr.colostate.edu/sgra', #TODO: replace with github
    license='LICENSE.txt',
    description='abstract transmission bus interface with GridLAB-D hooks',
    long_description=open('README.txt').read(),
    data_files=[                    ('data/example_bus_input',['data/example_bus_input/bus_nosetest.py',                                               'data/example_bus_input/constant_bus_translator.json',                                               'data/example_bus_input/constant_bus.json',                                               'data/example_bus_input/file_bus_translator.json',                                               'data/example_bus_input/file_bus.json',                                               'data/example_bus_input/gridlabd_bus.json',                                               'data/example_bus_input/multi_bus_translator.json',                                               'data/example_bus_input/example_gridlabd.glm',                                               'data/example_bus_input/power.player'])                ],
    install_requires=open('requirements.txt').read()
)
