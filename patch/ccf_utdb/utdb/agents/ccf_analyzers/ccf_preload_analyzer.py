#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_analyzers.ccf_coherency_analyzer import ccf_coherency_analyzer
from agents.ccf_common_base.ccf_common_base import ccf_llc_record_info, memory_data_entry
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_data_bases.ccf_address_db_agent import ccf_address_db_agent
from agents.ccf_data_bases.ccf_preload_db import ccf_preload_db
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

class ccf_preload_analyzer(ccf_coherency_analyzer):
    def __init__(self):
        self.configure()
        self.ccf_llc_db_agent_i = ccf_llc_db_agent.get_pointer()
        self.ccf_address_db_agent_i = ccf_address_db_agent.get_pointer()
        self.ccf_preload_db = ccf_preload_db.get_pointer()



    def run(self):
        self.all_addresses = self.ccf_preload_db.address_sorting()
        for address in self.all_addresses:
            for address_entry in address.EVENTS:
                if (int(address_entry.TIME) >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (int(address_entry.TIME) < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    address_event = self.ccf_preload_db.rec(address_entry)
                    self.analyze_record(address_event.r)

    def update_llc_db(self, record):
        self.ccf_llc_record_info = ccf_llc_record_info()
        self.ccf_llc_record_info.rec_time = int(record.TIME)
        self.ccf_llc_record_info.rec_address = record.ADDRESS
        self.ccf_llc_record_info.rec_set = record._SET
        self.ccf_llc_record_info.rec_way = record.WAY
        self.ccf_llc_record_info.rec_map = record.MAP
        self.ccf_llc_record_info.rec_state = record.STATE
        self.ccf_llc_record_info.rec_cv = record.CV_BITS
        self.ccf_llc_record_info.rec_data = record.DATA
        self.ccf_llc_record_info.rec_data_ecc = record.ECC
        self.ccf_llc_record_info.rec_unit = record.UNIT
        self.ccf_llc_record_info.rec_tag_ecc = record.TAG
        self.ccf_llc_record_info.rec_lru = record.LRU
        self.ccf_llc_record_info.rec_data_err_type = record.DATA_ER
        self.ccf_llc_record_info.rec_tag_err_type = record.TAG_ER
        self.ccf_llc_record_info.rec_stmap_err_type = record.STMAP_ER
        self.ccf_llc_record_info.rec_cv_err_type = record.CV_ER
        self.ccf_llc_db_agent_i.update_llc_ref_db(self.ccf_llc_record_info)

    def update_address_db(self, record):
        mem_entry = memory_data_entry()
        mem_entry.time = int(record.TIME)
        aligned_addr = CCF_FLOW_UTILS.get_idi_aligned_address(record.ADDRESS)
        mem_entry.cache_type = record.UNIT.split("_")[0]
        mem_entry.data = record.DATA
        mem_entry.state = record.STATE
        mem_entry.access_type = "PRELOAD"
        if record.MAP != str(CCF_COH_DEFINES.SNOOP_FILTER):
            self.ccf_address_db_agent_i.update_mem_db(aligned_addr, mem_entry)


    def analyze_record(self,record):
        if "LLC" in record.UNIT:
            self.update_llc_db(record)
            self.update_address_db(record)






