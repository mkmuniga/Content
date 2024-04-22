#!/usr/bin/env python3.6.3a
#################################################################################################
# cncu_types.py
#
# Owner: ranzohar & mlugassi
# Creation Date:      5/2021
#
# ###############################################
#
# Description:
#
#################################################################################################
from agents.cncu_agent.checkers.flows.address_decode.ccf_nc_mmio_base_flow import CCF_NC_MMIO_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.common.cncu_defines import CFI, SB, IDI, TARGET_TYPE, BAR
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_FUNNYIO_0x3_FLOW(CCF_NC_MMIO_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_0x3_chk_en

    @staticmethod
    def is_new_flow(flow: list):
        return flow[0].opcode in [IDI.OPCODES.port_in, IDI.OPCODES.port_out] and flow[0].addr[31:28] == 0x3

    def _set_expected_values(self):
        self.is_read = (self._initial_tran.opcode == IDI.OPCODES.port_in)
        self.exp_idi_tran = dict()
        self.exp_sb_tran = dict()
        self.exp_cfi_tran = dict()

        self.bar_match = CNCU_UTILS.get_funnyio_0x3_match_bar(self._initial_tran.addr)

        self.target = self.__get_target()

        if self.target in [TARGET_TYPE.SB]:
            self.exp_sb_tran = dict()
            self.exp_sb_tran["dest_pid"] = self._get_sb_dest_pid(self._initial_tran.addr)
            self.exp_sb_tran["opcode"] = self._get_sb_opcode(self.is_read)
            self.exp_sb_tran["src_pid"] = self._get_sb_src_pid(self.exp_sb_tran["dest_pid"])
            self.exp_sb_tran["fid"] = self._get_sb_fid(self._initial_tran.addr)
            self.exp_sb_tran["bar"] = self._get_sb_bar()
            self.exp_sb_tran["offset"], self.exp_sb_tran["be"] = self._get_base_sb_offset(self.is_read,
                                                                                          self._initial_tran.addr,
                                                                                          self._data, self._byteen)
            self.exp_sb_tran["sai"] = self._sai
            self.exp_sb_tran["wr_data"] = DoNotCheck
            if self.is_read:
                self.exp_idi_tran["rd_data"] = self._data
            else:
                self.exp_sb_tran["wr_data"] = self._get_sb_wr_data()
        if self.target in [TARGET_TYPE.CFI]:
            self.exp_cfi_tran["address"] = self._get_cfi_address(self.is_read,
                                                                 self._initial_tran.addr,
                                                                 self._initial_tran.opcode)
            self.exp_cfi_tran["rsp_id"] = CFI.EPS.ccf
            self.exp_cfi_tran["dest_id"] = self._get_cfi_dest_pid(self._initial_tran.addr, self._initial_tran.opcode)
            self.exp_cfi_tran["opcode"] = self._get_cfi_opcode(self.is_read, self._initial_tran.opcode)
            self.exp_cfi_tran["pkt_type"] = self._get_cfi_cfg_pkt_type(self.is_read, self.exp_cfi_tran["opcode"])
            self.exp_cfi_tran["sai"] = self._sai
            self.exp_cfi_tran["length"] = self._length if self.is_read else None
            self.exp_cfi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                      time=self._start_time,
                                                                      pkt_type=self.exp_cfi_tran["pkt_type"])
            self.exp_cfi_tran["vc_id"] = self._get_cfi_vc_id(self.is_read, self._initial_tran.opcode)
            self.exp_cfi_tran["wr_data"] = [[DoNotCheck, DoNotCheck]]
            if self.is_read:
                self.exp_idi_tran["rd_data"] = self._get_cfi_read_data()
            else:
                self.exp_cfi_tran["wr_data"] = self._get_cfi_write_data()

    def __get_target(self):
        if self.bar_match in [BAR.mchbar, BAR.tmbar, BAR.pm_bar, BAR.membar2, BAR.vtdbar_abort]:
            return TARGET_TYPE.SB
        return TARGET_TYPE.CFI
