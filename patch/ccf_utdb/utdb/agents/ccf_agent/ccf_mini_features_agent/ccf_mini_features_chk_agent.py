#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_queries.ccf_hw_col_qry import ccf_hw_col_qry
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG,EOT
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_mini_features_agent.ccf_mini_features_qry import ccf_mini_features_qry
from agents.ccf_agent.ccf_mini_features_agent.ccf_mini_features_chk import ccf_mini_features_chk
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_base_chk_agent

class ccf_mini_features_chk_agent(ccf_base_chk_agent):
    def create_ccf_coherency_queries(self):
        super().create_ccf_coherency_queries()
        self.ccf_mini_features_qry_i = ccf_mini_features_qry.create()

    def connect_logdbs_to_queries(self):
        super().connect_logdbs_to_queries()
        self.ccf_mini_features_qry_i.connect_to_db('ccf_custom_hw_col_db')


    def build_checkers(self):
        super().build_checkers()
        self.ccf_mini_features_chk_i = ccf_mini_features_chk.create()


    def build_coverage(self):
        super().build_coverage()

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)
        self.ccf_mini_features_chk_i.reset()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_mini_features_chk_agent run...")
        self.ccf_mini_features_chk_i.run()

        # if self.si.ccf_cov_en:
        #     self.ccf_mini_features_cov_i.run()

if __name__ == "__main__":
    ccf_mini_features_chk_agent.initial()