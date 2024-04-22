from agents.cncu_agent.checkers.flows.locks.ccf_nc_base_lock_flow import CCF_NC_BASE_LOCK_FLOW
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.common.cncu_defines import CFI
from agents.cncu_agent.common.cncu_types import UPI_TRANSACTION


class CCF_NC_SNCU_LOCK_CBO_DRAIN_FLOW(CCF_NC_BASE_LOCK_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.lock_chk_en

    def __init__(self, flow):
        super().__init__(flow)

    def _set_flow_fsm(self):
        self._add_cbo_drain_phase_to_fsm()

    @staticmethod
    def is_new_flow(flow):
        return type(flow[0]) is UPI_TRANSACTION and flow[0].msg_type == CFI.MSG_TYPE.stop_req3

    @property
    def _start_time(self):
        for lock_info in self.run_info.lock_flows_info:
            if lock_info.stop_req3_uri == self._uri:
                return lock_info.lock_time

    def __add_sb_msg_to_act_flow(self):
        for msg in self._get_act_cbo_drain_sb_msgs():
            msg.uri = self._uri
            self._act_flow.append(msg)

        self._act_flow.sort(key=lambda tran: tran.time)

    def _set_act_flow(self, flow):
        super()._set_act_flow(flow)
        self.__add_sb_msg_to_act_flow()

    def _set_expected_values(self):
        self._set_lock_base_expected_values()
