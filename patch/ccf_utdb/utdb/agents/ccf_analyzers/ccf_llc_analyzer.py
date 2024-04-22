#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_idi_analyzer.py
#
# Owner:              meirlevy
# Creation Date:      02.2021
#
# ###############################################
#
# Description:
#   This file contain ccf llc anaylzer to analayze any utdb line for the coherency data base from llc TRKs
#################################################################################################
from agents.ccf_analyzers.ccf_coherency_analyzer import ccf_coherency_analyzer
from agents.ccf_common_base.ccf_common_base import ccf_llc_record_info
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from val_utdb_bint import bint


class ccf_llc_analyzer(ccf_coherency_analyzer):
    def __init__(self):
        self.write_data_state_tag_uop_l ={"Wd", "Wdc", "Wdsc", "Wdsct", "Wdst", "Ws", "Wt", "Wsc", "Wds", "Wsct", "RdctWs", "RctWs"}
        self.configure()
        self.ccf_llc_db_agent_i = ccf_llc_db_agent.get_pointer()

    def is_record_valid(self,record):
        return ("LLC" in record.UNIT
                and (record.REJECTED != 1 or (record.REJECTED == 1 and record.OPCODE in self.write_data_state_tag_uop_l))
                and "FlushRea" not in record.ARBCMD)

    def get_map(self, rec_map):
        if self.is_field_valid(rec_map):
            map_num = int(rec_map)
            if map_num < CCF_COH_DEFINES.max_num_of_data_ways:
                return "DWAY_" + str(map_num)
            else:
                return "SF_ENTRY"
        else:
            return rec_map

    def get_record_info(self, record):
        self.llc_record_info = ccf_llc_record_info()
        self.llc_record_info.rec_time = record.TIME
        self.llc_record_info.rec_unit = record.UNIT
        self.llc_record_info.rec_lid = record.LID
        self.llc_record_info.rec_tid = record.TID
        if "-" not in record.PID:
            self.llc_record_info.rec_pid = record.PID
        self.llc_record_info.rejected = record.REJECTED
        self.llc_record_info.rec_opcode = record.OPCODE
        self.llc_record_info.rec_hitmiss = record.HIT_MISS
        self.llc_record_info.rec_arbcmd = record.ARBCMD
        self.llc_record_info.rec_tag_ecc = record.TAG_ECC
        self.llc_record_info.rec_set = record.SET
        self.llc_record_info.rec_way = record.WAY
        self.llc_record_info.rec_map = record.MAP
        self.llc_record_info.rec_half = record.HALF
        self.llc_record_info.rec_state = record.STATE
        self.llc_record_info.rec_new_state = record.NEW_STATE
        self.llc_record_info.rec_new_map = record.NEW_MAP
        self.llc_record_info.rec_state_wr_way = record.STATE_WR_WAY
        self.llc_record_info.rec_state_in_way = record.STATE_IN_WAY
        self.llc_record_info.rec_state_vl_way = record.STATE_VL_WAY
        self.llc_record_info.rec_cv_rd = record.CV_RD
        self.llc_record_info.rec_cv_wr = record.CV_WR
        self.llc_record_info.rec_lru_rd = record.LRU_RD
        self.llc_record_info.rec_lru_wr = record.LRU_WR
        self.llc_record_info.rec_data = record.DATA
        self.llc_record_info.rec_data_ecc = record.ECC
        self.llc_record_info.rec_hitmiss_vector = record.HITMISS_VECTOR
        self.llc_record_info.rec_address = record.ADDRESS
        self.llc_record_info.rec_pref_vul_rd = record.PFVL_RD
        self.llc_record_info.rec_pref_vul_wr = record.PFVL_WR
        self.llc_record_info.rec_cv_err = record.CV_ERR

    def create_flow_point(self, record):
        flow_point = self.llc_record_info
        return flow_point

    def update_ccf_flow(self, ccf_flow, ccf_flow_point):
        super().update_ccf_flow(ccf_flow, ccf_flow_point)
        if self.llc_record_info.is_lookup_uop() and ccf_flow.initial_tag_way is None and self.is_field_valid(self.llc_record_info.rec_way):
            ccf_flow.initial_tag_way = self.llc_record_info.rec_way

        #Victim know which Tag way it's going to evict
        if "Victim" in self.llc_record_info.rec_arbcmd:
            ccf_flow.initial_tag_way = self.llc_record_info.rec_way

        #if we have snoop conflict we are doing new LookUp
        if self.llc_record_info.rec_arbcmd == "FwdCnflt":
            ccf_flow.final_cache_state = None
            ccf_flow.final_map = None
            ccf_flow.final_tag_way = None

        if self.llc_record_info.is_late_wr_state():
            ccf_flow.final_cache_state = self.llc_record_info.rec_new_state
            ccf_flow.final_map = self.get_map(self.llc_record_info.rec_new_map)
            ccf_flow.final_tag_way = self.llc_record_info.rec_way
        elif self.is_field_valid(self.llc_record_info.rec_state):
            ccf_flow.final_cache_state = self.llc_record_info.rec_state
            if self.llc_record_info.rec_state == "LLC_I":
                #Once we are Ws to LLC_I cv field can be consider as 0s
                ccf_flow.final_cv = "0".zfill(CCF_COH_DEFINES.num_physical_cv_bits)

            if self.is_field_valid(self.llc_record_info.rec_map):
                if self.llc_record_info.rec_state == "LLC_I":
                    ccf_flow.final_map = "SF_ENTRY"
                else:
                    ccf_flow.final_map = self.get_map(self.llc_record_info.rec_map)

                if ccf_flow.initial_map is None and ("VIC" in self.llc_record_info.rec_lid or (self.llc_record_info.rec_pid is not None and "VIC" in self.llc_record_info.rec_pid)):
                    ccf_flow.initial_map = self.get_map(self.llc_record_info.rec_map)

                if self.is_field_valid(self.llc_record_info.rec_way):
                    ccf_flow.final_tag_way = self.llc_record_info.rec_way
        elif self.is_field_valid(self.llc_record_info.rec_map) and ccf_flow.final_cache_state is not None:
            ccf_flow.final_map = self.get_map(self.llc_record_info.rec_map)

        #probably a miss with no info in the tracker update final state to be LLC_I with SF_ENTRY
        elif ccf_flow.final_cache_state is None:
            ccf_flow.final_cache_state = "LLC_I"
            ccf_flow.final_map = "SF_ENTRY"


        #Here we handle initial_cv and final_cv field
        if self.is_field_valid(self.llc_record_info.rec_cv_wr):
            #If the RTL injects cv error while cv write the cv_wr will have indication of (E)
            if "(E)" in self.llc_record_info.rec_cv_wr:
                cv_b = ("{0:16b}".format(int(((self.llc_record_info.rec_cv_wr).split("(")[0]), 16))).strip()
                ccf_flow.inject_cv_err = True
            else:
                cv_b = ("{0:16b}".format(int(self.llc_record_info.rec_cv_wr, 16))).strip()
            ccf_flow.final_cv = cv_b.zfill(CCF_COH_DEFINES.num_physical_cv_bits)
        elif self.is_field_valid(self.llc_record_info.rec_cv_rd):
            ccf_flow.final_cv = bin(int(self.llc_record_info.rec_cv_rd, 16))[2:].zfill(CCF_COH_DEFINES.num_physical_cv_bits)
            if ccf_flow.initial_cv is None and ("VIC" in self.llc_record_info.rec_lid or (self.llc_record_info.rec_pid is not None and "VIC" in self.llc_record_info.rec_pid)):
                ccf_flow.initial_cv = ccf_flow.final_cv

        #CV err can be read when opcode is look up or R(read) with c(CV)
        if (self.llc_record_info.is_lookup_uop() or self.llc_record_info.is_cv_rd_uop()) and self.llc_record_info.had_cv_err():
            ccf_flow.cv_err = True

        if self.llc_record_info.rec_opcode is not None:
            ccf_flow.llc_uops.append(self.llc_record_info.rec_opcode)

        if self.llc_record_info.is_wr_data_uop():
            ccf_flow.data_written_to_cache = 1

        if self.llc_record_info.rec_half is not None and ccf_flow.cbo_half_id is None:
            ccf_flow.cbo_half_id = self.llc_record_info.rec_half

        if self.llc_record_info.is_lookup_uop() and self.llc_record_info.is_hit() and (self.llc_record_info.rec_pref_vul_rd == "1"):
            if (bint(int(self.llc_record_info.rec_cv_rd, 16)) == 0) and (self.llc_record_info.rec_state != "LLC_M"):
                ccf_flow.data_brought_by_llc_prefetch = 1

        if self.llc_record_info.is_wr_data_uop():
            ccf_flow.data_marked_as_brought_by_llc_prefetch = (self.llc_record_info.rec_pref_vul_wr == "1")


