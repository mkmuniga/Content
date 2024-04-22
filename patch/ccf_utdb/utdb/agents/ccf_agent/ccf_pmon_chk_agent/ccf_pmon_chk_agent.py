#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_pmon_chk_agent.py
#
# Owner:              CCF Val team.
# Description:
#################################################################################################
from agents.ccf_agent.ccf_pmon_chk_agent.ccf_pmon_chk_cov import ccf_pmon_chk_cov
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_base_chk_agent
from agents.ccf_agent.ccf_pmon_chk_agent.ccf_pmon_chk import ccf_pmon_chk
from val_utdb_report import VAL_UTDB_MSG
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.dbs.ccf_nc_sb_qry import CCF_NC_SB_QRY
from agents.ccf_queries.ccf_common_qry import CCF_COMMON_QRY, ccf_common_custom_qry 
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry


class ccf_pmon_chk_agent(ccf_base_chk_agent):

    def create_ccf_coherency_queries(self):
        super().create_ccf_coherency_queries()
        self.ccf_nc_sb_db =  CCF_NC_SB_DB.create()
        self.ccf_nc_sb_qry = CCF_NC_SB_QRY.create()
        self.ccf_common_qry = CCF_COMMON_QRY.create()
        self.ccf_common_cus_qry = ccf_common_custom_qry.create()
        self.ccf_coherency_qry_i = ccf_coherency_qry.create()

    def build_checkers(self):
        super().build_checkers()
        self.ccf_pmon_chk_i = ccf_pmon_chk.create()


    def build_coverage(self):
        super().build_coverage()
        self.ccf_pmon_chk_cov_i = ccf_pmon_chk_cov.create()

    def connect_logdbs_to_queries(self):
        super().connect_logdbs_to_queries()
        self.ccf_nc_sb_qry.connect_to_db('aligned_sb_logdb')
        self.ccf_common_qry.connect_to_db('merged_common_logdb')
        self.ccf_common_cus_qry.connect_to_db('ccf_custom_hw_col_db')
        self.ccf_coherency_qry_i.connect_to_db('merged_ccf_coherency_logdb')

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)
        self.ccf_nc_sb_db.run_db_builder()
        self.ccf_pmon_chk_i.reset()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)

        VAL_UTDB_MSG(time=0, msg="ccf_pmon_chk_agent run...")
        if self.si.ccf_pmon_chk_en:
            records=self.ccf_common_qry.get_common_records()
            for p in records:
              for t in p.EVENTS:
                VAL_UTDB_MSG(time=0, msg=t)
                timeperiod=self.ccf_common_qry.COMMON_REC(t).get_timeperiod()
                clk=self.ccf_common_qry.COMMON_REC(t).get_clk_name()
                info_msg = "timeperiod get: {}".format((timeperiod))
                VAL_UTDB_MSG(time=0, msg=info_msg)
                info_msg = "timeperiod get: {}".format((clk))
                VAL_UTDB_MSG(time=0, msg=info_msg)

        if self.si.ccf_pmon_chk_en:
            self.ccf_pmon_chk_i.check_pmon(timeperiod)

        if self.si.ccf_cov_en:
            self.ccf_pmon_chk_cov_i.run()

if __name__ == "__main__":
    ccf_pmon_chk_agent.initial()
