from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.dbs.ccf_nc_sb_qry import CCF_NC_SB_QRY
from val_utdb_base_components import val_utdb_component, EOT


class CCF_NC_SB_DB(val_utdb_component):

    def __init__(self):
        self._nc_sb_msgs_db = dict()
        self.qry: CCF_NC_SB_QRY = CCF_NC_SB_QRY.get_pointer()

    def run_db_builder(self):
        for group in self.qry.get_nc_sb_records():
            for record in group.EVENTS:
                sb_tran = self.qry.SB_REC(record).get_tran()
                if sb_tran.opcode not in self._nc_sb_msgs_db.keys():
                    self._nc_sb_msgs_db[sb_tran.opcode] = list()
                self._nc_sb_msgs_db[sb_tran.opcode].append(sb_tran)
        pass

    def get_trans_at_time(self, opcodes, start_time, end_time, filter_func=None):
        opcodes = opcodes if type(opcodes) is list else [opcodes]
        check_end_time = end_time != EOT
        match_trans = list()

        for opc in opcodes:
            if opc in self._nc_sb_msgs_db:
                for tran in self._nc_sb_msgs_db[opc]:
                    if (tran.get_uri() in [None, DoNotCheck] and (not tran.treated)) and \
                            start_time <= tran.get_start_time() and \
                            ((not check_end_time) or (tran.get_time() <= end_time)) and \
                            (filter_func is None or filter_func(tran)):
                        match_trans.append(tran)
        return match_trans

