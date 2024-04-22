#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_flow_base_chk_agent
from val_utdb_report import VAL_UTDB_MSG

from agents.ccf_agent.ccf_sad_chk_agent.ccf_sad_chk import ccf_sad_chk
from agents.ccf_agent.ccf_sad_chk_agent.ccf_sad_chk_cov import ccf_sad_chk_cov

from agents.ccf_common_base.ccf_cbregs_all_registers_cov import ccf_cbregs_all_registers_cov
from agents.ccf_common_base.ccf_egress_registers_cov import ccf_egress_registers_cov
from agents.ccf_common_base.ccf_ingress_registers_cov import ccf_ingress_registers_cov
from agents.ccf_common_base.ccf_ncdecs_registers_cov import ccf_ncdecs_registers_cov


class ccf_sad_chk_agent(ccf_flow_base_chk_agent):

    def build_checkers(self):
        super().build_checkers()
        self.ccf_sad_chk_i = ccf_sad_chk.create()

    def build_coverage(self):
        super().build_coverage()
        self.ccf_sad_chk_cov_i = ccf_sad_chk_cov.create()
        self.ccf_cbregs_all_registers_cov_i = ccf_cbregs_all_registers_cov.create()
        self.ccf_ingress_registers_cov_i = ccf_ingress_registers_cov.create()
        self.ccf_egress_registers_cov_i = ccf_egress_registers_cov.create()
        self.ccf_ncdecs_registers_cov_i = ccf_ncdecs_registers_cov.create()

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)
        self.ccf_sad_chk_i.reset()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_sad_chk_agent run...")

        if self.si.ccf_sad_chk_en:
            self.run_checker_on_each_flow(checker_ptr=self.ccf_sad_chk_i)

        if self.si.ccf_cov_en:
            self.ccf_sad_chk_cov_i.run()

if __name__ == "__main__":
    ccf_sad_chk_agent.initial()
