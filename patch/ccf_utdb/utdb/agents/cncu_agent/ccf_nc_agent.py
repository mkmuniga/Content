#!/usr/bin/env python3.6.3a

#################################################################################################
# cncu_agent.py
#
# Owner:              ranzohar & mlugassi

# Creation Date:      11.2020
#
# ###############################################
#
# Description:
#   This agent file creates, connects, and runs all components of this agent.
#   At first usage the user should find-replace the following values according to the real usage:
#           ccf_coherency_.*_en
#           DB_NAME_BY_INI_FILE
#
#################################################################################################
from agents.cncu_agent.checkers.ccf_nc_checker import CCF_NC_CHECKER
from agents.cncu_agent.common.ccf_nc_common_base import CCF_NC_BASE_AGENT
from agents.cncu_agent.common.ccf_nc_run_info import CCF_NC_RUN_INFO
from agents.cncu_agent.dbs.ccf_nc_mcast_qry import CCF_NC_MCAST_QRY
from agents.cncu_agent.dbs.ccf_nc_pmon_overflow_db import NC_PMON_OVERFLOW_DB
from agents.cncu_agent.dbs.ccf_nc_reset_db import NC_RESET_DB
from agents.cncu_agent.dbs.ccf_nc_seq_trk_qry import CCF_NC_SEQ_TRK_QRY
from agents.cncu_agent.utils.cncu_utils import REMAPPING
from agents.cncu_agent.utils.ccf_vcr_pla_handler import VCR_PLA_HANDLER
from agents.cncu_agent.dbs.cncu_flow_qry import CCF_NC_FLOW_QRY
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from agents.cncu_agent.dbs.ccf_sm_qry import CCF_SM_QRY
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.dbs.ccf_nc_sb_qry import CCF_NC_SB_QRY
from agents.cncu_agent.utils.ccf_sm_map import SM_MAP
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES
from agents.ccf_common_base.ccf_cbregs_all_registers_cov import ccf_cbregs_all_registers_cov
from agents.ccf_common_base.ccf_egress_registers_cov import ccf_egress_registers_cov
from agents.ccf_common_base.ccf_ingress_registers_cov import ccf_ingress_registers_cov
from agents.ccf_common_base.ccf_ncdecs_registers_cov import ccf_ncdecs_registers_cov


class ccf_nc_agent(CCF_NC_BASE_AGENT):

    def __init__(self):
        super().__init__()
        self.ccf_nc_checker: CCF_NC_CHECKER = None
        self.ccf_nc_flow_qry: CCF_NC_FLOW_QRY = None
        self.ccf_sm_qry: CCF_SM_QRY = None
        self.ccf_nc_sb_db: CCF_NC_SB_DB = None
        self.reset_db: NC_RESET_DB = None
        self.pmon_overflow_db: NC_PMON_OVERFLOW_DB = None
        self.ccf_nc_sb_qry: CCF_NC_SB_QRY = None
        self.ccf_nc_seq_trk_qry: CCF_NC_SEQ_TRK_QRY = None
        self.ccf_nc_mcast_qry: CCF_NC_MCAST_QRY = None
        self.ccf_nc_run_info: CCF_NC_RUN_INFO = None

    def build(self):
        super().build()
        self.ccf_nc_checker = CCF_NC_CHECKER.create()
        self.ccf_nc_flow_qry = CCF_NC_FLOW_QRY.create()
        self.ccf_sm_qry = CCF_SM_QRY.create()
        self.ccf_nc_sb_db = CCF_NC_SB_DB.create()
        self.reset_db = NC_RESET_DB.create()
        self.pmon_overflow_db = NC_PMON_OVERFLOW_DB.create()
        self.ccf_nc_sb_qry = CCF_NC_SB_QRY.create()
        self.ccf_nc_seq_trk_qry = CCF_NC_SEQ_TRK_QRY.create()
        self.ccf_nc_mcast_qry = CCF_NC_MCAST_QRY.create()
        self.ccf_nc_run_info = CCF_NC_RUN_INFO.create()
        
        # create coverage
        self.ccf_cbregs_all_registers_cov_i = ccf_cbregs_all_registers_cov.create()
        self.ccf_ingress_registers_cov_i = ccf_ingress_registers_cov.create()
        self.ccf_egress_registers_cov_i = ccf_egress_registers_cov.create()
        self.ccf_ncdecs_registers_cov_i = ccf_ncdecs_registers_cov.create()

        REMAPPING.set_remap_dict()
        VCR_PLA_HANDLER.build()
        SM_MAP.build(self.si.soc_mode)

    def connect(self):
        super().connect()
        self.ccf_nc_flow_qry.connect_to_db('merged_ccf_nc_logdb')
        self.ccf_sm_qry.connect_to_db('ccf_sm_logdb')
        self.ccf_nc_sb_qry.connect_to_db('aligned_sb_logdb')
        self.reset_db.connect_to_db(UNIQUE_DEFINES.custom_hw_col_db_name)
        self.pmon_overflow_db.connect_to_db(UNIQUE_DEFINES.custom_hw_col_db_name)
        self.ccf_nc_seq_trk_qry.connect_to_db('seq_trk_logdb')
        self.ccf_nc_mcast_qry.connect_to_db('merged_ccf_mcast_logdb')
        self.reset_db.connect_to_db(UNIQUE_DEFINES.custom_hw_col_db_name)
        if not UNIQUE_DEFINES.is_low_power_ccf:
            if self.si.soc_mode:
                self.reset_db.connect_to_db('soc_custom_hw_col_db')
            else:
                self.reset_db.connect_to_db('ccf_custom_hw_col_db')

    def run(self):
        super().run()
        SM_DB.run_db_builder(self.ccf_sm_qry)
        self.ccf_nc_run_info.set_run_info()
        self.ccf_nc_sb_db.run_db_builder()
        self.reset_db.build_db()
        self.pmon_overflow_db.build_db()
        self.ccf_nc_checker.run()


if __name__ == "__main__":
    ccf_nc_agent.initial()
