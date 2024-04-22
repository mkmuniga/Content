from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cp, ccf_cg


class ccf_ingress_registers_cov(ccf_base_cov):

    def __init__(self):
        super().__init__()

        self.ccf_reg_cov_flow_cntrl_always_snoop_all_ia_cg              : ccf_reg_cov_flow_cntrl_always_snoop_all_ia_cg              = ccf_reg_cov_flow_cntrl_always_snoop_all_ia_cg.get_pointer()
        self.ccf_reg_cov_flow_cntrl_force_snoop_all_cg                  : ccf_reg_cov_flow_cntrl_force_snoop_all_cg                  = ccf_reg_cov_flow_cntrl_force_snoop_all_cg.get_pointer()
        self.ccf_reg_cov_flow_cntrl_dis_spec_snoop_cg                   : ccf_reg_cov_flow_cntrl_dis_spec_snoop_cg                   = ccf_reg_cov_flow_cntrl_dis_spec_snoop_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_all_cg              : ccf_reg_cov_ni_control_force_selfsnoop_all_cg              = ccf_reg_cov_ni_control_force_selfsnoop_all_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_snoopfilter_only_cg : ccf_reg_cov_ni_control_force_selfsnoop_snoopfilter_only_cg = ccf_reg_cov_ni_control_force_selfsnoop_snoopfilter_only_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_drd_cg              : ccf_reg_cov_ni_control_force_selfsnoop_drd_cg              = ccf_reg_cov_ni_control_force_selfsnoop_drd_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_drd_prefetch_cg     : ccf_reg_cov_ni_control_force_selfsnoop_drd_prefetch_cg     = ccf_reg_cov_ni_control_force_selfsnoop_drd_prefetch_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_crd_cg              : ccf_reg_cov_ni_control_force_selfsnoop_crd_cg              = ccf_reg_cov_ni_control_force_selfsnoop_crd_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_crd_prefetch_cg     : ccf_reg_cov_ni_control_force_selfsnoop_crd_prefetch_cg     = ccf_reg_cov_ni_control_force_selfsnoop_crd_prefetch_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_rfo_cg              : ccf_reg_cov_ni_control_force_selfsnoop_rfo_cg              = ccf_reg_cov_ni_control_force_selfsnoop_rfo_cg.get_pointer()
        self.ccf_reg_cov_ni_control_force_selfsnoop_rfo_prefetch_cg     : ccf_reg_cov_ni_control_force_selfsnoop_rfo_prefetch_cg     = ccf_reg_cov_ni_control_force_selfsnoop_rfo_prefetch_cg.get_pointer()
        self.ccf_reg_cov_ni_control_crd_always_cachenear_cg             : ccf_reg_cov_ni_control_crd_always_cachenear_cg             = ccf_reg_cov_ni_control_crd_always_cachenear_cg.get_pointer()
        self.ccf_reg_cov_ni_control_drd_always_cachenear_cg             : ccf_reg_cov_ni_control_drd_always_cachenear_cg             = ccf_reg_cov_ni_control_drd_always_cachenear_cg.get_pointer()
        self.ccf_reg_cov_ni_control_rfo_always_cachenear_cg             : ccf_reg_cov_ni_control_rfo_always_cachenear_cg             = ccf_reg_cov_ni_control_rfo_always_cachenear_cg.get_pointer()
        self.ccf_reg_cov_ni_control_disable_data_vulnerable_cg          : ccf_reg_cov_ni_control_disable_data_vulnerable_cg          = ccf_reg_cov_ni_control_disable_data_vulnerable_cg.get_pointer()
        self.ccf_reg_cov_ni_control_disable_go_s_for_drd_hit_cg         : ccf_reg_cov_ni_control_disable_go_s_for_drd_hit_cg         = ccf_reg_cov_ni_control_disable_go_s_for_drd_hit_cg.get_pointer()
        self.ccf_reg_cov_dbp_arac_cntrl_isobserverind_cg                : ccf_reg_cov_dbp_arac_cntrl_isobserverind_cg                = ccf_reg_cov_dbp_arac_cntrl_isobserverind_cg.get_pointer()

        self.registers_cov = {
            "flow_cntrl_always_snoop_all_ia": self.ccf_reg_cov_flow_cntrl_always_snoop_all_ia_cg,
            "flow_cntrl_force_snoop_all": self.ccf_reg_cov_flow_cntrl_force_snoop_all_cg,
            "flow_cntrl_dis_spec_snoop": self.ccf_reg_cov_flow_cntrl_dis_spec_snoop_cg,
            "ni_control_force_selfsnoop_all": self.ccf_reg_cov_ni_control_force_selfsnoop_all_cg,
            "ni_control_force_selfsnoop_snoopfilter_only": self.ccf_reg_cov_ni_control_force_selfsnoop_snoopfilter_only_cg,
            "ni_control_force_selfsnoop_drd": self.ccf_reg_cov_ni_control_force_selfsnoop_drd_cg,
            "ni_control_force_selfsnoop_drd_prefetch": self.ccf_reg_cov_ni_control_force_selfsnoop_drd_prefetch_cg,
            "ni_control_force_selfsnoop_crd": self.ccf_reg_cov_ni_control_force_selfsnoop_crd_cg,
            "ni_control_force_selfsnoop_crd_prefetch": self.ccf_reg_cov_ni_control_force_selfsnoop_crd_prefetch_cg,
            "ni_control_force_selfsnoop_rfo": self.ccf_reg_cov_ni_control_force_selfsnoop_rfo_cg,
            "ni_control_force_selfsnoop_rfo_prefetch": self.ccf_reg_cov_ni_control_force_selfsnoop_rfo_prefetch_cg,
            "ni_control_crd_always_cachenear": self.ccf_reg_cov_ni_control_crd_always_cachenear_cg,
            "ni_control_drd_always_cachenear": self.ccf_reg_cov_ni_control_drd_always_cachenear_cg,
            "ni_control_rfo_always_cachenear": self.ccf_reg_cov_ni_control_rfo_always_cachenear_cg,
            "ni_control_disable_data_vulnerable": self.ccf_reg_cov_ni_control_disable_data_vulnerable_cg,
            "ni_control_disable_go_s_for_drd_hit": self.ccf_reg_cov_ni_control_disable_go_s_for_drd_hit_cg,
            "dbp_arac_cntrl_isobserverind": self.ccf_reg_cov_dbp_arac_cntrl_isobserverind_cg
        }

    def create_cg(self):
        # define covergroups here
        pass


class ccf_reg_cov_dbp_arac_cntrl_isobserverind_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp(list(range(0, pow(2, 5))))


class ccf_reg_cov_ni_control_force_selfsnoop_all_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_snoopfilter_only_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_drd_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_drd_prefetch_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_crd_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_crd_prefetch_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_rfo_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_force_selfsnoop_rfo_prefetch_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_crd_always_cachenear_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_drd_always_cachenear_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_rfo_always_cachenear_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_disable_data_vulnerable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ni_control_disable_go_s_for_drd_hit_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_flow_cntrl_always_snoop_all_ia_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_flow_cntrl_force_snoop_all_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])

class ccf_reg_cov_flow_cntrl_dis_spec_snoop_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])

