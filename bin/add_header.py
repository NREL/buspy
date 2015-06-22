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
'''

import argparse
import os
from collections import OrderedDict

START_LICENSE = '[LICENSE]'
LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'doc', 'license_header.txt')
END_LICENSE = '[/LICENSE]'


ARGS = OrderedDict()

ARGS['filename']     = ( [],
                        {'type'       :str, 
                         'help'       :'the python filename (or directory with [-d] or [--folder]) to add the license file to'} )

ARGS['-d']           = ( ['--folder'],
                          {'action'     :'store_true', 
                           'default'    :False, 
                           'help'       :"""(optional) The provided first parameter is a directory.
                                         All .py files in the directory will add the license.
                                         Default: False"""} )

ARGS['-l']           = ( ['--license'],
                           {'default'    :LICENSE_FILE, 
                           'help'       :"""(optional) The filename of the license to add to the Python files"""} )

ARGS['-r']           = ( ['--recursive'],
                          {'action'     :'store_true', 
                           'default'    :False, 
                           'help'       :"""(optional) Recursively add license to files. Only works if [-d] or [--folder] is specified."""} )

ARGS['-x']           = ( ['--remove'],
                          {'action'     :'store_true', 
                           'default'    :False, 
                           'help'       :"""(optional) Remove the license from the given file only, do not add the provided license."""} )



def get_header(s):
    '''
    Splits .py file into its header and body. If no header is found on line 0, one is created.
    '''
    header = ''
    body = ''
    
    lines = s.splitlines(True)
    
    #check if has a header
    if (len(lines)) > 0 and ('\'\'\'' in lines[0]):
        eoh = False
        header += lines[0]
        for l in lines[1:]:
            if not eoh:
                header += l
                if '\'\'\'' in l:
                    eoh = True
            else:
                body += l
    else: #no header
        header = '\'\'\'' + os.linesep + '\'\'\'' + os.linesep
        body = s
    
    return header, body

def has_license(header):
    return (START_LICENSE in header) and (END_LICENSE in header)

def rem_license(header):
    ret_header = ''
    if has_license(header):
        found_beg_license = False
        found_end_license = False
        for l in header.splitlines(True):
            #look for START_LICENSE
            if not found_beg_license:
                if START_LICENSE in l:
                    found_beg_license = True
                else:
                    ret_header += l
            #look for END_LICENSE if already found start
            elif not found_end_license:
                if END_LICENSE in l:
                    found_end_license = True
            #past the license portion, add remainder of header
            else:
                ret_header += l
            
    else: #no license to remove
        ret_header = header
        
    return ret_header

def add_license(header,lic):
    if has_license(header):
        raise Exception('There is already a license in the provided header. Please rem_license prior to adding a new one.')
    
    ret_head = ''
    
    lines = header.splitlines(True)
    ret_head += lines[0]
    
    #add license to header
    ret_head += '%s%s' % (START_LICENSE,os.linesep)
    ret_head += '%s%s' % (lic,os.linesep)
    ret_head += '%s%s' % (END_LICENSE,os.linesep)
    
    #add the rest of the header
    for l in lines[1:]:
        ret_head += l
    
    return ret_head

def is_python_file(fname):
    return os.path.splitext(fname)[1].lower() == '.py'

def get_python_files(dirname):
    ret = []
    
    for item in os.listdir(dirname):
        full_path = os.path.join(dirname,item)
        if os.path.isfile(full_path) and is_python_file(item):
            ret.append(full_path)
    
    return ret

if __name__ == '__main__':
    #TODO: parse args
    parser = argparse.ArgumentParser(description="""Script for adding
    a license to the header of Python files.""")
    
    #add the arguments from ARGS
    for key in ARGS.keys():
        parser.add_argument(key, *ARGS[key][0], **ARGS[key][1])
     
    args = parser.parse_args()
    
    #read current license
    with open(args.license) as f:
        current_license = f.read()
        
    #get filenames to change
    if not args.folder: #individual file
        if not is_python_file(args.filename):
            raise Exception('ERROR: \'%s\' is not a .py file' % args.filename)
        
        python_files = [args.filename]
    else: #directory
        python_files = []
        dirname = os.path.abspath(args.filename)
        if not args.recursive:
            python_files.extend(get_python_files(dirname))
        else:
            for cur_dir, sub_dirs, files in os.walk(dirname):
                python_files.extend(get_python_files(cur_dir))
        
    #iterate through files
    for current_file in python_files:
        print 'Adding license to: %s' % current_file
        with open(current_file) as f:
            current_file_text = f.read()
            
        header, body = get_header(current_file_text)
        
        if has_license(header):
            header = rem_license(header)
            
        #only add license if not remove-only
        if not args.remove:
            header = add_license(header,current_license)
        
        with open(current_file,'w') as f:
            f.write(header+body)
        
    