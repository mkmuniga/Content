#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base import ccf_mlc_record_info
from agents.ccf_common_base.ccf_common_base_class import ccf_base_analyzer
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_mlc_db import ccf_mlc_db
from val_utdb_bint import bint
from collections import OrderedDict

class ccf_mlc_analyzer(ccf_base_analyzer):
    def __init__(self):
        self.configure()
        self.mlc_db = {}
        self.ccf_mlc_db = ccf_mlc_db.get_pointer()

    def reset(self):
        self.mlc_db = {}

    def remove_non_digit_chars(self, str):
        return ''.join(char for char in str if char.isdigit())

    def run(self):
        self.all_addresses = self.ccf_mlc_db.address_sorting()
        for address in self.all_addresses:
            for address_entry in address.EVENTS:
                entry_time = self.remove_non_digit_chars(str(address_entry.TIME))
                if (int(entry_time) >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (int(entry_time) < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    address_event = self.ccf_mlc_db.rec(address_entry)
                    self.prepare_record(address_event.r)
        self.mlc_db = OrderedDict(sorted(self.mlc_db.items()))

    def prepare_record(self, rec):
        mlc_rec = ccf_mlc_record_info()
        mlc_rec.time = self.remove_non_digit_chars(str(rec.TIME))
        mlc_rec.unit = rec.UNIT
        mlc_rec.address = rec.ADDRESS
        mlc_rec.data = rec.DATA.replace(" ", "")
        mlc_rec.core_state = rec.C_ST
        mlc_rec.superQ_state = rec.SQST
        mlc_rec.address = CCF_FLOW_UTILS.get_idi_aligned_address(rec.ADDRESS)

        if (mlc_rec.address not in self.mlc_db.keys()):
           self.mlc_db[mlc_rec.address] = [mlc_rec]
        else:
           self.mlc_db[mlc_rec.address].append(mlc_rec)




