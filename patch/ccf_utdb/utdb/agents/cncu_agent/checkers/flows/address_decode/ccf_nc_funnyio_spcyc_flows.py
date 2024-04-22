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
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_FUNNYIO_SPCYC_FLOW(CCF_NC_ADDR_DECODE_BASE_FLOW):

    def checker_enabled(self):
        return self.si.spcyc_chk_en

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, addr=DoNotCheck)
        )

        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data,
                            opcode=CFI.OPCODES.nc_msg_s,
                            msg_type=CFI.MSG_TYPE.shutdown,
                            param_a=0x0,
                            rsp_id=CFI.EPS.ccf,
                            dest_id=CFI.EPS.ioc0,
                            chunk=0,
                            pkt_type=self.exp_cfi_tran["pkt_type"],
                            vc_id=CFI.VC_IDS.vc0_ncs,
                            rctrl=self.exp_cfi_tran["rctrl"],
                            data=self.exp_cfi_tran["wr_data"][0]),
            UPI_TRANSACTION(interface=CFI.IFCS.rx_data,
                            opcode=CFI.OPCODES.nc_msg_s,
                            msg_type=CFI.MSG_TYPE.shutdown,
                            param_a=0x0,
                            rsp_id=CFI.EPS.ccf,
                            dest_id=CFI.EPS.ioc0,
                            chunk=1,
                            pkt_type=self.exp_cfi_tran["pkt_type"],
                            vc_id=CFI.VC_IDS.vc0_ncs,
                            rctrl=self.exp_cfi_tran["rctrl"],
                            data=self.exp_cfi_tran["wr_data"][1])
            )
        self._add_fsm_bubble(
            UPI_TRANSACTION(interface=CFI.IFCS.tx_rsp,
                            opcode=CFI.OPCODES.nccmpu,
                            dest_id=CFI.EPS.ccf,
                            pkt_type=CFI.PKT_TYPE.sr_u,
                            vc_id=CFI.VC_IDS.vc0_ndr)
        )

        self._add_fsm_bubble([
            IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=DoNotCheck,
                            module_id=self._module_id, addr=DoNotCheck)
        ])

    @staticmethod
    def is_new_flow(flow: list):
        return type(flow[0]) == IDI_TRANSACTION and \
               CNCU_UTILS.is_flow_reached_nc(flow) and \
               flow[0].opcode == IDI.OPCODES.spcyc

    def _set_expected_values(self):
        super()._set_expected_values()
        exp_data = [0 for j in range(GLOBAL.cacheline_size_in_bytes)]
        self.exp_cfi_tran["wr_data"] = [exp_data[0:32], exp_data[32:64]]
        self.exp_cfi_tran["pkt_type"] = CFI.PKT_TYPE.ncm
        self.exp_cfi_tran["rctrl"] = CNCU_UTILS.get_nc_flow_rctrl(ral_utils=self.ral_utils,
                                                                  time=self._start_time,
                                                                  pkt_type=self.exp_cfi_tran["pkt_type"])


