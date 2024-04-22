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
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import SB, IDI, SAI, GLOBAL
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from val_utdb_bint import bint
from agents.cncu_agent.checkers.flows.address_decode.cncu_addr_decode_base_flow import CNCU_ADDR_DECODE_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, SB_TRANSACTION


class CNCU_FUNNYIO_0x2_0x5_FLOW(CNCU_ADDR_DECODE_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_0x2_0x5_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, addr=self.exp_idi_tran["address"])
        )

        if not self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull,
                                addr=self.exp_idi_tran["address"], module_id=self.exp_idi_tran["module_id"])
            )

            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=self.exp_idi_tran["address"], chunk=0),
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=self.exp_idi_tran["address"], chunk=1)
            )

        self._add_fsm_bubble(
            SB_TRANSACTION(opcode=self.exp_sb_tran["opcode"],
                           src_pid=self.exp_sb_tran["src_pid"],
                           dest_pid=self.exp_sb_tran["dest_pid"],
                           addr=self.exp_sb_tran["offset"],
                           byte_en=self.exp_sb_tran["be"],
                           fid=self.exp_sb_tran["fid"],
                           bar=self.exp_sb_tran["bar"],
                           sai=self.exp_sb_tran["sai"],
                           data=self.exp_sb_tran["wr_data"])
        )
        self._add_fsm_bubble(
            # need to add CMP opcode
            SB_TRANSACTION(src_pid=self.exp_sb_tran["dest_pid"], dest_pid=self.exp_sb_tran["src_pid"])
        )

        if self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp,
                                opcode=IDI.OPCODES.go,
                                module_id=self.exp_idi_tran["module_id"],
                                addr=self.exp_idi_tran["address"]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data,
                                addr=self.exp_idi_tran["address"],
                                chunk=0,
                                module_id=self.exp_idi_tran["module_id"],
                                data=self.exp_idi_tran["rd_data"][0]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data,
                                addr=self.exp_idi_tran["address"],
                                chunk=1,
                                module_id=self.exp_idi_tran["module_id"],
                                data=self.exp_idi_tran["rd_data"][1])
            )
        else:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                addr=self.exp_idi_tran["address"], module_id=self.exp_idi_tran["module_id"])
            )

    @staticmethod
    def is_new_flow(flow: list):
        return flow[0].opcode in [IDI.OPCODES.port_out, IDI.OPCODES.port_in] and flow[0].addr[31:28] in [0x2, 0x5]

    def _set_expected_values(self):
        super()._set_expected_values()
        self.is_read = self._initial_tran.opcode == IDI.OPCODES.port_in

        self.funnyio_type = self._initial_tran.addr[31:28]

        self.exp_idi_tran["module_id"] = self._module_id
        self.exp_idi_tran["address"] = self._initial_tran.addr

        is_untrusted_0x5 = self.funnyio_type == 0x5 and self._sai not in [SAI.sunpass, SAI.ucode]
        self.is_cr_sink = is_untrusted_0x5 and self.ral_utils.read_reg_field(block_name="ncdecs",
                                 reg_name="NCRADECS_OVRD",
                                 field_name="TRUSTED_PATH_OVRD",
                                 time=self._initial_tran.get_time()) == 0

        self.exp_sb_tran["offset"], self.exp_sb_tran["be"] = self.__get_sb_offset(self.is_read, self._initial_tran.addr, self._data, self._byteen)
        is_io_cross_dw = self.funnyio_type == 0x2 and\
                         self._initial_tran.addr[39:39] == 0 and \
                         CNCU_UTILS.is_cross_dw(self.exp_sb_tran["offset"], self.exp_sb_tran["be"], self.is_read,
                                                self._length, self._initial_tran.opcode)
        is_mmio_cross_qw = self.funnyio_type == 0x2 and \
                           self._initial_tran.addr[39:39] == 1 and \
                           CNCU_UTILS.is_cross_qw(self.exp_sb_tran["offset"], self.exp_sb_tran["be"], self.is_read,
                                                  self._length, self._initial_tran.opcode)
        is_cr_cross_qw = self.funnyio_type == 0x5 and \
                         CNCU_UTILS.is_cross_qw(self.exp_sb_tran["offset"], self.exp_sb_tran["be"], self.is_read,
                                                self._length, self._initial_tran.opcode)
        if is_io_cross_dw or is_mmio_cross_qw or is_cr_cross_qw:
            self.is_abort = True

        if not self.is_abort:
            self.exp_sb_tran["opcode"] = self.__get_sb_opcode(self._initial_tran.addr, self.funnyio_type, self._initial_tran.opcode)
            self.exp_sb_tran["cmp_opcode"] = (SB.OPCODES.cmpd if self.is_read else SB.OPCODES.cmp)
            self.exp_sb_tran["dest_pid"] = self.__get_sb_dest_pid(self._initial_tran.addr)
            self.exp_sb_tran["src_pid"] = self._get_sb_src_pid(self.exp_sb_tran["dest_pid"])
            self.exp_sb_tran["fid"] = self.__get_sb_fid(self._initial_tran.addr)
            self.exp_sb_tran["bar"] = self.__get_sb_bar(self._initial_tran.addr)
            self.exp_sb_tran["sai"] = self._get_sai(self.exp_sb_tran["dest_pid"])

            self.exp_sb_tran["wr_data"] = DoNotCheck
            if self.is_read:
                if is_untrusted_0x5:
                    self.exp_idi_tran["rd_data"] = [DoNotCheck, DoNotCheck] # nice to have - allow all '1 and all '0 only
                else:
                    self.exp_idi_tran["rd_data"] = self._data
            else:
                self.exp_sb_tran["wr_data"] = self._get_sb_wr_data()
        else:
            self._set_sb_abort(self.is_read)

    def __get_sb_fid(self, address):
        fid = bint(0)
        if self.funnyio_type in [0x2, 0x5] and address[38] == 1:
            fid = self.ral_utils.read_reg_field(block_name="ncuracu",
                                 reg_name="NcuGlobalFunnyIOOvr",
                                 field_name="FID",
                                 time=self._initial_tran.get_time())
        elif self.funnyio_type == 0x5:
            fid[2:0] = self._lp_id
            fid[7:3] = self._get_logical_module_id()[4:0]
        return fid

    def __get_sb_bar(self, address):
        bar = bint(0)
        if self.funnyio_type in [0x2, 0x5] and address[38] == 1:
            bar = self.ral_utils.read_reg_field(block_name="ncuracu",
                                 reg_name="NcuGlobalFunnyIOOvr",
                                 field_name="BAR",
                                 time=self._initial_tran.get_time())
        elif self.funnyio_type == 0x5:
            bar[2:0] = address[41:39] 
        return bar


    def __get_sb_opcode(self, address, funnyio_type, opcode):
        if funnyio_type == 0x1:
            return SB.OPCODES.cfg_wr if opcode == IDI.OPCODES.port_out else SB.OPCODES.cfg_rd
        if funnyio_type == 0x2:
            is_mmio = address[39:39] == 0x1
            if is_mmio:
                return SB.OPCODES.mem_wr if opcode == IDI.OPCODES.port_out else SB.OPCODES.mem_rd
            return SB.OPCODES.io_wr if opcode == IDI.OPCODES.port_out else SB.OPCODES.io_rd
        if funnyio_type == 0x5:
            return SB.OPCODES.cr_wr if opcode == IDI.OPCODES.port_out else SB.OPCODES.cr_rd

    def __get_sb_be(self):
        if self._initial_tran.opcode == IDI.OPCODES.port_out:
            for be in self.be:
                for byte in range(0, 64, 4):
                    if be[byte+7:byte] != 0:
                        return be[byte+7:byte]

    def __get_sb_dest_pid(self, address):
        dest_pid = bint(0x0)
        dest_pid[7:0] = address[23:16]
        dest_pid[11:8] = address[27:24]
        dest_pid[15:12] = address[37:34]

        if self.is_cr_sink:
            return SB.EPS.ncevents

        if self.is_read and dest_pid[7:0] > 200:
            master_read_pid = SB.get_read_master(dest_pid)
            return self.remap_dest_pid(master_read_pid)

        return self.remap_dest_pid(dest_pid)

    def __get_sb_offset(self, is_read, addr, data, be):
        offset, be = self._get_base_sb_offset(is_read, addr, data, be)
        if self.is_cr_sink:
            return GLOBAL.cr_sink_addr, be
        if addr[33] == 0:
            return offset, be
        offset[48:16] = self.ral_utils.read_reg_field(block_name="ncuracu",
                                 reg_name="NcuGlobalFunnyIOOvr",
                                 field_name="EXTRA_OFFSET",
                                 time=self._initial_tran.get_time())
        return offset, be

