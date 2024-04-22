from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import IDI, CFI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_BASE_UNLOCK_FLOW:

    def _add_start_req_phase_to_fsm(self):
        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_s, chunk=0,
                            msg_type=CFI.MSG_TYPE.start_req1, param_a=0x0,
                            data=DoNotCheck),
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_s, chunk=1,
                            msg_type=CFI.MSG_TYPE.start_req1, param_a=0x0,
                            data=DoNotCheck)
        )

        if not self.cb["ignore_lock"]:
            if len(self._get_enabled_modules()) > 0:
                self._add_fsm_bubble(
                    self._for_all_modules(
                        IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_req, opcode=IDI.OPCODES.start_req, addr=0x0),
                        enabled_only=True
                    ),
                    self._for_all_modules(
                        IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_rsp, opcode=IDI.OPCODES.rsp_start_done, addr=0x0),
                        enabled_only=True
                    )
                )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_rsp, pkt_type=CFI.PKT_TYPE.sr_u, vc_id=CFI.VC_IDS.vc0_ndr,
                            dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nccmpu)
        )

    def _set_unlock_base_expected_values(self):
        self.__set_unlock_base_chicken_bits()
        self.__set_unlock_base_expected_cfi()

    def __set_unlock_base_chicken_bits(self):
        self.cb = dict()
        self.cb["ignore_lock"] = self.ral_utils.read_reg_field(block_name="ncevents",
                                                               reg_name="NcuEvOveride",
                                                               field_name="IgnLockFlow",
                                                               time=self._start_time) == 1

    def __set_unlock_base_expected_cfi(self):
        self.exp_unlock_base_cfi = dict()
        self.exp_unlock_base_cfi["data_chunk0"], self.exp_unlock_base_cfi["data_chunk1"] = CNCU_UTILS.get_blank_data(num_of_chunks=2,
                                                                                                                     num_of_bytes=32)

    def _check_start_req_arrived_before_rsp_start_done(self):
        for i in self._get_enabled_modules():
            self._check_arriving_order(before=IDI_TRANSACTION(module_id=i, opcode=IDI.OPCODES.start_req),
                                       after=IDI_TRANSACTION(module_id=i, opcode=IDI.OPCODES.rsp_start_done))
