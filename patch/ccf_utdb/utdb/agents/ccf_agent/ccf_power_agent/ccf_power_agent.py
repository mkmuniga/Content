#!/usr/bin/env python3.6.3

from val_utdb_components import val_utdb_agent
from agents.ccf_data_bases.ccf_power_sb_db import CCF_POWER_SB_DB
from agents.ccf_queries.ccf_power_sb_qry import CCF_POWER_SB_QRY

from agents.ccf_agent.ccf_power_agent.ccf_power_checkers.ccf_power_checkers import CCF_POWER_CHECKER
from agents.ccf_agent.ccf_power_agent.ccf_power_utils.ccf_power_si import POWER_SI
from agents.ccf_agent.ccf_power_agent.ccf_power_utils.ccf_power_ral_utils import POWER_RAL_AGENT
from agents.ccf_agent.ccf_power_agent.ccf_power_utils.ccf_power_hw_db import POWER_HW_DB

class ccf_power_agent(val_utdb_agent):
    ral_utils: POWER_RAL_AGENT

    def __init__(self):
        super().__init__()
        self.ccf_power_ral_utils: POWER_RAL_AGENT = None
        self.ccf_power_checker: CCF_POWER_CHECKER = None
        self.ccf_power_sb_db: CCF_POWER_SB_DB = None
        self.ccf_power_sb_qry: CCF_POWER_SB_QRY = None
        self.ccf_power_hw_db: POWER_HW_DB = None
        self.configure()

    def configure(self):
        self.set_si(POWER_SI.get_pointer())
        self.ccf_power_ral_utils = POWER_RAL_AGENT.create()

    def build(self):
        #self.ccf_power_checker = CCF_POWER_CHECKER.create()
        self.ccf_power_sb_db = CCF_POWER_SB_DB.create()
        self.ccf_power_sb_qry = CCF_POWER_SB_QRY.create()
        self.ccf_power_hw_db  =  POWER_HW_DB.create()

    def connect(self):
        self.ccf_power_sb_qry.connect_to_db('merged_pmsb_logdb')
        self.ccf_power_hw_db.connect_to_db('ccf_custom_hw_col_db')


    def run(self):
        self.ccf_power_checker = CCF_POWER_CHECKER.get_pointer()
        self.ccf_power_sb_db.run_db_builder()
        self.ccf_power_checker.run()


if __name__ == "__main__":
    ccf_power_agent.initial()
