from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_queries.ccf_power_sb_qry import CCF_POWER_SB_QRY
from val_utdb_base_components import val_utdb_component


class CCF_POWER_SB_DB(ccf_base_component):

    def __init__(self):
        self.qry: CCF_POWER_SB_QRY = CCF_POWER_SB_QRY.get_pointer()

    def run_db_builder(self):
        for group in self.qry.get_power_sb_records():
            for record in group.EVENTS:
                sb_tran = self.qry.SB_REC(record).get_tran()
                if sb_tran.opcode not in self.power_sb_msgs_db.keys():
                    self.power_sb_msgs_db[sb_tran.opcode] = list()
                self.power_sb_msgs_db[sb_tran.opcode].append(sb_tran)

    def get_msgs_in_time_by_opcode(self, opcodes, start_time, end_time, filter_func=None):
        opcodes = opcodes if type(opcodes) is list else [opcodes]
        msgs_in_time = list()

        for opcode in opcodes:
            opcode_msgs_in_time = list()
            if opcode in self.power_sb_msgs_db.keys():
                for i in range(len(self.power_sb_msgs_db[opcode])):
                    idx = i - len(opcode_msgs_in_time)
                    if start_time <= self.power_sb_msgs_db[opcode][idx].time <= end_time:
                        if filter_func is None or filter_func(self.power_sb_msgs_db[opcode][idx]):
                            opcode_msgs_in_time.append(self.power_sb_msgs_db[opcode].pop(idx))
                msgs_in_time = msgs_in_time + opcode_msgs_in_time
        return msgs_in_time

