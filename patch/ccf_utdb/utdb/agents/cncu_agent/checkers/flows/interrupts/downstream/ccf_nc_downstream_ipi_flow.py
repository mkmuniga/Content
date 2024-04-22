from val_utdb_bint import bint

from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.checkers.flows.interrupts.ccf_nc_base_interrupts_flow import \
    CCF_NC_INTERRUPT_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import CFI, IDI, GLOBAL
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION


class CCF_NC_DOWNSTREAM_IPI_INTERRUPT_FLOW(CCF_NC_INTERRUPT_BASE_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.interrupts_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req)
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull,
                            addr=self.exp_idi["original_addr"], module_id=self.exp_idi["module_id"])
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, byteen=0x3, chunk=0),
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, byteen=0x0, chunk=1)
        )

        if self.cb["fast_ipi"]:
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
        else:
            self._add_fsm_bubble(
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc0_ncb,
                                rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, chunk=0, #byteen=0x3,
                                rctrl=self.exp_cfi["rctrl"],
                                opcode=self.exp_cfi["opcode"],
                                addr=self.exp_cfi["address"],
                                data=self.exp_cfi["data_chunk0"],
                                sai=DoNotCheck),
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.pw, vc_id=CFI.VC_IDS.vc0_ncb,
                                rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, chunk=1, #byteen=0x0,
                                rctrl=self.exp_cfi["rctrl"],
                                opcode=self.exp_cfi["opcode"],
                                addr=self.exp_cfi["address"],
                                data=self.exp_cfi["data_chunk1"],
                                sai=DoNotCheck)
            )

            self._add_fsm_bubble(
                UPI_TRANSACTION(interface=CFI.IFCS.tx_rsp, pkt_type=CFI.PKT_TYPE.sr_u, vc_id=CFI.VC_IDS.vc0_ndr,
                                dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nccmpu)
            )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                            addr=DoNotCheck,  # there is a difference between CCF and IDIB, and this is not a real RTL value
                            module_id=self.exp_idi["module_id"])
        )

    @staticmethod
    def is_new_flow(flow):
        return flow[0].opcode in [IDI.OPCODES.int_logical, IDI.OPCODES.int_physical] and \
               flow[0].tran_type == IDI.TYPES.c2u_req

    def _set_expected_values(self):
        self.__set_chicken_bits()
        self.__set_expected_idi()
        if not self.cb["fast_ipi"]:
            self.__set_expected_cfi()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["opcode"] = self._initial_tran.opcode
        self.exp_idi["address"] = self.__get_idi_interrupt_addr()
        self.exp_idi["original_addr"] = self._initial_tran.addr
        if self.cb["fast_ipi"]:
            self.exp_idi["int_data"] = self._get_int_data()

    def __set_expected_cfi(self):
        self.exp_cfi = dict()
        self.exp_cfi["opcode"] = CFI.OPCODES.int_physical if self._initial_tran.opcode == IDI.OPCODES.int_physical \
            else CFI.OPCODES.int_logical
        self.exp_cfi["address"] = self.__get_cfi_interrupt_addr()
        self.exp_cfi["data_chunk0"], self.exp_cfi["data_chunk1"] = self._data[0], self._data[1]
        self.exp_cfi["rctrl"] = self._get_rctrl(pkt_type=CFI.PKT_TYPE.pw)

    def __set_chicken_bits(self):
        self.cb = dict()
        self.cb["fast_ipi"] = self.ral_utils.read_reg_field(block_name="ncdecs",
                                                            reg_name="NCRADECS_OVRD",
                                                            field_name="FastIpi",
                                                            time=self._start_time) == 1

    def __get_idi_interrupt_addr(self):
        addr = bint(self._initial_tran.addr[GLOBAL.mktme_lsb:0])
        addr[2:0] = 0
        return addr

    def __get_cfi_interrupt_addr(self):
        addr = self.__get_idi_interrupt_addr()
        addr = addr << 3
        return addr
