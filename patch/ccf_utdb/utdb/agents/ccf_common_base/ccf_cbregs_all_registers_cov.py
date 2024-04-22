from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cp, ccf_cg


class ccf_cbregs_all_registers_cov(ccf_base_cov):

    def __init__(self):
        super().__init__()

        self.ccf_reg_cov_ltctrlsts_ltpmoncntclr_cg                : ccf_reg_cov_ltctrlsts_ltpmoncntclr_cg                = ccf_reg_cov_ltctrlsts_ltpmoncntclr_cg.get_pointer()
        self.ccf_reg_cov_ltctrlsts_private_cg                     : ccf_reg_cov_ltctrlsts_private_cg                     = ccf_reg_cov_ltctrlsts_private_cg.get_pointer()
        self.ccf_reg_cov_ltctrlsts_inacm_cg                       : ccf_reg_cov_ltctrlsts_inacm_cg                       = ccf_reg_cov_ltctrlsts_inacm_cg.get_pointer()
        self.ccf_reg_cov_ltctrlsts_loc3guarddis_cg                : ccf_reg_cov_ltctrlsts_loc3guarddis_cg                = ccf_reg_cov_ltctrlsts_loc3guarddis_cg.get_pointer()
        self.ccf_reg_cov_cbregs_spare_sadalwaystohom_cg           : ccf_reg_cov_cbregs_spare_sadalwaystohom_cg           = ccf_reg_cov_cbregs_spare_sadalwaystohom_cg.get_pointer()
        self.ccf_reg_cov_pam0_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam0_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam0_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_pam1_0_0_0_pci_loenable_cg               : ccf_reg_cov_pam1_0_0_0_pci_loenable_cg               = ccf_reg_cov_pam1_0_0_0_pci_loenable_cg.get_pointer()
        self.ccf_reg_cov_pam1_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam1_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam1_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_pam2_0_0_0_pci_loenable_cg               : ccf_reg_cov_pam2_0_0_0_pci_loenable_cg               = ccf_reg_cov_pam2_0_0_0_pci_loenable_cg.get_pointer()
        self.ccf_reg_cov_pam2_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam2_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam2_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_pam3_0_0_0_pci_loenable_cg               : ccf_reg_cov_pam3_0_0_0_pci_loenable_cg               = ccf_reg_cov_pam3_0_0_0_pci_loenable_cg.get_pointer()
        self.ccf_reg_cov_pam3_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam3_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam3_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_pam4_0_0_0_pci_loenable_cg               : ccf_reg_cov_pam4_0_0_0_pci_loenable_cg               = ccf_reg_cov_pam4_0_0_0_pci_loenable_cg.get_pointer()
        self.ccf_reg_cov_pam4_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam4_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam4_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_pam5_0_0_0_pci_loenable_cg               : ccf_reg_cov_pam5_0_0_0_pci_loenable_cg               = ccf_reg_cov_pam5_0_0_0_pci_loenable_cg.get_pointer()
        self.ccf_reg_cov_pam5_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam5_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam5_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_pam6_0_0_0_pci_loenable_cg               : ccf_reg_cov_pam6_0_0_0_pci_loenable_cg               = ccf_reg_cov_pam6_0_0_0_pci_loenable_cg.get_pointer()
        self.ccf_reg_cov_pam6_0_0_0_pci_hienable_cg               : ccf_reg_cov_pam6_0_0_0_pci_hienable_cg               = ccf_reg_cov_pam6_0_0_0_pci_hienable_cg.get_pointer()
        self.ccf_reg_cov_cbo_coh_config_client_nem_mode_cg        : ccf_reg_cov_cbo_coh_config_client_nem_mode_cg        = ccf_reg_cov_cbo_coh_config_client_nem_mode_cg.get_pointer()
        self.ccf_reg_cov_cbomcaconfig_disable_sad_err_cg          : ccf_reg_cov_cbomcaconfig_disable_sad_err_cg          = ccf_reg_cov_cbomcaconfig_disable_sad_err_cg.get_pointer()
        self.ccf_reg_cov_cbomcaconfig_new_sad_err_dis_cg          : ccf_reg_cov_cbomcaconfig_new_sad_err_dis_cg          = ccf_reg_cov_cbomcaconfig_new_sad_err_dis_cg.get_pointer()
        self.ccf_reg_cov_cbomcaconfig_monitor_mmio_sad_err_dis_cg : ccf_reg_cov_cbomcaconfig_monitor_mmio_sad_err_dis_cg = ccf_reg_cov_cbomcaconfig_monitor_mmio_sad_err_dis_cg
        self.ccf_reg_cov_cbomcastat_sad_error_code_cg             : ccf_reg_cov_cbomcastat_sad_error_code_cg             = ccf_reg_cov_cbomcastat_sad_error_code_cg.get_pointer()
        self.ccf_reg_cov_mc_ctl_sad_err_wb_to_mmio_cg             : ccf_reg_cov_mc_ctl_sad_err_wb_to_mmio_cg             = ccf_reg_cov_mc_ctl_sad_err_wb_to_mmio_cg.get_pointer()
        self.ccf_reg_cov_mc_ctl_sad_err_ia_access_to_gsm_cg       : ccf_reg_cov_mc_ctl_sad_err_ia_access_to_gsm_cg       = ccf_reg_cov_mc_ctl_sad_err_ia_access_to_gsm_cg.get_pointer()
        self.ccf_reg_cov_mc_ctl_sad_corruping_err_other_cg        : ccf_reg_cov_mc_ctl_sad_corruping_err_other_cg        = ccf_reg_cov_mc_ctl_sad_corruping_err_other_cg.get_pointer()
        self.ccf_reg_cov_mc_ctl_sad_non_corruping_err_other_cg    : ccf_reg_cov_mc_ctl_sad_non_corruping_err_other_cg    = ccf_reg_cov_mc_ctl_sad_non_corruping_err_other_cg.get_pointer()

        self.registers_cov = {
            "ltctrlsts_ltpmoncntclr": self.ccf_reg_cov_ltctrlsts_ltpmoncntclr_cg,
            "ltctrlsts_private": self.ccf_reg_cov_ltctrlsts_private_cg,
            "ltctrlsts_inacm": self.ccf_reg_cov_ltctrlsts_inacm_cg,
            "ltctrlsts_loc3guarddis": self.ccf_reg_cov_ltctrlsts_loc3guarddis_cg,
            "cbregs_spare_sadalwaystohom": self.ccf_reg_cov_cbregs_spare_sadalwaystohom_cg,
            "pam0_0_0_0_pci_hienable": self.ccf_reg_cov_pam0_0_0_0_pci_hienable_cg,
            "pam1_0_0_0_pci_loenable": self.ccf_reg_cov_pam1_0_0_0_pci_loenable_cg,
            "pam1_0_0_0_pci_hienable": self.ccf_reg_cov_pam1_0_0_0_pci_hienable_cg,
            "pam2_0_0_0_pci_loenable": self.ccf_reg_cov_pam2_0_0_0_pci_loenable_cg,
            "pam2_0_0_0_pci_hienable": self.ccf_reg_cov_pam2_0_0_0_pci_hienable_cg,
            "pam3_0_0_0_pci_loenable": self.ccf_reg_cov_pam3_0_0_0_pci_loenable_cg,
            "pam3_0_0_0_pci_hienable": self.ccf_reg_cov_pam3_0_0_0_pci_hienable_cg,
            "pam4_0_0_0_pci_loenable": self.ccf_reg_cov_pam4_0_0_0_pci_loenable_cg,
            "pam4_0_0_0_pci_hienable": self.ccf_reg_cov_pam4_0_0_0_pci_hienable_cg,
            "pam5_0_0_0_pci_loenable": self.ccf_reg_cov_pam5_0_0_0_pci_loenable_cg,
            "pam5_0_0_0_pci_hienable": self.ccf_reg_cov_pam5_0_0_0_pci_hienable_cg,
            "pam6_0_0_0_pci_loenable": self.ccf_reg_cov_pam6_0_0_0_pci_loenable_cg,
            "pam6_0_0_0_pci_hienable": self.ccf_reg_cov_pam6_0_0_0_pci_hienable_cg,
            "CBO_COH_CONFIG_CLIENT_NEM_MODE": self.ccf_reg_cov_cbo_coh_config_client_nem_mode_cg,
            "cbomcaconfig_disable_sad_err": self.ccf_reg_cov_cbomcaconfig_disable_sad_err_cg,
            "cbomcaconfig_new_sad_err_dis": self.ccf_reg_cov_cbomcaconfig_new_sad_err_dis_cg,
            "cbomcaconfig_monitor_mmio_sad_err_dis": self.ccf_reg_cov_cbomcaconfig_monitor_mmio_sad_err_dis_cg,
            "cbomcastat_sad_error_code": self.ccf_reg_cov_cbomcastat_sad_error_code_cg,
            "mc_ctl_sad_err_wb_to_mmio": self.ccf_reg_cov_mc_ctl_sad_err_wb_to_mmio_cg,
            "mc_ctl_sad_err_ia_access_to_gsm": self.ccf_reg_cov_mc_ctl_sad_err_ia_access_to_gsm_cg,
            "mc_ctl_sad_corruping_err_other": self.ccf_reg_cov_mc_ctl_sad_corruping_err_other_cg,
            "mc_ctl_sad_non_corruping_err_other": self.ccf_reg_cov_mc_ctl_sad_non_corruping_err_other_cg
        }

    def create_cg(self):
        # define covergroups here
        pass


class ccf_reg_cov_mc_ctl_sad_err_wb_to_mmio_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_mc_ctl_sad_err_ia_access_to_gsm_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_mc_ctl_sad_corruping_err_other_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_mc_ctl_sad_non_corruping_err_other_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_cbomcastat_sad_error_code_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 24, 27])


class ccf_reg_cov_cbomcaconfig_disable_sad_err_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_cbomcaconfig_new_sad_err_dis_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_cbomcaconfig_monitor_mmio_sad_err_dis_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_cbregs_spare_sadalwaystohom_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_cbo_coh_config_client_nem_mode_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_pam0_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam1_0_0_0_pci_loenable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam1_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam2_0_0_0_pci_loenable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam2_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam3_0_0_0_pci_loenable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam3_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam4_0_0_0_pci_loenable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam4_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam5_0_0_0_pci_loenable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam5_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam6_0_0_0_pci_loenable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_pam6_0_0_0_pci_hienable_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1, 2, 3])


class ccf_reg_cov_ltctrlsts_ltpmoncntclr_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ltctrlsts_private_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ltctrlsts_inacm_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])


class ccf_reg_cov_ltctrlsts_loc3guarddis_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0, 1])



