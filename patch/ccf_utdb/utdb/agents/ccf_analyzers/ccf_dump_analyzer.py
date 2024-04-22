#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base import memory_dump_entry
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.ccf_common_base_class import ccf_base_analyzer
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_dump_db import ccf_dump_db
from collections import OrderedDict
from val_utdb_bint import bint
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

class ccf_dump_analyzer(ccf_base_analyzer):
    def __init__(self):
        self.configure()
        self.ccf_dump_db = ccf_dump_db.get_pointer()

    def run(self):
        self.all_addresses = self.ccf_dump_db.address_sorting()
        for address in self.all_addresses:
            for address_entry in address.EVENTS:
                if (int(address_entry.TIME) >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (int(address_entry.TIME) <= COH_GLOBAL.global_vars["END_OF_TEST"]):
                    address_event = self.ccf_dump_db.rec(address_entry)
                    self.analyze_record(address_event.r)

        ccf_dbs.sort_dump_db()

    def analyze_record(self, record):
        dump_entry = memory_dump_entry()
        dump_entry.time = int(record.TIME)

        aligned_addr = CCF_FLOW_UTILS.get_idi_aligned_address(record.ADDRESS)

        dump_entry.cache_type = record.UNIT
        dump_entry.data = record.DATA.replace(" ", "")
        dump_entry.state = record.STATE
        if record.CV_BITS != "-":
            dump_entry.cv = bin(int(record.CV_BITS, 16))[2:].zfill(CCF_COH_DEFINES.num_physical_cv_bits)
        dump_entry.way = record.WAY
        dump_entry.set = record._SET
        dump_entry.map = record.MAP
        dump_entry.half = record.HALF

        self.update_address_db(aligned_addr, dump_entry)


    def update_address_db(self, address, entry):
        if (address not in self.dump_db.keys()):
           self.dump_db[address] = [entry]
        else:
           self.dump_db[address].append(entry)




