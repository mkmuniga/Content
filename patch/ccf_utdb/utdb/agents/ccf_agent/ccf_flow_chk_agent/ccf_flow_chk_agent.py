#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_flow_base_chk_agent
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from val_utdb_report import VAL_UTDB_MSG

from agents.ccf_agent.ccf_flow_chk_agent.ccf_flow_chk import ccf_flow_chk
from agents.ccf_agent.ccf_flow_chk_agent.ccf_flow_chk_cov import ccf_flow_chk_cov


class ccf_flow_chk_agent(ccf_flow_base_chk_agent):

    def build_checkers(self):
        super().build_checkers()
        self.ccf_flow_chk_i = ccf_flow_chk.create()
        self.ccf_flow_chk_i.checker_enable = self.si.ccf_flow_chk_en

    def create_ccf_coherency_queries(self):
        super().create_ccf_coherency_queries()
        self.ccf_coherency_qry_i = ccf_coherency_qry.create()

    def connect_logdbs_to_queries(self):
        super().connect_logdbs_to_queries()
        self.ccf_coherency_qry_i.connect_to_db('merged_ccf_coherency_logdb')

    def build_coverage(self):
        self.ccf_flow_chk_cov_i = ccf_flow_chk_cov.create()

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_flow_chk_agent run...")
        self.run_checker_on_each_flow(checker_ptr=self.ccf_flow_chk_i)

        if self.si.ccf_cov_en:
            self.ccf_flow_chk_cov_i.run()
        VAL_UTDB_MSG(time=0, msg="ccf_flow_chk_agent run is Done")

if __name__ == "__main__":
    ccf_flow_chk_agent.initial()
