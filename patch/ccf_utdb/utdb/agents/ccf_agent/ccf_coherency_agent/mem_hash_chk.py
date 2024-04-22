from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_queries.ccf_gcfi_qry import ccf_gcfi_qry
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from agents.ccf_common_base.coh_global import COH_GLOBAL

class mem_hash_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.gcfi_qry = ccf_gcfi_qry.get_pointer()


    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow)


    def expected_trans_port_id(self, flow):
        if flow.flow_is_hom():
            return flow.cbo_half_id
        else:
            return "0"

    def is_victim_record(self, record):
        return "VIC" in record.PID

    def get_flow_key(self, record):
        if self.is_victim_record(record):
            return record.PID
        else:
            return record.TID

    def check_trans_santa_ring_port_id(self):
        self.get_all_record = self.gcfi_qry.get_all_records()
        for rec in self.get_all_record:
            for rec_entry in rec.EVENTS:
                if rec_entry.TIME >= COH_GLOBAL.global_vars["START_OF_TEST"] and rec_entry.TIME <=  COH_GLOBAL.global_vars["END_OF_TEST"]:
                    if "REQ" in rec_entry.UNIT and "Snp" in rec_entry.OPCODE: #TODO @abibas write checker for snoop req when arch defined
                        continue
                    if str(rec_entry.SANTA_PORT_ID) != self.expected_trans_port_id(self.ccf_flows[self.get_flow_key(rec_entry)]):
                        err_msg = "(mem_hash_chk): The URI -{} Got out on gCFI port-{} but we expected it to be on Port-{}"\
                            .format(rec_entry.TID, rec_entry.SANTA_PORT_ID, self.expected_trans_port_id(self.ccf_flows[self.get_flow_key(rec_entry)]))
                        VAL_UTDB_ERROR(time=rec_entry.TIME, msg=err_msg)

    def run(self):
        self.check_trans_santa_ring_port_id()














