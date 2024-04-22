#!/usr/intel/pkgs/python3/3.6.3a/bin/python3.6

'''
==============================================================================================
== this is a machine generated script meant to be used as uploader.                         ==
==============================================================================================
'''

import os
import sys
import re
from argparse import ArgumentParser

utdb_home = os.getenv("UTDB_HOME") if os.getenv("UTDB_HOME") else exit("Error: UTDB_HOME is not defined.\
 get latest version from /p/hdk/rtl/cad/x86-64_linux26/dt/utdb/")
sys.path.append(os.path.join(utdb_home, "lib"))

from uploader import *


def upload_cbo(input_file_path, output_dir):
    schema = table_schema()
    schema.add_record_schema('CBO', [
        field(name='TIME', type=FieldType.UINT),
        field(name='LOCATION', type=FieldType.STRING),
        field(name='PAYLOAD', type=FieldType.STRING),
        field(name='SOP', type=FieldType.STRING),
        field(name='EOP', type=FieldType.STRING),
        field(name='ADDRESS'),
        field(name='TXN_TYPE', type=FieldType.STRING),
        field(name='CID', type=FieldType.STRING),
        field(name='RING', type=FieldType.STRING),
        field(name='MSG', type=FieldType.STRING),
        field(name='RTID', type=FieldType.STRING),
        field(name='MISC', type=FieldType.STRING),
        field(name='EVENT', type=FieldType.STRING),
    ])

    
    reader = Reader(file_path=input_file_path, schema=schema, separator='|', include='\d+'
    , exclude='', type_selector=None)
    writer = Writer(output_dir)
    upload(reader, writer)


def match_and_upload(input_file_path, output_dir, utdb_name):
    # Finds the correct uploader method by the input-file name.
    # Calls the FIRST uploader that matches, uploads and finishs.
    
    if output_dir == None:
        output_dir = os.getcwd()
    print(utdb_name)
    if utdb_name == None:
        in_file_dir, in_file_name = os.path.split(input_file_path)
        utdb_name = in_file_name[:in_file_name.find('.')] + '_utdb'
    output_dir = os.path.join(output_dir, utdb_name)
    pattern_to_uploader_dict = {
        '[^cbo_*trk.log*$]': upload_cbo,
    }

    in_file_dir, in_file_name = os.path.split(input_file_path)
    if in_file_name.endswith('.gz'):
        in_file_name = in_file_name[:-len('.gz')]

    for file_pattern, uploader in pattern_to_uploader_dict.items():
        if re.search(file_pattern, in_file_name):
            uploader(input_file_path, output_dir)
            return
        print(file_pattern)
        print(in_file_name)
    raise Exception("UTDB uploader *Error*: input tracker/log \'" + in_file_name + "\' doesn't match uploader ")


def get_args():
    parser = ArgumentParser('utdb uploader')
    parser.add_argument('-i', '--input-file-path', type=argparse.FileType('r'), help='input tracker/log file path', required=True,  nargs='+')
    parser.add_argument('-O', '--output-dir', help='path to where to create utdb. default: <run dir>')
    parser.add_argument('-u', '--utdb-name', help='name of the resulted utdb dir. default: the name of <input-log> with \'_utdb\' suffix')
   
    args = parser.parse_args()
    files = []
    for g in args.input_file_path:
      if g:
        if not os.path.exists(g.name):
            raise Exception("UTDB uploader *Error*: input tracker/log \'" + g.name + "\' does not exists.")
        files.append(g.name)
    print(files)
    return files, args.output_dir, args.utdb_name


# **************************************************************************************
# main function for command line usage
# **************************************************************************************
if __name__ == "__main__":
    
    input_file_path ,output_dir, utdb_name = get_args()
    i = 0
    for f in input_file_path:
        utdb_name_1= utdb_name + str(i)
        match_and_upload(f, output_dir, utdb_name_1)
        i = i + 1

