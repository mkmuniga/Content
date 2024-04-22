from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import CFI, IDI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_DOWNSTREAM_INTA_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, opcode=IDI.OPCODES.inta, addr=0x0, length=1),
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(opcode=CFI.OPCODES.int_ack, rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.ioc0,
                            interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pr, vc_id=CFI.VC_IDS.vc0_ncs,
                            addr=0x0, chunk=0, length=1,
                            rctrl=self.exp_cfi["rctrl"],
                            data=self.exp_cfi["data_chunk0"],
                            sai=DoNotCheck),
            UPI_TRANSACTION(opcode=CFI.OPCODES.int_ack, rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.ioc0,
                            interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pr, vc_id=CFI.VC_IDS.vc0_ncs,
                            addr=0x0, chunk=1, length=1,
                            rctrl=self.exp_cfi["rctrl"],
                            data=self.exp_cfi["data_chunk1"],
                            sai=DoNotCheck)
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, opcode=CFI.OPCODES.nc_data, dest_id=CFI.EPS.ccf,
                            pkt_type=CFI.PKT_TYPE.sr_cd, vc_id=CFI.VC_IDS.vc0_drs, addr=0x0, chunk=0),
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, opcode=CFI.OPCODES.nc_data, dest_id=CFI.EPS.ccf,
                            pkt_type=CFI.PKT_TYPE.sr_cd, vc_id=CFI.VC_IDS.vc0_drs, addr=0x0, chunk=1)
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=0x0, chunk=0,
                            module_id=self.exp_idi["module_id"],
                            data=self.exp_idi["data_chunk0"]),
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=0x0, chunk=1,
                            module_id=self.exp_idi["module_id"],
                            data=self.exp_idi["data_chunk1"]),
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go, addr=0x0,
                            module_id=self.exp_idi["module_id"]),
            append_to_last_bubble=True
        )

    @staticmethod
    def is_new_flow(flow):
        return flow[0].opcode == IDI.OPCODES.inta and flow[0].tran_type == IDI.TYPES.c2u_req

    def _set_expected_values(self):
        self.__set_expected_idi()
        self.__set_expected_cfi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["data_chunk0"], self.exp_idi["data_chunk1"] = self.__get_data_chunks()

    def __set_expected_cfi(self):
        self.exp_cfi = dict()
        self.exp_cfi["rctrl"] = self._get_rctrl(pkt_type=CFI.PKT_TYPE.pr)
        self.exp_cfi["data_chunk0"], self.exp_cfi["data_chunk1"] = self._get_pr_data()

    def __get_data_chunks(self):
        read_data = CNCU_UTILS.get_idi_data_from_cfi(data=self._data, offset=0x0, length=self._length)
        return read_data[0], read_data[1]

    def _additional_checks(self):
        self._check_arriving_order(before=[UPI_TRANSACTION(chunk=0, opcode=CFI.OPCODES.nc_data)],
                                   after=IDI_TRANSACTION(chunk=0))
        self._check_arriving_order(before=UPI_TRANSACTION(chunk=1, opcode=CFI.OPCODES.nc_data),
                                   after=IDI_TRANSACTION(chunk=1))
