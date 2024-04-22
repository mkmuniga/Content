from val_utdb_report import VAL_UTDB_MSG
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_cov import ccf_cg, ccf_cp, ccf_base_cov
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

class CCF_LLC_CHK_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.hitmiss_cp = ccf_cp([0, 1])

        valid_maps = list(range(0,CCF_COH_DEFINES.max_num_of_data_ways))
        valid_maps.append(CCF_COH_DEFINES.SNOOP_FILTER)
        self.llc_data_way_cp = ccf_cp(valid_maps)
        self.llc_tag_way_cp = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_tag_ways)))

        self.llc_half_cp = ccf_cp([0, 1])
        self.llc_slice_cp = ccf_cp(list(range(0, self.si.num_of_cbo)))
        self.set_cp = ccf_cp(list(range(0, CCF_COH_DEFINES.num_of_sets)))
        self.llc_uop_cp = ccf_cp(CCF_FLOW_UTILS.llc_opcodes)

        self.reject_cp = ccf_cp([0, 1])
        #self.lru_cp = ccf_cp(list(range(0,3)))


        self.cv_cp = ccf_cp(list(range(0, CCF_COH_DEFINES.num_physical_cv_bits)))

        self.llc_data_chk_cp = ccf_cp([0, 1])
        self.llc_data_ecc_chk_cp = ccf_cp([0, 1])

        self.mca_data_ecc_cp = ccf_cp([self.si.ccf_preload_data_correctable_errs])

        self.vul_accepected_cp = ccf_cp([1]) #We need to count only when it happened
        self.silent_evict_accepted_cp = ccf_cp([1])#We need to count only when it happened

class ccf_llc_chk_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.ccf_llc_chk_cg: CCF_LLC_CHK_CG = CCF_LLC_CHK_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        VAL_UTDB_MSG(time=0, msg="End of llc chk coverage Run..")
