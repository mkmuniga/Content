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
from agents.cncu_agent.common.cncu_defines import IDI, CFI, GLOBAL
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UPI_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_FUNNYIO_SUB_DECODE_FLOW(CCF_NC_ADDR_DECODE_BASE_FLOW):

    def checker_enabled(self):
        return self.si.funnyio_sub_decode_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req)
        )

        if not self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull,
                                addr=DoNotCheck, module_id=self._module_id)
            )

            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=DoNotCheck, chunk=0),
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=DoNotCheck, chunk=1)
            )

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
                                opcode=CFI.OPCODES.nccmpu,
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
                                data=self.exp_cfi_tran["wr_data"][0]),
                UPI_TRANSACTION(interface=CFI.IFCS.tx_data,
                                opcode=CFI.OPCODES.nc_data,
                                dest_id=CFI.EPS.ccf,
                                chunk=1,
                                pkt_type=CFI.PKT_TYPE.sr_cd,
                                vc_id=CFI.VC_IDS.vc0_drs,
                                data=self.exp_cfi_tran["wr_data"][1])
            )

        if self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                module_id=self._module_id, addr=DoNotCheck),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=DoNotCheck, chunk=0,
                                module_id=self._module_id, data=self.exp_idi_tran["rd_data"][0]),
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_data, addr=DoNotCheck, chunk=1,
                                module_id=self._module_id, data=self.exp_idi_tran["rd_data"][1]),
                append_to_last_bubble=True
            )
        else:
            self._add_fsm_bubble([
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                addr=DoNotCheck, module_id=self._module_id)
            ])

    @staticmethod
    def is_new_flow(flow: list):
        is_funnyio = flow[0].opcode in [IDI.OPCODES.port_out, IDI.OPCODES.port_in]
        is_creg_pla = CNCU_UTILS.is_creg_pla_flow(flow)
        is_other_lt = is_funnyio and flow[0].addr[31:20] == 0xFED and flow[0].addr[19:16] not in [0x6, 0x7]
        return is_funnyio and not is_creg_pla and not is_other_lt

    def _set_expected_values(self):
        self.is_read = self._initial_tran.opcode == IDI.OPCODES.port_in
        self.exp_idi_tran = dict()
        self.exp_cfi_tran = dict()

        self.exp_cfi_tran["rsp_id"] = CFI.EPS.ccf
        self.exp_cfi_tran["dest_id"] = CFI.EPS.ioc0
        self.exp_cfi_tran["opcode"] = self.__get_cfi_io_opcode(self.is_read)
        self.exp_cfi_tran["address"] = self._get_cfi_address(self.is_read, self._initial_tran.addr[GLOBAL.addr_width-1:0], self._initial_tran.opcode)
        self.exp_cfi_tran["pkt_type"] = self.__get_cfi_io_pkt_type(self.is_read)
        self.exp_cfi_tran["sai"] = self.__get_cfi_io_sai()
        self.exp_cfi_tran["length"] = self._length if self.is_read else None
        self.exp_cfi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                  time=self._start_time,
                                                                  pkt_type=self.exp_cfi_tran["pkt_type"])
        self.exp_cfi_tran["vc_id"] = CFI.VC_IDS.vc0_ncs
        self.exp_cfi_tran["vc_id"] = self.__get_cfi_vc_id()
        self.exp_cfi_tran["wr_data"] = [DoNotCheck, DoNotCheck]
        if self.is_read:
            self.exp_idi_tran["rd_data"] = self._get_cfi_read_data()
        else:
            self.exp_cfi_tran["wr_data"] = self._data

    def __get_cfi_io_opcode(self, is_read):
        if is_read:
            return CFI.OPCODES.nc_io_rd
        return CFI.OPCODES.nc_io_wr

    def __get_cfi_io_pkt_type(self, is_read):
        if is_read:
            return CFI.PKT_TYPE.pr
        return CFI.PKT_TYPE.pw

    def __get_cfi_io_sai(self):
        return self._sai

    def __get_cfi_vc_id(self):
        return CFI.VC_IDS.vc0_ncs

