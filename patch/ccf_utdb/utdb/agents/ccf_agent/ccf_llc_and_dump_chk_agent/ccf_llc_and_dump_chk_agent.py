#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_agent.py
#
# Owner:              CCF Val team.
# Description:
#################################################################################################
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_base_chk_agent
from agents.ccf_agent.ccf_llc_and_dump_chk_agent.ccf_dump_chk import ccf_dump_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_llc_chk import ccf_llc_chk
from agents.ccf_agent.ccf_llc_and_dump_chk_agent.ccf_llc_chk_cov import ccf_llc_chk_cov
from agents.ccf_data_bases.ccf_dump_db import ccf_dump_db
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import ccf_flow_cov
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import ccf_coherency_cov
from agents.ccf_common_base.ccf_cbregs_all_registers_cov import ccf_cbregs_all_registers_cov
from agents.ccf_common_base.ccf_egress_registers_cov import ccf_egress_registers_cov
from agents.ccf_common_base.ccf_ingress_registers_cov import ccf_ingress_registers_cov
from agents.ccf_common_base.ccf_ncdecs_registers_cov import ccf_ncdecs_registers_cov
from val_utdb_report import VAL_UTDB_MSG

class ccf_llc_and_dump_chk_agent(ccf_base_chk_agent):

    def create_ccf_coherency_queries(self):
        super().create_ccf_coherency_queries()
        if self.preload_logdb_exist and self.si.ccf_dump_chk_en:
            self.ccf_dump_db_i = ccf_dump_db.create()

    def build_checkers(self):
        super().build_checkers()
        self.ccf_llc_chk_i = ccf_llc_chk.create()
        self.ccf_dump_chk_i = ccf_dump_chk.create()

    def build_coverage(self):
        super().build_coverage()
        self.ccf_coherency_cov_i = ccf_coherency_cov.create()
        self.ccf_flow_cov_i = ccf_flow_cov.create()
        self.ccf_llc_chk_cov_i = ccf_llc_chk_cov.create()
        
        self.ccf_cbregs_all_registers_cov_i = ccf_cbregs_all_registers_cov.create()
        self.ccf_ingress_registers_cov_i = ccf_ingress_registers_cov.create()
        self.ccf_egress_registers_cov_i = ccf_egress_registers_cov.create()
        self.ccf_ncdecs_registers_cov_i = ccf_ncdecs_registers_cov.create()

    def connect_logdbs_to_queries(self):
        super().connect_logdbs_to_queries()
        if self.preload_logdb_exist and self.si.ccf_dump_chk_en:
            self.ccf_dump_db_i.connect_to_db('ccf_mem_dump_logdb')

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_llc_and_dump_chk_agent run...")

        #LLC checker
        if self.si.ccf_llc_chk_en:
            self.ccf_llc_chk_i.run()

        # Dump chekcer
        if self.si.ccf_dump_chk_en and self.si.ccf_llc_chk_en:
            self.ccf_dump_chk_i.llc_db = self.ccf_llc_chk_i.dump_llc_ref_db
            self.ccf_dump_chk_i.run()

        if self.si.ccf_cov_en:
            self.ccf_llc_chk_cov_i.run()

if __name__ == "__main__":
    ccf_llc_and_dump_chk_agent.initial()
