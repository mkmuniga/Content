#!/usr/bin/env python3.6.3accf_nc_cfg_base_flows
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
from agents.cncu_agent.checkers.flows.address_decode.cncu_addr_decode_base_flow import CNCU_ADDR_DECODE_BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.common.cncu_defines import IDI, TARGET_TYPE, UFI, GLOBAL
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, SB_TRANSACTION, UFI_TRANSACTION
from agents.cncu_agent.utils.ccf_mmio_patching_handler import MMIO_PATCH_ACTION, MMIO_PATCHING_HANDLER, \
    MMIO_PATCH_DETECT_TYPE
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from val_utdb_bint import bint


class CNCU_DOWNSTREAM_MMIO_FLOW(CNCU_ADDR_DECODE_BASE_FLOW):

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

        elif self.target in [TARGET_TYPE.UFI]:
            self._add_fsm_bubble(
                UFI_TRANSACTION(interface=UFI.IFCS.data,
                                opcode=self.exp_ufi_tran["opcode"],
                                crnid=UFI.EPS.ccf,
                                cdnid=DoNotCheck,  # TODO: ranzohar - ask gadi to write it in HAS
                                chunk=0,
                                addr=self.exp_ufi_tran["address"],
                                pkt_type=self.exp_ufi_tran["pkt_type"],
                                vc_id=self.exp_ufi_tran["vc_id"],
                                sai=self.exp_ufi_tran["sai"],
                                length=self.exp_ufi_tran["length"],
                                rtid=DoNotCheck, tee=DoNotCheck, a_par=DoNotCheck, byteen=DoNotCheck, d_par=DoNotCheck,
                                i_par=DoNotCheck, poison=DoNotCheck,  # TODO: ranzohar - add support
                                data=self.exp_ufi_tran["wr_data"][0]),
                UFI_TRANSACTION(interface=UFI.IFCS.data,
                                opcode=self.exp_ufi_tran["opcode"],
                                crnid=UFI.EPS.ccf,
                                cdnid=DoNotCheck,  # TODO: ranzohar - ask gadi to write it in HAS
                                chunk=1,
                                addr=self.exp_ufi_tran["address"],
                                pkt_type=self.exp_ufi_tran["pkt_type"],
                                vc_id=self.exp_ufi_tran["vc_id"],
                                sai=self.exp_ufi_tran["sai"],
                                length=self.exp_ufi_tran["length"],
                                rtid=DoNotCheck, tee=DoNotCheck, a_par=DoNotCheck, byteen=DoNotCheck, d_par=DoNotCheck,
                                i_par=DoNotCheck, poison=DoNotCheck,  # TODO: ranzohar - add support
                                data=self.exp_ufi_tran["wr_data"][1])
            )
            if self.is_read:
                self._add_fsm_bubble(
                    UFI_TRANSACTION(interface=UFI.IFCS.data,
                                    opcode=UFI.OPCODES.nc_data,
                                    cdnid=UFI.EPS.ccf,
                                    chunk=0,
                                    pkt_type=UFI.PKT_TYPE.sr_cd,
                                    vc_id=UFI.VC_IDS.vc0_drs,
                                    rtid=DoNotCheck, tee=DoNotCheck, d_par=DoNotCheck, poison=DoNotCheck,
                                    pcls=DoNotCheck,  # TODO: ranzohar - add support
                                    data=DoNotCheck),
                    UFI_TRANSACTION(interface=UFI.IFCS.data,
                                    opcode=UFI.OPCODES.nc_data,
                                    cdnid=UFI.EPS.ccf,
                                    chunk=1,
                                    pkt_type=UFI.PKT_TYPE.sr_cd,
                                    vc_id=UFI.VC_IDS.vc0_drs,
                                    rtid=DoNotCheck, tee=DoNotCheck, d_par=DoNotCheck, poison=DoNotCheck,
                                    pcls=DoNotCheck,  # TODO: ranzohar - add support
                                    data=DoNotCheck)
                )
            else:
                self._add_fsm_bubble(
                    UFI_TRANSACTION(interface=UFI.IFCS.rsp,
                                    cdnid=UFI.EPS.ccf,
                                    opcode=UFI.OPCODES.nccmpu,
                                    pkt_type=UFI.PKT_TYPE.sr_u,
                                    rtid=DoNotCheck, tee=DoNotCheck, pcls=DoNotCheck,  # TODO: ranzohar - add support
                                    vc_id=UFI.VC_IDS.vc0_ndr)
                )

        if self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                module_id=self.exp_idi_tran["module_id"], addr=DoNotCheck),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=DoNotCheck, chunk=0,
                                module_id=self.exp_idi_tran["module_id"], data=self.exp_idi_tran["rd_data"][0]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=DoNotCheck, chunk=1,
                                module_id=self.exp_idi_tran["module_id"], data=self.exp_idi_tran["rd_data"][1]),
                append_to_last_bubble=True
            )
        else:
            self._add_fsm_bubble([
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                addr=DoNotCheck, module_id=self.exp_idi_tran["module_id"])
            ])

    def checker_enabled(self):
        return self.si.mmio_chk_en and not self.si.sad_always_hom_en

    @staticmethod
    def is_new_flow(flow: list):
        if flow[0].addr is not None:
            addr_without_mktme = flow[0].addr[GLOBAL.addr_width-1:0]
        else:
            addr_without_mktme = flow[0].addr
        return type(flow[0]) == IDI_TRANSACTION and \
               not CNCU_UTILS.is_idi_interrupt_flow(addr_without_mktme, flow[0].opcode) and \
               not CNCU_UTILS.is_idi_lock_flow(flow[0].opcode) and \
               not CNCU_UTILS.is_idi_funny_io_access_flow(flow[0].opcode) and \
               not CNCU_UTILS.is_idi_cfg_access_flow(addr_without_mktme, flow[0].opcode) and \
               CNCU_UTILS.is_flow_reached_nc(flow) and \
               flow[0].opcode not in [IDI.OPCODES.spcyc]

    def _set_expected_values(self):
        super()._set_expected_values()
        addr_without_mktme = self._initial_tran.addr[GLOBAL.addr_width-1:0]
        self.is_read = self._initial_tran.opcode in [IDI.OPCODES.prd,
                                                     IDI.OPCODES.crd,
                                                     IDI.OPCODES.crd_pref,
                                                     IDI.OPCODES.crd_uc,
                                                     IDI.OPCODES.drd,
                                                     IDI.OPCODES.drd_opt,
                                                     IDI.OPCODES.drd_ns,
                                                     IDI.OPCODES.drd_pref,
                                                     IDI.OPCODES.drd_opt_pref,
                                                     IDI.OPCODES.rdcurr,
                                                     IDI.OPCODES.drdpte,
                                                     IDI.OPCODES.rfo,
                                                     IDI.OPCODES.rfo_pref,
                                                     IDI.OPCODES.ucrdf]

        self.is_partial_read = self._initial_tran.opcode in [IDI.OPCODES.prd,
                                     IDI.OPCODES.crd_uc,
                                     IDI.OPCODES.ucrdf]
        self.is_partial_write = self._initial_tran.opcode in [IDI.OPCODES.wcil,
                                      IDI.OPCODES.wcil_ns,
                                      IDI.OPCODES.wil]
        offset, be = self._get_base_sb_offset(self.is_read, self._initial_tran.addr, self._data, self._byteen)
        self.bar_match = CNCU_UTILS.get_match_bar(self._initial_tran.addr[GLOBAL.addr_width - 1:0])

        self.target = self.__get_target()

        self.is_abort, self.target = CNCU_UTILS.mmio_abort_detection(self.target,
                                                                     addr_without_mktme,
                                                                     offset,
                                                                     be,
                                                                     self.is_read,
                                                                     self._length,
                                                                     self._initial_tran.opcode)

        # MMIO patching
        mmio_patch_detect, mmio_patch_action, mmio_patch_or_mask, mmio_patch_and_mask = None, None, None, None
        if self.si.mmio_patching_chk_en:
            mmio_patch_detect, mmio_patch_action, mmio_patch_or_mask, mmio_patch_and_mask = MMIO_PATCHING_HANDLER.get_mmio_patching_detection_and_action(addr_without_mktme,
                                                                                                                self._initial_tran.opcode,
                                                                                                                self._initial_tran.get_time())
            if mmio_patch_detect in [MMIO_PATCH_DETECT_TYPE.MMIO, MMIO_PATCH_DETECT_TYPE.BAR]:
                if mmio_patch_action in [MMIO_PATCH_ACTION.abort0, MMIO_PATCH_ACTION.abort1]:
                    self.is_abort = True
                    self.target = TARGET_TYPE.SB
                elif mmio_patch_action == MMIO_PATCH_ACTION.abort_dw: # and (self.is_partial_read or self.is_partial_write)TODO: abibas : need to chech with gadi: If we send full cacheline opcode to the last byte of address, rtl doesnt identifies cross DW .
                    is_cross_dw = CNCU_UTILS.is_cross_dw(offset, be, self.is_read, self._length, self._initial_tran.opcode)
                    if is_cross_dw:
                        self.is_abort = True
                        if self.is_read:
                            self.target = TARGET_TYPE.SB
                        else:
                            self.target = TARGET_TYPE.CFI

        if self.target in [TARGET_TYPE.SB]:
            if not self.is_abort:
                self.exp_sb_tran["offset"] = offset
                self.exp_sb_tran["be"] = be
                self.exp_sb_tran["dest_pid"] = self._get_sb_dest_pid(addr_without_mktme)
                self.exp_sb_tran["src_pid"] = self._get_sb_src_pid(self.exp_sb_tran["dest_pid"])
                self.exp_sb_tran["opcode"] = self.__get_sb_opcode(self.is_read)
                self.exp_sb_tran["fid"] = self._get_sb_fid(self._initial_tran.addr)
                self.exp_sb_tran["bar"] = self._get_sb_bar()

                self.exp_sb_tran["sai"] = self.__get_sai()
                self.exp_sb_tran["wr_data"] = DoNotCheck
                if self.is_read:
                    self.exp_idi_tran["rd_data"] = self._data
                    if mmio_patch_action == MMIO_PATCH_ACTION.data_mask and not (self._initial_tran.opcode == IDI.OPCODES.prd and self._length == 0) and not self._is_ur:
                        self.exp_idi_tran["rd_data"] = MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask)
                else:
                    self.exp_sb_tran["wr_data"] = self._get_sb_wr_data()
                    if mmio_patch_action == MMIO_PATCH_ACTION.data_mask and not self._is_ur:
                        self.exp_sb_tran["wr_data"] = MMIO_PATCHING_HANDLER.mask_data_sb(self._flat_data, be, mmio_patch_and_mask, mmio_patch_or_mask)
            else:
                self._set_sb_abort(self.is_read)
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

        if self.target in [TARGET_TYPE.UFI]:
            self.exp_ufi_tran["address"] = self._get_cfi_address(self.is_read, addr_without_mktme, self._initial_tran.opcode)
            self.exp_ufi_tran["rsp_id"] = CFI.EPS.ccf
            self.exp_ufi_tran["opcode"] = self._get_cfi_opcode(self.is_read, self._initial_tran.opcode)
            self.exp_ufi_tran["pkt_type"] = self._get_cfi_cfg_pkt_type(self.is_read, self.exp_ufi_tran["opcode"])
            self.exp_ufi_tran["sai"] = self.__get_sai()
            self.exp_ufi_tran["length"] = self._length if self.is_read else None
            self.exp_ufi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                      time=self._start_time,
                                                                      pkt_type=self.exp_ufi_tran["pkt_type"])
            self.exp_ufi_tran["vc_id"] = self._get_cfi_vc_id(self.is_read, self._initial_tran.opcode)
            self.exp_ufi_tran["wr_data"] = [[DoNotCheck, DoNotCheck]]
            if self.is_read:
                self.exp_idi_tran["rd_data"] = self._get_cfi_read_data()
                if mmio_patch_action == MMIO_PATCH_ACTION.data_mask:
                    self.exp_idi_tran["rd_data"] = self._get_relevant_data_on_cl(MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask))

            if not self.is_abort:
                self.exp_ufi_tran["dest_id"] = self._get_cfi_dest_pid(self._initial_tran.addr, self._initial_tran.opcode)

                if not self.is_read:
                    self.exp_ufi_tran["wr_data"] = self._get_cfi_write_data()
                    if mmio_patch_action == MMIO_PATCH_ACTION.data_mask:
                        self.exp_ufi_tran["wr_data"] = [MMIO_PATCHING_HANDLER.mask_data_idi(self._flat_data, self._data, mmio_patch_and_mask, mmio_patch_or_mask)]


class CCF_NC_MMIO_BASE_FLOW(CCF_NC_ADDR_DECODE_BASE_FLOW):




    def _get_sb_opcode(self, is_read):
        return SB.OPCODES.mem_rd if is_read else SB.OPCODES.mem_wr

    def _get_cfi_opcode(self, is_read, idi_opcode):
        if idi_opcode == IDI.OPCODES.enqueue:
            return CFI.OPCODES.ncenqueue
        if is_read:
            if idi_opcode in [IDI.OPCODES.prd, IDI.OPCODES.port_in]:
                return CFI.OPCODES.nc_rd_ptl
            if idi_opcode in [IDI.OPCODES.crd, IDI.OPCODES.crd_pref, IDI.OPCODES.crd_uc, IDI.OPCODES.drd, IDI.OPCODES.drd_opt, IDI.OPCODES.drd_ns, IDI.OPCODES.drd_opt_pref, IDI.OPCODES.drd_pref, IDI.OPCODES.drdpte, IDI.OPCODES.rfo, IDI.OPCODES.rfo_pref, IDI.OPCODES.ucrdf]:
                return CFI.OPCODES.nc_rd
            return CFI.OPCODES.nc_mem_rd
        else:
            if idi_opcode in [IDI.OPCODES.wcilf, IDI.OPCODES.wcilf_ns]:
                return CFI.OPCODES.wc_wr
            if idi_opcode in [IDI.OPCODES.wilf]:
                return CFI.OPCODES.nc_wr
            if idi_opcode == IDI.OPCODES.wil:
                return CFI.OPCODES.nc_wr_ptl
            if idi_opcode in [IDI.OPCODES.wcil, IDI.OPCODES.wcil_ns, IDI.OPCODES.port_out]:
                return CFI.OPCODES.wc_wr_ptl
            if idi_opcode in [IDI.OPCODES.wcilf, IDI.OPCODES.wcilf_ns]:
                return CFI.OPCODES.wc_wr
            return CFI.OPCODES.nc_mem_wr

    def _get_sb_dest_pid(self, address):
        self.is_abort = False
        if self.bar_match == BAR.mchbar:
            mchbar_sub = SM_DB.get_sub_region_by_offset(BAR.mchbar, address[16:0])

            full_dest = bint(SM_MAP.map[mchbar_sub])
            if self.is_read:
                full_dest = self.remap_dest_pid(SB.get_read_master(full_dest))
            if "RSVD" in mchbar_sub:
                self.is_abort = True
            else:
                return full_dest
        elif self.bar_match == BAR.tmbar:
            tmbar_sub = SM_DB.get_sub_region_by_offset(BAR.tmbar, address[16:0])
            full_dest = bint(SM_MAP.map[tmbar_sub])
            if self.is_read:
                full_dest = self.remap_dest_pid(SB.get_read_master(full_dest))
            if "RSVD" in tmbar_sub:
                self.is_abort = True
            else:
                return full_dest
        elif self.bar_match == BAR.pm_bar:
            return SB.EPS.punit
        elif self.bar_match == BAR.membar2:
            return SB.EPS.ioc
        elif self.bar_match == BAR.safbar:
            full_dest = bint(0)
            full_dest[15:13] = 0x7 # 3 upper bits of portID hardcoded to 111
            full_dest[12:0] = address[24:12]
            if full_dest not in self._get_safbar_allowed_list():
                self.is_abort = True
            else:
                if self.is_read:
                    full_dest = SB.get_read_master(self.remap_dest_pid(full_dest))
                return self.remap_dest_pid(full_dest)
        elif self.bar_match == BAR.regbar:
            full_dest = bint(0)
            full_dest[15:8] = SB.EPS.compute_seg_pid
            full_dest[7:0] = address[26:19]

            if full_dest[7:0] not in self._get_regbar_allowed_list():
                self.is_abort = True
            else:
                if self.is_read:
                    full_dest = SB.get_read_master(self.remap_dest_pid(full_dest))
                return self.remap_dest_pid(full_dest)

        elif self.bar_match == BAR.vtdbar_abort:
            self.is_abort = True

        elif self.bar_match == BAR.edrambar:
            self.is_abort = True

        if self.is_abort:
            full_dest = SB.EPS.ncevents
            return full_dest

        return None, None

    def _get_cfi_dest_pid(self, address, idi_opcode):
        if idi_opcode == IDI.OPCODES.enqueue:
            return self._handle_enqueue()
        if self.bar_match == BAR.vtdbar:
            vtdbar_sub_num = int(SM_DB.get_sub_region_by_offset(BAR.vtdbar, address[18:0])[-1])
            if vtdbar_sub_num < 2:
                return CFI.EPS.svtu
            else:
                return CFI.EPS.ioc_vtu
        if self.bar_match in [BAR.ipubar0, BAR.ipubar2]:
            return CFI.EPS.ipu
        if self.bar_match in [BAR.vpubar0, BAR.vpubar2]:
            return CFI.EPS.vpu0
        if self.bar_match in [BAR.iaxbar0, BAR.iaxbar2]:
            return CFI.EPS.iax
        if self.bar_match == BAR.membar2:
            return CFI.EPS.ioc0
        if self.bar_match == BAR.lmembar:
            return CFI.EPS.media0
        if self.bar_match == BAR.gttmmadr:
            return CFI.EPS.media0
        if self.bar_match == BAR.sriov0:
            return CFI.EPS.media0
        if self.bar_match == BAR.vgagsa:
            return CFI.EPS.media0
        return CFI.EPS.ioc0

    def _handle_enqueue(self):
        if self.bar_match in [BAR.iaxbar0, BAR.iaxbar2]:
            return CFI.EPS.iax
        return CFI.EPS.sncu

    def _get_sb_fid(self, addr):
        fid = bint(0)
        if self.is_abort:
            fid[7:3] = 7
        elif self.bar_match == BAR.safbar:
            return 0
        elif self.bar_match == BAR.regbar:
            fid[2:0] = addr[18:16]
        else:
            fid[7:3] = BAR.get_device(self.bar_match)

        return fid

    def _get_sb_bar(self):
        if self.is_abort:
            return 7
        return bint(BAR.get_bar(self.bar_match))

    def _get_cfi_cfg_pkt_type(self, is_read, cfi_opcode):
        if cfi_opcode in [CFI.OPCODES.wc_wr, CFI.OPCODES.nc_wr]:
            return CFI.PKT_TYPE.sa_d
        return CFI.PKT_TYPE.pr if is_read else CFI.PKT_TYPE.pw

    def _get_safbar_allowed_list(self):
        allow_list = list()
        fields = ["portid0", "portid1", "portid2", "portid3", "portid4", "portid5", "portid6", "portid7"]
        allow_comp_list_regs = ["safbar_comp_allowed_list0",
                           "safbar_comp_allowed_list1",
                           "safbar_comp_allowed_list2",
                           "safbar_comp_allowed_list3"]
        allow_gt_list_regs = ["safbar_gt_allowed_list0"]
        allow_soc_list_regs = ["safbar_soc_allowed_list0"]

        for reg in allow_comp_list_regs:
            for field in fields:
                portid = self.ral_utils.read_reg_field(block_name="ncdecs", reg_name=reg, field_name=field,
                                              time=self._initial_tran.time)
                portid[15:8] = SB.EPS.compute_seg_pid
                if portid[7:0] != 0:
                    allow_list.append(portid)

        for reg in allow_soc_list_regs:
            for field in fields:
                portid = self.ral_utils.read_reg_field(block_name="ncdecs", reg_name=reg, field_name=field,
                                              time=self._initial_tran.time)
                if portid[7:0] != 0:
                    portid[15:8] = SB.EPS.chipset_s0_seg_pid
                    allow_list.append(portid)
                    portid[15:8] = SB.EPS.chipset_s1_seg_pid
                    allow_list.append(portid)

        for reg in allow_gt_list_regs:
            for field in fields:
                portid = self.ral_utils.read_reg_field(block_name="ncdecs", reg_name=reg, field_name=field,
                                              time=self._initial_tran.time)
                if portid[7:0] != 0:
                    portid[15:8] = SB.EPS.gt_seg_pid
                    allow_list.append(portid)

        if self.ral_utils.read_reg_field(block_name="ncdecs", reg_name="NCRADECS_OVRD", field_name="dis_safbar_cfi_host_mcast",
                                              time=self._initial_tran.time) == 0:
            allow_list.append(SB.EPS.mcast_cfi_host)
        return allow_list

    def _get_regbar_allowed_list(self):
        curr_portid = bint(0)
        allow_list = list()
        allowed_regbar_regs = ["regbar_epmask0",
                               "regbar_epmask1",
                               "regbar_epmask2",
                               "regbar_epmask3",
                               "regbar_epmask4",
                               "regbar_epmask5",
                               "regbar_epmask6",
                               "regbar_epmask7"]

        for reg in allowed_regbar_regs:
            mask = self.ral_utils.read_reg_field(block_name="ncdecs", reg_name=reg,
                                          field_name="mask",
                                          time=self._initial_tran.time)
            for i,b in enumerate(mask):
                if i == 32:
                    break
                if b == 1:
                    allow_list.append(curr_portid)
                curr_portid += 1
        return allow_list

    def _get_cfi_vc_id(self, is_read, idi_opcode):
        if idi_opcode == IDI.OPCODES.enqueue or is_read:
            return CFI.VC_IDS.vc0_ncs
        return CFI.VC_IDS.vc0_ncb

    def _get_cfi_write_data(self):
        returned_data = list()
        cfi_data = self._data[0] + self._data[1]
        frag_start = None

        def new_frag(start_data, end_data):
            idi_data = [None for j in range(GLOBAL.cacheline_size_in_bytes)]
            idi_data[start_data:end_data] = cfi_data[start_data:end_data]
            return [idi_data[0:32], idi_data[32:64]]

        for i in range(0, GLOBAL.num_of_qw_in_cacheline):
            start_of_qw = i*8
            qw = cfi_data[start_of_qw:start_of_qw+8]
            data_exist = any(byte is not None for byte in qw)
            if data_exist:
                partial_qw_write = any(byte is None for byte in qw)
                if partial_qw_write:
                    if frag_start is not None:
                        returned_data.append(new_frag(frag_start, start_of_qw))
                    returned_data.append(new_frag(start_of_qw, start_of_qw+8))
                    frag_start = None
                elif frag_start is None:
                    frag_start = start_of_qw
            elif frag_start is not None:
                returned_data.append(new_frag(frag_start, start_of_qw))
                frag_start = None
        if frag_start is not None:
            returned_data.append(new_frag(frag_start, GLOBAL.cacheline_size_in_bytes))
        return returned_data



    def __get_target(self):
        if self._initial_tran.opcode == IDI.OPCODES.enqueue:
            return TARGET_TYPE.CFI
        if CNCU_UTILS.is_mmio_sb_target(self._initial_tran.addr[GLOBAL.addr_width - 1:0], self._initial_tran.opcode):
            return TARGET_TYPE.SB
        return TARGET_TYPE.CFI

    def __lt_abort(self):
        if self.bar_match not in [BAR.lt0, BAR.lt1]:
            return False
        if self._initial_tran.addr[31:12] == bint(0xfed43) and self.ral_utils.read_reg_field(block_name="ncevents", reg_name="LTCtrlSts", field_name="InACM",
                                      time=self._initial_tran.time) != 1:
            return True
        if self._initial_tran.addr[31:16] == bint(0xfed2) and self.ral_utils.read_reg_field(block_name="ncevents", reg_name="LTCtrlSts", field_name="Private",
                                      time=self._initial_tran.time) != 1:
            return True
        return False

    def __get_sai(self):
        if self.bar_match in [BAR.lt0, BAR.lt1] and self._initial_tran.opcode != IDI.OPCODES.enqueue:
            inject_fed43 = self._initial_tran.addr[31:12] == bint(0xfed43)
            inject_fed2 = self._initial_tran.addr[31:16] == bint(0xfed2)
            inject_fed8 = self._initial_tran.addr[31:16] == bint(0xfed8) and self.ral_utils.read_reg_field(block_name="ncevents", reg_name="LTCtrlSts", field_name="InACM", time=self._initial_tran.time) == 1
            if inject_fed43 or inject_fed2 or inject_fed8:
                return SAI.lt_sai
        if "dest_pid" in self.exp_sb_tran.keys():
            return self._get_sai(self.exp_sb_tran["dest_pid"])
        return self._sai

    def __get_sb_opcode(self, is_read):
        if self.bar_match == BAR.regbar and not self.is_abort:
            for i in range(0, 8):
                remap = self.ral_utils.read_reg_fields(block_name="ncdecs", reg_name=f"regbar_remap{i}", field_names=["Valid", "Convert", "PortID"], time=self._initial_tran.time)
                if remap["Valid"] == 1 and remap["Convert"] == 1 and remap["PortID"] == self.exp_sb_tran["dest_pid"][7:0]:
                    if is_read:
                        return SB.OPCODES.cr_rd
                    else:
                        return SB.OPCODES.cr_wr
        return self._get_sb_opcode(is_read)
