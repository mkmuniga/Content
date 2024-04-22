from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import find_tran
from agents.cncu_agent.common.cncu_defines import IDI, CFI
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.common.ccf_nc_run_info import CCF_NC_RUN_INFO
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION, ATOMIC_ACTION_TYPE, IDI_TRANSACTION, \
    UPI_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


def have_nc_traffic_in_flow(flow):
    have_upi_nc_traffic = find_tran(UPI_TRANSACTION(), flow) is not None
    have_sb_traffic = find_tran(SB_TRANSACTION(), flow) is not None
    return have_upi_nc_traffic or have_sb_traffic

def is_nc_flow_to_sncu_over_cfi(flow):
    return find_tran(UPI_TRANSACTION(dest_id=CFI.EPS.sncu), flow) is not None

def get_flow_lock_info(start_time):
    run_info = CCF_NC_RUN_INFO.get_pointer()
    for lock_info in run_info.lock_flows_info:
        if lock_info.from_ccf() and lock_info.lock_time <= start_time <= lock_info.unlock_time:
            return lock_info
    return None


class CCF_NC_CCF_ATOMIC_ACTION_FLOW(CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.lock_chk_en

    def _set_flow_info(self, flow):
        if len(self._act_flow) > 0 and type(self._act_flow[0]) == IDI_TRANSACTION:
            super()._set_flow_info(flow)
            self.is_nc_flow = have_nc_traffic_in_flow(flow)
            self.to_sncu = is_nc_flow_to_sncu_over_cfi(flow)
            self.lock_info = get_flow_lock_info(self._start_time)

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req,
                            module_id=self.exp_idi["module_id"],
                            lp_id=self.exp_idi["lp_id"])
        )

    @staticmethod
    def is_new_flow(flow):
        if type(flow[0]) is IDI_TRANSACTION and flow[0].tran_type == IDI.TYPES.c2u_req and \
                flow[0].opcode not in [IDI.OPCODES.lock, IDI.OPCODES.split_lock, IDI.OPCODES.unlock,
                                       IDI.OPCODES.mem_push_wr_ns]:
            return get_flow_lock_info(flow[0].get_time()) is not None

        return False

    def _set_act_flow(self, flow):
        self._act_flow = [flow[0]]

    def _set_expected_values(self):
        self.__set_expected_idi()
        self._update_lock_info_atomic_action_details()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"], self.exp_idi["lp_id"] = self.lock_info.module_id, self.lock_info.lp_id

    def _update_lock_info_atomic_action_details(self):
        traffic_type = self._get_nc_traffic_type()
        self.lock_info.atomic_actions.append(traffic_type)
        self.lock_info.required_nc_during_lock = self.is_nc_flow and not self.to_sncu

    def _get_nc_traffic_type(self):
        if self.is_nc_flow:
            if CNCU_UTILS.is_idi_interrupt_flow(self._initial_tran.addr, self._initial_tran.opcode):
                return ATOMIC_ACTION_TYPE.INTERRUPT_ACCESS
            elif CNCU_UTILS.is_idi_mmio_access_flow(self._initial_tran.addr, self._initial_tran.opcode):
                return ATOMIC_ACTION_TYPE.MMIO_ACCESS
            elif CNCU_UTILS.is_idi_cfg_access_flow(self._initial_tran.addr, self._initial_tran.opcode):
                return ATOMIC_ACTION_TYPE.CFG_ACCESS
        return ATOMIC_ACTION_TYPE.DRAM_ACCESS
