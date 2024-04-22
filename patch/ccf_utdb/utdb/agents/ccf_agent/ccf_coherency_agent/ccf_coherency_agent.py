#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_agent.py
#
# Owner:              CCF Val team.
# Description:
#################################################################################################
from val_utdb_base_components import EOT

from agents.ccf_queries.ccf_corrupted_llc_preload_qry import ccf_corrupted_llc_preload_qry
from agents.ccf_agent.ccf_data_chk_agent.ccf_data_chk import ccf_data_chk
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import ccf_flow_cov
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_queries.ccf_gcfi_qry import ccf_gcfi_qry
from agents.ccf_queries.ccf_llc_coherency_qry import ccf_llc_coherency_qry
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import ccf_coherency_cov
from agents.ccf_agent.ccf_coherency_agent.ccf_sad_mca_cov import ccf_sad_mca_cov
from agents.ccf_data_bases.ccf_preload_db import ccf_preload_db
from agents.ccf_data_bases.ccf_santa_db import ccf_santa_db
from agents.ccf_data_bases.ccf_mlc_db import ccf_mlc_db
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from agents.ccf_queries.ccf_power_qry import ccf_power_qry
from agents.ccf_queries.ccf_sb_agent_qry import CCF_SB_AGENT_QRY
from agents.ccf_queries.ccf_power_sb_qry import CCF_POWER_SB_QRY
from agents.ccf_queries.ccf_hw_col_qry import ccf_hw_col_qry
from agents.ccf_common_base.ccf_power_state_agent import ccf_power_state_agent
from agents.ccf_common_base.ccf_cbregs_all_registers_cov import ccf_cbregs_all_registers_cov
from agents.ccf_common_base.ccf_egress_registers_cov import ccf_egress_registers_cov
from agents.ccf_common_base.ccf_ingress_registers_cov import ccf_ingress_registers_cov
from agents.ccf_common_base.ccf_ncdecs_registers_cov import ccf_ncdecs_registers_cov

from agents.ccf_queries.ccf_window_qry import ccf_window_qry
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_chk import ccf_coherency_chk
from agents.ccf_common_base.ccf_ral_chk import ccf_ral_chk
from agents.ccf_data_bases.ccf_flows_pandas_gen import ccf_flows_pandas_gen
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from agents.ccf_agent.ccf_coherency_agent.ccf_sad_mca_chk import ccf_sad_mca_chk
from agents.ccf_agent.ccf_coherency_agent.mem_hash_chk import mem_hash_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_mini_features_chk import ccf_mini_features_chk
from agents.cncu_agent.dbs.ccf_sm_qry import CCF_SM_QRY
from agents.ccf_common_base.ccf_monitor_agent import ref_monitor_array
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_srfsm_sb_qry import CcfSrfsmSbQry
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_params import *
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.dbs.ccf_nc_sb_qry import CCF_NC_SB_QRY

class ccf_coherency_agent(ccf_base_agent):

    ########################
    ### Build functions

    def create_ccf_coherency_queries(self):
        self.ccf_coherency_qry_i = ccf_coherency_qry.create()
        self.ccf_llc_coherency_qry_i = ccf_llc_coherency_qry.create()
        if self.si.mem_hash_chk_en == 1:
            self.ccf_gcfi_qry_i = ccf_gcfi_qry.create()
        if self.si.corrupted_llc_preload_en == 1:
            self.ccf_corrupted_llc_preload_qry_i = ccf_corrupted_llc_preload_qry.create()

        if self.preload_logdb_exist: #emulation doesn't have this database
            self.ccf_preload_db_i = ccf_preload_db.create()
            self.ccf_mlc_db_i = ccf_mlc_db.create()

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
        self.ccf_hw_col_qry_i = ccf_hw_col_qry.create()
        self.ccf_nc_sb_db =  CCF_NC_SB_DB.create()
        #BDADON self.ccf_nc_sb_qry = CCF_NC_SB_QRY.create()

    def build_checkers(self):

        self.ccf_data_chk_i = ccf_data_chk.create()

        self.ccf_coherency_chk_i = ccf_coherency_chk.create()
        
        self.ccf_ral_chk_i = ccf_ral_chk.create()

        self.ccf_sad_mca_chk_i = ccf_sad_mca_chk.create()
        self.ccf_mem_hash_chk_i = mem_hash_chk.create()

        self.ccf_mini_features_chk_i = ccf_mini_features_chk.create()

        self.ccf_srfsm_sb_qry = CcfSrfsmSbQry.create()



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
        if self.sm_logdb_exist:
            self.ccf_sm_qry_i.connect_to_db('ccf_sm_logdb')

        if self.si.ccf_soc_mode:    
            #BDADON self.ccf_hw_col_qry_i.connect_to_db('soc_custom_hw_col_db') 
            self.ccf_hw_col_qry_i.connect_to_db('ccf_custom_hw_col_db')
        else:
            self.ccf_hw_col_qry_i.connect_to_db('ccf_custom_hw_col_db')

        if self.si.mem_hash_chk_en == 1:
            self.ccf_gcfi_qry_i.connect_to_db('merged_gcfi_logdb')
        self.ccf_window_db_i.connect_to_db('cpipe_windows_logdb')
        #BDADON self.ccf_nc_sb_qry.connect_to_db('aligned_sb_logdb')

        

    ######################
    ### Build

    def build(self):
        super().build()

        #Create all agent queries
        self.create_ccf_coherency_queries()

        #Build agents that will help get data from LOGDBs
        self.ccf_llc_db_agent_i = ccf_llc_db_agent.create()

        # Flow Checkers
        self.build_checkers()

        #create pandas df generator
        self.ccf_flows_pandas_gen_i = ccf_flows_pandas_gen.create()

        # create coverage
        #BDADON - huge numbers at SOC!!
        if self.si.ccf_cov_en:
            self.ccf_coherency_cov_i = ccf_coherency_cov.create()
            self.ccf_sad_mca_cov_i = ccf_sad_mca_cov.create()
            self.ccf_flow_cov_i = ccf_flow_cov.create()
            self.ccf_cbregs_all_registers_cov_i = ccf_cbregs_all_registers_cov.create()
            self.ccf_ingress_registers_cov_i = ccf_ingress_registers_cov.create()
            self.ccf_egress_registers_cov_i = ccf_egress_registers_cov.create()
            self.ccf_ncdecs_registers_cov_i = ccf_ncdecs_registers_cov.create()


        self.ref_monitor_array = ref_monitor_array.create()



    def connect(self):
        super().connect()

        self.connect_logdbs()
        self.ccf_srfsm_sb_qry.connect_to_db('merged_sb_logdb')

    def run(self):
        ccf_power_state_agent.run_db_builder(self.ccf_power_qry_i)
        ccf_power_state_agent.initialize_test_power_flow_db()

        self.sr_commands = self.ccf_srfsm_sb_qry.get_time_ordered_sr_commands(SBO_SRFSM_PID)
        #BDADON self.ccf_nc_sb_db.run_db_builder()
        for idx in range(len(ccf_power_state_agent.test_power_flow_db)):
            COH_GLOBAL.global_vars["POWER_DB_INDEX"] = idx
            COH_GLOBAL.global_vars["START_OF_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["START_TEST"]
            COH_GLOBAL.global_vars["END_OF_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["END_TEST"]
            c6_entry = ccf_power_state_agent.test_power_flow_db[idx]["C6_TIME_IN_RANGE"]
            c6_exit = []
            for i in range(len(self.sr_commands)):
                if i % 2 == 1: #takes restore comand only (not save commands)
                    if self.sr_commands[i].time > COH_GLOBAL.global_vars["START_OF_TEST"] and self.sr_commands[i].time < COH_GLOBAL.global_vars["END_OF_TEST"]:
                        c6_exit.append(self.sr_commands[i].time)
            COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"] = dict(zip(c6_entry, c6_exit))

            self.run_test(is_cold_reset=ccf_power_state_agent.test_power_flow_db[idx]["COLD_RESET"])


    def reset_db(self, is_cold_reset):
        ccf_dbs.reset_ccf_flows()

        ccf_dbs.reset_mem_db()


        #Reset ref monitor + initial DB structure
        ccf_dbs.reset_ref_monitor_per_cbo_db()
        self.ref_monitor_array.config(self.si.num_of_cbo)

        self.ccf_llc_db_agent_i.reset()

        self.ccf_mini_features_chk_i.reset()
        self.ccf_sad_mca_chk_i.reset()




        if is_cold_reset:
            self.ccf_sad_mca_chk_i.cold_reset_only()

    def run_test(self, is_cold_reset):
        VAL_UTDB_MSG(time=0, msg="ccf_coherency_agent run...")
        self.reset_db(is_cold_reset)
        ccf_registers.get_pointer().get_registers_value()

        if self.sm_logdb_exist:
            SM_DB.run_db_builder(self.ccf_sm_qry_i)

        #Load all ccf dbs for that test.
        ccf_dbs.load_all_ccf_dbs()

        if len(self.ccf_flows) != 0:
            #ccf_coherency_checkers
            self.ccf_coherency_chk_i.run()
            if self.si.mem_hash_chk_en:
                self.ccf_mem_hash_chk_i.run()

            self.ccf_ral_chk_i.run()

            #BDADON self.ccf_flows_pandas_gen_i.run()

            if self.si.ccf_cov_en:
                self.ccf_coherency_cov_i.run()
        else:
            VAL_UTDB_ERROR(time=EOT, msg="Tried to get ccf_flows but it's empty dict - all ccf coherency agent checks was skipped please check your test.")

if __name__ == "__main__":
    ccf_coherency_agent.initial()
