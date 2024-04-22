from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.common.cncu_defines import IDI
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION


class CCF_NC_UPSTREAM_DPT_FLOW(CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            self._for_all_modules(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_req, opcode=IDI.OPCODES.dpt, addr=0x0,
                                int_data=self.exp_idi["int_data"]),
                enabled_only=True
            )
        )

    @staticmethod
    def is_new_flow(flow):
        return flow[0].opcode == IDI.OPCODES.dpt and flow[0].tran_type == IDI.TYPES.u2c_req

    def _set_expected_values(self):
        self.exp_idi = dict()
        self.exp_idi["int_data"] = self._initial_tran.int_data

    def __is_dpt_blocked(self):
        return self.ral_utils.read_reg_field(block_name="ncevents", reg_name="NcuEvOveride",
                                                                  field_name="DPT_BLK_EV", time=self._start_time) == 1

    def __is_dpt_during_lock(self):
        for lock_info in self.run_info.lock_flows_info:
            if lock_info.lock_time <= self._start_time <= lock_info.unlock_time:
                return True
        return False

    def __is_dpt_blocked_during_lock(self):
        return self.ral_utils.read_reg_field(block_name="ncevents", reg_name="NcuEvOveride",
                                                                  field_name="DPT_LOCK_DIS", time=self._start_time) == 1

    def _additional_checks(self):
        if self.__is_dpt_blocked():
            VAL_UTDB_ERROR(time=self._start_time,
                           msg="\nDPT message was sent while it was blocked by ncevents.NcuEvOveride.DPT_BLK_EV")

        if self.__is_dpt_blocked_during_lock() and self.__is_dpt_during_lock():
            VAL_UTDB_ERROR(time=self._start_time,
                           msg="\nDPT message was sent during lock while it was blocked by "
                               "ncevents.NcuEvOveride.DPT_LOCK_DIS")
