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
from agents.cncu_agent.common.cncu_defines import IDI, UFI
from agents.cncu_agent.checkers.flows.address_decode.cncu_addr_decode_base_flow import CNCU_ADDR_DECODE_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UFI_TRANSACTION


class CNCU_CFG_BASE_FLOW(CNCU_ADDR_DECODE_BASE_FLOW):

    def _set_flow_fsm(self):
        self._add_fsm_bubble(
            IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_req, addr=self.exp_idi_tran["address"])
        )

        if not self.is_read:
            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.writepull,
                                addr=DoNotCheck, module_id=self.exp_idi_tran["module_id"])
            )

            self._add_fsm_bubble(
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=DoNotCheck, chunk=0),
                IDI_TRANSACTION(tran_type=IDI.TYPES.c2u_data, addr=DoNotCheck, chunk=1)
            )

        self._add_fsm_bubble(
            UFI_TRANSACTION(interface=UFI.IFCS.data,
                            opcode=self.exp_ufi_tran["opcode"],
                            crnid=UFI.EPS.ccf,
                            cdnid=DoNotCheck, #TODO: ranzohar - ask gadi to write it in HAS
                            chunk=0,
                            addr=self.exp_ufi_tran["address"],
                            pkt_type=self.exp_ufi_tran["pkt_type"],
                            vc_id=self.exp_ufi_tran["vc_id"],
                            sai=self.exp_ufi_tran["sai"],
                            length=self.exp_ufi_tran["length"],
                            rtid=DoNotCheck, tee=DoNotCheck, a_par=DoNotCheck, byteen=DoNotCheck, d_par=DoNotCheck, i_par=DoNotCheck, poison=DoNotCheck, #TODO: ranzohar - add support
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
                            rtid=DoNotCheck, tee=DoNotCheck, a_par=DoNotCheck, byteen=DoNotCheck, d_par=DoNotCheck, i_par=DoNotCheck, poison=DoNotCheck,  # TODO: ranzohar - add support
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
                                rtid=DoNotCheck, tee=DoNotCheck, d_par=DoNotCheck, poison=DoNotCheck, pcls=DoNotCheck,  # TODO: ranzohar - add support
                                data=DoNotCheck),
                UFI_TRANSACTION(interface=UFI.IFCS.data,
                                opcode=UFI.OPCODES.nc_data,
                                cdnid=UFI.EPS.ccf,
                                chunk=1,
                                pkt_type=UFI.PKT_TYPE.sr_cd,
                                vc_id=UFI.VC_IDS.vc0_drs,
                                rtid=DoNotCheck, tee=DoNotCheck, d_par=DoNotCheck, poison=DoNotCheck, pcls=DoNotCheck,  # TODO: ranzohar - add support
                                data=DoNotCheck)
            )
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
            self._add_fsm_bubble(
                UFI_TRANSACTION(interface=UFI.IFCS.rsp,
                                cdnid=UFI.EPS.ccf,
                                opcode=UFI.OPCODES.nccmpu,
                                pkt_type=UFI.PKT_TYPE.sr_u,
                                rtid=DoNotCheck, tee=DoNotCheck, pcls=DoNotCheck,  # TODO: ranzohar - add support
                                vc_id=UFI.VC_IDS.vc0_ndr)
            )
            self._add_fsm_bubble([
                IDI_TRANSACTION(tran_type=IDI.TYPES.u2c_rsp, opcode=IDI.OPCODES.go,
                                addr=DoNotCheck, module_id=self.exp_idi_tran["module_id"])
            ])

    def _get_cfi_cfg_opcode(self, is_read):
        return UFI.OPCODES.nc_cfg_rd if is_read else UFI.OPCODES.nc_cfg_wr

    def _get_cfi_cfg_pkt_type(self, is_read):
        return UFI.PKT_TYPE.pr if is_read else UFI.PKT_TYPE.pw
