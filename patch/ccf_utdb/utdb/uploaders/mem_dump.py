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


def upload_dump(input_file_path, output_dir):
    schema = table_schema()
    schema.add_record_schema('CCF_MEM_DUMP', [
        field(name='TIME', type=FieldType.UINT),
        field(name='UNIT', type=FieldType.STRING),
        field(name='HALF', type=FieldType.STRING),
        field(name='ADDRESS', type=FieldType.STRING),
        field(name='TAG', type=FieldType.STRING),
        field(name='_SET', type=FieldType.STRING),
        field(name='WAY', type=FieldType.STRING),
        field(name='MAP', type=FieldType.STRING),
        field(name='STATE', type=FieldType.STRING),
        field(name='CV_BITS', type=FieldType.STRING),
        field(name='DATA', type=FieldType.STRING),
        field(name='TAG_ER', type=FieldType.STRING),
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
    if utdb_name == None:
        in_file_dir, in_file_name = os.path.split(input_file_path)
        utdb_name = in_file_name[:in_file_name.find('.')] + '_utdb'
    output_dir = os.path.join(output_dir, utdb_name)
    pattern_to_uploader_dict = {
        '^ccf_mem_dump.log*$': upload_dump,
    }

    in_file_dir, in_file_name = os.path.split(input_file_path)
    if in_file_name.endswith('.gz'):
        in_file_name = in_file_name[:-len('.gz')]

    for file_pattern, uploader in pattern_to_uploader_dict.items():
        if re.search(file_pattern, in_file_name):
            uploader(input_file_path, output_dir)
            return
    raise Exception("UTDB uploader *Error*: input tracker/log \'" + in_file_name + "\' doesn't match uploader ")


def get_args():
    parser = ArgumentParser('utdb uploader')
    parser.add_argument('-i', '--input-file-path', help='input tracker/log file path', required=True)
    parser.add_argument('-O', '--output-dir', help='path to where to create utdb. default: <run dir>')
    parser.add_argument('-u', '--utdb-name', help='name of the resulted utdb dir. default: the name of <input-log> with \'_utdb\' suffix')
    args = parser.parse_args()
    if args.input_file_path:
        if not os.path.exists(args.input_file_path):
            raise Exception("UTDB uploader *Error*: input tracker/log \'" + args.input_file_path + "\' does not exists.")
    return args.input_file_path, args.output_dir, args.utdb_name


# **************************************************************************************
# main function for command line usage
# **************************************************************************************
if __name__ == "__main__":
    input_file_path ,output_dir, utdb_name = get_args()
    match_and_upload(input_file_path, output_dir, utdb_name)

