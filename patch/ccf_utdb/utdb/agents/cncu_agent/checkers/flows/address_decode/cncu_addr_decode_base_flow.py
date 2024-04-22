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

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.common.cncu_defines import IDI, SB, SAI, CFI, GLOBAL, UFI
from agents.cncu_agent.checkers.flows.ccf_nc_base_flow import CNCU_BASE_FLOW
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, UFI_TRANSACTION, CFI_TRANSACTION
from val_utdb_bint import bint

from agents.cncu_agent.utils.cncu_utils import REMAPPING


class CNCU_ADDR_DECODE_BASE_FLOW(CNCU_BASE_FLOW):

    def _set_act_flow(self, flow):
        if flow[0].opcode not in [IDI.OPCODES.port_in, IDI.OPCODES.port_out]:
            self._act_flow.append(flow[0])

            for tran in flow[1:]:
                if not (type(tran) is IDI_TRANSACTION and tran.is_snoop()) or len(self._act_flow) > 1:
                    self._act_flow.append(tran)
        else:
            super()._set_act_flow(flow)

    def _get_sb_src_pid(self, dest_pid):
        src_pid = SB.EPS.ncracu
        if (201 <= dest_pid[7:0] <= 223) or (224 <= dest_pid[15:8] <= 237):
            src_pid = 0xfefe
        return src_pid

    def _get_base_sb_offset(self, is_read, address, data, be):
        offset = bint(0x0)
        offset[15:2] = address[15:2]
        if is_read:
            if self._length == 0 and self._initial_tran.opcode != IDI.OPCODES.prd:
                sb_be = bint(0xff)
            else:
                len = bint(0x0)
                for n in range(self._length):
                    len[n] = 1
                sb_be = len << address[1:0]
            return offset, sb_be
        else:
            idi_be = bint(0x0)
            idi_be[31:0]  = self._byteen[0]
            idi_be[GLOBAL.cacheline_size_in_bytes-1:32] = self._byteen[1]
            sb_be = idi_be[GLOBAL.cacheline_size_in_bytes-1:int(address[5:0])] << address[1:0]
            return offset, sb_be

    def _get_cfi_address(self, is_read, address, idi_opcode):
        addr = bint(0x0)
        addr[64:6] = address[64:6]
        if is_read:
            if idi_opcode in [IDI.OPCODES.crd, IDI.OPCODES.crd_pref, IDI.OPCODES.ucrdf, IDI.OPCODES.drd, IDI.OPCODES.drd_opt, IDI.OPCODES.drd_ns, IDI.OPCODES.drd_pref, IDI.OPCODES.drd_opt_pref, IDI.OPCODES.rfo, IDI.OPCODES.rfo_pref, IDI.OPCODES.drdpte, IDI.OPCODES.crd_uc]:
                return addr
            return address

        return addr

    def _get_sai(self, dest_pid):
        if dest_pid == SB.EPS.sink:
            return DoNotCheck
        if dest_pid in SB.EPS.cores:
            return SAI.hw_cpu
        return self._sai

    def remap_dest_pid(self, dest_pid):
        if dest_pid in SB.EPS.cbo:
            i = SB.EPS.cbo.index(dest_pid)
            if i >= self.si.num_of_cbo:
                return SB.EPS.sink
            return SB.EPS.cbo[REMAPPING.logical2physical[i]]

        elif dest_pid in SB.EPS.all_core:
            i = SB.EPS.all_core.index(dest_pid)
            if self.si.num_of_cbo <= i <= 7:
                return SB.EPS.sink
            return SB.EPS.all_core[REMAPPING.logical2physical[i]]
        return dest_pid

    def _get_sb_wr_data(self):
        data = []
        exp_data = []
        for chunk in self._data:
            for byte in chunk:
                if byte is not None:
                    data.append(byte)
        data_ind = 0
        for n in range(8):
            if self.exp_sb_tran["be"][7:n] == 0:
                break
            if self.exp_sb_tran["be"][n] == 0:
                exp_data.append(0)
            else:
                exp_data.append(data[data_ind])
                data_ind+=1
        return exp_data

    def _get_cfi_read_data(self):
        return self._get_relevant_data_on_cl(self._data)

    def _get_relevant_data_on_cl(self, data):
        if self._length == 0:
            if self._initial_tran.opcode == IDI.OPCODES.prd:
                return [DoNotCheck, DoNotCheck]
            return data
        cfi_data = data[0] + data[1]
        idi_data = [None for j in range(GLOBAL.cacheline_size_in_bytes)]
        ind = int(self._initial_tran.addr[5:0])
        for i in range(self._length):
            if ind+i < GLOBAL.cacheline_size_in_bytes: # in case of read cross CL
                idi_data[ind+i] = cfi_data[ind+i]
        return [idi_data[0:32], idi_data[32:64]]

    def _additional_checks(self):
        if hasattr(self, "is_read") and self.is_read:
            self._check_arriving_order(before=[UFI_TRANSACTION(chunk=0, opcode=UFI.OPCODES.nc_data)],
                                       after=IDI_TRANSACTION(chunk=0))
            self._check_arriving_order(before=UFI_TRANSACTION(chunk=1, opcode=UFI.OPCODES.nc_data),
                                       after=IDI_TRANSACTION(chunk=1))
            self._check_arriving_order(before=[CFI_TRANSACTION(chunk=0, opcode=CFI.OPCODES.nc_data)],
                                       after=IDI_TRANSACTION(chunk=0))
            self._check_arriving_order(before=CFI_TRANSACTION(chunk=1, opcode=CFI.OPCODES.nc_data),
                                       after=IDI_TRANSACTION(chunk=1))

    def _set_expected_values(self):
        self.is_abort = False
        self.exp_idi_tran = dict()
        self.exp_sb_tran = dict()
        self.exp_ufi_tran = dict()
        self.exp_cfi_tran = dict()

    def _set_sb_abort(self, is_read):
        print("time: {}, uri: {} was sb aborted".format(self._initial_tran.get_time(), self._uri))
        self.exp_sb_tran["dest_pid"] = SB.EPS.ncevents
        self.exp_sb_tran["src_pid"] = SB.EPS.ncracu
        self.exp_sb_tran["offset"] = DoNotCheck
        self.exp_sb_tran["be"] = DoNotCheck
        self.exp_sb_tran["fid"] = 0x38
        self.exp_sb_tran["bar"] = 0x7

        self.exp_sb_tran["sai"] = DoNotCheck
        self.exp_sb_tran["wr_data"] = DoNotCheck

        if is_read:
            self.exp_sb_tran["opcode"] = SB.OPCODES.mem_rd
            self.exp_idi_tran["rd_data"] = self._data
        else:
            self.exp_sb_tran["opcode"] = SB.OPCODES.mem_wr


