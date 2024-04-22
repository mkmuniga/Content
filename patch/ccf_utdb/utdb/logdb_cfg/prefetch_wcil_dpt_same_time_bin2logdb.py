#!/usr/intel/bin/python3.6.3a
from val_uvm_tracker import *
import tableWriter

logdb_header = [
        {'name': 'TIME', 'record_type': 'dpt_wcil_prefetch', 'header_type': 'bigint unsigned'},
        {'name': 'SAME_TIME_VALID', 'record_type': 'dpt_wcil_prefetch', 'header_type': 'int'},
]

class PrefetchWcilDptAtSameTimeTracker(val_uvm_tracker):
    trans_list = []
    logdb_writer = None
    text_writer = None

    def build_phase(self, phase):
        self.add_source_to_cb_mapping({source: self.req_trans})
        self.init_writers()
        self.add_headers()

    def req_trans(self, src, txn):
        trans_values = dict()
        trans_values['TIME'] = get_sim_time()
        trans_values['SAME_TIME_VALID'] = 1
        self.trans_list.append(trans_values)


    def init_writers(self):
        if args.logdb is not None:
            self.logdb_writer = tableWriter.tableWriter(storage=tableWriter.STORAGE.LOGDB, path=logdbs[0], page=100)
        if args.text is not None:
            self.text_writer = tableWriter.tableWriter(storage=tableWriter.STORAGE.FILE, path=texts[0], page=100)

    def add_headers(self):
        if args.logdb is not None:
            for h in logdb_header:
                self.logdb_writer.add_header(**h)
        if args.text is not None:
            for h in trk_header:
                self.text_writer.add_header(**h)

    def final_phase(self, phase):
        self.final_print()

    def final_print(self):
        self.print_logdb()
        if args.logdb is not None:
            self.logdb_writer.close_writer()
        if args.text is not None:
            self.text_writer.close_writer()

    def print_logdb(self):
        for trans in self.trans_list:
            if args.logdb is not None:
                self.logdb_writer.push_row(**trans)
            if args.text is not None:
                self.text_writer.push_row(**trans)
