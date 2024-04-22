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
from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import DoNotCheck
from agents.cncu_agent.common.cncu_defines import SB, IDI, GLOBAL, SAI
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES
from val_utdb_bint import bint
from agents.cncu_agent.checkers.flows.address_decode.ccf_nc_addr_decode_base_flow import CCF_NC_ADDR_DECODE_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, SB_TRANSACTION


class CCF_NC_FUNNYIO_0x4_FLOW(CCF_NC_ADDR_DECODE_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_0x4_chk_en

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
                           fid=self.exp_sb_tran["fid"],
                           bar=self.exp_sb_tran["bar"],
                           sai=self.exp_sb_tran["sai"],
                           data=self.exp_sb_tran["wr_data"],
                           byte_en=self.exp_sb_tran["be"])
        )
        self._add_fsm_bubble(
            # need to add CMP opcode
            SB_TRANSACTION(src_pid=self.exp_sb_tran["dest_pid"], dest_pid=self.exp_sb_tran["src_pid"])
        )

        if self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                addr=self.exp_idi_tran["address"], module_id=self.exp_idi_tran["module_id"]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=self.exp_idi_tran["address"], chunk=0,
                                module_id=self.exp_idi_tran["module_id"], data=self.exp_idi_tran["rd_data"][0]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=self.exp_idi_tran["address"], chunk=1,
                                module_id=self.exp_idi_tran["module_id"], data=self.exp_idi_tran["rd_data"][1])
            )
        else:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                addr=self.exp_idi_tran["address"], module_id=self.exp_idi_tran["module_id"])
            )

    @staticmethod
    def is_new_flow(flow: list):
        return flow[0].opcode in [IDI.OPCODES.port_out, IDI.OPCODES.port_in] and flow[0].addr[31:28] == 0x4

    def _set_expected_values(self):
        self.exp_idi_tran = dict()
        self.exp_sb_tran = dict()

        self.is_read = self._initial_tran.opcode == IDI.OPCODES.port_in

        self.exp_idi_tran["module_id"] = self._module_id
        self.exp_idi_tran["address"] = self._initial_tran.addr

        self.pla_reg = self.vcr_pla_handler.get_pla_reg(self._initial_tran.addr, self._initial_tran.get_time())
        self.exp_sb_tran = dict()
        self.exp_sb_tran["opcode"] = self.__get_sb_opcode(self._initial_tran.opcode)
        self.exp_sb_tran["cmp_opcode"] = (SB.OPCODES.cmpd if self.is_read else SB.OPCODES.cmp)

        sai = self._sai
        self.exp_sb_tran["bar"] = self.__get_sb_bar()

        if self.is_read:
            len = bint(0x0)
            for n in range(self._length):
                len[n] = 1
            self.exp_sb_tran["be"] = len << self._initial_tran.addr[1:0]
        else:
            be = self.__get_wr_sb_be()
            self.exp_sb_tran["be"] = be << self._initial_tran.addr[1:0]

        self.exp_sb_tran["wr_data"] = DoNotCheck
        self.exp_sb_tran["rd_data"] = DoNotCheck
        if self.pla_reg is not None:
            invalid_sai = (sai not in [SAI.ucode, SAI.sunpass] or (sai == SAI.ucode and self.pla_reg.trusted == 1)) and self.ral_utils.read_reg_field(block_name="ncdecs",
                                 reg_name="NCRADECS_OVRD",
                                 field_name="TRUSTED_PATH_OVRD",
                                 time=self._initial_tran.get_time()) == 0
            invalid_addr = self.pla_reg.valid == 0
            is_cr_sink = invalid_sai or invalid_addr
            if is_cr_sink:
                self.exp_sb_tran["offset"] = GLOBAL.cr_sink_addr
                self.exp_sb_tran["fid"] = DoNotCheck
            else:
                self.exp_sb_tran["offset"] = self.pla_reg.reg_offset
                if self._initial_tran.addr[2] == 1:
                    self.exp_sb_tran["offset"] += 0x4

                lp_id_xor = self._initial_tran.addr[27:25]
                self.exp_sb_tran["fid"] = self.__get_sb_fid(lp_id_xor)

            self.exp_sb_tran["dest_pid"] = self.__get_sb_dest_pid(self.is_read, is_cr_sink)
            self.exp_sb_tran["src_pid"] = self._get_sb_src_pid(self.exp_sb_tran["dest_pid"])

            if self.is_read:
                if sai not in [SAI.ucode, SAI.sunpass]:
                    self.exp_idi_tran["rd_data"] = [DoNotCheck, DoNotCheck] # nice to have - allow all '1 and all '0 only
                else:
                    self.exp_idi_tran["rd_data"] = self._data
                if is_cr_sink:
                    self.exp_sb_tran["rd_data"] = self.__create_cr_sink_exp_data()
            else:
                self.exp_sb_tran["wr_data"] = self._get_sb_wr_data()
        else:
            self.exp_sb_tran["offset"] = GLOBAL.cr_sink_addr
            self.exp_sb_tran["src_pid"] = SB.EPS.ncracu
            self.exp_sb_tran["dest_pid"] = SB.EPS.ncevents
            self.exp_sb_tran["fid"] = DoNotCheck

            if self.is_read:
                self.exp_sb_tran["rd_data"] = self.__create_cr_sink_exp_data()
                self.exp_idi_tran["rd_data"] = self._data
            else:
                self.exp_sb_tran["wr_data"] = self._get_sb_wr_data()
        self.exp_sb_tran["sai"] = self._get_sai(self.exp_sb_tran["dest_pid"])

    def __get_sb_dest_pid(self, is_read, is_cr_sink):
        if is_cr_sink:
            return SB.EPS.ncevents
        if is_read and self.pla_reg.port_id[7:0] > 200:
            read_master = SB.get_read_master(self.pla_reg.port_id)
            return self.remap_dest_pid(read_master)
        return self.remap_dest_pid(self.pla_reg.port_id)


    def __get_sb_fid(self, lp_id_xor):
        fid = bint(0)
        fid[2:0] = self._lp_id ^ lp_id_xor
        fid[7:3] = self._get_logical_module_id()
        return fid


    def __get_sb_bar(self):
        bar = bint(0)
        bar[1:0] = UNIQUE_DEFINES.ccf_id
        return bar


    def __get_sb_opcode(self, opcode):
        return SB.OPCODES.cr_wr if opcode == IDI.OPCODES.port_out else SB.OPCODES.cr_rd

    def __get_wr_sb_be(self):
        for be in self._byteen:
            for byte in range(0, 64, 4):
                if be[byte+3:byte] != 0:
                    return be[byte+7:byte]

    def __create_cr_sink_exp_data(self):
        data = []
        for i in range(self.exp_sb_tran["be"]):
            data.append(0)
        return data