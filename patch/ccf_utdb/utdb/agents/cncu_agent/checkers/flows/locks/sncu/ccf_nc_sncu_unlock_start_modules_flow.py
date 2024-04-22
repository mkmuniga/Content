from agents.cncu_agent.checkers.flows.locks.ccf_nc_base_unlock_flow import CCF_NC_BASE_UNLOCK_FLOW
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.common.cncu_defines import CFI
from agents.cncu_agent.common.cncu_types import UPI_TRANSACTION


class CCF_NC_SNCU_UNLOCK_START_MODULES_FLOW(CCF_NC_BASE_UNLOCK_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.lock_chk_en

    def _set_flow_fsm(self):
        self._add_start_req_phase_to_fsm()

    @staticmethod
    def is_new_flow(flow):
        return type(flow[0]) is UPI_TRANSACTION and flow[0].msg_type == CFI.MSG_TYPE.start_req1

    def _set_expected_values(self):
        self._set_unlock_base_expected_values()
