from agents.ccf_common_base.ccf_common_cov import ccf_cp, ccf_cg, ccf_base_cov


class SAD_MCA_CG(ccf_cg):

    def __init__(self):
         super().__init__()

    def coverpoints(self):

        self.CBO_SAD_ERR_NONE = ccf_cp(["CBO_SAD_ERR_NONE"])
        self.CBO_SAD_ERR_RSO_NO_MATCH = ccf_cp(["CBO_SAD_ERR_RSO_NO_MATCH"])
        self.CBO_SAD_ERR_IA_TO_GSM = ccf_cp(["CBO_SAD_ERR_IA_TO_GSM"])
        self.CBO_SAD_ERR_MMIO_MODIFIED = ccf_cp(["CBO_SAD_ERR_MMIO_MODIFIED"])
        self.CBO_SAD_ERR_VGA_MODIFIED = ccf_cp(["CBO_SAD_ERR_VGA_MODIFIED"])
        self.CBO_SAD_ERR_PAM_MODIFIED = ccf_cp(["CBO_SAD_ERR_PAM_MODIFIED"])
        self.CBO_SAD_ERR_SETMON_TO_MMIO = ccf_cp(["CBO_SAD_ERR_SETMON_TO_MMIO"])
        self.CBO_SAD_ERR_SMM_C_RD = ccf_cp(["CBO_SAD_ERR_SMM_C_RD"])
        self.CBO_SAD_ERR_MMCFG = ccf_cp(["CBO_SAD_ERR_MMCFG"])
        self.CBO_SAD_ERR_CRAB_RSP = ccf_cp(["CBO_SAD_ERR_CRAB_RSP"])
        self.CBO_SAD_ERR_IA_RSP_GSM = ccf_cp(["CBO_SAD_ERR_IA_RSP_GSM"])
        self.CBO_SAD_ERR_LLC_NO_WAY = ccf_cp(["CBO_SAD_ERR_LLC_NO_WAY"])
        self.CBO_SAD_ERR_LLCDATA_INV_WAY = ccf_cp(["CBO_SAD_ERR_LLCDATA_INV_WAY"])
        self.CBO_SAD_ERR_EXT_SNP_NC = ccf_cp(["CBO_SAD_ERR_EXT_SNP_NC"])
        self.CBO_SAD_ERR_MMIO_FLUSH = ccf_cp(["CBO_SAD_ERR_MMIO_FLUSH"])
        self.CBO_SAD_ERR_VGA_FLUSH = ccf_cp(["CBO_SAD_ERR_VGA_FLUSH"])
        self.CBO_SAD_ERR_IA_EXC_IMR = ccf_cp(["CBO_SAD_ERR_IA_EXC_IMR"])
        self.CBO_SAD_ERR_IA_RSPM_IMR = ccf_cp(["CBO_SAD_ERR_IA_RSPM_IMR"])
        self.CBO_SAD_ERR_PCOMMIT_TO_MMIO = ccf_cp(["CBO_SAD_ERR_PCOMMIT_TO_MMIO"])
        self.CBO_SAD_ERR_IMR = ccf_cp(["CBO_SAD_ERR_IMR"])
        self.CBO_SAD_ERR_EVICT_IN_NEM = ccf_cp(["CBO_SAD_ERR_EVICT_IN_NEM"])

        self.sad_mca= ccf_cp(["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","WB2MMIO","IA_ACCESS_2_GSM"])
        self.disable_sad_err = ccf_cp(["0","1"])
        self.new_sad_err_dis = ccf_cp(["0","1"])
        self.monitor_mmio_sad_err_dis = ccf_cp(["0","1"])
        self.enable_sad_err_clflush = ccf_cp(["0","1"])
        self.disable_sad_err_wb2mmio_on_reject = ccf_cp(["0","1"])
        self.disable_iagtexc_imr_saderr_code = ccf_cp(["0","1"])
        self.sad_corruping_err_other = ccf_cp(["0","1"])
        self.sad_non_corruping_err_other = ccf_cp(["0","1"])
        self.sad_err_wb_to_mmio = ccf_cp(["0","1"])
        self.sad_err_ia_access_to_gsm = ccf_cp(["0","1"])
        self.dis_wb2mmio_fix = ccf_cp(["0","1"])
        self.nem_mode = ccf_cp(["0","1"])
        self.mca_logged_addr = ccf_cp(["with mktme","no mktme"])

        self.corr_with_cb = self.cross(self.sad_mca,self.sad_corruping_err_other)
        self.corr_with_cb.ignore(sad_mca =["NON_CORRUPTING_OTHER","WB2MMIO","IA_ACCESS_2_GSM"])
        self.non_corr_with_cb = self.cross(self.sad_mca ,self.sad_non_corruping_err_other)
        self.non_corr_with_cb.ignore(sad_mca = ["CORRUPTING_OTHER","WB2MMIO","IA_ACCESS_2_GSM"])
        self.wb2mmio_with_cb = self.cross(self.sad_mca ,self.sad_err_wb_to_mmio)
        self.wb2mmio_with_cb.ignore(sad_mca = ["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","IA_ACCESS_2_GSM"])
        self.wb2mmio_rspm_with_cb = self.cross(self.sad_mca, self.dis_wb2mmio_fix)
        self.wb2mmio_rspm_with_cb.ignore(sad_mca = ["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","IA_ACCESS_2_GSM"])
        self.ia_access_to_gsm_with_cb = self.cross(self.sad_mca ,self.sad_err_ia_access_to_gsm)
        self.ia_access_to_gsm_with_cb.ignore(sad_mca = ["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","WB2MMIO"])
        self.sad_mca_with_cb = self.cross(self.sad_mca,self.disable_sad_err)
        self.new_sad_mca_with_cb = self.cross(self.sad_mca, self.new_sad_err_dis)
        self.corr_monitor_dis = self.cross(self.sad_mca ,self.monitor_mmio_sad_err_dis)
        self.corr_monitor_dis.ignore(sad_mca =["NON_CORRUPTING_OTHER","WB2MMIO","IA_ACCESS_2_GSM"])
        self.ia_access_to_gsm_monitor_dis = self.cross(self.sad_mca ,self.monitor_mmio_sad_err_dis)
        self.ia_access_to_gsm_monitor_dis.ignore(sad_mca = ["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","WB2MMIO"])
        self.mca_if_clflush_en = self.cross(self.sad_mca,self.enable_sad_err_clflush)
        self.mca_if_clflush_en.ignore(sad_mca ="WB2MMIO")
        self.dis_wb2mmio = self.cross(self.sad_mca ,self.disable_sad_err_wb2mmio_on_reject)
        self.dis_wb2mmio.ignore(sad_mca = ["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","IA_ACCESS_2_GSM"])
        self.dis_iagtexc_imr = self.cross(self.sad_mca,self.disable_iagtexc_imr_saderr_code)
        self.dis_iagtexc_imr.ignore(sad_mca=["CORRUPTING_OTHER","NON_CORRUPTING_OTHER","WB2MMIO"])


class ccf_sad_mca_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.ccf_sad_mca_cg: SAD_MCA_CG = SAD_MCA_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass
