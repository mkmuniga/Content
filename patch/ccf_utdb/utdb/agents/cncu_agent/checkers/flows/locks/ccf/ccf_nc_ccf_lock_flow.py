from agents.cncu_agent.checkers.flows.locks.ccf_nc_base_lock_flow import CCF_NC_BASE_LOCK_FLOW
from agents.cncu_agent.common.cncu_defines import IDI, CFI, SB, SAI
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CCF_NC_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION, SB_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_CCF_LOCK_FLOW(CCF_NC_BASE_LOCK_FLOW, CCF_NC_BASE_FLOW):

    def __init__(self, flow):
        super().__init__(flow)

    def checker_enabled(self):
        return self.si.lock_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req)
        )

        if self.is_valid_lock_flow():
            self._add_fsm_bubble(
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                                rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nc_msg_s, chunk=0,
                                param_a=0x0,
                                msg_type=self.exp_cfi["msg_type"],
                                data=self.exp_cfi["data_chunk0"],
                                rctrl=self.exp_cfi["rctrl"]),
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, pkt_type=CFI.PKT_TYPE.ncm, vc_id=CFI.VC_IDS.vc0_ncs,
                                rsp_id=CFI.EPS.ccf, dest_id=CFI.EPS.sncu, opcode=CFI.OPCODES.nc_msg_s, chunk=1,
                                param_a=0x0,
                                msg_type=self.exp_cfi["msg_type"],
                                data=self.exp_cfi["data_chunk1"],
                                rctrl=self.exp_cfi["rctrl"])
            )

            if not UNIQUE_DEFINES.is_low_power_ccf:
                self._add_fsm_bubble(
                    SB_TRANSACTION(msg_type=SB.MSG_TYPE.posted, src_pid=SB.EPS.sncu, dest_pid=SB.EPS.pmc,
                                   opcode=SB.OPCODES.ncu_pcu_msg, eh=1, sai=SAI.hw_cpu,
                                   data=self.exp_sb["lock_start_data"])
                )

                self._add_fsm_bubble(
                    SB_TRANSACTION(msg_type=SB.MSG_TYPE.posted, src_pid=SB.EPS.pmc, dest_pid=SB.EPS.sncu,
                                   opcode=SB.OPCODES.pcu_ncu_msg, eh=1, sai=SAI.pm_pcs,
                                   data=self.exp_sb["lock_start_ack_data"])
                )

            self._add_stop_modules_phase_to_fsm()

            # MCAST token taking is begin checked as part of the MCAST token checker and in sNCU IP

            self._add_cbo_drain_phase_to_fsm()

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
        return flow[0].opcode in [IDI.OPCODES.lock, IDI.OPCODES.split_lock] and flow[0].tran_type == IDI.TYPES.c2u_req

    def is_valid_lock_flow(self):
        return self._initial_tran.opcode == IDI.OPCODES.lock and self._initial_tran.addr[11:6] in [0x4, 0x8, 0xA] or \
               self._initial_tran.opcode == IDI.OPCODES.split_lock and self._initial_tran.addr[11:6] in [0x5]

    def __add_sb_msg_to_act_flow(self):
        cfi_lock_idxs = self._find_tran_idx(UPI_TRANSACTION(msg_type=self.__get_cfi_lock_opcode()),
                                            get_all_matches=True)
        if len(cfi_lock_idxs) == 2 and cfi_lock_idxs[1] + 1 < len(self._act_flow):
            lock_start_sb_msg = self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.ncu_pcu_msg,
                                                                      SB.OPCODES.pcu_ncu_msg],
                                                             start_time=self._act_flow[cfi_lock_idxs[1]].time,
                                                             end_time=self._act_flow[
                                                                 cfi_lock_idxs[1] + 1].time)

            for msg in lock_start_sb_msg + self._get_act_cbo_drain_sb_msgs():
                msg.uri = self._uri
                self._act_flow.append(msg)

            self._act_flow.sort(key=lambda tran: tran.time)

    def _set_act_flow(self, flow):
        super()._set_act_flow(flow)
        self.__add_sb_msg_to_act_flow()

    def _set_expected_values(self):
        self._set_lock_base_expected_values()
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
        self.exp_cfi["msg_type"] = self.__get_cfi_lock_opcode()

    def __set_expected_sb(self):
        self.exp_sb = dict()
        self.exp_sb["lock_start_data"] = self.__get_exp_lock_start_data()
        self.exp_sb["lock_start_ack_data"] = self.__get_exp_lock_start_ack_data()

    def __get_cfi_lock_opcode(self):
        return CFI.MSG_TYPE.lock if self._get_flow_initial_tran().opcode == IDI.OPCODES.lock else CFI.MSG_TYPE.split_lock

    def __get_exp_lock_start_data(self):
        data = CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=4)
        data[3][6] = 1
        return data

    def __get_exp_lock_start_ack_data(self):
        data = CNCU_UTILS.get_blank_data(num_of_chunks=1, num_of_bytes=4)
        data[3][6] = 1
        return data

    def __check_stop_req_arrived_before_rsp_stop_done(self):
        for i in self._get_enabled_modules():
            self._check_arriving_order(before=IDI_TRANSACTION(module_id=i, opcode=IDI.OPCODES.stop_req),
                                       after=IDI_TRANSACTION(module_id=i, opcode=IDI.OPCODES.rsp_stop_done))

    def _additional_checks(self):
        self.__check_stop_req_arrived_before_rsp_stop_done()
