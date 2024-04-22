from val_utdb_bint import bint

from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.cncu_defines import CFI, IDI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION


class CCF_NC_UPSTREAM_VLW_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc1_rwd,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_b,
                            msg_type=CFI.MSG_TYPE.vlw, param_a=0x0, chunk=0),
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc1_rwd,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_b,
                            msg_type=CFI.MSG_TYPE.vlw, param_a=0x0, chunk=1)
        )

        if len(self._get_enabled_modules()) > 0:
            self._add_fsm_bubble(
                self._for_all_modules(
                    IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_req, opcode=IDI.OPCODES.vlw,
                                    addr=self.exp_idi["address"], int_data=0x0),
                    IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_rsp, opcode=IDI.OPCODES.rsp_i_hit_i,
                                    addr=self.exp_idi["address"]),
                    enabled_only=True
                )
            )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_rsp, pkt_type=CFI.PKT_TYPE.sr_u, vc_id=CFI.VC_IDS.vc1_ndr,
                            dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nccmpu)
        )

    @staticmethod
    def is_new_flow(flow):
        return flow[0].opcode == CFI.OPCODES.nc_msg_b and flow[0].msg_type == CFI.MSG_TYPE.vlw

    def _set_expected_values(self):
        self.__set_expected_idi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["address"] = self.__get_vlw_addr()

    def __get_vlw_addr(self):
        vlw_addr = bint(0)
        vlw_addr[27:20] = self._data[1][0]
        vlw_addr[37:30] = self._data[1][2]
        return vlw_addr
