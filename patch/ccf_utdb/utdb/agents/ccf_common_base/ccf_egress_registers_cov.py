
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cp, ccf_cg


class ccf_egress_registers_cov(ccf_base_cov):

    def __init__(self):
        super().__init__()

        self.ccf_reg_cov_egr_misc_cfg_bw_read_counter_with_pref_cg : ccf_reg_cov_egr_misc_cfg_bw_read_counter_with_pref_cg = ccf_reg_cov_egr_misc_cfg_bw_read_counter_with_pref_cg.get_pointer()

        self.registers_cov = {
            "egr_misc_cfg_bw_read_counter_with_pref": self.ccf_reg_cov_egr_misc_cfg_bw_read_counter_with_pref_cg
        }

    def create_cg(self):
        # define covergroups here
        pass


class ccf_reg_cov_egr_misc_cfg_bw_read_counter_with_pref_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])


