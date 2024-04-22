
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cp, ccf_cg


class ccf_ncdecs_registers_cov(ccf_base_cov):

    def __init__(self):
        super().__init__()

        self.ccf_reg_cov_ncradecs_ovrd_trusted_path_ovrd_cg         : ccf_reg_cov_ncradecs_ovrd_trusted_path_ovrd_cg         = ccf_reg_cov_ncradecs_ovrd_trusted_path_ovrd_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_fastipi_cg                   : ccf_reg_cov_ncradecs_ovrd_fastipi_cg                   = ccf_reg_cov_ncradecs_ovrd_fastipi_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev2_cg   : ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev2_cg   = ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev2_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev4_cg   : ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev4_cg   = ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev4_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev5_cg   : ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev5_cg   = ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev5_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev11_cg  : ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev11_cg  = ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev11_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev12_cg  : ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev12_cg  = ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev12_cg.get_pointer()
        self.ccf_reg_cov_ncradecs_ovrd_dis_safbar_cfi_host_mcast_cg : ccf_reg_cov_ncradecs_ovrd_dis_safbar_cfi_host_mcast_cg = ccf_reg_cov_ncradecs_ovrd_dis_safbar_cfi_host_mcast_cg.get_pointer()

        self.registers_cov = {
            "NCRADECS_OVRD_TRUSTED_PATH_OVRD"        : self.ccf_reg_cov_ncradecs_ovrd_trusted_path_ovrd_cg,
            "NCRADECS_OVRD_FastIpi"                  : self.ccf_reg_cov_ncradecs_ovrd_fastipi_cg,
            "NCRADECS_OVRD_always_shadowmcast_dev2"  : self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev2_cg,
            "NCRADECS_OVRD_always_shadowmcast_dev4"  : self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev4_cg,
            "NCRADECS_OVRD_always_shadowmcast_dev5"  : self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev5_cg,
            "NCRADECS_OVRD_always_shadowmcast_dev11" : self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev11_cg,
            "NCRADECS_OVRD_always_shadowmcast_dev12" : self.ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev12_cg,
            "NCRADECS_OVRD_dis_safbar_cfi_host_mcast": self.ccf_reg_cov_ncradecs_ovrd_dis_safbar_cfi_host_mcast_cg
        }

    def create_cg(self):
        # define covergroups here
        pass


class ccf_reg_cov_ncradecs_ovrd_dis_safbar_cfi_host_mcast_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_trusted_path_ovrd_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_fastipi_cg(ccf_cg):

    def coverpoints(self):

        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev2_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev4_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev5_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev11_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])

class ccf_reg_cov_ncradecs_ovrd_always_shadowmcast_dev12_cg(ccf_cg):

    def coverpoints(self):
        self.reg_val_cp = ccf_cp([0,1])






