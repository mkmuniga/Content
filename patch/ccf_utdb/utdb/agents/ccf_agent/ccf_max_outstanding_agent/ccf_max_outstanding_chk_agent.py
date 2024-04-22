#!/usr/bin/env python3.6.3
#from agents.ccf_agent.ccf_max_outstanding_agent.ccf_max_outstandi import ccf_max_outstanding_chk
from agents.ccf_agent.ccf_max_outstanding_agent.ccf_max_outstanding_cov import ccf_max_outstanding_chk_cov
from agents.ccf_agent.ccf_max_outstanding_agent.ccf_max_outstanding_qry import ccf_max_outstanding_qry, ccf_max_outstanding_custom_qry
from agents.ccf_agent.ccf_max_outstanding_agent.ccf_max_outstanding_chk import ccf_max_outstanding_chk
from agents.ccf_data_bases.ccf_santa_db import ccf_santa_db
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_base_chk_agent
from val_utdb_report import VAL_UTDB_MSG

class ccf_max_outstanding_chk_agent(ccf_base_chk_agent):
    def create_ccf_coherency_queries(self):
        super().create_ccf_coherency_queries()
        self.ccf_max_outstanding_qry_i = ccf_max_outstanding_qry.create()
        self.ccf_max_outstanding_chk_i = ccf_max_outstanding_chk.create()
        self.ccf_max_outstanding_chk_cov_i = ccf_max_outstanding_chk_cov.create()
        self.ccf_max_outstanding_custom_qry_i = ccf_max_outstanding_custom_qry.create()


    def connect_logdbs_to_queries(self):
        super().connect_logdbs_to_queries()
        self.ccf_max_outstanding_qry_i.connect_to_db('merged_ccf_coherency_logdb')
        self.ccf_max_outstanding_custom_qry_i.connect_to_db('ccf_custom_hw_col_db')


    def build_checkers(self):
        super().build_checkers()


    def build_coverage(self):
        super().build_coverage()
        self.ccf_max_outstanding_chk_cov_i = ccf_max_outstanding_chk_cov.create()


    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)
        self.ccf_max_outstanding_chk_i.reset()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_max_outstanding_chk_agent run...")
        self.ccf_max_outstanding_chk_i.run()
        if self.si.ccf_cov_en:
            self.ccf_max_outstanding_chk_cov_i.run()



if __name__ == "__main__":
    ccf_max_outstanding_chk_agent.initial()
