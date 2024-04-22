from val_utdb_report import VAL_UTDB_MSG

from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import CCF_MONITOR_CG, CCF_GENERAL_FLOW_CG, SAD_CHANGE_CG
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov


class ccf_sad_cov_collect(ccf_base_component):
    def collect_mktme_crababort_coverage(self, mktme_crab, region):
        ccf_flow_cg = CCF_GENERAL_FLOW_CG.get_pointer()
        if ("CRABABORT" != region):
            ccf_flow_cg.sample(mktme_crababort=mktme_crab)
        if not mktme_crab:
            ccf_flow_cg.sample(legal_mktme_sad=region)

    def collect_set_monitor_coverage(self, region):
        ccf_monitor_cg = CCF_MONITOR_CG.get_pointer()
        ccf_monitor_cg.sample(setmonitor_hit_region=region)

class ccf_sad_chk_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.ccf_general_flow_cg: CCF_GENERAL_FLOW_CG = CCF_GENERAL_FLOW_CG.get_pointer()
        self.ccf_monitor_cg: CCF_MONITOR_CG = CCF_MONITOR_CG.get_pointer()
        self.sad_change_cg: SAD_CHANGE_CG = SAD_CHANGE_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        VAL_UTDB_MSG(time=0, msg="End of sad checker coverage Run..")