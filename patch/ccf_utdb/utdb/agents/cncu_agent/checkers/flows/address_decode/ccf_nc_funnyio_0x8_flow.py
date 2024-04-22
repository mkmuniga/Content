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
from val_utdb_bint import bint

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.common.cncu_defines import IDI, CFI, TARGET_TYPE
from agents.cncu_agent.checkers.flows.address_decode.cncu_cfg_base_flow import CCF_NC_CFG_BASE_FLOW
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_FUNNYIO_0x8_FLOW(CCF_NC_CFG_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_0x8_chk_en

    @staticmethod
    def is_new_flow(flow: list):
        return flow[0].opcode in [IDI.OPCODES.port_out, IDI.OPCODES.port_in] and flow[0].addr[31:28] == 0x8

    def _set_expected_values(self):
        super()._set_expected_values()
        self.is_read = self._initial_tran.opcode == IDI.OPCODES.port_in

        offset, be = self._get_base_sb_offset(self.is_read, self._initial_tran.addr, self._data, self._byteen)

        self.segment = bint(0)
        self.bus = self._initial_tran.addr[27:20]
        self.function = self._initial_tran.addr[14:12]
        self.device = self._initial_tran.addr[19:15]

        self._define_cfg_devices()
        self.target = self._get_cfg_target(self._initial_tran.addr)

        self.exp_idi_tran["module_id"] = self._module_id
        self.exp_idi_tran["address"] = self._initial_tran.addr

        self.is_abort, self.target = CNCU_UTILS.cfg_abort_detection(self.target,
                                                                    self._initial_tran.addr,
                                                                    offset,
                                                                    be,
                                                                    self.is_read,
                                                                    self._length,
                                                                    self._initial_tran.opcode)

        if self.target in [TARGET_TYPE.SB, TARGET_TYPE.SB_CFI]:
            self.exp_sb_tran["offset"] = offset
            self.exp_sb_tran["be"] = be

            if not self.is_abort:
                self.exp_sb_tran["opcode"] = self._get_sb_cfg_opcode(self.is_read)
                self.exp_sb_tran["fid"] = self._get_sb_cfg_fid()
                self.exp_sb_tran["dest_pid"] = self._get_sb_cfg_dest_pid()
                self.exp_sb_tran["src_pid"] = self._get_sb_src_pid(self.exp_sb_tran["dest_pid"])
                self.exp_sb_tran["bar"] = 0
                self.exp_sb_tran["sai"] = self._get_sai(self.exp_sb_tran["dest_pid"])
                self.exp_sb_tran["wr_data"] = DoNotCheck
                if self.is_read:
                    self.exp_idi_tran["rd_data"] = self._data
                else:
                    self.exp_sb_tran["wr_data"] = self._get_sb_wr_data()
            else:
                self._set_sb_abort(self.is_read)
        if self.target in [TARGET_TYPE.CFI, TARGET_TYPE.SB_CFI]:
            self.exp_cfi_tran["rsp_id"] = CFI.EPS.ccf
            self.exp_cfi_tran["opcode"] = self._get_cfi_cfg_opcode(self.is_read)
            self.exp_cfi_tran["address"] = self._get_cfi_address(self.is_read, self._initial_tran.addr, self._initial_tran.opcode)
            self.exp_cfi_tran["pkt_type"] = self._get_cfi_cfg_pkt_type(self.is_read)
            self.exp_cfi_tran["sai"] = self._sai
            self.exp_cfi_tran["length"] = self._length if self.is_read else None
            self.exp_cfi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                      time= self._start_time,
                                                                      pkt_type=self.exp_cfi_tran["pkt_type"])
            self.exp_cfi_tran["vc_id"] = CFI.VC_IDS.vc0_ncs
            self.exp_cfi_tran["wr_data"] = [DoNotCheck, DoNotCheck]
            if self.is_read:
                self.exp_idi_tran["rd_data"] = self._get_cfi_read_data()

            if not self.is_abort:
                self.exp_cfi_tran["dest_id"] = self._get_cfi_cfg_dest_pid()

                if not self.is_read:
                    self.exp_cfi_tran["wr_data"] = self._data
            else:
                self._set_sncu_abort(self.is_read)