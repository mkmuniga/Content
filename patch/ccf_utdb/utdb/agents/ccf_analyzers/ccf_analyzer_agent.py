#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_agent.py
#
# Owner:              CCF Val team.
# Description:
#################################################################################################

import os
from agents.ccf_analyzers.ccf_ufi_analyzer import ccf_ufi_analyzer

from agents.ccf_analyzers.ccf_cbo_analyzer import ccf_cbo_analyzer
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_queries.ccf_corrupted_llc_preload_qry import ccf_corrupted_llc_preload_qry
from agents.ccf_analyzers.ccf_llc_analyzer import ccf_llc_analyzer
from agents.ccf_analyzers.ccf_idi_analyzer import ccf_idi_analyzer
from agents.ccf_analyzers.ccf_cfi_analyzer import ccf_cfi_analyzer
from agents.ccf_analyzers.ccf_preload_analyzer import ccf_preload_analyzer
from agents.ccf_analyzers.ccf_mlc_analyzer import ccf_mlc_analyzer
from agents.ccf_analyzers.ccf_dump_analyzer import ccf_dump_analyzer
from agents.ccf_analyzers.ccf_cpipe_windows_analyzer import ccf_cpipe_windows_analyzer
from agents.ccf_data_bases.ccf_address_db_agent import ccf_address_db_agent
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_queries.ccf_llc_coherency_qry import ccf_llc_coherency_qry
from agents.ccf_data_bases.ccf_coherency_db_constructor import ccf_coherency_db_constructor
from agents.ccf_data_bases.ccf_preload_db import ccf_preload_db
from agents.ccf_data_bases.ccf_santa_db import ccf_santa_db
from agents.ccf_data_bases.ccf_mlc_db import ccf_mlc_db
from agents.ccf_data_bases.ccf_dump_db import ccf_dump_db
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from agents.ccf_queries.ccf_power_qry import ccf_power_qry
from agents.ccf_queries.ccf_sb_agent_qry import CCF_SB_AGENT_QRY
from agents.ccf_queries.ccf_power_sb_qry import CCF_POWER_SB_QRY
from agents.ccf_common_base.ccf_power_state_agent import ccf_power_state_agent
from agents.ccf_common_base.ccf_sb_agent import ccf_sb_agent
from agents.ccf_data_bases.ccf_power_sb_db import CCF_POWER_SB_DB
from agents.ccf_queries.ccf_window_qry import ccf_window_qry
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.cncu_agent.dbs.ccf_sm_qry import CCF_SM_QRY
from agents.ccf_common_base.ccf_monitor_agent import ref_monitor_array
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES


class ccf_analyzer_agent(ccf_base_agent):

    @property
    def preload_logdb_exist(self):
        return os.path.exists(self.ccf_pp_params_ptr.params["test_path"] + "/LOGDB/preload_logdb")

    @property
    def sm_logdb_exist(self):
        return os.path.exists(self.ccf_pp_params_ptr.params["test_path"] + "/LOGDB/ccf_sm_logdb")

    ########################
    ### Build functions

    def create_ccf_coherency_queries(self):
        self.ccf_coherency_qry_i = ccf_coherency_qry.create()
        self.ccf_llc_coherency_qry_i = ccf_llc_coherency_qry.create()

        if self.si.corrupted_llc_preload_en == 1:
            self.ccf_corrupted_llc_preload_qry_i = ccf_corrupted_llc_preload_qry.create()

        if self.preload_logdb_exist:  # emulation doesn't have this database
            self.ccf_preload_db_i = ccf_preload_db.create()
            self.ccf_mlc_db_i = ccf_mlc_db.create()
            if self.si.ccf_dump_chk_en:
                self.ccf_dump_db_i = ccf_dump_db.create()

        if self.sm_logdb_exist:  # emulation doesn't have this database
            self.ccf_sm_db_i = SM_DB.get_pointer()
            self.ccf_sm_qry_i = CCF_SM_QRY.create()

        self.ccf_power_qry_i = ccf_power_qry.create()

        # For now SoC doesn't have our URI SB TRK therefore cannot use the merged_sb_logdb
        if not self.si.ccf_soc_mode:
            self.ccf_sb_agent_qry_i = CCF_SB_AGENT_QRY.create()
            self.ccf_power_sb_qry_i = CCF_POWER_SB_QRY.create()
        self.ccf_santa_db_i = ccf_santa_db.create()

        self.ccf_window_db_i = ccf_window_qry.create()

    def create_analyzers(self):
        self.ccf_preload_analyzer_i = ccf_preload_analyzer.create()
        self.ccf_mlc_analyzer_i = ccf_mlc_analyzer.create()
        self.ccf_cpipe_windows_analyzer_i = ccf_cpipe_windows_analyzer.create()

        if self.si.ccf_dump_chk_en:
            self.ccf_dump_analyzer_i = ccf_dump_analyzer.create()

        self.ccf_idi_analyzer_i = ccf_idi_analyzer.create()
        self.ccf_cbo_analyzer_i = ccf_cbo_analyzer.create()
        self.ccf_cfi_analyzer_i = ccf_cfi_analyzer.create()
        self.ccf_ufi_analyzer_i = ccf_ufi_analyzer.create()
        self.ccf_llc_analyzer_i = ccf_llc_analyzer.create()

    ######################
    ### Connect functions

    def connect_logdbs(self):
        # connect query to data base
        self.ccf_coherency_qry_i.connect_to_db('merged_ccf_coherency_logdb')
        self.ccf_santa_db_i.connect_to_db('merged_ccf_coherency_logdb')
        self.ccf_llc_coherency_qry_i.connect_to_db('merged_ccf_llc_coherency_logdb')
        if self.si.corrupted_llc_preload_en == 1:
            self.ccf_corrupted_llc_preload_qry_i.connect_to_db('corrupted_llc_preload_logdb')
        self.ccf_power_qry_i.connect_to_db('pmc_logdb')
        # For now SoC doesn't have our URI SB TRK therefore cannot use the merged_sb_logdb
        if not self.si.ccf_soc_mode:
            self.ccf_sb_agent_qry_i.connect_to_db('merged_sb_logdb')
            self.ccf_power_sb_qry_i.connect_to_db('merged_pmsb_logdb')
        if self.preload_logdb_exist:
            self.ccf_preload_db_i.connect_to_db('preload_logdb')
            self.ccf_mlc_db_i.connect_to_db('mlc_logdb')
            if self.si.ccf_dump_chk_en:
                self.ccf_dump_db_i.connect_to_db('ccf_mem_dump_logdb')
        if self.sm_logdb_exist:
            self.ccf_sm_qry_i.connect_to_db('ccf_sm_logdb')

        self.ccf_window_db_i.connect_to_db('cpipe_windows_logdb')

    ######################
    ### Build

    def build(self):
        super().build()
        self.ccf_pp_params_ptr = ccf_pp_params.get_pointer()

        # initial CCF_UTILS values
        CCF_UTILS.initial_ccf_utils(self.si)

        # Create all agent queries
        self.create_ccf_coherency_queries()

        self.create_analyzers()

        # Build agents that will help get data from LOGDBs
        self.ccf_coherency_db_constructor_i = ccf_coherency_db_constructor.create()
        self.ccf_address_db_agent_i = ccf_address_db_agent.create()
        self.ccf_llc_db_agent_i = ccf_llc_db_agent.create()

        # For now SoC doesn't have our URI SB TRK therefore cannot use the merged_sb_logdb
        if not self.si.ccf_soc_mode:
            self.ccf_sb_agent_i = ccf_sb_agent.create()
            self.ccf_pmsb_agent_i = CCF_POWER_SB_DB.create()

        self.ref_monitor_array = ref_monitor_array.create()

    def connect(self):
        super().connect()

        self.connect_logdbs()

    def run(self):
        # For now SoC doesn't have our URI SB TRK therefore cannot use the merged_sb_logdb
        if not self.si.ccf_soc_mode:
            self.ccf_sb_agent_i.run_db_builder()
            self.ccf_pmsb_agent_i.run_db_builder()

        ccf_power_state_agent.run_db_builder(self.ccf_power_qry_i)
        ccf_power_state_agent.initialize_test_power_flow_db()

        for idx in range(len(ccf_power_state_agent.test_power_flow_db)):
            COH_GLOBAL.global_vars["POWER_DB_INDEX"] = idx
            COH_GLOBAL.global_vars["START_OF_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["START_TEST"]
            COH_GLOBAL.global_vars["END_OF_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["END_TEST"]
            COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["C6_TIME_IN_RANGE"]
            self.analyzing_stage(is_cold_reset=ccf_power_state_agent.test_power_flow_db[idx]["COLD_RESET"])


    def reset_db(self, is_cold_reset):
        ccf_dbs.reset_ccf_flows()

        ccf_dbs.reset_mem_db()

        # Reset ref monitor + initial DB structure
        ccf_dbs.reset_ref_monitor_per_cbo_db()
        self.ref_monitor_array.config(self.si.num_of_cbo*CCF_COH_DEFINES.num_of_ccf_clusters)

        self.ccf_mlc_analyzer_i.reset()
        if self.si.ccf_dump_chk_en:
            ccf_dbs.reset_dump_db()
        self.ccf_llc_db_agent_i.reset()

    def analyzing_stage(self, is_cold_reset):
        self.reset_db(is_cold_reset)
        ccf_registers.get_pointer().get_registers_value()

        if self.sm_logdb_exist:
            SM_DB.run_db_builder(self.ccf_sm_qry_i)

        if self.preload_logdb_exist:
            self.ccf_preload_analyzer_i.run()
            self.ccf_mlc_analyzer_i.run()
            if self.si.ccf_dump_chk_en:
                self.ccf_dump_analyzer_i.run()

        self.ccf_coherency_db_constructor_i.run()

        self.ccf_address_db_agent_i.run()

        ccf_dbs.dump_all_ccf_dbs()

if __name__ == "__main__":
    ccf_analyzer_agent.initial()
