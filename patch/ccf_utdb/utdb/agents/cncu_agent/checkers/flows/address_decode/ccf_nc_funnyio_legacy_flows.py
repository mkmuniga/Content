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

from agents.cncu_agent.checkers.flows.address_decode.ccf_nc_addr_decode_base_flow import \
    CCF_NC_ADDR_DECODE_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.common.cncu_defines import IDI, CFI, GLOBAL, SAI, TARGET_TYPE
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION, SB_TRANSACTION
from agents.cncu_agent.utils.ccf_mmio_patching_handler import MMIO_PATCHING_HANDLER, MMIO_PATCH_DETECT_TYPE, \
    MMIO_PATCH_ACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_FUNNYIO_LEGACY_FLOW(CCF_NC_ADDR_DECODE_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_legacy_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, addr=DoNotCheck)
        )

        if not self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=DoNotCheck,
                                module_id=self._module_id,
                                addr=DoNotCheck)
            )

            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=DoNotCheck, chunk=0),
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=DoNotCheck, chunk=1)
            )

        if self.target in [TARGET_TYPE.SB]:
            self._add_fsm_bubble([
                SB_TRANSACTION(opcode=self.exp_sb_tran["opcode"],
                               src_pid=self.exp_sb_tran["src_pid"],
                               dest_pid=self.exp_sb_tran["dest_pid"],
                               addr=self.exp_sb_tran["offset"],
                               fid=self.exp_sb_tran["fid"],
                               byte_en=self.exp_sb_tran["be"],
                               bar=self.exp_sb_tran["bar"],
                               sai=self.exp_sb_tran["sai"],
                               data=self.exp_sb_tran["wr_data"])
            ])
            self._add_fsm_bubble([
                SB_TRANSACTION(src_pid=self.exp_sb_tran["dest_pid"],
                               dest_pid=self.exp_sb_tran["src_pid"])
            ])

        if self.target in [TARGET_TYPE.CFI]:
            self._add_fsm_bubble(
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, opcode=self.exp_cfi_tran["opcode"], rsp_id=CFI.EPS.ccf,
                                dest_id=self.exp_cfi_tran["dest_id"],
                                chunk=0,
                                addr=self.exp_cfi_tran["address"],
                                pkt_type=self.exp_cfi_tran["pkt_type"],
                                vc_id=self.exp_cfi_tran["vc_id"],
                                sai=self.exp_cfi_tran["sai"],
                                rctrl=self.exp_cfi_tran["rctrl"],
                                length=self.exp_cfi_tran["length"],
                                data=self.exp_cfi_tran["wr_data"][0]),
                UPI_TRANSACTION(interface=CFI.IFCS.rx_data, opcode=self.exp_cfi_tran["opcode"], rsp_id=CFI.EPS.ccf,
                                dest_id=self.exp_cfi_tran["dest_id"],
                                chunk=1,
                                addr=self.exp_cfi_tran["address"],
                                pkt_type=self.exp_cfi_tran["pkt_type"],
                                vc_id=self.exp_cfi_tran["vc_id"],
                                sai=self.exp_cfi_tran["sai"],
                                rctrl=self.exp_cfi_tran["rctrl"],
                                length=self.exp_cfi_tran["length"],
                                data=self.exp_cfi_tran["wr_data"][1])
            )
            if not self.is_read:
                self._add_fsm_bubble(
                    UPI_TRANSACTION(interface=CFI.IFCS.tx_rsp,
                                    opcode=DoNotCheck,
                                    dest_id=CFI.EPS.ccf,
                                    pkt_type=CFI.PKT_TYPE.sr_u,
                                    vc_id=CFI.VC_IDS.vc0_ndr)
                )
            else:
                self._add_fsm_bubble(
                    UPI_TRANSACTION(interface=CFI.IFCS.tx_data,
                                    opcode=CFI.OPCODES.nc_data,
                                    dest_id=CFI.EPS.ccf,
                                    chunk=0,
                                    pkt_type=CFI.PKT_TYPE.sr_cd,
                                    vc_id=CFI.VC_IDS.vc0_drs,
                                    data=DoNotCheck),
                    UPI_TRANSACTION(interface=CFI.IFCS.tx_data,
                                    opcode=CFI.OPCODES.nc_data,
                                    dest_id=CFI.EPS.ccf,
                                    chunk=1,
                                    pkt_type=CFI.PKT_TYPE.sr_cd,
                                    vc_id=CFI.VC_IDS.vc0_drs,
                                    data=DoNotCheck)
                )

        if self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                module_id=self._module_id, addr=DoNotCheck),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, module_id=self._module_id,
                                addr=DoNotCheck, chunk=0,
                                data=self.exp_idi_tran["rd_data"][0]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, module_id=self._module_id,
                                addr=DoNotCheck, chunk=1,
                                data=self.exp_idi_tran["rd_data"][1]),
                append_to_last_bubble=True
            )
        else:
            self._add_fsm_bubble([
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=DoNotCheck,
                                module_id=self._module_id, addr=DoNotCheck)
            ])

    @staticmethod
    def is_new_flow(flow: list):
        return flow[0].opcode in [IDI.OPCODES.port_out, IDI.OPCODES.port_in] and flow[0].addr <= 0x10002

    def _set_expected_values(self):
        super()._set_expected_values()
        self.is_read = self._initial_tran.opcode == IDI.OPCODES.port_in

        offset, be = self._get_base_sb_offset(self.is_read, self._initial_tran.addr, self._data, self._byteen)

        self.target = TARGET_TYPE.CFI
        self.is_abort, self.target = CNCU_UTILS.io_abort_detection(self.target,
                                                                   self._initial_tran.addr,
                                                                   offset,
                                                                   be,
                                                                   self.is_read,
                                                                   self._length,
                                                                   self._initial_tran.opcode)

        # MMIO patching
        mmio_patch_detect, mmio_patch_action, mmio_patch_or_mask, mmio_patch_and_mask = None, None, None, None
        if self.si.mmio_patching_chk_en:
            mmio_patch_detect, mmio_patch_action, mmio_patch_or_mask, mmio_patch_and_mask = MMIO_PATCHING_HANDLER.get_mmio_patching_detection_and_action(
                self._initial_tran.addr,
                self._initial_tran.opcode,
                self._initial_tran.get_time())
            if mmio_patch_detect in [MMIO_PATCH_DETECT_TYPE.IO]:
                if mmio_patch_action in [MMIO_PATCH_ACTION.abort0, MMIO_PATCH_ACTION.abort1]:
                    self.is_abort = True
                    self.target = TARGET_TYPE.SB

        if self.target in [TARGET_TYPE.SB]:
            self._set_sb_abort(self.is_read)

        if self.target in [TARGET_TYPE.CFI]:
            self.exp_cfi_tran["rsp_id"] = CFI.EPS.ccf
            self.exp_cfi_tran["opcode"] = self.__get_cfi_opcode(self.is_read)
            self.exp_cfi_tran["address"] = self._get_cfi_address(self.is_read,
                                                                 self._initial_tran.addr[GLOBAL.addr_width - 1:0],
                                                                 self._initial_tran.opcode)
            self.exp_cfi_tran["pkt_type"] = self.__get_cfi_lt_pkt_type(self.is_read)
            self.exp_cfi_tran["sai"] = self._sai
            self.exp_cfi_tran["length"] = self._length if self.is_read else None
            self.exp_cfi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                      time=self._start_time,
                                                                      pkt_type=self.exp_cfi_tran["pkt_type"])
            self.exp_cfi_tran["vc_id"] = self.__get_cfi_vc_id()
            self.exp_cfi_tran["wr_data"] = [DoNotCheck, DoNotCheck]
            if self.is_read:
                self.exp_idi_tran["rd_data"] = self._get_cfi_read_data()
                if mmio_patch_action == MMIO_PATCH_ACTION.data_mask:
                    self.exp_idi_tran["rd_data"] = self._get_relevant_data_on_cl(MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask))
            if not self.is_abort:
                self.exp_cfi_tran["dest_id"] = self.__get_cfi_dest()

                if not self.is_read:
                    self.exp_cfi_tran["wr_data"] = self._data
                    if mmio_patch_action == MMIO_PATCH_ACTION.data_mask:
                        self.exp_cfi_tran["wr_data"] = MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask)
            else:
                self._set_sncu_abort(self.is_read)

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

    def __get_cfi_opcode(self, is_read):
        if is_read:
            return CFI.OPCODES.nc_io_rd
        return CFI.OPCODES.nc_io_wr

    def __get_cfi_lt_pkt_type(self, is_read):
        if is_read:
            return CFI.PKT_TYPE.pr
        return CFI.PKT_TYPE.pw

    def __get_cfi_vc_id(self):
        return CFI.VC_IDS.vc0_ncs

    def __get_cfi_dest(self):
        is_vga0 = 0x3b0 <= self._initial_tran.addr <= 0x3bb
        is_vga1 = 0x3c0 <= self._initial_tran.addr <= 0x3df
        if (is_vga0 or is_vga1) and self.si.vgaio_en:
            return CFI.EPS.media0
        return CFI.EPS.ioc0

