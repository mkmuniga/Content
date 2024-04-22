from val_utdb_bint import bint
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_INTERRUPT_BASE_FLOW:

    def _get_int_data(self):
        int_data = bint(0)
        int_data[7:0] = self._data[0][0]
        int_data[15:8] = self._data[0][1]
        return int_data

    def _get_rctrl(self, pkt_type):
        is_interrupt = CNCU_UTILS.is_interrupt_for_rctrl(self._initial_tran.addr, self._initial_tran.opcode)
        return CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                            time=self._start_time,
                                            pkt_type=pkt_type,
                                            is_interrupt=is_interrupt)
