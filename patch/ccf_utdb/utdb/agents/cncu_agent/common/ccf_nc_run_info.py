from val_utdb_base_components import val_utdb_component

from agents.cncu_agent.common.cncu_defines import IDI, CFI
from agents.cncu_agent.common.cncu_types import LOCK_INFO
from agents.cncu_agent.dbs.cncu_flow_qry import CCF_NC_FLOW_QRY


class CCF_NC_RUN_INFO(val_utdb_component):

    def __init__(self):
        self.nc_flow_qry: CCF_NC_FLOW_QRY = CCF_NC_FLOW_QRY.get_pointer()

        self.lock_flows_info = list()

    def set_run_info(self):
        self.set_locks_info()
        pass

    def set_locks_info(self):
        ccf_inflight_locks = dict()
        sncu_inflight_locks = list()

        for flow in self.nc_flow_qry.get_lock_flows_trans():
            if flow[0].opcode in [IDI.OPCODES.lock, IDI.OPCODES.split_lock]:
                if flow[0].module_id not in ccf_inflight_locks.keys():
                    ccf_inflight_locks[flow[0].module_id] = list()
                ccf_inflight_locks[flow[0].module_id].append(LOCK_INFO(lock_flow=flow))

            elif flow[0].opcode == IDI.OPCODES.unlock:
                if flow[0].module_id in ccf_inflight_locks.keys():
                    lock_flow_details = ccf_inflight_locks[flow[0].module_id].pop()
                    lock_flow_details.update_unlock_details(flow)
                    self.lock_flows_info.append(lock_flow_details)
            elif flow[0].msg_type == CFI.MSG_TYPE.stop_req1:
                sncu_inflight_locks.append(LOCK_INFO(lock_flow=flow))
            elif flow[0].msg_type == CFI.MSG_TYPE.stop_req3:
                sncu_inflight_locks[0].update_stop_req3_details(flow)
            elif flow[0].msg_type == CFI.MSG_TYPE.start_req1:
                lock_flow_details = sncu_inflight_locks.pop()
                lock_flow_details.update_unlock_details(flow)
                self.lock_flows_info.append(lock_flow_details)

        for key in ccf_inflight_locks:
            for lock_info in ccf_inflight_locks[key]:
                self.lock_flows_info.append(lock_info)

        for lock_info in sncu_inflight_locks:
            self.lock_flows_info.append(lock_info)
