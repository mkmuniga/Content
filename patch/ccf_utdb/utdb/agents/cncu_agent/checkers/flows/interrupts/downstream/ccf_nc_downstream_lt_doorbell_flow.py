from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.cncu_defines import CFI, IDI, GLOBAL, SAI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION


class CCF_NC_DOWNSTREAM_LT_DOORBELL_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, opcode=IDI.OPCODES.port_out)
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull,
                            addr=self.exp_idi["address"],
                            module_id=self.exp_idi["module_id"])
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, byteen=0x3, chunk=0),
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, byteen=0x0, chunk=1)
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nc_lt_wr,
                            chunk=0, sai=SAI.lt_sai,  #byteen=0x3
                            addr=self.exp_cfi["address"],
                            rctrl=self.exp_cfi["rctrl"],
                            data=self.exp_cfi["data_chunk0"]),
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nc_lt_wr,
                            chunk=1, sai=SAI.lt_sai,  #byteen=0x0
                            addr=self.exp_cfi["address"],
                            rctrl=self.exp_cfi["rctrl"],
                            data=self.exp_cfi["data_chunk1"])
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_rsp, pkt_type=CFI.PKT_TYPE.sr_u, vc_id=CFI.VC_IDS.vc0_ndr,
                            dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nccmpu)
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                            addr=self.exp_idi["address"],
                            module_id=self.exp_idi["module_id"])
        )

    @staticmethod
    def is_new_flow(flow):
        return flow[0].opcode == IDI.OPCODES.port_out and flow[0].addr[31:8] == GLOBAL.lt_doorbell_base_addr

    def _set_expected_values(self):
        self.__set_expected_idi()
        self.__set_expected_cfi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["address"] = self._initial_tran.addr

    def __set_expected_cfi(self):
        self.exp_cfi = dict()
        self.exp_cfi["address"] = self._initial_tran.addr << 3
        self.exp_cfi["rctrl"] = self._get_rctrl(pkt_type=CFI.PKT_TYPE.pw)
        self.exp_cfi["data_chunk0"], self.exp_cfi["data_chunk1"] = self._data[0], self._data[1]
