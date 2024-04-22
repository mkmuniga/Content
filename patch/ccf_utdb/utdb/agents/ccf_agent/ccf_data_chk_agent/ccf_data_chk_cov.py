from val_utdb_report import VAL_UTDB_MSG
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cg, ccf_cp

class CCF_DATA_CHK_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.cfi_write_chks = ccf_cp([0, 1])
        self.llc_write_chks = ccf_cp([0, 1])
        self.core_write_chks = ccf_cp([0, 1])

        self.opcodes = ccf_cp(CCF_FLOW_UTILS.flow_opcodes)
        self.sad_result = ccf_cp(['HOM', 'MMIO', 'MMIOPTL', 'CFG', 'IO', 'CRABABORT', 'NA', None])
        self.cfi_writes_CROSS_opcodes = self.cross(self.cfi_write_chks, self.opcodes, self.sad_result)
        self.llc_writes_CROSS_opcodes = self.cross(self.llc_write_chks, self.opcodes, self.sad_result)
        self.core_writes_CROSS_opcodes = self.cross(self.core_write_chks, self.opcodes, self.sad_result)

class ccf_data_chk_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.ccf_data_chk_cg: CCF_DATA_CHK_CG = CCF_DATA_CHK_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        VAL_UTDB_MSG(time=0, msg="End of data chk coverage Run..")
