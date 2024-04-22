#!/usr/bin/env python3.6.3a
#################################################################################################
# cncu_types.py
#
# Owner: ranzohar & mlugassi
# Creation Date:      5/2020
#
# ###############################################
#
# Description:
#
#################################################################################################
from enum import Enum

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import data_bytes_to_flat_data
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import BASE_TRANSACTION, DoNotCheck
from agents.cncu_agent.common.cncu_defines import CFI, IDI


class NC_TRANSACTION(BASE_TRANSACTION):

    def __init__(self, time=DoNotCheck, uri=DoNotCheck, opcode=None, addr=None, data=None, sai=None):
        self.time = time
        self.uri = uri
        self.addr = addr
        self.opcode = opcode
        self.data = data
        self.sai = sai

    def get_src(self):
        raise NotImplementedError()

    def get_dest(self):
        raise NotImplementedError()


class IDI_TRANSACTION(NC_TRANSACTION):

    def __init__(self, time=DoNotCheck, uri=DoNotCheck, lid=DoNotCheck, opcode=None, addr=None, data=None, sai=None,
                 module_id=None, lp_id=None, tran_type=None, length=None, byteen=None, chunk=None, int_data=None, unit=None):
        super().__init__(time=time, uri=uri, opcode=opcode, addr=addr, data=data, sai=sai)
        self.lid = lid
        self.tran_type = tran_type
        self.module_id = module_id
        self.lp_id = lp_id
        self.length = length
        self.byteen = byteen
        self.chunk = chunk
        self.int_data = int_data
        self.unit = unit

    def _get_attr_to_print_in_hex(self):
        return ["addr", "byteen", "sai"]

    def _get_attr_to_print_in_bytes(self):
        return ["data"]

    def get_uri(self):
        return self.uri

    def get_unit(self):
        return self.unit
    
    def get_time(self):
        return self.time

    def get_src(self):
        return self.module_id

    def get_dest(self):
        return None

    def is_snoop(self):
        snoop_opcode_list = ["SnpCode", "CDFSnpCode", "SpecSnpCode", "SpecCDFSnpCode", "SnpData", "CDFSnpData",
                             "SpecSnpData", "SpecCDFSnpData", "SnpInv", "CDFSnpInv", "SpecSnpInv", "SpecCDFSnpInv",
                             "SelfSnpInv", "CDFSelfSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv",
                             "CDFBackInv", "SpecBackInv", "SpecCDFBackInv", "SnpCurr", "CDFSnpCurr", "SnpClean"]
        snoop_response_opcode_list = ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI",
                                      "RspSFwdFE", "RspNack", "RspIHitFSE", "RspIFwdFE", "RspVhitV", "RspVFwdV", "RspEFFFwdMO"]
        all_snoop_opcodes_list = snoop_opcode_list + snoop_response_opcode_list

        return "_SNP_" in self.lid or self.tran_type in [IDI.TYPES.c2u_rsp, IDI.TYPES.u2c_req] and [True for opcode in all_snoop_opcodes_list if opcode.lower() == self.opcode.lower()]

    def _get_needed_attributes(self):
        needed_attrs = None

        if self.tran_type in [IDI.TYPES.u2c_req, IDI.TYPES.u2c_rsp, IDI.TYPES.u2c_data]:
            needed_attrs = ["tran_type", "addr", "module_id"]

            if self.tran_type == IDI.TYPES.u2c_req:
                needed_attrs += ["opcode"]
                if self.opcode in [IDI.OPCODES.int_logical, IDI.OPCODES.int_physical,
                                   IDI.OPCODES.lt_write, IDI.OPCODES.vlw, IDI.OPCODES.dpt]:
                    needed_attrs += ["int_data"]
            elif self.tran_type == IDI.TYPES.u2c_rsp:
                needed_attrs += ["opcode"]
            elif self.tran_type == IDI.TYPES.u2c_data:
                needed_attrs += ["data", "chunk"]

        elif self.tran_type is None or self.tran_type is DoNotCheck:
            needed_attrs = ["tran_type"]

        return needed_attrs


class CFI_TRANSACTION(NC_TRANSACTION):

    def __init__(self, time=DoNotCheck, uri=DoNotCheck,uri_lid=None,protocol_id=None, trace_packet=None, addr=None, opcode=None, rsp_id=None,
                 dest_id=None, data=None, interface=None, pkt_type=None, vc_id=None,
                 length=None, sai=None, chunk=None,
                 param_a=None, byteen=None, msg_type=None, rctrl=None, rtid=None, tee=None, mem_loc=None, crnid=None,
                 cdnid=None, a_par=None, d_par=None, i_par=None, posion=None, pcls=None):
        super().__init__(time=time, uri=uri, opcode=opcode, addr=addr, data=data, sai=sai)
        self.uri_lid = uri_lid
        self.rsp_id = rsp_id
        self.protocol_id = protocol_id
        self.dest_id = dest_id
        self.interface = interface
        self.pkt_type = pkt_type
        self.vc_id = vc_id
        self.length = length
        self.chunk = chunk
        self.param_a = param_a
        self.msg_type = msg_type
        self.rctrl = rctrl
        self.byteen = byteen
        self.trace_packet = trace_packet
        self.rtid = rtid
        self.tee = tee
        self.mem_loc = mem_loc
        self.crnid = crnid
        self.cdnid = cdnid
        self.a_par = a_par
        self.d_par = d_par
        self.i_par = i_par
        self.posion = posion
        self.pcls = pcls
        if self.data is not None:
            self.flat_data = data_bytes_to_flat_data(self.data)
        # elif self.flat_data is not None:
        #     self.data = str_to_bytes(hex(self.flat_data)[2:])

    def get_uri(self):
        return self.uri

    def get_time(self):
        return self.time

    def get_src(self):
        return self.rsp_id

    def get_dest(self):
        return self.dest_id

    def _get_attr_to_print_in_hex(self):
        return ["addr", "byteen", "sai", "msg_type", "rtid", "rctrl", "flat_data"]

    def _get_attr_to_print_in_bytes(self):
        return ["data"]

    def _get_needed_attributes(self):
        needed_attrs = ["interface", "pkt_type", "opcode", "dest_id", "vc_id", "rtid"]

        if self.pkt_type == CFI.PKT_TYPE.sa_d:
            needed_attrs += ["addr", "rsp_id", "data", "flat_data", "chunk", "rctrl", "mem_loc", "tee",
                             "crnid", "clos", "a_par", "d_par", "posion"]
        elif self.pkt_type == CFI.PKT_TYPE.pw:
            needed_attrs += ["sai", "addr", "rsp_id", "data", "flat_data", "byteen", "chunk", "rctrl",
                             "tee", "crnid", "a_par", "d_par", "i_par", "posion"]
        elif self.pkt_type == CFI.PKT_TYPE.pr:
            needed_attrs += ["sai", "addr", "rsp_id", "length", "data", "flat_data", "chunk", "rctrl", "tee",
                             "crnid", "a_par"]
        elif self.pkt_type == CFI.PKT_TYPE.sr_cd:
            needed_attrs += ["pcls", "data", "flat_data", "chunk", "rctrl", "cdnid", "tee", "d_par", "posion"]
        elif self.pkt_type == CFI.PKT_TYPE.ncm:
            needed_attrs += ["msg_type", "param_a", "rsp_id", "data", "flat_data", "chunk", "rctrl",
                             "crnid", "cdnid", "sai", "d_par", "posion"]
        elif self.pkt_type == CFI.PKT_TYPE.sr_u:
            needed_attrs += ["pcls", "tee", "cdnid"]

        elif self.get_dest() in [None, DoNotCheck]:
            needed_attrs = ["dest_id"]

        return needed_attrs


class UFI_TRANSACTION(NC_TRANSACTION):

    def __init__(self, time=DoNotCheck, uri=DoNotCheck,uri_lid=None,protocol_id=None, trace_packet=None, addr=None, opcode=None, data=None, interface=None, pkt_type=None, vc_id=None,
                 length=None, sai=None, chunk=None,
                 param_a=None, byteen=None, msg_type=None, rtid=None, tee=None, mem_loc=None, crnid=None,
                 cdnid=None, a_par=None, d_par=None, i_par=None, poison=None, pcls=None):
        super().__init__(time=time, uri=uri, opcode=opcode, addr=addr, data=data, sai=sai)
        self.uri_lid = uri_lid
        self.protocol_id = protocol_id
        self.interface = interface
        self.pkt_type = pkt_type
        self.vc_id = vc_id
        self.length = length
        self.chunk = chunk
        self.param_a = param_a
        self.msg_type = msg_type
        self.byteen = byteen
        self.trace_packet = trace_packet
        self.rtid = rtid
        self.tee = tee
        self.mem_loc = mem_loc
        self.crnid = crnid
        self.cdnid = cdnid
        self.a_par = a_par
        self.d_par = d_par
        self.i_par = i_par
        self.poison = poison
        self.pcls = pcls
        if self.data is None:
            self.flat_data = None
        elif self.data == DoNotCheck or self.data == [DoNotCheck, DoNotCheck]:
            self.flat_data = DoNotCheck
        else:
            self.flat_data = data_bytes_to_flat_data(self.data)

    def get_uri(self):
        return self.uri

    def get_time(self):
        return self.time

    def _get_attr_to_print_in_hex(self):
        return ["addr", "byteen", "sai", "msg_type", "rtid", "rctrl", "flat_data"]

    def _get_attr_to_print_in_bytes(self):
        return ["data"]

    def _get_needed_attributes(self):
        needed_attrs = ["interface", "pkt_type", "opcode", "vc_id", "rtid"]

        if self.pkt_type == CFI.PKT_TYPE.sa_d:
            needed_attrs += ["addr", "data", "flat_data", "chunk" "mem_loc", "tee",
                             "crnid", "clos", "a_par", "d_par", "poison"]
        elif self.pkt_type == CFI.PKT_TYPE.pw:
            needed_attrs += ["sai", "addr", "data", "flat_data", "byteen", "chunk",
                             "tee", "crnid", "a_par", "d_par", "i_par", "poison"]
        elif self.pkt_type == CFI.PKT_TYPE.pr:
            needed_attrs += ["sai", "addr", "length", "data", "flat_data", "chunk", "tee",
                             "crnid", "a_par"]
        elif self.pkt_type == CFI.PKT_TYPE.sr_cd:
            needed_attrs += ["pcls", "data", "flat_data", "chunk", "cdnid", "tee", "d_par", "poison"]
        elif self.pkt_type == CFI.PKT_TYPE.ncm:
            needed_attrs += ["msg_type", "param_a", "data", "flat_data", "chunk",
                             "crnid", "cdnid", "sai", "d_par", "poison"]
        elif self.pkt_type == CFI.PKT_TYPE.sr_u:
            needed_attrs += ["pcls", "tee", "cdnid"]

        elif self.get_dest() in [None, DoNotCheck]:
            needed_attrs = ["dest_id"]

        return needed_attrs


class SB_TRANSACTION(NC_TRANSACTION):

    def __init__(self, time=DoNotCheck, start_time=DoNotCheck, uri=DoNotCheck, msg_type=None, src_pid=None, dest_pid=None, opcode=None,
                 tag=None, misc=None, eh=None, byte_en=None, fid=None, bar=None, addr_len=None, rsp=None,
                 sai=None, addr=None, data=None):
        super().__init__(time=time, uri=uri, opcode=opcode, addr=addr, data=data, sai=sai)
        self.start_time = start_time
        self.msg_type = msg_type
        self.src_pid = src_pid
        self.dest_pid = dest_pid
        self.tag = tag
        self.misc = misc
        self.eh = eh
        self.byte_en = byte_en
        self.fid = fid
        self.bar = bar
        self.addr_len = addr_len
        self.rsp = rsp
        self.treated = False
        self.flat_data = data_bytes_to_flat_data(self.data) if self.data not in [None, DoNotCheck] else None

    def get_uri(self):
        return self.uri

    def get_time(self):
        return self.time

    def get_end_time(self):
        return self.time

    def get_start_time(self):
        return self.start_time

    def get_src(self):
        return self.src_pid

    def get_dest(self):
        return self.dest_pid

    def _get_attr_to_print_in_hex(self):
        return ["addr", "byteen", "src_pid", "dest_pid", "sai"]

    def _get_attr_to_print_in_bytes(self):
        return ["data"]


class SEQ_TRK_ITEM:
    def __init__(self, time, parent_name, seq_name, cmd, addr, sqr_name, env_phase, seq_status):
        self.time = time
        self.parent_name = parent_name
        self.seq_name = seq_name
        self.cmd = cmd
        self.addr = addr
        self.sqr_name = sqr_name
        self.env_phase = env_phase
        self.seq_status = seq_status

    def get_time(self):
        return self.time


class ATOMIC_ACTION_TYPE(Enum):
    DRAM_ACCESS = 0
    MMIO_ACCESS = 1
    CFG_ACCESS = 2
    INTERRUPT_ACCESS = 3


class LOCK_INFO:

    def __init__(self, lock_flow):
        self.lock_uri = lock_flow[0].get_uri()
        self.module_id = lock_flow[0].module_id if type(lock_flow[0]) is IDI_TRANSACTION else None
        self.lp_id = lock_flow[0].lp_id if type(lock_flow[0]) is IDI_TRANSACTION else None
        self.stop_req3_uri = None
        self.stop_req3_time = None
        self.unlock_time = None
        self.unlock_uri = None
        self.required_nc_during_lock = None
        self.atomic_actions = list()
        if self.from_ccf():
            self.lock_time = lock_flow[-1].get_time()
        else:
            self.lock_time = lock_flow[-2].get_time()

    def update_stop_req3_details(self, stop_req3):
        if not self.from_ccf():
            self.stop_req3_uri = stop_req3[0].get_uri()
            self.stop_req3_time = stop_req3[0].get_time()

    def update_unlock_details(self, unlock_flow):
        self.unlock_uri = unlock_flow[0].get_uri()
        if self.from_ccf():
            self.unlock_time = unlock_flow[0].get_time()
        else:
            self.unlock_time = unlock_flow[-2].get_time()

    def from_ccf(self):
        return not (self.module_id is None and self.lp_id is None)
