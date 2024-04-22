from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.cncu_defines import CFI, IDI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION


class CCF_NC_UPSTREAM_IPI_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc1_rwd,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, chunk=0),
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc1_rwd,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, chunk=1)
        )

        if len(self._get_enabled_modules()) > 0:
            self._add_fsm_bubble(
                self._for_all_modules(
                    IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_req,
                                    opcode=self.exp_idi["opcode"],
                                    addr=self.exp_idi["address"],
                                    int_data=self.exp_idi["int_data"]),
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
        return flow[0].opcode in [CFI.OPCODES.int_logical, CFI.OPCODES.int_physical] and \
               flow[0].pkt_type == CFI.PKT_TYPE.pw

    def _set_expected_values(self):
        self.__set_expected_idi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["address"] = self._initial_tran.addr >> 3
        self.exp_idi["opcode"] = IDI.OPCODES.int_physical if self._initial_tran.opcode == CFI.OPCODES.int_physical \
            else IDI.OPCODES.int_logical
        self.exp_idi["int_data"] = self._get_int_data()
