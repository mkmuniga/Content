#!/usr/intel/pkgs/python3/3.6.3/bin/python3.6
import argparse
from uploader import *


class CommonBaseUploader():

    def __init__(self):
        self.schema: table_schema = None
        self.input_log = None
        self.output_dir = None
        self.utdb_name = None
        self.utdb_dir = None
        self.seperator = '|'
        self.include_regex = '\d+'
        #  reader = Reader(file_path=input_log, schema=schema, separator='|', include='\d+', exclude='', type_selector=None)
        self.exclude = ''
        self.no_manual_upload = False
        self.writer = None

    def main(self):
        self.input_log, self.output_dir, self.utdb_name = self._get_args()
        self._set_utdb_dir()
        self.create_schema()
        self.set_reader_parameters()

        self.writer = Writer(self.utdb_dir)

        self._upload()

    def _get_args(self):
        parser = argparse.ArgumentParser('utdb uploader')
        parser.add_argument('-i', '--input_log',
                            help='input tracker/log file path',
                            required=True)
        parser.add_argument('-O', '--output_dir',
                            default=os.getcwd(),
                            help='path to where to create utdb. default: <run dir>')
        parser.add_argument('-u', '--utdb_name',
                            help='name of the resulted utdb dir. default: the name of <input-log> with "_utdb" suffix')
        args = parser.parse_args()
        if args.input_log:
            if not os.path.exists(args.input_log):
                raise Exception('UTDB uploader *Error*: input tracker/log "' + args.input_log + '" does not exists.')
        if not args.utdb_name:
            args.utdb_name = str(os.path.basename(args.input_log).split('.')[0]) + '_utdb'
        return args.input_log, args.output_dir, args.utdb_name

    def _set_utdb_dir(self):
        self.utdb_dir = os.path.join(self.output_dir, self.utdb_name)
        if not os.path.exists(self.utdb_dir):
            os.makedirs(self.utdb_dir)

    def create_schema(self):
        raise Exception('create_schema must be implemented in inherit class')

    def set_reader_parameters(self):
        pass

    def _upload(self):
        self.manual_upload()
        if self.no_manual_upload:
            self.reader_upload()

    def manual_upload(self):
        self.no_manual_upload = True

    def reader_upload(self):
        if not self.schema:
            raise Exception('self.schema must be set by create_schema')
        reader = Reader(file_path=self.input_log,
                        schema=self.schema,
                        separator=self.seperator,
                        include=self.include_regex,
                        exclude=self.exclude,
                        type_selector=None)
        try:
            upload(reader, self.writer)
        except Exception as e:
            print(e)
