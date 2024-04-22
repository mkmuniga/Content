from val_utdb_bint import bint

from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import CFI, IDI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_DOWNSTREAM_EOI_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, opcode=IDI.OPCODES.eoi, addr=0x800)
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull, addr=0x800,
                            module_id=self.exp_idi["module_id"])
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=0x800, byteen=0x1, chunk=0),
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=0x800, byteen=0x0, chunk=1)
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncb,
                            rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.ioc0, opcode=CFI.OPCODES.nc_msg_b,
                            msg_type=CFI.MSG_TYPE.eoi, chunk=0, param_a=0x0,  #byteen=0x1, TODO PLT mlugassi - enable after using CFI LOGDB from its script
                            rctrl=self.exp_cfi["rctrl"],
                            data=self.exp_cfi["data_chunk0"],
                            sai=DoNotCheck),
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncb,
                            rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.ioc0, opcode=CFI.OPCODES.nc_msg_b,
                            msg_type=CFI.MSG_TYPE.eoi, chunk=1, param_a=0x0,  #byteen=0x1, TODO PLT mlugassi - enable after using CFI LOGDB from its script
                            rctrl=self.exp_cfi["rctrl"],
                            data=self.exp_cfi["data_chunk1"],
                            sai=DoNotCheck)
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
        return flow[0].opcode == IDI.OPCODES.eoi

    def _set_expected_values(self):
        self.__set_expected_idi()
        self.__set_expected_cfi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["address"] = self._initial_tran.addr

    def __set_expected_cfi(self):
        self.exp_cfi = dict()
        self.exp_cfi["rctrl"] = self._get_rctrl(pkt_type=CFI.PKT_TYPE.ncm)
        self.exp_cfi["data_chunk0"], self.exp_cfi["data_chunk1"] = self.__get_cfi_data_chunks()

    def __get_cfi_data_chunks(self):
        return self.__get_ncm_data(), CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=32)

    def __get_ncm_data(self):
        data = CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=32)

        for i in range(8):
            data[i] = self._data[0][i]
            if data[i] is None:
                data[i] = bint(0)
        return data
