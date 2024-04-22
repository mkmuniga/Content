#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_flow_base_chk_agent
from val_utdb_report import VAL_UTDB_MSG

from agents.ccf_agent.ccf_data_chk_agent.ccf_data_chk import ccf_data_chk
from agents.ccf_agent.ccf_data_chk_agent.ccf_data_chk_cov import ccf_data_chk_cov
from agents.ccf_data_bases.ccf_dbs import ccf_dbs


class ccf_data_chk_agent(ccf_flow_base_chk_agent):

    def build_checkers(self):
        super().build_checkers()
        self.ccf_data_chk_i = ccf_data_chk.create()
        self.ccf_data_chk_i.checker_enable = self.si.ccf_data_chk_en

    def build_coverage(self):
        self.ccf_data_chk_cov_i = ccf_data_chk_cov.create()

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)

    def sort_dbs(self):
        ccf_dbs.sort_ccf_flows()
        if self.si.ccf_data_chk_en:
            self.ccf_data_chk_i.sort_dbs()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_data_chk_agent run...")

        self.sort_dbs()

        self.run_checker_on_each_flow(checker_ptr=self.ccf_data_chk_i)

        if self.si.ccf_cov_en:
            self.ccf_data_chk_cov_i.run()
        VAL_UTDB_MSG(time=0, msg="ccf_data_chk_agent run is Done")

if __name__ == "__main__":
    ccf_data_chk_agent.initial()
