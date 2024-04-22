#!/usr/bin/env python3.6.3
from agents.ccf_common_base.uxi_utils import UXI_UTILS
from val_utdb_components import val_utdb_object

from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES


class stable_registers():
   def __init__(self):
        self.ymm_mask = None
        self.mktme_mask = None


class ccf_flow_point(val_utdb_object):
    def __init__(self):
        self.unit = None
        self.interface = None
        self.time = None
        self.type = None

    def print_flow_point(self):
        print("Time:",self.time,"Unit: ",self.unit," Interface: ",self.interface)

class ccf_reject(val_utdb_object):
    def __init__(self):
        self.time = None
        self.reject_reason = None
        self.llc_state = None
        self.arbcommand = None
        self.is_ismq = None

    def new_recect(self, time, reject_reason, llc_state, arbcommand):
        self.time = time
        self.reject_reason = reject_reason
        self.llc_state = llc_state
        self.arbcommand = arbcommand

    def rejected_at_victim_first_pipe_pass(self):
        return self.arbcommand == "Victim"


class snoop_request(val_utdb_object):
    def __init__(self):
        self.snoop_req_opcode = None
        self.snoop_req_core = None
        self.time_on_idi_if = None

    def get_req_core(self):
        return int(self.snoop_req_core.split("_")[-1])


class snoop_response(val_utdb_object):
    def __init__(self):
        self.snoop_rsp_opcode = None
        self.original_snoop_rsp_opcode = None
        self.snoop_rsp_core   = None
        self.time_on_idi_if   = None
        self.uri_lid          = None
        self.num_of_data_with_snoop_rsp = None
        self.last_data_time_on_idi_if = None

    def get_rsp_core(self):
        return int(self.snoop_rsp_core)

    def get_rec_opcode_str(self):
        return self.snoop_rsp_opcode

class pipe_pass_info(val_utdb_object):
    def __init__(self):
        self.arbcommand_time = None
        self.arbcommand_opcode = None
        self.clean_evict_value = False
        self.monitor_hit_value = False
        self.sent_go_in_pipe_pass = False
        self.evict_clean_throttle = False

    def get_clean_evict_value(self):
        return self.clean_evict_value

    def get_evict_clean_throttle_value(self):
        return self.evict_clean_throttle

    def get_monitor_hit_value(self):
        return self.monitor_hit_value

    def get_pipe_arbcommand(self):
        return self.arbcommand_opcode

    def is_sent_go_in_pipe_pass(self):
        return self.sent_go_in_pipe_pass

    def get_pipe_arbcommand_time(self):
        return self.arbcommand_time

class ccf_record_info(val_utdb_object):
    def __init__(self):
        self.reset_record_info()

    def reset_record_info(self):
        self.rec_time = None
        self.rec_unit = None
        self.rec_tid = None
        self.rec_lid = None
        self.rec_pid = None
        self.rec_opcode = None
        self.checked_by_transition_checker = False

    def get_rec_opcode_str(self):
        return self.rec_opcode

    def get_time(self):
        return self.rec_time

    def is_record_belong_to_interface(self, interface):
        if interface == "IDI":
            return ("IDI" in self.rec_unit) or ("XBAR" in self.rec_unit)
        elif interface == "LLC":
            return "LLC" in self.rec_unit
        elif interface == "CFI":
            return "CCF_VC_SANTA" in self.rec_unit
        elif interface == "UFI":
            return "UFI" in self.rec_unit


class ccf_mlc_record_info(val_utdb_object):
    def __init__(self):
        self.time = 0
        self.unit = None
        self.address = None
        self.core_state = None
        self.superQ_state = None
        self.data = None

class ccf_idi_record_info(ccf_record_info):
    def __init__(self):
        self.reset()

    def reset(self):
        super().__init__()
        self.address = None
        self.address_parity = None
        self.rec_idi_interface = None
        self.cqid = None
        self.uqid = None
        self.lpid = None
        self.clos = None
        self.rec_selfsnoop = None
        self.rec_cache_near = None
        self.rec_logic_id = None
        self.rec_physical_id = None
        self.rec_lpid = None
        self.rec_go_type = None
        self.rec_bogus = None
        self.rec_pre = None
        self.hash = None
        self.data = None
        self.data_parity = None
        self.chunk = None
        self.non_temporal = None
        self.dbp_params = None
        self.src = None
        self.target = None

    def print_info(self):
        attrs = vars(self)
        return '\n'.join("%s: %s" % item for item in attrs.items())

    def is_c2u_req_if(self):
        return "C2U REQ" in self.rec_idi_interface

    def is_c2u_dir(self):
        return "C2U " in self.rec_idi_interface

    def is_u2c_dir(self):
        return "U2C " in self.rec_idi_interface

    def is_req_if(self):
        return " REQ" in self.rec_idi_interface

    def is_rsp_if(self):
        return " RSP" in self.rec_idi_interface

    def is_data_if(self):
        return " DATA" in self.rec_idi_interface

    def is_u2c_req_if(self):
        return "U2C REQ" in self.rec_idi_interface

    def is_u2c_rsp_if(self):
        return "U2C RSP" in self.rec_idi_interface

    def is_c2u_rsp_if(self):
        return "C2U RSP" in self.rec_idi_interface

    def is_c2u_data_if(self):
        return "C2U DATA" in self.rec_idi_interface

    def is_u2c_snoop(self):
        return self.is_u2c_req_if() and "SNP" in self.rec_lid

    def is_c2u_snoop_response(self):
        return self.is_c2u_rsp_if() and "SNP" in self.rec_lid

    def is_c2u_snoop_data_response(self):
        return self.is_c2u_data_if() and "SNP" in self.rec_lid

    def is_u2c_data_if(self):
        return "U2C DATA" in self.rec_idi_interface

    def is_go(self):
        return "IDI_GO" in self.rec_opcode

    def is_extcmp(self):
        return "EXTCMP" in self.rec_opcode

    def is_any_writepull(self):
        return "WRITEPULL" in self.rec_opcode

    def is_go_wr_pull(self):
        return "GO_WRITEPULL" in self.rec_opcode

    def is_fast_go_write_pull(self):
        return "FAST_GO_WRITEPULL" in self.rec_opcode

    def is_fast_go_extcmp(self):
        return "FASTGO_EXTCMP" in self.rec_opcode

    def is_fast_go(self):
        return "FAST_GO" in self.rec_opcode

    def is_any_kind_of_go(self):
        return self.is_go() or self.is_go_wr_pull() or self.is_fast_go_write_pull() or self.is_fast_go_extcmp()

    def is_core_unit(self):
        return ("IA" in self.rec_unit) or \
                ("AT" in self.rec_unit) or \
                ("XBAR_C" in self.rec_unit)

    def get_core_physical_id(self):
        return int(self.rec_unit.split("_")[-1])


    def is_same_uri_lid(self, uri_lid):
        return uri_lid == self.rec_lid

    def print_idi_info(self):
        attrs = vars(self)
        return ('\n'.join("%s: %s" % item for item in attrs.items()))

    def get_pkt_type(self):
        return self.rec_idi_interface

    def is_using_only_uqid(self):
        return self.is_u2c_req_if() or self.is_c2u_data_if() or self.is_c2u_rsp_if()

    def is_using_cqid(self):
        return self.cqid is not None

    def is_using_uqid(self):
        return self.uqid is not None

    def is_selfsnpinv(self):
        self_snoop_inv_types = ["SelfSnpInv", "SelfCDFSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv"]
        return [True for snoop_opcode in self_snoop_inv_types if snoop_opcode.lower() == self.rec_opcode.lower()]

    def is_u2c_lock_or_unlock_req(self):
        return self.rec_opcode in ["STOPREQ", "STARTREQ"]

    def is_c2u_lock_or_unlock_rsp(self):
        return self.rec_opcode in ["RspStopDone", "RspStartDone"]


class ccf_addr_entry(val_utdb_object):
    def __init__(self):
        self.time = None
        self.uri_lid = None
        self.uri_tid = None
        self.uri_pid = None
        self.prefetch_uri_tid = None
        self.conflict_with_uri = None
        self.unit = None
        self.rec_opcode = None
        self.addressless = None
        self.full_address = None
        self.real_address = None
        self.tor_id = None
        self.record_type = ""
        self.Allocated = 0
        self.TorAllocate = 0
        self.TorIfaAllocate = 0
        self.snoop_conflict_allocated = 0
        self.victim_due_to_partial_hit_while_snoop_conflict_allocated = 0
        self.current_prefetch_elimination_allocation_status = 0
        self.current_prefetch_elimination_ifa_allocation_status= 0
        self.is_any_prefetch_elimination_allocated_in_tor = 0
        self.AllowSnoop = 0
        self.PromotionWindow = 0
        self.Occupancy = None


    def allocate(self, record):
        self.time = record.time

    def get_time(self):
        return self.time

    def get_cbo_id(self):
        return self.unit.split("_")[1]

class tmp_data_time_struct(val_utdb_object):
    def __init__(self):
        self.data = None
        self.time = 0
        self.byteen = None

class memory_data_entry(val_utdb_object):
    def __init__(self):
        self.time = 0
        self.data = None
        self.state = None
        self.cache_type = None
        self.access_type = None
        self.tid = None
        self.byteen = None

    def get_time(self):
        return self.time

    def is_m(self):
        return (self.state != None and ((self.state == "M") or ("M->" in self.state)))

class memory_dump_entry(val_utdb_object):
    def __init__(self):
        self.time = 0
        self.cache_type = None
        self.set = None
        self.way = None
        self.state = None
        self.map = None
        self.cv = None
        self.data = None
        self.half = None
        self.cache_type = None

class llc_refmodel_entry(val_utdb_object):
    def __init__(self):
        self.time = 0
        self.slice = None
        self.half = None
        self.set = None
        self.way = None
        self.map = None
        self.state = None
        self.cv = None
        self.data = None
        self.data_ecc = None
        self.lru = None
        self.tag_ecc = None
        self.address = None

    def get_time(self):
        return int(self.time)

class ccf_llc_record_info(ccf_record_info):
    def __init__(self):
        self.reset()

    def reset(self):
        super().__init__()
        self.rejected = None
        self.rec_address = None
        self.rec_hitmiss = None
        self.rec_arbcmd = None
        self.rec_tag_ecc = None
        self.rec_set = None
        self.rec_way = None
        self.rec_map = None
        self.rec_map = None
        self.rec_half = None
        self.rec_state = None
        self.rec_new_state = None
        self.rec_new_map = None
        self.rec_state_wr_way = None
        self.rec_state_in_way = None
        self.rec_state_vl_way = None
        self.rec_cv_rd = None
        self.rec_cv_wr = None
        self.rec_lru_rd = None
        self.rec_lru_wr = None
        self.rec_data_ecc = None
        self.rec_hitmiss_vector = None
        self.rec_pref_vul_rd = None
        self.rec_pref_vul_wr = None
        self.rec_cv_err = None

    def get_phy_cbo_id(self):
        return self.rec_unit.split("_")[1]

    def get_data_way(self):
        return self.rec_map.lstrip('0')

    def get_late_data_way(self):
        return self.rec_new_map.lstrip('0')

    def get_tag_way(self):
        return self.rec_way.lstrip('0')

    def is_hit(self):
        return self.rec_hitmiss == "Hit"

    def get_tag(self):
        return self.rec_tag_ecc.split("(")[0]

    def get_tag_ecc(self):
        return self.rec_tag_ecc.split("(")[1][:-1]

    def get_set(self):
        return self.rec_set

    def is_late_wr_state(self):
        return ("-" not in (self.rec_new_state) and int(self.rec_state_wr_way, 16))

    def is_wr_data_uop(self):
        if 'R' in self.rec_opcode and 'W' in self.rec_opcode:
            return "d" in self.rec_opcode.split("W")[1]
        else:
            return 'W' in self.rec_opcode and 'd' in self.rec_opcode

    def is_rd_data_uop(self):
        return 'Rd' in self.rec_opcode and not self.is_lookup_uop() and self.rec_map != str(CCF_COH_DEFINES.SNOOP_FILTER)

    def is_lookup_uop(self):
        return "LR" in self.rec_opcode

    def is_cv_rd_uop(self):
        return "R" in self.rec_opcode and "c" in self.rec_opcode

    def get_time(self):
        return int(self.rec_time)

    def get_llc_aligned_address(self):
        #tag address = address[41:17] while address[17] is only for sf_restructure
        #set  = address[16:6] -> 2048 LLC sets
        tag =  self.get_tag()
        bin_tag = bin(int(self.get_tag(), 16))[2:]
        bin_set = bin(int(self.rec_set, 16))[2:].zfill(CCF_COH_DEFINES.num_of_set_bits)#need to pad to 11 digits in order to have correct address
        bin_addr = bin_tag + bin_set + "000000"
        new_address = hex(int(bin_addr,2))
        return ('0x' + new_address[2:].zfill(CCF_COH_DEFINES.address_lenth_in_hex))

    def get_half(self):
        if self.rec_unit != None and len(self.rec_unit) < 6:  # taking the half from HALF column in llc_trk
            return int(self.rec_half)
        else:
            #stzur hotfix num cbos can be 2 digits in SoC (CBO0-31), because of it taking char #6 is not accurate
            # return int(self.rec_unit[6])  # taking the half from the UNIT inside preload_trk
            return int(self.rec_unit.split(".")[1])


    def get_slice_num(self):
        return int(self.rec_unit[4])

    def had_cv_err(self):
        return self.rec_cv_err == "1"

class ccf_cbo_record_info(ccf_record_info):
    def __init__(self):
        self.reset()

    def reset(self):
        self.reset_record_info()
        self.cid = None
        self.sqid = None
        self.qid = None
        self.ring = None
        self.msg = None
        self.rtid = None
        self.address = None
        self.half_id = None
        self.selfsnp = None
        self.reqcv = None
        self.response_table_row = None
        self.entry_accepted = None
        self.entry_rejected = None
        self.number_of_rejects = 0
        self.entry_rejected_reasons = []
        self.prefetch_promotion = None
        self.prefetch_elimination_flow = None
        self.llc_initial_state = None
        self.llc_initial_cv = None
        self.llc_cv_shared = None
        self.llc_initial_map = None
        self.monitor_hit = None
        self.allocated_tag_way = None
        self.allocated_data_way = None
        self.data_vic_avail = None
        self.go_s_opt = None
        self.go_s_counter_above_th = None
        self.data_vulnerable = None
        self.dead_dbp = None
        self.found_free_data_way = None
        self.edram = None
        self.sad_results = None
        self.cache_near = None
        self.victim_state = None
        self.victim_map = None
        self.victim_tag_way = None
        self.victim_clean_evict = None
        self.clean_evict = None
        self.TorOccupAboveTH = None
        self.EvctClnThrottle = None
        self.send_go = None
        self.htid = None
        self.clos_en = None


    def get_cbo_id(self):
        return self.rec_unit.split("_")[1]

    def get_tor_id(self):
        return self.qid

    def print_info(self):
        attrs = vars(self)
        return '\n'.join("%s: %s" % item for item in attrs.items())

class ccf_cfi_record_info(ccf_record_info):
    def __init__(self):
        self.reset()

    def reset(self):
        super().__init__()

        self.interface = None
        self.msg_class = None
        self.protocol_id = None
        self.pkt_type = None
        self.vc_id = None
        self.rctrl = None
        self.dst_id = None
        self.rsp_id = None
        self.address = None
        self.rtid = None
        self.htid = None
        self.address_parity = None
        self.chunk = None
        self.data = ""
        self.data_parity = None
        self.paramA = None
        self.msg_type = None
        self.pcls = None
        self.dbpinfo = None
        self.dbp_params = None
        self.cachefar = None
        self.traffic_class = None
        self.core_id = None
        self.is_wb = None
        self.trace_pkt = None
        self.eop = None
        self.length = None

    def print_info(self):
        attrs = vars(self)
        return '\n'.join("%s: %s" % item for item in attrs.items())

    def get_transaction_time(self):
        return self.rec_time

    def get_santa_id(self):
        if self.rec_unit == CCF_UTILS.get_santa_name(0):
            return "0"
        elif self.rec_unit == CCF_UTILS.get_santa_name(1):
            return "1"
        else:
            return None

    def get_cfi_interface(self):
        return self.interface.split("_")[1]

    def is_req_channel(self):
        return self.get_cfi_interface() == "REQ"

    def is_rsp_channel(self):
        return self.get_cfi_interface() == "RSP"

    def is_data_channel(self):
        return self.get_cfi_interface() == "DATA"

    def is_upi_rd_data(self):
        return ("DRS" in self.vc_id) and (self.pkt_type == "SR-CD") and self.is_u2c_dir()

    def is_cfi_wr_data(self):
        return "RwD" in self.vc_id

    def is_upi_wb(self):
        return "UPI_WB" in self.vc_id and self.pkt_type in ["SA-D", "PW"]

    def is_upi_snp_rsp_wb(self):
        return "VC0_DRS" in self.vc_id and self.pkt_type == "SR-HD"
    def is_upi_snp_rsp_si(self):
        return "VC0_NDR" in self.vc_id and self.msg_class == "RSP" and self.pkt_type == "SR-H"
    def is_upi_snp_rsp(self):
        return self.is_upi_snp_rsp_wb() or self.is_upi_snp_rsp_si()

    def is_upi_c(self):
        return self.protocol_id == "UPI.C"

    def is_upi_nc(self):
        return self.protocol_id == "UPI.NC"

    def is_cxm(self):
        return self.protocol_id == "CXM"

    def is_upi_c_write_opcode(self):
        return self.rec_opcode in ["WbMtoI", "WbMtoS", "WbMtoE", "WbEtoI", "NonSnpWr", "WbMtoIPush", "EvctCln", "WbMtoIPtl", "WbMtoEPtl", "NonSnpWrPtl"]

    def is_upi_dirty_wb(self):
        return self.rec_opcode in ["WbMtoI", "WbMtoS", "WbMtoE","WbMtoIPush", "WbMtoIPtl", "WbMtoEPtl"]
    def is_upi_clean_wb(self):
        return self.rec_opcode in ["WbEtoI"]

    def is_upi_c_read_opcode(self):
        return self.rec_opcode in ["RdCode", "RdData", "RdDataMig", "RdInvOwn", "InvXtoI", "RemMemSpecRd", "InvItoE", "RdInv", "InvItoM", "NonSnpRd"]

    def is_upi_c_read_opcode_besides_Inv(self):
        return self.rec_opcode in ["RdCode", "RdData", "RdDataMig", "RdInvOwn", "RemMemSpecRd", "RdInv", "NonSnpRd"]

    def is_upi_c_reqfwdcnflt(self):
        return self.rec_opcode == "ReqFwdCnflt" and self.vc_id == "UPI_WB" and self.pkt_type == "SA"

    def is_upi_c_fwdcnflto(self):
        return self.rec_opcode == "FwdCnfltO" and self.vc_id == "VC0_NDR" and self.pkt_type == "SR-O"

    def is_upi_c_snoop(self):
        return self.rec_opcode in ["SnpCur", "SnpCode", "SnpData", "SnpDataMig", "SnpInvOwn", "SnpLCur", "SnpLCode", "SnpLData", "SnpLDataMig", "SnpLInv", "SnpLFlush"]

    def is_upi_c_snoop_rsp(self):
        return self.rec_opcode in ["RspI", "RspS", "RspE", "RspFwd", "RspFwdS", "RspI", "RspFwdIWb", "RspFwdSWb", "RspIWb", "RspSWb"]

    def is_upi_nc_write_opcode(self):
        upi_nc_write_opcodes = ["NcWr", "WcWr", "NcWrPtl", "WcWrPtl", "NcCfgWr", "NcLTWr", "NcIOWr"]
        return self.rec_opcode in upi_nc_write_opcodes

    def is_upi_nc_read_opcode(self):
        upi_nc_read_opcodes = ["NcRd", "NcRdPtl", "NcCfgRd", "NcLTRd", "NcIORd"]
        return self.rec_opcode in upi_nc_read_opcodes

    def is_upi_nc_read_data_opcode(self):
        upi_nc_read_opcodes = ["NCData"]
        return self.rec_opcode in upi_nc_read_opcodes

    def is_upi_c_cmp(self):
        upi_cmp_opcode = {"M_CmpO", "E_CmpO", "SI_CmpO", "CmpU"} #See CFI HasTable  5.3
        return ("NDR" in self.vc_id) and (self.rec_opcode.lower().strip() in (string.lower().strip() for string in upi_cmp_opcode)) and self.is_upi_c()

    def is_upi_CmpU(self):
        return "CmpU" in self.rec_opcode

    def is_upi_CmpO(self):
        return "CmpO" in self.rec_opcode


    def is_upi_nc_cmp(self):
        upi_nc_cmp_opcode = ["NCCmpU"]
        return ("NDR" in self.vc_id) and (self.rec_opcode.lower().strip() in (string.lower().strip() for string in upi_nc_cmp_opcode))

    def is_upi_nc_retry(self):
        upi_nc_cmp_opcode = ["NCRetry"]
        return ("NDR" in self.vc_id) and (self.rec_opcode.lower().strip() in (string.lower().strip() for string in upi_nc_cmp_opcode))

    def is_cfi_got_req(self):
        return "REQ" in self.vc_id and self.is_c2u_dir() and self.pkt_type == "SA"

    def get_pkt_type(self):
        return self.vc_id

    def is_c2u_dir(self):
        return CCF_UTILS.get_cfi_c2u_dir_str() in self.interface

    def is_u2c_dir(self):
        return CCF_UTILS.get_cfi_u2c_dir_str() in self.interface

    def is_upi_c_c2u_req(self):
        return self.is_upi_c() and self.is_c2u_dir() and self.vc_id == "UPI_REQ" and self.pkt_type == "SA"

    def is_upi_c_c2u_rsp(self):
        return self.is_upi_c() and self.is_c2u_dir() and self.vc_id == "VC0_NDR" and self.pkt_type == "SR-H"

    def is_upi_c_c2u_data(self):
        #Can be snoop response with data or WB
        return (self.is_upi_c() and self.is_c2u_dir()) and \
               ((self.vc_id == "VC0_DRS" and self.pkt_type == "SR-HD") or (self.vc_id == "UPI_WB" and self.pkt_type in ["SA-D", "PW", "SA"]))

    def is_upi_c_c2u_data_with_data(self):
        #Can be snoop response with data or WB
        return (self.is_upi_c() and self.is_c2u_dir()) and \
               ((self.vc_id == "VC0_DRS" and self.pkt_type == "SR-HD") or (self.vc_id == "UPI_WB" and self.pkt_type in ["SA-D", "PW"]))

    def is_upi_c_u2c_req(self):
        #Can be snoops from HA
        return self.is_upi_c() and self.is_u2c_dir() and self.vc_id == "UPI_SNP" and self.pkt_type in ["SA-S", "SA-SL"]

    def is_upi_c_u2c_rsp(self):
        #Completion and conflict order
        return self.is_upi_c() and self.is_u2c_dir() and self.vc_id == "VC0_NDR" and self.pkt_type in ["SR-U", "SR-O"]

    def is_upi_c_u2c_data(self):
        #Data response for reads
        return self.is_upi_c() and self.is_u2c_dir() and self.vc_id == "VC0_DRS" and self.pkt_type == "SR-CD"

    def is_upi_nc_c2u_req(self):
        #reads or lock msg
        return False
        return self.is_upi_nc() and self.is_cfi_c2u_dir() and (self.vc_id == "VC0_NCS" and self.pkt_type == "NCM")

    def is_upi_nc_c2u_rsp(self):
        return None

    def is_upi_nc_c2u_data(self):
        return (self.is_upi_nc() and self.is_c2u_dir()) and \
               ((self.vc_id in ["VC0_NCS", "VC0_NCB", "VC1_RwD"] and self.pkt_type == "PW") or
                (self.vc_id == "VC0_NCB" and self.pkt_type in ["SA-D", "NCM"]) or
                (self.vc_id == "VC0_NCS" and self.pkt_type in ["PR", "NCM"]))

    def is_upi_nc_c2u_write_data(self):
        return (self.is_upi_nc() and self.is_c2u_dir()) and \
               ((self.vc_id in ["VC0_NCS", "VC0_NCB", "VC1_RwD"] and self.pkt_type == "PW") or
                (self.vc_id == "VC0_NCB" and self.pkt_type == "SA-D"))

    def is_upi_nc_u2c_req(self):
        return None

    def is_upi_nc_u2c_rsp(self):
        #Completion and conflict order
        return self.is_upi_nc() and self.is_u2c_dir() and ((self.vc_id in ["VC0_NDR", "VC1_NDR"] and self.pkt_type in ["SR-U", "SR-H"])
                                                           or (self.vc_id == "VC0_NDR" and self.pkt_type == "SR-U"))
    def is_upi_nc_u2c_data(self):
        #Data response for reads
        return self.is_upi_nc() and self.is_u2c_dir() and self.vc_id == "VC0_DRS" and self.pkt_type == "SR-CD"

    def is_cfi_write_data(self):
        return (self.is_upi_c_c2u_data_with_data() and ("RspCurData" not in self.rec_opcode)) or self.is_upi_nc_c2u_write_data() or self.is_cfi_wr_data()

    def is_cfi_read_data(self):
        return self.is_upi_c_u2c_data() or self.is_upi_nc_u2c_data()

    def is_cfi_data_access(self):
        return self.is_cfi_write_data() or self.is_cfi_read_data()

    def get_msg_type_num(self):
        return int(self.msg_type.split("(")[1][:-1])

    def print_cfi_info(self):
        attrs = vars(self)
        return ('\n'.join("%s: %s" % item for item in attrs.items()))

class ccf_ufi_record_info(ccf_record_info):
    def __init__(self):
        self.reset()

    def reset(self):
        super().__init__()

        self.ufi_id = None
        self.ifc_type = None
        self.protocol = None
        self.channel = None
        self.vc_id = None
        self.pkt_type = None #HEADER_TYPE
        self.address = None
        self.address_parity = None
        self.rtid = None
        self.htid = None
        self.crnid = None
        self.cdnid = None
        self.hdnid = None
        self.hnid = None
        self.clos = None
        self.tee = None
        self.pcls = None
        self.memlock = None
        self.tsxabort = None
        self.param_a = None
        self.msg_type = None
        self.sai = None
        self.low_address = None
        self.length = None
        self.chunk = None
        self.data = ""
        self.data_parity = None #PAYLOAD_PARITY
        self.poison = None

    def print_info(self):
        attrs = vars(self)
        return '\n'.join("%s: %s" % item for item in attrs.items())

    def is_c2u_dir(self):
        return CCF_UTILS.is_ufi_c2u_dir(self.ifc_type)

    def is_u2c_dir(self):
        return CCF_UTILS.is_ufi_u2c_dir(self.ifc_type)

    def is_req_channel(self):
        return self.channel == "REQ"

    def is_rsp_channel(self):
        return self.channel == "RSP"

    def is_data_channel(self):
        return self.channel == "DATA"

    def is_uxi_c(self):
        return self.protocol == "UXI.C"

    def is_uxi_nc(self):
        return self.protocol == "UXI.NC"

    def is_uxi_req(self):
        return "REQ" in self.channel and CCF_UTILS.is_ufi_c2u_dir(self.ifc_type) and self.pkt_type == "SA"

    def is_uxi_snp_rsp_wb(self):
        return (UXI_UTILS.is_in_coh_snp_rsp_opcodes(self.rec_opcode)) and (self.vc_id == "VN0_RSP") and (self.channel == "DATA") and (self.pkt_type == "SR-HD") #TODO: check if the vc_id is correct

    def is_uxi_snp_rsp_without_data(self):
        return (UXI_UTILS.is_in_coh_snp_rsp_opcodes(self.rec_opcode)) and (self.vc_id == "VN0_RSP") and (self.channel == "RSP") and (self.pkt_type == "SR-H")

    def is_uxi_snp_rsp(self):
        return UXI_UTILS.is_in_coh_snp_rsp_opcodes(self.rec_opcode)

    def is_uxi_wb(self):
        return (UXI_UTILS.is_in_coh_write_opcodes(self.rec_opcode)) and (self.vc_id == "VN0_WB") and (self.channel == "DATA") and (self.pkt_type in ["SA-D", "PW"])

    def is_uxi_nc_write_opcode(self):
        return UXI_UTILS.is_in_nc_write_opcdes(self.rec_opcode)

    def is_uxi_rd_data(self):
        return (UXI_UTILS.is_in_coh_read_opcodes(self.rec_opcode)) and (self.pkt_type == "SA") and (self.channel == "REQ")

    def is_uxi_nc_read_data_opcode(self):
        return UXI_UTILS.is_in_nc_read_opcodes(self.rec_opcode)

    def is_uxi_cmp(self):
        return UXI_UTILS.is_in_coh_cmp_opcodes(self.rec_opcode)

    def is_uxi_nc_cmp(self):
        return UXI_UTILS.is_in_nc_cmp_opcodes(self.rec_opcode)

    def is_uxi_nc_retry(self):
        ufi_nc_retry_opcode = ["NcRetry"]
        return self.rec_opcode in ufi_nc_retry_opcode

    def is_uxi_reqfwdcnflt(self):
        return UXI_UTILS.is_uxi_reqfwdcnflt(self.rec_opcode)

    def is_uxi_fwdcnflto(self):
        return UXI_UTILS.is_uxi_fwdcnflto(self.rec_opcode)

    def is_conflict_related_opcode(self):
        return self.is_uxi_reqfwdcnflt() or self.is_uxi_fwdcnflto()

    def is_ufi_write_data(self):
        return self.is_c2u_dir and \
               ((UXI_UTILS.is_in_coh_snp_rsp_with_data_opcodes(self.rec_opcode) and ("RspCurData" not in self.rec_opcode))\
                or UXI_UTILS.is_in_coh_write_opcodes(self.rec_opcode) \
                or UXI_UTILS.is_in_nc_write_opcdes(self.rec_opcode))

    def is_ufi_read_data(self):
        return self.is_u2c_dir() and (UXI_UTILS.is_in_coh_data_rtn_opcodes(self.rec_opcode) or UXI_UTILS.is_in_nc_data_rtn_opcodes(self.rec_opcode))

    def is_ufi_data_access(self):
        return self.is_ufi_write_data() or self.is_ufi_read_data()



class ccf_sb_record_info():
    def __init__(self):
        self.time = None
        self.end_point = None
        self.direction = None
        self.posted = None
        self.type = None
        self.src_pid = None
        self.dest_pid = None
        self.opcode = None
        self.tag = None
        self.misc = None
        self.eh = None
        self.be = None
        self.fid = None
        self.bar = None
        self.addr_len = None
        self.rsp = None
        self.sai = None
        self.address = None
        self.data = None

    def reset(self):
        self.time = None
        self.end_point = None
        self.direction = None
        self.posted = None
        self.type = None
        self.src_pid = None
        self.dest_pid = None
        self.opcode = None
        self.tag = None
        self.misc = None
        self.eh = None
        self.be = None
        self.fid = None
        self.bar = None
        self.addr_len = None
        self.rsp = None
        self.sai = None
        self.address = None
        self.data = None

    def print_sb_info(self):
        attrs = vars(self)
        return '\n'.join("%s: %s" % item for item in attrs.items())
