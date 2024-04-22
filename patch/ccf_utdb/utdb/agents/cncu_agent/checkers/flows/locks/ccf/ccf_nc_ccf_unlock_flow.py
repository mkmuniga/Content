from agents.cncu_agent.checkers.flows.locks.ccf_nc_base_unlock_flow import CCF_NC_BASE_UNLOCK_FLOW
from agents.cncu_agent.common.cncu_defines import IDI, CFI, SB, SAI
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION, SB_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_CCF_UNLOCK_FLOW(CCF_NC_BASE_UNLOCK_FLOW, CCF_NC_BASE_FLOW):

    def checker_enabled(self):
        return self.si.lock_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, opcode=IDI.OPCODES.unlock)
        )
        if self.is_valid_unlock_flow():
            self._add_fsm_bubble(
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                                rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nc_msg_s, chunk=0, param_a=0x0,
                                msg_type=CFI.MSG_TYPE.unlock,
                                data=self.exp_cfi["data_chunk0"],
                                rctrl=self.exp_cfi["rctrl"]),
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                                rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nc_msg_s, chunk=1, param_a=0x0,
                                msg_type=CFI.MSG_TYPE.unlock,
                                data=self.exp_cfi["data_chunk1"],
                                rctrl=self.exp_cfi["rctrl"])
            )

            self._add_start_req_phase_to_fsm()

            if not UNIQUE_DEFINES.is_low_power_ccf:
                self._add_fsm_bubble(
                    SB_TRANSACTION(msg_type=SB.MSG_TYPE.posted, src_pid=SB.EPS.sncu, dest_pid=SB.EPS.pmc,
                                   opcode=SB.OPCODES.ncu_pcu_msg, eh=1, sai=SAI.hw_cpu,
                                   data=self.exp_sb["lock_end_data"])
                )

                self._add_fsm_bubble(
                    SB_TRANSACTION(msg_type=SB.MSG_TYPE.posted, src_pid=SB.EPS.pmc, dest_pid=SB.EPS.sncu,
                                   opcode=SB.OPCODES.pcu_ncu_msg, eh=1, sai=SAI.pm_pcs,
                                   data=self.exp_sb["lock_end_ack_data"])
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
        return flow[0].opcode == IDI.OPCODES.unlock and flow[0].tran_type == IDI.TYPES.c2u_req

    def is_valid_unlock_flow(self):
        return self._initial_tran.addr[11:6] in [0x3]

    def __add_sb_msg_to_act_flow(self):
        flow_cmps_idxs = self._find_tran_idx(UPI_TRANSACTION(opcode=CFI.OPCODES.nccmpu), get_all_matches=True)

        if len(flow_cmps_idxs) == 2:
            sb_msgs_of_flow = self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.ncu_pcu_msg, SB.OPCODES.pcu_ncu_msg],
                                                                    start_time=self._act_flow[flow_cmps_idxs[0]].time,
                                                                    end_time=self._act_flow[flow_cmps_idxs[1]].time)

            for msg in sb_msgs_of_flow:
                msg.uri = self._uri
                self._act_flow.append(msg)

            self._act_flow.sort(key=lambda tran: tran.time)

    def _set_act_flow(self, flow):
        super()._set_act_flow(flow)
        self.__add_sb_msg_to_act_flow()

    def _set_expected_values(self):
        self._set_unlock_base_expected_values()
        self.__set_expected_idi()
        self.__set_expected_cfi()
        self.__set_expected_sb()

    def __set_expected_idi(self):
        self.exp_idi = dict()
        self.exp_idi["module_id"] = self._module_id
        self.exp_idi["address"] = self._initial_tran.addr

    def __set_expected_cfi(self):
        self.exp_cfi = dict()
        self.exp_cfi["data_chunk0"], self.exp_cfi["data_chunk1"] = CNCU_UTILS.get_blank_data(num_of_chunks=2,
                                                                                             num_of_bytes=32)

        self.exp_cfi["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils, time=self._start_time,
                                                             pkt_type=CFI.PKT_TYPE.ncm)

    def __set_expected_sb(self):
        self.exp_sb = dict()
        self.exp_sb["lock_end_data"] = self.__get_exp_lock_end_data()
        self.exp_sb["lock_end_ack_data"] = self.__get_exp_lock_end_ack_data()

    def __get_exp_lock_end_data(self):
        data = CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=4)
        data[3][7] = 1
        return data

    def __get_exp_lock_end_ack_data(self):
        data = CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=4)
        data[3][7] = 1
        return data

    def _additional_checks(self):
        self._check_start_req_arrived_before_rsp_start_done()
