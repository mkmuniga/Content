from val_utdb_base_components import val_utdb_component

from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_queries.ccf_sb_agent_qry import CCF_SB_AGENT_QRY

class ccf_sb_agent(ccf_base_component):

    def __init__(self):
        self.qry: CCF_SB_AGENT_QRY = CCF_SB_AGENT_QRY.get_pointer()

    def run_db_builder(self):
        for group in self.qry.get_power_sb_records():
            for record in group.EVENTS:
                sb_tran = self.qry.SB_REC(record).get_tran()
                if sb_tran.opcode not in self.pmc_gpsb_msgs_db.keys():
                    self.pmc_gpsb_msgs_db[sb_tran.opcode] = list()
                self.pmc_gpsb_msgs_db[sb_tran.opcode].append(sb_tran)
