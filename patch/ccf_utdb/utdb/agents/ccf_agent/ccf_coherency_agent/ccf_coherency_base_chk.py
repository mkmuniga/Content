#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_chk.py
#
# Owner:              asaffeld
# Creation Date:      2.2021
#
# ###############################################
#
# Description:
#   This file contains all info on ccf_coherency_base_chk
#   basic functions every sub checkers has to implement
#################################################################################################
from agents.ccf_common_base.ccf_common_base_class import ccf_base_chk
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import CCF_CHECKER_CG

class ccf_coherency_base_chk(ccf_base_chk):
    flow_csv_db = {}
    checker_enable = 1
    checker_name = "ccf_coherency_base_chk"

    def should_check_flow(self, flow: ccf_flow):
        return self.checker_enable


    def check_flow(self, flow: ccf_flow):
        pass

    def collect_coverage(self):
        if self.si.ccf_cov_en:
            ccf_chk_cg = CCF_CHECKER_CG.get_pointer()
            ccf_chk_cg.sample(checker=self.checker_name)
