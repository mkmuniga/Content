from agents.cncu_agent.common.cncu_base_agent import CNCU_BASE_AGENT
from agents.cncu_agent.dbs.ccf_sm_qry import CCF_SM_QRY
from agents.cncu_agent.dbs.cncu_flow_qry import CNCU_FLOW_QRY
from val_utdb_report import VAL_UTDB_MSG


class CNCU_BASE_FLOW_AGENT(CNCU_BASE_AGENT):

    def __init__(self):
        super().__init__()
        # self.ccf_nc_checker: CCF_NC_CHECKER = None
        self.ccf_nc_flow_qry: CNCU_FLOW_QRY = None
        self.ccf_sm_qry: CCF_SM_QRY = None
        # self.ccf_nc_sb_db: CCF_NC_SB_DB = None
        # self.reset_db: NC_RESET_DB = None
        # self.pmon_overflow_db: NC_PMON_OVERFLOW_DB = None
        # self.ccf_nc_sb_qry: CCF_NC_SB_QRY = None
        # self.ccf_nc_seq_trk_qry: CCF_NC_SEQ_TRK_QRY = None
        # self.ccf_nc_mcast_qry: CCF_NC_MCAST_QRY = None
        # self.ccf_nc_run_info: CCF_NC_RUN_INFO = None

    def build(self):
        super().build()
        # self.ccf_nc_checker = CCF_NC_CHECKER.create()
        self.ccf_nc_flow_qry = CNCU_FLOW_QRY.create()
        self.ccf_sm_qry = CCF_SM_QRY.create()
        # self.ccf_nc_sb_db = CCF_NC_SB_DB.create()
        # self.reset_db = NC_RESET_DB.create()
        # self.pmon_overflow_db = NC_PMON_OVERFLOW_DB.create()
        # self.ccf_nc_sb_qry = CCF_NC_SB_QRY.create()
        # self.ccf_nc_seq_trk_qry = CCF_NC_SEQ_TRK_QRY.create()
        # self.ccf_nc_mcast_qry = CCF_NC_MCAST_QRY.create()
        # self.ccf_nc_run_info = CCF_NC_RUN_INFO.create()
        #
        # REMAPPING.set_remap_dict()
        # VCR_PLA_HANDLER.build()
        # SM_MAP.build(self.si.soc_mode)

    def connect(self):
        super().connect()
        self.ccf_nc_flow_qry.connect_to_db('merged_ccf_nc_logdb')
        self.ccf_sm_qry.connect_to_db('ccf_sm_logdb')
        # self.ccf_nc_sb_qry.connect_to_db('aligned_sb_logdb')
        # self.reset_db.connect_to_db(UNIQUE_DEFINES.custom_hw_col_db_name)
        # self.pmon_overflow_db.connect_to_db(UNIQUE_DEFINES.custom_hw_col_db_name)
        # self.ccf_nc_seq_trk_qry.connect_to_db('seq_trk_logdb')
        # self.ccf_nc_mcast_qry.connect_to_db('merged_ccf_mcast_logdb')
        # self.reset_db.connect_to_db(UNIQUE_DEFINES.custom_hw_col_db_name)
        # if not UNIQUE_DEFINES.is_low_power_ccf:
        #     if self.si.soc_mode:
        #         self.reset_db.connect_to_db('soc_custom_hw_col_db')
        #     else:
        #         self.reset_db.connect_to_db('ccf_custom_hw_col_db')

    def run(self):
        super().run()
        nc_flows_db = self.ccf_nc_flow_qry.get_nc_flows()
        for flow in nc_flows_db:
            uri = flow[0].get_uri()
            time = flow[0].get_time()
            VAL_UTDB_MSG(time=time, msg=f"Checking URI = {uri}")
            checker_flow = self._get_related_checker_flow(flow)
            if checker_flow is not None:
                checker_flow.check()

    def _get_related_checker_flow(self, flow):
        raise NotImplementedError()
