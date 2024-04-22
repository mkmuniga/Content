#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_bw_counter_chk_agent.ccf_bw_counter_chk import ccf_bw_counter_chk
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_flow_base_chk_agent
from val_utdb_report import VAL_UTDB_MSG


class ccf_bw_counter_chk_agent(ccf_flow_base_chk_agent):

    def build_checkers(self):
        super().build_checkers()
        self.ccf_bw_counter_chk_i = ccf_bw_counter_chk.create()
        self.ccf_bw_counter_chk_i.checker_enable = self.si.ccf_pp_bw_counter_chk_en

    def reset_db(self, is_cold_reset):
        super().reset_db(is_cold_reset)
        self.ccf_bw_counter_chk_i.reset()

    def run_test(self, is_cold_reset):
        super().run_test(is_cold_reset)
        VAL_UTDB_MSG(time=0, msg="ccf_bw_counter_chk_agent run...")
        if self.si.ccf_pp_bw_counter_chk_en:
            self.ccf_bw_counter_chk_i.initialize_dict()
            self.run_checker_on_each_flow(checker_ptr=self.ccf_bw_counter_chk_i)
            self.ccf_bw_counter_chk_i.ccf_bw_ral_check()

if __name__ == "__main__":
    ccf_bw_counter_chk_agent.initial()
