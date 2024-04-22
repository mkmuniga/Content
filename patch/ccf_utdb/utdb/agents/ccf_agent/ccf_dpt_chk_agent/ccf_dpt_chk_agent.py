#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_dpt_chk_agent.ccf_prefetch_dpt_chk import ccf_prefetch_dpt_chk
from agents.ccf_agent.ccf_dpt_chk_agent.ccf_dpt_chk_cov import ccf_dpt_chk_cov
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_base_chk_agent
from agents.ccf_agent.ccf_dpt_chk_agent.ccf_wcil_dpt_chk import ccf_wcil_dpt_chk
from agents.ccf_data_bases.ccf_cbos_db import ccf_cbos_db
from agents.ccf_data_bases.ccf_prefetch_wcil_dpt_at_same_time_db import ccf_prefetch_wcil_dpt_at_same_time_db
from val_utdb_report import VAL_UTDB_MSG

from agents.ccf_data_bases.ccf_santa_db import ccf_santa_db
from agents.ccf_queries.ccf_hw_col_qry import ccf_hw_col_qry


class ccf_dpt_chk_agent(ccf_base_chk_agent):
    def create_ccf_coherency_queries(self):
        super().create_ccf_coherency_queries()
        self.ccf_cbos_db_db_i = ccf_cbos_db.create()
        self.ccf_prefetch_wcil_dpt_at_same_time_db_i = ccf_prefetch_wcil_dpt_at_same_time_db.create()
        self.ccf_santa_db_i = ccf_santa_db.create()
        self.ccf_hw_col_qry_i = ccf_hw_col_qry.create()

    def connect_logdbs_to_queries(self):
        super().connect_logdbs_to_queries()
        self.ccf_cbos_db_db_i.connect_to_db('cbos_logdb')
        self.ccf_prefetch_wcil_dpt_at_same_time_db_i.connect_to_db('prefetch_wcil_dpt_same_time_logdb')
        self.ccf_santa_db_i.connect_to_db('merged_ccf_coherency_logdb')
        self.ccf_hw_col_qry_i.connect_to_db('ccf_custom_hw_col_db')

    def build_checkers(self):
        super().build_checkers()
        self.ccf_prefetch_dpt_chk_i = ccf_prefetch_dpt_chk.create()
        self.ccf_wcil_dpt_chk_i = ccf_wcil_dpt_chk.create()

    def build_coverage(self):
        super().build_coverage()
        self.ccf_dpt_chk_cov_i = ccf_dpt_chk_cov.create()

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)
        self.ccf_prefetch_dpt_chk_i.reset()
        # self.ccf_wcil_dpt_chk_i.reset()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_dpt_chk_agent run...")
        self.ccf_prefetch_dpt_chk_i.run()
        self.ccf_wcil_dpt_chk_i.run()

        if self.si.ccf_cov_en:
            self.ccf_dpt_chk_cov_i.run()

if __name__ == "__main__":
    ccf_dpt_chk_agent.initial()
