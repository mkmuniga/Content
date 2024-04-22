from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import IDI, CFI, SB, SAI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION, SB_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_BASE_LOCK_FLOW:

    def _add_stop_modules_phase_to_fsm(self):
        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_s, chunk=0,
                            msg_type=CFI.MSG_TYPE.stop_req1,
                            data=DoNotCheck),
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_s, chunk=1,
                            msg_type=CFI.MSG_TYPE.stop_req1,
                            data=DoNotCheck)
        )

        if not self.cb["ignore_lock"]:
            if len(self._get_enabled_modules()) > 0:
                self._add_fsm_bubble(
                    self._for_all_modules(
                        IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_req, opcode=IDI.OPCODES.stop_req, addr=0x0),
                        enabled_only=True
                    ),
                    self._for_all_modules(
                        IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_rsp, opcode=IDI.OPCODES.rsp_stop_done, addr=0x0),
                        enabled_only=True
                    )
                )

            self._add_fsm_bubble(
                UPI_TRANSACTION(interface=CFI.IFCS.rx_rsp, pkt_type=CFI.PKT_TYPE.sr_u, vc_id=CFI.VC_IDS.vc0_ndr,
                                dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nccmpu)
            )

    def _add_cbo_drain_phase_to_fsm(self):
        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_s, chunk=0,
                            msg_type=CFI.MSG_TYPE.stop_req3,
                            data=DoNotCheck),
            UPI_TRANSACTION(interface=CFI.IFCS.tx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                            rsp_id=CFI.EPS.sncu, dest_id=CFI.EPS.ccf, opcode=CFI.OPCODES.nc_msg_s, chunk=1,
                            msg_type=CFI.MSG_TYPE.stop_req3,
                            data=DoNotCheck),
        )

        if not self.cb["skip_cbo_drain"] and not self.cb["ignore_lock"] and not UNIQUE_DEFINES.is_low_power_ccf:
            self._add_fsm_bubble(
                SB_TRANSACTION(msg_type=SB.MSG_TYPE.posted, src_pid=SB.EPS.ncevents, dest_pid=SB.EPS.mcast_cbo_all,
                               opcode=SB.OPCODES.cbo_drain, eh=1, sai=SAI.hw_cpu,
                               data=self.exp_lock_base_cfi["cbo_drain_data"])
            )

            self._add_fsm_bubble(
                self._from_all_cbos(
                    SB_TRANSACTION(msg_type=SB.MSG_TYPE.posted, dest_pid=SB.EPS.ncevents,
                                   opcode=SB.OPCODES.cbo_ack, eh=1, sai=SAI.hw_cpu)
                )
            )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_rsp, pkt_type=CFI.PKT_TYPE.sr_u, vc_id=CFI.VC_IDS.vc0_ndr,
                            dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nccmpu)
        )

    def _get_act_cbo_drain_sb_msgs(self):
        stop_req3_idxs = self._find_tran_idx(UPI_TRANSACTION(msg_type=CFI.MSG_TYPE.stop_req3), get_all_matches=True)
        if len(stop_req3_idxs) == 2 and stop_req3_idxs[1] + 1 < len(self._act_flow):
            cbo_drain_sb_msgs = self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.cbo_drain, SB.OPCODES.cbo_ack],
                                                             start_time=self._act_flow[stop_req3_idxs[1]].time,
                                                             end_time=self._act_flow[stop_req3_idxs[1] + 1].time)
            return cbo_drain_sb_msgs
        return list()

    def _set_lock_base_expected_values(self):
        self.__set_lock_base_chicken_bits()
        self.__set_lock_base_expected_cfi()

    def __set_lock_base_chicken_bits(self):
        self.cb = dict()
        self.cb["ignore_lock"] = self.ral_utils.read_reg_field(block_name="ncevents",
                                                               reg_name="NcuEvOveride",
                                                               field_name="IgnLockFlow",
                                                               time=self._start_time) == 1

        self.cb["skip_cbo_drain"] = self.ral_utils.read_reg_field(block_name="ncevents",
                                                                  reg_name="NcuEvOveride",
                                                                  field_name="SkipLkCboDrain",
                                                                  time=self._start_time) == 1

    def __set_lock_base_expected_cfi(self):
        self.exp_lock_base_cfi = dict()
        self.exp_lock_base_cfi["data_chunk0"], self.exp_lock_base_cfi["data_chunk1"] = CNCU_UTILS.get_blank_data(
            num_of_chunks=2,
            num_of_bytes=32)
        self.exp_lock_base_cfi["cbo_drain_data"] = self.__get_exp_cbo_drain_data()

    def __get_exp_cbo_drain_data(self):
        data = CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=4)
        data[0][0] = 1
        return data
