from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cg, ccf_cp
from agents.ccf_agent.ccf_max_outstanding_agent.ccf_max_outstanding_qry import ccf_max_outstanding_custom_qry
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from val_utdb_report import VAL_UTDB_MSG
class MAX_OUTSTANDING_CG(ccf_cg):
    def __init__(self):
        super().__init__()


    def coverpoints(self):
        self.wr_ifa_block_santa_0_cp = ccf_cp(["WR_MAX_OUTSTANDING_SANTA_0_BLOCK"])
        self.wr_ifa_block_santa_1_cp = ccf_cp(["WR_MAX_OUTSTANDING_SANTA_1_BLOCK"])
        self.rd_ifa_block_santa_0_cp = ccf_cp(["RD_MAX_OUTSTANDING_SANTA_0_BLOCK"])
        self.rd_ifa_block_santa_1_cp = ccf_cp(["RD_MAX_OUTSTANDING_SANTA_1_BLOCK"])
        self.general_block_cp = ccf_cp(["GENERAL_BLOCK"])
        self.specific_block_cp= ccf_cp(["SPECIFIC_BLOCK"])
        self.range_threshold_cp = ccf_cp(["low","high"])
        self.block_with_threshold_cb = self.cross(self.range_threshold_cp ,self.specific_block_cp)

class max_outstanding_collect_cov(ccf_base_component):
    def __init__(self):
        super().__init__()
        self.ccf_max_outstanding_custom_qry = ccf_max_outstanding_custom_qry.get_pointer()
        self.ccf_ral_agent_i = ccf_ral_agent.create()

    def collect_max_outstanding_ifa_block_cov(self):
        max_outstanding_cg = MAX_OUTSTANDING_CG.get_pointer()
        self.all_hw_col_rec = self.ccf_max_outstanding_custom_qry.get_all_max_outstanding_block()
        for rec in self.all_hw_col_rec:
            for rec_entry in rec.EVENTS:
                if rec_entry.DATA0 == 1 and "WritesBlock" in rec_entry.SIGNAL_NAME and "santa0" in rec_entry.SIGNAL_NAME:
                    max_outstanding_cg.sample(wr_ifa_block_santa_0_cp="WR_MAX_OUTSTANDING_SANTA_0_BLOCK")
                if rec_entry.DATA0 == 1 and "WritesBlock" in rec_entry.SIGNAL_NAME and "santa1" in rec_entry.SIGNAL_NAME:
                    max_outstanding_cg.sample(wr_ifa_block_santa_1_cp="WR_MAX_OUTSTANDING_SANTA_1_BLOCK")
                if rec_entry.DATA0 == 1 and "ReadsBlock" in rec_entry.SIGNAL_NAME and "santa0" in rec_entry.SIGNAL_NAME:
                    max_outstanding_cg.sample(rd_ifa_block_santa_0_cp="RD_MAX_OUTSTANDING_SANTA_0_BLOCK")
                if rec_entry.DATA0 == 1 and "ReadsBlock" in rec_entry.SIGNAL_NAME and "santa1" in rec_entry.SIGNAL_NAME:
                    max_outstanding_cg.sample(rd_ifa_block_santa_1_cp="RD_MAX_OUTSTANDING_SANTA_1_BLOCK")

    def collect_max_outstanding_cncu_count_block_cov(self):
        max_outstanding_cg = MAX_OUTSTANDING_CG.get_pointer()
        self.all_general_specific_hw_col_rec = self.ccf_max_outstanding_custom_qry.get_all_max_outstanding_specific_general_block()
        for rec in self.all_general_specific_hw_col_rec:
            for rec_entry in rec.EVENTS:
                threshold_general = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                  "ncdecs", "NcuMaxoutstandingCtl",
                                                                  "GeneralCounterThreshold", rec_entry.TIME)
                threshold_specific = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                  "ncdecs", "NcuMaxoutstandingCtl",
                                                                  "GeneralCounterEn", rec_entry.TIME)
                threshold_gen_level = "low" if threshold_general < 30 else "high"
                threshold_spe_level = "low" if threshold_specific <  30 else "high"


                if rec_entry.DATA0 == 1 and "MaxOutStandingSBlock" in rec_entry.SIGNAL_NAME:
                    max_outstanding_cg.sample(range_threshold_cp = threshold_gen_level, specific_block_cp="SPECIFIC_BLOCK")
                if rec_entry.DATA0 == 1 and "MaxOutStandingGBlock" in rec_entry.SIGNAL_NAME:
                    max_outstanding_cg.sample(range_threshold_cp = threshold_spe_level,general_block_cp="GENERAL_BLOCK")

class ccf_max_outstanding_chk_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.max_outstanding_collect_cov_i = max_outstanding_collect_cov.create()
        self.ccf_max_outstanding_cg: MAX_OUTSTANDING_CG = MAX_OUTSTANDING_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        self.max_outstanding_collect_cov_i.collect_max_outstanding_ifa_block_cov()
        self.max_outstanding_collect_cov_i.collect_max_outstanding_cncu_count_block_cov()
        VAL_UTDB_MSG(time=0, msg="End of max_outstanding chk coverage Run..")







