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
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES
from val_utdb_bint import bint
from agents.cncu_agent.checkers.flows.address_decode.ccf_nc_addr_decode_base_flow import CCF_NC_ADDR_DECODE_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, SB_TRANSACTION


class CCF_NC_FUNNYIO_0x6_FLOW(CCF_NC_ADDR_DECODE_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_0x6_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req)
        )

        self._add_fsm_bubble(
            SB_TRANSACTION(opcode=self.exp_sb_tran["opcode"],
                           src_pid=self.exp_sb_tran["src_pid"],
                           dest_pid=self.exp_sb_tran["dest_pid"],
                           addr=self.exp_sb_tran["offset"],
                           fid=self.exp_sb_tran["fid"],
                           bar=self.exp_sb_tran["bar"],
                           sai=self.exp_sb_tran["sai"],
                           byte_en=self.exp_sb_tran["be"])
        )
        self._add_fsm_bubble(
            SB_TRANSACTION(opcode=self.exp_sb_tran["cmp_opcode"],
                           src_pid=self.exp_sb_tran["dest_pid"],
                           dest_pid=self.exp_sb_tran["src_pid"],
                           data=self.exp_sb_tran["data"])
        )

        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                            addr=self.exp_idi_tran["address"], module_id=self.exp_idi_tran["module_id"]),
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=self.exp_idi_tran["address"], chunk=0,
                            module_id=self.exp_idi_tran["module_id"], data=self.exp_idi_tran["rd_data"][0]),
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=self.exp_idi_tran["address"], chunk=1,
                            module_id=self.exp_idi_tran["module_id"], data=self.exp_idi_tran["rd_data"][1])
        )

    @staticmethod
    def is_new_flow(flow: list):
        return flow[0].opcode == IDI.OPCODES.port_in and flow[0].addr[31:28] == 0x6 and \
               not CNCU_UTILS.is_creg_pla_flow(flow)

    def _set_expected_values(self):
        self.exp_idi_tran = dict()
        self.exp_sb_tran = dict()

        self.exp_idi_tran["module_id"] = self._module_id
        self.exp_idi_tran["address"] = self._initial_tran.addr

        self.pla_reg = self.vcr_pla_handler.get_pla_reg(self._initial_tran.addr, self._initial_tran.get_time())

        self.exp_sb_tran = dict()

        len = bint(0x0)
        for n in range(self._length):
            len[n] = 1
        self.exp_sb_tran["be"] = len << self._initial_tran.addr[1:0]
        self.exp_sb_tran["src_pid"] = SB.EPS.ncracu
        self.exp_sb_tran["dest_pid"] = SB.EPS.ncevents
        self.exp_sb_tran["data"] = DoNotCheck
        self.exp_sb_tran["offset"] = DoNotCheck
        self.exp_sb_tran["cmp_opcode"] = SB.OPCODES.cmp

        exp_data = bint(0x0)
        if self.pla_reg is not None:
            exp_data[37:34] = self.pla_reg.port_id[15:12]
            if self.pla_reg.valid == 1:
                exp_data[31:28] = 0x5
            exp_data[27:16] = self.pla_reg.port_id[11:0]
            exp_data[15:2] = self.pla_reg.reg_offset[15:2]
            exp_data[1:1] = self.pla_reg.valid
            if self.pla_reg.valid == 1:
                exp_data[0:0] = self.pla_reg.trusted
            if self._sai in [SAI.ucode, SAI.sunpass]:
                self.exp_sb_tran["cmp_opcode"] = SB.OPCODES.cmpd
                self.exp_sb_tran["data"] = self.__get_sb_exp_data(exp_data)
        else:
            self.exp_sb_tran["cmp_opcode"] = SB.OPCODES.cmpd
            # self.exp_sb_tran["offset"] = GLOBAL.cr_sink_addr
            self.exp_sb_tran["data"] = self.__get_sb_exp_data(bint(0x0))

        self.exp_sb_tran["opcode"] = DoNotCheck

        self.exp_sb_tran["fid"] = DoNotCheck
        self.exp_sb_tran["bar"] = DoNotCheck
        self.exp_sb_tran["sai"] = self._sai

        self.exp_idi_tran["rd_data"] = self._data

    def __get_sb_exp_data(self, exp_data):
        data = []
        i = 0
        for j in range(8):
            if self.exp_sb_tran["be"][7:j] == 0:
                break
            data.append(exp_data[i + 7:i])
            i += 8
        return data
