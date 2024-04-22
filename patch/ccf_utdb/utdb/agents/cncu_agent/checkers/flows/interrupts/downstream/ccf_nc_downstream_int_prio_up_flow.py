from val_utdb_bint import bint

from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import CFI, IDI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_DOWNSTREAM_INT_PRIO_UP_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, opcode=IDI.OPCODES.int_prio_up)
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull,
                            addr=self.exp_idi["address"],
                            module_id=self.exp_idi["module_id"])
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, byteen=0xff, chunk=0),
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, byteen=0x0, chunk=1)
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc0_ncb,
                            rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.int_prio_up,
                            chunk=0, #bytten=0xff,
                            addr=self.exp_cfi["address"],
                            data=self.exp_cfi["data_chunk0"],
                            rctrl=self.exp_cfi["rctrl"],
                            sai=DoNotCheck),
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc0_ncb,
                            rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.int_prio_up,
                            chunk=1, #bytten=0xff,
                            addr=self.exp_cfi["address"],
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
                            module_id=self.exp_idi["module_id"],
                            addr=self.exp_idi["address"])
        )

    @staticmethod
    def is_new_flow(flow):
        return flow[0].opcode == IDI.OPCODES.int_prio_up

    def _set_expected_values(self):
        self.__set_expected_idi()
        self.__set_expected_cfi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["address"] = self._initial_tran.addr

    def __set_expected_cfi(self):
        self.exp_cfi = dict()
        self.exp_cfi["address"] = self.__get_cfi_addr_with_tid()
        self.exp_cfi["rctrl"] = self._get_rctrl(pkt_type=CFI.PKT_TYPE.pw)
        self.exp_cfi["data_chunk0"], self.exp_cfi["data_chunk1"] = self._data[0], self._data[1]

    def __get_cfi_addr_with_tid(self):
        addr = bint(0)
        if UNIQUE_DEFINES.is_low_power_ccf:
            addr[11:6] = self._lp_id
        else:
            addr[11:6] = 0x3f
        return addr
