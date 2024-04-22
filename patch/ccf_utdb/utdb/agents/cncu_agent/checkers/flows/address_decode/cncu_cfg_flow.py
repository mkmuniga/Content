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
from agents.cncu_agent.common.cncu_defines import IDI, CFI, TARGET_TYPE, GLOBAL, UFI
from agents.cncu_agent.checkers.flows.address_decode.cncu_cfg_base_flow import CNCU_CFG_BASE_FLOW
from agents.cncu_agent.utils.ccf_mmio_patching_handler import MMIO_PATCHING_HANDLER, MMIO_PATCH_DETECT_TYPE, \
    MMIO_PATCH_ACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CNCU_CFG_FLOW(CNCU_CFG_BASE_FLOW):

    def checker_enabled(self):
        return self.si.cfg_chk_en and not self.si.sad_always_hom_en

    @staticmethod
    def is_new_flow(flow: list):
        addr_without_mktme = bint(0)
        if flow[0].addr is not None:
            addr_without_mktme = flow[0].addr[GLOBAL.addr_width-1:0]
        return CNCU_UTILS.is_idi_cfg_access_flow(addr_without_mktme, flow[0].opcode)

    def _set_expected_values(self):
        super()._set_expected_values()
        self.is_read = self._initial_tran.opcode in [IDI.OPCODES.prd]

        clean_addr = CNCU_UTILS.get_clean_cfg_address(self._initial_tran.addr)

        self.exp_idi_tran["module_id"] = self._module_id
        self.exp_idi_tran["address"] = self._initial_tran.addr

        # MMIO patching
        mmio_patch_detect, mmio_patch_action, mmio_patch_or_mask, mmio_patch_and_mask = None, None, None, None
        if self.si.mmio_patching_chk_en:
            mmio_patch_detect, mmio_patch_action, mmio_patch_or_mask, mmio_patch_and_mask = MMIO_PATCHING_HANDLER.get_mmio_patching_detection_and_action(
                self._initial_tran.addr,
                self._initial_tran.opcode,
                self._initial_tran.get_time())
            if mmio_patch_detect in [MMIO_PATCH_DETECT_TYPE.CFG]:
                if mmio_patch_action in [MMIO_PATCH_ACTION.abort0, MMIO_PATCH_ACTION.abort1]:
                    self.is_abort = True
                    self.target = TARGET_TYPE.SB

        self.exp_ufi_tran["opcode"] = self._get_cfi_cfg_opcode(self.is_read)
        self.exp_ufi_tran["address"] = self._get_cfi_address(self.is_read, clean_addr, self._initial_tran.opcode)
        self.exp_ufi_tran["pkt_type"] = self._get_cfi_cfg_pkt_type(self.is_read)
        self.exp_ufi_tran["sai"] = self._sai
        self.exp_ufi_tran["length"] = self._length if self.is_read else None
        self.exp_ufi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                  time=self._start_time,
                                                                  pkt_type=self.exp_ufi_tran["pkt_type"])
        self.exp_ufi_tran["vc_id"] = self.__get_ufi_vc_id(self.is_read)
        self.exp_ufi_tran["wr_data"] = [DoNotCheck, DoNotCheck]
        if self.is_read:
            self.exp_idi_tran["rd_data"] = self._get_cfi_read_data()
            if mmio_patch_action == MMIO_PATCH_ACTION.data_mask and not (self._initial_tran.opcode == IDI.OPCODES.prd and self._length == 0):
                self.exp_idi_tran["rd_data"] = self._get_relevant_data_on_cl(MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask))
        else:
            # self.exp_ufi_tran["wr_data"] = self.__get_clear_ufi_data()
            wr_data = self.__get_clear_ufi_data()
            self.exp_ufi_tran["wr_data"] = self.__get_ufi_data_with_idbe(wr_data)
            if mmio_patch_action == MMIO_PATCH_ACTION.data_mask:
                self.exp_ufi_tran["wr_data"] = MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask)

        if self.is_read and mmio_patch_action == MMIO_PATCH_ACTION.abort0:
            self.exp_idi_tran["rd_data"] = self._get_relevant_data_on_cl(
                [[0 for j in range(int(GLOBAL.cacheline_size_in_bytes / 2))],
                 [0 for j in range(int(GLOBAL.cacheline_size_in_bytes / 2))]]
            )
        elif self.is_read and mmio_patch_action == MMIO_PATCH_ACTION.abort1:
            self.exp_idi_tran["rd_data"] = self._get_relevant_data_on_cl(
                [[0xff for j in range(int(GLOBAL.cacheline_size_in_bytes / 2))],
                 [0xff for j in range(int(GLOBAL.cacheline_size_in_bytes / 2))]]
            )

    def __get_ufi_vc_id(self, is_read):
        return UFI.VC_IDS.vc0_ncs

    def __get_clear_ufi_data(self):
        data = self._data
        for i, chunk in enumerate(data):
            for j, byte in enumerate(data[i]):
                if byte is None:
                    data[i][j] = 0
        return data

    def __get_ufi_data_with_idbe(self, data):
        data_with_idbe = data
        for i in range(2):
            for j in range(4):
                qw_byteen = self._byteen[i][(j*8)+8:j*8]
                if qw_byteen not in [0, 0xff]:
                    l = j*8
                    hole = None
                    for k, byte in enumerate(qw_byteen):
                        if byte == 0:
                            hole = k
                            break
                    if hole > 0:
                        data_with_idbe[i][l+1:l+hole] = data[i][l:l+hole-1]
                    data_with_idbe[i][l] = qw_byteen
        return data_with_idbe





