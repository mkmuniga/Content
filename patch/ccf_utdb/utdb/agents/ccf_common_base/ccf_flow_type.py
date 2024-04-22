from collections import OrderedDict

import re

from val_utdb_base_components import val_utdb_object, EOT
from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_MSG, VAL_UTDB_ERROR
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base import pipe_pass_info, snoop_request, snoop_response, ccf_llc_record_info, \
    ccf_idi_record_info, ccf_cfi_record_info, ccf_ufi_record_info, ccf_cbo_record_info
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_systeminit.ccf_systeminit import ccf_systeminit
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.uxi_utils import UXI_UTILS
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB



class ccf_flow(val_utdb_object):

    def __init__(self):
        self.uri = {"TID": None, "PID": None, "LID": None}
        self.flow_key = None
        self.opcode = None
        self.original_opcode = None #In case we are using CBs that can replace opcodes.
        self.address = None
        self.go_type = ""
        self.received_pipe_first_pass_info = 0
        self.received_core_read_data = 0
        self.received_core_write_data = 0
        self.cache_near = None
        self.snoop_type = None
        self.snooped_cores = []
        self.snoop_requests = []
        self.snoop_responses = []
        self.final_snp_rsp = None
        self.cbo_snoop_response = None
        self.santa_snoop_response = None
        self.core_flow_is_bogus = False
        self.uncore_flow_is_bogus = False
        self.srp_en = "0"
        self.srp_hr_fill = "0"
        self.selfsnoop = None
        self.requestor_logic_id = None
        self.requestor_physical_id = None
        self.lpid = None
        self.clos = None
        self.allocated_tag_way = None
        self.allocated_data_way = None
        self.flow_origin = None
        self.sad_results = None
        self.had_conflict = False
        self.conflict_with_uri = None
        self.reqfwdcnflt_was_sent = False
        self.got_fwdcnflto = False
        self.data_ways_available = None
        self.go_s_opt = None
        self.go_s_counter_above_th = None
        self.data_vulnerable = None
        self.dead_dbp = None #Core DBP
        self.dead_dbp_from_idi = None #Core DBP from idi req len
        self.dbpinfo = None  #Mufasa DBP (DBP to MS$)
        self.dbp_params = None  #dbp params from mufasa
        self.idi_dbp_params = None  #dbp params from ccf to core
        self.idi_dbpinfo = None #dbp info from core
        self.clean_evict = None
        self.found_free_data_way = None
        self.initial_cache_state = None
        self.final_cache_state = None
        self.initial_cv = None
        self.initial_cv_shared = None
        self.final_cv = None
        self.initial_map = None
        self.final_map = None
        self.initial_tag_way = None
        self.final_tag_way = None
        self.llc_uops = []
        self.data_written_to_cache = None
        self.flow_progress = []
        self.pipe_passes_information = []
        self.rejected_reasons = []
        self.reject_time = dict()
        self.accept_time = None
        self.first_accept_time = None
        self.go_accept_time = None
        self.number_of_rejects = 0
        self.flow_promoted = None
        self.prefetch_elimination_flow = None
        self.pref_used_for_promotion = None
        self.promoted_uri = None
        self.flow_promoted_time = None
        self.TorOccupAboveTH = None
        self.tor_occupancy = None
        self.is_monflow_promoted_time = None
        self.promotion_flow_orig_pref_uri = None
        self.victim_flow = dict()
        self.victim_clean_evict = None
        self.initial_time_stamp = None
        self.cbo_id_log = None
        self.cbo_id_phys = None
        self.cbo_tor_qid = None
        self.cbo_half_id = None
        self.santa_id = None
        self.cfi_protocol = None
        self.cfi_upi_wr_data = ""
        self.cfi_upi_rd_data = ""
        self.cfi_upi_num_of_data_chunk = 0
        self.ufi_uxi_wr_data = ""
        self.ufi_uxi_rd_data = ""
        self.ufi_uxi_num_of_data_chunk = 0
        self.ufi_uxi_cmpo = None
        self.cfi_or_ufi_uxi_cmpu = None
        self.cfi_upi_retry = None
        self.cfi_upi_data_pcls = None
        self.current_monitor_array = None
        self.go_monitor_array = None
        self.clos_en = None
        self.response_table_row = []
        self.data_brought_by_llc_prefetch = None
        self.data_marked_as_brought_by_llc_prefetch = None
        self.yens_magic_msr_val = False
        self.cv_err = False
        self.inject_cv_err = False

    def get_flow_info_str(self):
        return self.flow_info_str


    #General functions
    ################################
    def get_sort_time(self):
        if self.first_accept_time is not None:
            return self.first_accept_time
        else:
            return self.initial_time_stamp

    #Fucntions related to address
    ##############################

    def address_formating(self, address, format):
        if (format == bint) and (type(address) != bint):
            return bint(int(address, 16))
        elif (format == str) and (type(address) != str):
            return hex(address)[2:0]
        else:
            VAL_UTDB_ERROR(time=EOT, msg="non valid format is being use in get_address function")

        return address

    def get_address(self, **kwargs):
        user_args = kwargs.keys()

        #Conditions that make us not return the address as is
        if len(user_args) == 0:
            if self.is_llc_special_opcode() and ccf_addressless_db.get_pointer().tid_exist_in_address_db(uri_tid=self.uri['TID']):
                return ccf_addressless_db.get_pointer().get_real_address_by_uri(uri_tid=self.uri['TID'])
            else:
                return self.address
        else:
            m_addr = self.address
            if ("msb" in user_args) or ("lsb" in user_args):
                msb_bit = kwargs["msb"] if ("msb" in user_args) else CCF_COH_DEFINES.address_msb
                lsb_bit = kwargs["lsb"] if ("lsb" in user_args) else CCF_COH_DEFINES.address_lsb
                m_addr = bint(int(m_addr, 16))[msb_bit:lsb_bit]

            #return address in specific format (currently supporting: string and bint)
            if ("format" in user_args):
                return self.address_formating(m_addr, kwargs["format"])
            else:
                return m_addr

    def is_spcyc_addr_zero(self):
        bin_addr = bint(int(self.address,16))
        return bin_addr[11:6] == 0

    def is_tag_bit_zero(self):
        return bint(int(self.address,16))[CCF_COH_DEFINES.tag_lsb] == 1


    #End of data analysis
    #########################
    def get_effective_opcode(self):
        if (self.opcode == "CLWB") and (ccf_registers.get_pointer().convert_clwb_to_clflushopt[self.cbo_id_phys] == 1):
            msg_info = "Our Original opcode is CLWB but convert_clwb_to_clflushopt bit is one therefore the effective flow opcode will be CLFlushOpt"
            VAL_UTDB_MSG(time=self.initial_time_stamp, msg=msg_info)
            return "CLFLUSHOPT"
        elif self.is_snoop_opcode() and not (self.is_snpinv() or self.is_snpinvown()) and \
                ccf_registers.get_pointer().ccf_ral_agent_ptr.read_reg_field("ingress_" + str(self.cbo_id_phys), "flow_cntrl", "force_snpinv", self.first_accept_time) == 1:
                return "SnpInvOwn"
        else:
            return self.opcode

    def update_opcode(self):
        new_opcode = self.get_effective_opcode()
        if new_opcode != self.opcode:
            self.original_opcode = self.opcode
            self.opcode = new_opcode

    def update_snp_rsp_for_wb2mmio_fix(self):
        is_nem_mode = ccf_systeminit.get_pointer().is_nem_test
        if (is_nem_mode or (not self.flow_is_hom())) and (self.is_drd() or self.is_crd() or self.is_monitor() or self.is_rfo() or self.is_specitom() or self.is_llc_special_opcode()):
            if self.cbo_id_phys is not None:
                if is_nem_mode:
                    should_manipulate_rsp = (ccf_ral_agent.get_pointer().read_reg_field("cbregs_all" + str(self.cbo_id_phys), "cbregs_spare", "dis_wb2mmio_fix_nem", self.initial_time_stamp) == 0)
                else:
                    should_manipulate_rsp = (ccf_ral_agent.get_pointer().read_reg_field("cbregs_all" + str(self.cbo_id_phys), "cbregs_spare", "dis_wb2mmio_fix", self.initial_time_stamp) == 0)

                if should_manipulate_rsp:
                    for rsp in self.snoop_responses:
                        if rsp.snoop_rsp_opcode == "RspIFwdMO":
                                rsp.original_snoop_rsp_opcode = "RspIFwdMO"
                                rsp.snoop_rsp_opcode = "RspIHitI"
                        elif rsp.snoop_rsp_opcode == "RspSFwdMO":
                                rsp.original_snoop_rsp_opcode = "RspSFwdMO"
                                rsp.snoop_rsp_opcode = "RspSHitFSE"
            else:
                err_msg = "Val_Assert (update_snp_rsp_for_wb2mmio_fix): we tried to take cbo_id_phys from flow object but it was None, " \
                          "please check your code/simulation it may happen if the trx never got to CBO (TID- {})".format(self.uri['TID'])
                VAL_UTDB_ERROR(time=self.initial_time_stamp, msg=err_msg)

    def update_final_snp_rsp(self):
        if len(self.snoop_responses) > 0:
            for rsp in self.snoop_responses:
                if self.final_snp_rsp in ["RspVFwdV", "RspNack", "RspStopDone", "RspStartDone"]:
                    break
                if self.final_snp_rsp == "RspEFFwdMO":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp == "RspSFwdMO":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspEFFwdMO"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp == "RspIFwdMO":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp == "RspSFwdFE":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp == "RspIFwdFE":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO", "RspSFwdFE"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode

                elif self.final_snp_rsp == "RspVHitV":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO", "RspSFwdFE", "RspIFwdFE"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode

                elif self.final_snp_rsp == "RspSHitFSE":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO", "RspSFwdFE", "RspIFwdFE", "RspVHitV"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode

                elif self.final_snp_rsp == "RspIHitFSE":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO", "RspSFwdFE", "RspIFwdFE", "RspVHitV", "RspSHitFSE"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp == "RspSI":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO", "RspSFwdFE", "RspIFwdFE", "RspVHitV", "RspSHitFSE", "RspIHitFSE"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp == "RspIHitI" or self.final_snp_rsp == "RspFlushed":
                    if rsp.snoop_rsp_opcode in ["RspVFwdV", "RspSFwdMO", "RspEFFwdMO", "RspIFwdMO", "RspSFwdFE", "RspIFwdFE", "RspVHitV", "RspSHitFSE", "RspIHitFSE", "RspSI"]:
                        self.final_snp_rsp = rsp.snoop_rsp_opcode
                elif self.final_snp_rsp is None:
                    self.final_snp_rsp = rsp.snoop_rsp_opcode
                else:
                    err_msg = "Val_Assert (update_final_snp_rsp): we got unknown snoop response please check your code - snoop response - {}".format(rsp.snoop_rsp_opcode)
                    VAL_UTDB_ERROR(time=rsp.time_on_idi_if, msg=err_msg)

    def set_yens_magic_msr(self):
        if self.initial_map_dway():
            data_way = int(self.initial_map.split("_")[-1])
            my_ymm_mask = ccf_registers.get_pointer().ccf_ral_agent_ptr.read_reg_field("ingress_" + str(self.cbo_id_phys),"l3_protected_ways", "ymm_mask",self.first_accept_time)
            max_dways = CCF_UTILS.get_max_num_of_dways()
            ymm_mask_bin = format(my_ymm_mask,"b").zfill(max_dways)
            self.yens_magic_msr_val = (ymm_mask_bin[::-1][data_way]) == "1"
        else:
            self.yens_magic_msr_val = False

    @property
    def flow_info_str(self):
        info_str = ""

        if len(self.pipe_passes_information) > 0:
            monitor_hit_str = "Monitor Hit(first pass): {}, Monitor Hit(snoop response): {}, Monitor Hit(go pass): {}".format((self.get_monitor_hit_value("first") or "NA"), (self.get_monitor_hit_value("SNP_RSP") or "NA"), (self.get_monitor_hit_value("go_sent") or "NA"))
            evict_clean_throttle_str = "Evict_clean_throttle(first pass): {}, Evict_clean_throttle(snoop response): {}".format(self.get_evict_clean_throttle_value("first" or "NA"), self.get_evict_clean_throttle_value("SNP_RSP") or "NA")
        else:
            monitor_hit_str = "Monitor Hit: this flow didn't enter the cpipe"
            evict_clean_throttle_str = "Evict_clean_throttle: this flow didn't enter the cpipe"



        info_str =  "Flow info for TID: {}, LID: {}, PID:{}\n".format(str(self.uri["TID"]),str(self.uri["LID"]),str(self.uri["PID"]))
        info_str += "Flow Origin: {}\n".format(str(self.flow_origin))
        info_str += "Flow Initial Time Stamp: {}, Flow Accept Time in Cpipe: {}\n".format(str(self.initial_time_stamp), str(self.accept_time))
        info_str += "Core requestor Logic ID: {}\n".format(str(self.requestor_logic_id))
        info_str += "Core requestor Physical ID: {}\n".format(str(self.requestor_physical_id))
        info_str += "CBO Physical ID: {}\n".format(str(self.cbo_id_phys))
        info_str += "CBO Logical ID: {}\n".format(str(self.cbo_id_log))
        info_str += "Opcode: {}\n".format(str(self.opcode))
        info_str += "Address: {}\n".format(str(self.address))
        info_str += "Initial Cache State: {}, Initial CV: {}, cv_is_share: {}, Initial Map: {}, Cache Near: {} SelfSnoop: {}\n".format(str(self.initial_cache_state), str(self.initial_cv), str(self.initial_cv_shared), str(self.initial_map), str(int(self.is_cache_near())), str(self.selfsnoop or "NA"))
        info_str += "{}\n".format(monitor_hit_str)
        info_str += "{}\n".format(evict_clean_throttle_str)
        info_str += "GO Type: {}\n".format(str(self.go_type))
        info_str += "Received core Read Data: {}\n".format((self.received_core_read_data))
        info_str += "Received core Write Data: {}\n".format(str(self.received_core_write_data))
        info_str += "Snoop Type: {}\n".format(str(self.snoop_type))
        info_str += "CBo Snoop Responses: {}\n".format(str(self.cbo_snoop_response))
        info_str += "Data Ways Available: {}\n".format(str(self.data_ways_available))
        info_str += "GO_S_OPT: {}\n".format(str(self.go_s_opt))
        info_str += "Keep Data Vulnerable: {}\n".format(str(self.data_vulnerable))
        info_str += "Final Cache State: {}\n".format(str(self.final_cache_state))
        info_str += "Final CV: {}\n".format(str(self.final_cv))
        info_str += "Final Map: {}\n".format(str(self.final_map))
        info_str += "Final Tag Way: {}\n".format(str(self.final_tag_way))
        info_str += "Data Written to Cache: {}\n".format(str(self.data_written_to_cache))
        info_str += "UOP: {}\n".format(str(self.llc_uops))
        info_str += "Pipe ArbCommands: {}\n".format(str(self.get_list_of_arbcommand_opcodes()))
        info_str += "Rejecting Reasons: {}\n".format(str(self.rejected_reasons))
        info_str += "Number of Rejects: {}\n".format(str(self.number_of_rejects))
        info_str += "Snoop Responses: {}\n".format(str(self.get_list_of_snp_rsp_opcodes()))
        info_str += "Final Snoop Response: {}\n".format(str(self.final_snp_rsp))
        info_str += "Core Flow Is Bogus: {}\n".format(str(self.core_flow_is_bogus))
        info_str += "SAD Results: {}\n".format(str(self.sad_results))
        info_str += "Flow Promoted: {}\n".format(str(self.flow_promoted))
        info_str += "Yens Magic MSR Value: {}\n".format(str(self.yens_magic_msr_val))
        info_str += "FreeInvWay: {}\n".format(str(self.found_free_data_way))
        return info_str



    def end_of_data_analysis_tasks(self):
        self.update_opcode()
        self.update_snp_rsp_for_wb2mmio_fix()
        self.update_final_snp_rsp()
        self.set_yens_magic_msr()

    #Get values from ccf flow class
    ###############################
    def get_dbp_params(self):
        return self.dbp_params

    def is_yens_magic_msr(self):
        return self.yens_magic_msr_val


    #SAD questions
    #####################
    def flow_is_hom(self):
        #In NEM test we are not using SM
        if (not ccf_systeminit.get_pointer().is_nem_test) and self.is_llc_special_opcode() and ccf_addressless_db.get_pointer().tid_exist_in_address_db(uri_tid=self.uri['TID']):
            address_without_mktme = self.get_address_wo_mktme_int()
            return "DRAM" in SM_DB.get_pointer().get_memory_space(address_without_mktme)

        if self.sad_results is not None:
            return "HOM" in self.sad_results
        return None

    def flow_hit_mmio_lt(self):
        address_without_mktme = self.get_address_wo_mktme_int()
        region = SM_DB.get_pointer().get_region(address_without_mktme)
        if region is not None:
            return "MMIO_LT" in region
        else:
            return False

    def is_cfg(self):
        if self.sad_results is not None:
            return "CFG" in self.sad_results
        return None

    def is_mmio(self):
        if self.sad_results is not None:
            return "MMIO" in self.sad_results
        return None

    def is_sad_na(self):
        if self.sad_results is not None:
            return "NA" == self.sad_results
        return None

    def is_sad_io(self):
        if self.sad_results is not None:
            return "IO" == self.sad_results
        return None

    def is_sad_lt(self):
        if self.sad_results is not None:
            return "LT" == self.sad_results
        return None

    def is_nc_crababort_flow(self):
        return (not self.flow_is_hom()) and (self.opcode in ["MEMPUSHWR", "MEMPUSHWR_NS", "WBMTOI", "WBMTOE", "WBEFTOI", "WBEFTOE"])

    def is_sad_crababort(self):
        return (self.sad_results is not None) and ("CRABABORT" in self.sad_results)

    def flow_is_crababort(self):
        if (self.sad_results is not None) and (("CRABABORT" in self.sad_results) or self.is_nc_crababort_flow()):
            return True
        return None

    def is_lt_doorbell(self):
        bint_addr = bint(int(self.address,16))
        bint_addr[7:0] = 0
        return self.is_sad_lt() and (hex(bint_addr) == "0xfed20e00")


    def is_0x3(self):
        bint_addr = bint(int(self.address, 16))
        return self.is_sad_io() and (hex(bint_addr[31:28]) == "0x3")


    def is_coherent_flow(self):
        return self.flow_is_hom() or self.is_victim() or self.is_flusher_origin()

    def is_non_coherent_flow(self):
        return not self.is_coherent_flow()


    #functions related to CLR
    #########################
    def get_clos_value(self):
        if self.is_snoop_opcode() or self.is_victim():
            return 0 #snoop/victim always use default CLOS which is 0
        elif ccf_registers.get_pointer().override_core_clos[self.cbo_id_phys] == 1:
            return ccf_registers.get_pointer().iaoverrideclosval[self.cbo_id_phys]
        else:
            return int(self.clos)

    #the CV is marked as shared in the cores (encoding of the CV bits in mode=1 see CCF HAS)
    def initial_cv_is_shared(self):
        return self.initial_cv_shared == "1"

    def initial_cv_value(self, value):
        if self.initial_cv is not None:
            return self.initial_cv.count("1") == value
        return None

    def initial_cv_more_than_value(self, value):
        if self.initial_cv is not None:
            return self.initial_cv.count("1") > value

    def initial_cv_zero(self):
        return self.initial_cv_value(value=0)

    def initial_cv_one(self):
        return self.initial_cv_value(value=1)

    def initial_cv_more_than_one(self):
        return self.initial_cv_more_than_value(value=1)

    def initial_cv_more_than_zero(self):
        return self.initial_cv_more_than_value(value=0)

    def initial_cv_with_selfsnoop_more_than_zero(self):
        return self.initial_cv_more_than_one() or (self.initial_cv_one() and (not self.req_core_initial_cv_bit_is_one() or self.need_to_selfsnoop_req_core()))

    def initial_cv_with_selfsnoop_zero(self):
        if self.initial_cv is not None:
            return self.initial_cv_zero() or (self.initial_cv_one() and self.req_core_initial_cv_bit_is_one() and not self.need_to_selfsnoop_req_core())

    def initial_cv_with_selfsnoop_one(self):
        if self.initial_cv is not None:
            return (self.initial_cv_one() and not self.req_core_initial_cv_bit_is_one()) or \
                   (self.initial_cv_one() and self.req_core_initial_cv_bit_is_one() and self.need_to_selfsnoop_req_core())


    def final_cv_zero(self):
        if self.final_cv is not None:
            return self.final_cv.count("1") == 0

    def final_cv_one(self):
        if self.final_cv is not None:
            return self.final_cv.count("1") == 1
        return None

    def final_cv_not_zero(self):
        if self.final_cv is not None:
            return self.final_cv.count("1") > 0
        return None

    def final_cv_is_all_one(self):
        if self.final_cv is not None:
            return self.final_cv.count("1") == CCF_COH_DEFINES.num_of_ccf_clusters * CCF_UTILS.get_num_of_cbo_enable()
        return None

    def final_req_cv_one(self):
        if self.final_cv is not None:
            flipped_cv = self.final_cv[::-1]
            return flipped_cv[self.requestor_logic_id] == '1'
        return None

    def final_req_cv_zero(self):
        return not self.final_req_cv_one()

    def get_num_of_valid_cores_in_final_cv(self):
        if self.final_cv is not None:
            flipped_cv = self.final_cv[::-1]
            return flipped_cv.count('1')
        return 0

    def get_initial_cv_bit_by_index(self, index):
        if self.initial_cv is not None:
            flipped_cv = self.initial_cv[::-1]
            return flipped_cv[index]
        return None

    def get_final_cv_bit_by_index(self, index):
        if self.final_cv is not None:
            flipped_cv = self.final_cv[::-1]
            return flipped_cv[index]
        return None

    def get_exp_final_cv_with_req_cv(self):
        if self.initial_cv is not None:
            flipped_cv = self.initial_cv[::-1]
            x = list(flipped_cv)
            x[self.requestor_logic_id] = '1'
            no_sep = ""
            flipped_cv = no_sep.join(x)
            return flipped_cv[::-1] #flip it back

    def get_exp_final_cv_with_req_cv_zero(self):
        if self.initial_cv is not None:
            num_of_cv = self.get_num_of_valid_cores_in_final_cv()
            flipped_cv = self.initial_cv[::-1]
            x = list(flipped_cv)
            if num_of_cv > 2 :
                if self.requestor_logic_id%2 == 0:
                    shared_core_in_cv = self.requestor_logic_id + 1
                else:
                    shared_core_in_cv = self.requestor_logic_id - 1

                if x[shared_core_in_cv] == '1':
                    x[self.requestor_logic_id] = '1'
                else:
                    x[self.requestor_logic_id] = '0'
            else:
                x[self.requestor_logic_id] = '0'
            no_sep = ""
            flipped_cv = no_sep.join(x)
            return flipped_cv[::-1] #flip it back

    #Check if initial cv doesn't exist in the final CV
    def is_initial_cv_exist_in_final_cv(self):
        if self.initial_cv is not None:
            initial_cv_ind = [m.start() for m in re.finditer('1', self.initial_cv)]
            final_cv_ind = [m.start() for m in re.finditer('1', self.final_cv)]
            return all(cvbit in final_cv_ind for cvbit in initial_cv_ind)

    def final_cv_more_than_one(self):
        if self.final_cv is not None:
            return self.final_cv.count("1") > 1
        return None

    def has_cv_err(self):
        return self.cv_err

    #This method is checking the case of transaction with cv error that is not fixed and the cv is not wrriten
    #But the initial_cv is not identical to the final_cv although this is what expected
    #Because the inital_cv is padding with 1's acording to the cv_err feature - in order to create snoops
    #But the final_cv is the cv before the 1's padding - the cv with the error from the beginning.
    def has_cv_err_with_no_fix(self):
        return self.has_cv_err() and not self.is_last_uop_fit_opcode_letters(["w", "c"])

    def is_cv_err_injection(self):
        return self.inject_cv_err

    def is_ms_chche_observer(self):
        bin_addr = bint(int(self.address,16))
        mask = bint(ccf_registers.get_pointer().dbp_ms_cache_mask[self.cbo_id_phys])
        for i in range(0,5):
            if (bin_addr[6+i] == bin_addr[11+i]) or ((bin_addr[11+i] == 1) and (mask[i] == 0)):
                return False
        return True

    def is_core_observer(self):
        bin_addr = bint(int(self.address,16))
        mask = bint(ccf_registers.get_pointer().dbp_ms_cache_mask[self.cbo_id_phys])
        for i in range(0,5):
            if (bin_addr[6+i] != bin_addr[11+i]) or ((bin_addr[11+i] == 1) and (mask[i] == 0)):
                return False
        return True

    def get_address_wo_mktme_int(self):
        return int(hex(bint(int(self.get_address(), 16))[CCF_COH_DEFINES.mktme_lsb-1:0]), 16)

    def flow_accessed_mktme(self):
        m_address = self.get_address()
        return int(bint(int(m_address, 16))[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.mktme_lsb]) != 0

    def is_tor_occup_above_threshold(self):
        return self.TorOccupAboveTH

    def is_tor_occup_above_threshold_in_thist_pass(self):
        return self.TorOccupAboveTH

    #def is_EvctClnThrottle(self):
    #    return self.EvctClnThrottle == "1"

    def is_data_written_to_cache(self):
        if self.data_written_to_cache is not None:
            return self.data_written_to_cache == 1
        return False

    def is_map_dway(self, map):
        return map is not None and "DWAY" in map

    def is_map_sf(self, map):
        return map is not None and "SF_ENTRY" in map

    def initial_map_dway(self):
        return self.is_map_dway(self.initial_map)

    def final_map_dway(self):
        return self.is_map_dway(self.final_map)

    def initial_map_sf(self):
        return self.is_map_sf(self.initial_map)

    def final_map_sf(self):
        return self.is_map_sf(self.final_map)

    def is_state_llc_i(self,state):
        return state is not None and "LLC_I" in state

    def is_state_llc_s(self,state):
        return state is not None and "LLC_S" in state

    def is_state_llc_e(self,state):
        return state is not None and "LLC_E" in state

    def is_state_llc_m(self,state):
        return state is not None and "LLC_M" in state

    def is_brought_by_prefetch(self):
        return self.data_brought_by_llc_prefetch == 1

    def is_data_marked_as_brought_by_llc_prefetch(self):
        return self.data_marked_as_brought_by_llc_prefetch

    def initial_state_llc_i(self):
        return self.is_state_llc_i(self.initial_cache_state)

    def final_state_llc_i(self):
        return self.is_state_llc_i(self.final_cache_state)

    def initial_state_llc_s(self):
        return self.is_state_llc_s(self.initial_cache_state)

    def final_state_llc_s(self):
        return self.is_state_llc_s(self.final_cache_state)

    def initial_state_llc_e(self):
        return self.is_state_llc_e(self.initial_cache_state)

    def final_state_llc_e(self):
        return self.is_state_llc_e(self.final_cache_state)

    def initial_state_llc_m(self):
        return self.is_state_llc_m(self.initial_cache_state)

    def final_state_llc_m(self):
        return self.is_state_llc_m(self.final_cache_state)

    def final_state_llc_m_or_e(self):
        return self.is_state_llc_m(self.final_cache_state) or self.is_state_llc_e(self.final_cache_state)

    def initial_state_llc_m_or_e(self):
        return self.is_state_llc_m(self.initial_cache_state) or self.is_state_llc_e(self.initial_cache_state)

    def initial_state_llc_e_or_s(self):
        return self.is_state_llc_e(self.initial_cache_state) or self.is_state_llc_s(self.initial_cache_state)

    def initial_state_llc_m_or_e_or_s(self):
        return self.is_state_llc_m(self.initial_cache_state) or self.is_state_llc_e(self.initial_cache_state) or self.is_state_llc_s(self.initial_cache_state)

    def final_state_llc_m_or_e_or_s(self):
        return self.is_state_llc_m(self.final_cache_state) or self.is_state_llc_e(self.final_cache_state) or self.is_state_llc_s(self.final_cache_state)

    def map_unchanged(self):
        return (self.initial_map == self.final_map) or (self.initial_state_llc_i() and self.final_state_llc_i())

    def state_unchanged(self):
        return (self.initial_cache_state == self.final_cache_state)

    def cv_unchanged(self):
        return (self.initial_cv == self.final_cv) or (self.initial_state_llc_i() and self.final_state_llc_i())

    def llc_unchanged(self):
        return self.map_unchanged() and self.state_unchanged() and self.cv_unchanged()

    def hit_in_cache(self):
        return not self.initial_state_llc_i()

    def is_llc_miss(self):
        return (not self.hit_in_cache()) or self.is_initial_stale_data()

    def is_llc_hit_sf_without_snoop(self):
        return self.initial_map_sf() and self.req_core_initial_cv_bit_is_one() and self.initial_cv_one() and not self.need_to_selfsnoop_req_core()

    def is_alloc_from_victim(self):
        return (len(self.victim_flow) != 0) and \
                any([True for vic in self.victim_flow if ((vic["TAG_WAY"] == self.allocated_tag_way) and vic["MAP"] == self.allocated_data_way)])


    def is_alloc_tag_and_victim_map_data(self):
        return (len(self.victim_flow) != 0) and \
                any([True for vic in self.victim_flow if ((vic["TAG_WAY"] == self.allocated_tag_way) and vic["MAP"] != "SF_ENTRY")])

    def is_victim_line(self):
        return len(self.victim_flow) != 0

    def is_victim_map_sf_line(self):
        return self.is_victim_line() and \
               any([True for vic in self.victim_flow if vic["MAP"] == "SF_ENTRY"])

    def is_allocating_line(self):
        return ((self.allocated_data_way is not None) or (self.allocated_tag_way is not None))

    def is_allocating_tag_way_only(self):
        return ((self.allocated_data_way is None) or (self.allocated_data_way == "SF_ENTRY")) and (self.allocated_tag_way is not None)


    #TODO: please check this function validity and remove the comment after that.
    def is_flow_with_silent_evict(self):
        if ((self.allocated_tag_way is None) and (self.allocated_data_way is None)) or (self.allocated_data_way == "SF_ENTRY") or self._first_llc_trans.rec_state_in_way is "-":
            return False
        else:
            if int(self._first_llc_trans.rec_state_in_way, 16) > 0:
                return True
            #the following good is not good enough and not needed, since we can have silent eviction also in order to get the data way-we don't need to check here if eviction is justified
            #if self.initial_tag_way is not None and int(self._first_llc_trans.rec_state_in_way, 16) > 0:
            #    return bint(int(self._first_llc_trans.rec_state_in_way, 16))[int(self.initial_tag_way)] == 0
            #else:
            #    return bint(int(self._first_llc_trans.rec_state_in_way, 16))[int(self.allocated_tag_way)] == 1

    def get_silent_evict_way(self):
        if self.is_flow_with_silent_evict():
            rec_state_in_way = bint(int(self._first_llc_trans.rec_state_in_way, 16))
            for i in range(CCF_COH_DEFINES.max_num_of_tag_ways):
                if rec_state_in_way[i] == 1:
                    return i
        else:
            return None

    def is_last_uop_fit(self, op):
        last_uop = self.llc_uops[-1]
        return sorted(op.lower()) == sorted(last_uop.lower())

    def is_last_uop_fit_opcode_letters(self, op_letters):
        last_uop = self.llc_uops[-1]
        for letter in op_letters:
            if letter.lower() not in last_uop.lower():
                return False
        return True

    def is_conflict_flow(self):
        return self.had_conflict

    def snoop_sent(self):
        return self.snoop_type is not None

    def all_snoops_where_snpinv(self):
        for snp in self.snoop_requests:
            if "snpinv" not in snp.snoop_req_opcode.lower():
                return False
        return True

    def is_flow_should_contain_invalidation_snoop(self):
        Drd_Crd_flow_condition = (self.is_drd() or self.is_crd() or self.is_drd_shared_opt()) and self.is_selfsnoop_and_req_cv()

        return self.is_rfo() or self.is_partial_or_uncachable_rd() or Drd_Crd_flow_condition or self.is_itom() or \
               self.is_specitom() or self.is_wcil() or self.is_wcilf() or self.is_mempushwr() or self.is_wil() or \
               self.is_wilf() or self.is_clflush() or self.is_clflush_opt() or self.is_cldemote() or \
               self.is_llcwbinv() or self.is_llcinv() or self.is_snpinvown() or self.is_snpinvmig() or \
               self.is_snpinv() or self.is_snpLDrop()



    def flow_should_not_snoop_due_to_cv_shared_indication(self):
        #WbStoI was exclude since we are not sending any snoops for it and we will ignore shared indication in this case.
        exclude_cases = self.is_wbstoi()
        return self.initial_cv_is_shared() and not self.is_selfsnoop_and_req_cv() \
               and self.initial_cv_with_selfsnoop_more_than_zero() \
               and not self.is_flow_should_contain_invalidation_snoop() \
               and not exclude_cases


    ######################

    def get_all_write_data_from_idi(self):
        all_data = " "
        c2u_data_transactions = self.get_flow_progress(record_type=ccf_idi_record_info, direction="C2U", channel="DATA")
        for tran in c2u_data_transactions:
            if "_SNP_" not in tran.rec_lid:
                if tran.chunk == CCF_COH_DEFINES.data_chunk_0:
                    all_data = all_data + tran.data
                elif tran.chunk == CCF_COH_DEFINES.data_chunk_1:
                    all_data = tran.data + all_data
        return all_data

    def is_nc_partial_write_flow(self):
        is_partial_write = False
        if self.sad_results != 'HOM' and self.opcode in ["WCIL", "WCIL_NS", "WIL"]:
            all_data = self.get_all_write_data_from_idi()
            is_partial_write = "-" in all_data

        return is_partial_write


    #################



    def is_snoop_rsp_in_snoop_responses(self, rsp_needed):
        return self.final_snp_rsp is not None and rsp_needed in self.final_snp_rsp

    def is_original_snoop_rsp_in_snoop_responses(self, rsp_needed):
        return self.final_snp_rsp is not None and rsp_needed in self.final_snp_rsp

    def get_list_of_snp_rsp_opcodes(self):
        snp_rsp_list = []
        for rsp in self.snoop_responses:
            snp_rsp_list.append(rsp.snoop_rsp_opcode)
        return snp_rsp_list

    def snoop_rsp_m(self):
        return self.is_snoop_rsp_in_snoop_responses("FwdMO") and self.snoop_sent()

    def snoop_rsp_IFwdM(self):
        return self.is_snoop_rsp_in_snoop_responses("IFwdMO") and self.snoop_sent()

    #check is snoop rsp is M before manipulate due to wb2mmio_dis_fix cb
    def original_snoop_is_rsp_IFwdM(self):
        for snp_rsp in self.snoop_responses:
            if self.is_non_coherent_flow() and (snp_rsp.original_snoop_rsp_opcode is not None):
                return "IFwdMO" in snp_rsp.original_snoop_rsp_opcode

        return self.snoop_rsp_IFwdM()

    def original_snoop_rsp_m(self):
        for snp_rsp in self.snoop_responses:
            if self.is_non_coherent_flow() and (snp_rsp.original_snoop_rsp_opcode is not None):
                return "FwdMO" in snp_rsp.original_snoop_rsp_opcode

        return self.snoop_rsp_m()

    def snoop_rsp_f(self):
        return self.is_snoop_rsp_in_snoop_responses("FwdFE") and self.snoop_sent()

    def snoop_rsp_v_fwd(self):
        return self.snoop_sent() and self.is_snoop_rsp_in_snoop_responses("RspVFwdV")

    def snoop_rsp_v_hit(self):
        return self.snoop_sent() and self.is_snoop_rsp_in_snoop_responses("RspVHitV")

    def snoop_rsp_with_data(self):
        return self.snoop_rsp_m() or self.original_snoop_rsp_m() or self.snoop_rsp_f() or self.snoop_rsp_v_fwd()

    def snoop_rsp_clean_data_fwd(self):
        return self.snoop_sent() and self.is_snoop_rsp_in_snoop_responses("Fwd") and not self.snoop_rsp_m()

    def snoop_rsp_opcode_with_data(self, snoop_opcode):
        snoops_with_data_opcodes = ["RspSFwdMO", "RspIFwdMO", "RspIFwdFE", "RspSFwdFE", "RspEFFwdMO", "RspVFwdV"]
        return (snoop_opcode is not None) and snoop_opcode.lower().strip() in (string.lower() for string in snoops_with_data_opcodes)

    def snoop_rsp_i(self):
        return not self.core_still_has_data_after_snoop() and not self.snoop_rsp_f() and not self.snoop_rsp_m() and not self.snoop_rsp_v_fwd() and self.snoop_sent()

    def snoop_rsp_si(self):
        return self.is_snoop_rsp_in_snoop_responses("RspSI") and self.snoop_sent()

    def snoop_rsp_s(self):
        return self.core_still_has_data_after_snoop() and not self.snoop_rsp_f() and not (self.snoop_rsp_m() or self.original_snoop_rsp_m()) and not self.snoop_rsp_v_fwd() and self.snoop_sent()

    def snoop_rsp_s_fwd(self):
        return self.snoop_rsp_f() and self.is_snoop_rsp_in_snoop_responses("RspS")

    def snoop_rsp_i_fwd(self):
        return self.snoop_rsp_f() and self.is_snoop_rsp_in_snoop_responses("RspI")

    def snoop_rsp_s_fwd_m(self):
        return self.snoop_sent() and self.is_snoop_rsp_in_snoop_responses("RspSFwdMO")

    def snoop_rsp_nack(self):
        return self.is_snoop_rsp_in_snoop_responses("Nack") and self.snoop_sent()

    def snoop_rsp_hit(self):
        return self.is_snoop_rsp_in_snoop_responses("Hit") and self.snoop_sent()

    def snoop_rsp_s_hit(self):
        return self.is_snoop_rsp_in_snoop_responses("SHit") and self.snoop_sent()

    def snoop_rsp_i_hit(self):
        return self.is_snoop_rsp_in_snoop_responses("IHit") and self.snoop_sent()

    def snoop_rsp_i_hit_i(self):
        return self.is_snoop_rsp_in_snoop_responses("IHitI") and self.snoop_sent()

    def snoop_rsp_i_fwd_x(self):
        return (self.snoop_rsp_f() or self.snoop_rsp_m()) and not self.core_still_has_data_after_snoop()

    def snoop_rsp_s_fwd_x(self):
        return (self.snoop_rsp_f() or self.snoop_rsp_m()) and self.core_still_has_data_after_snoop()

    def snoop_rsp_flushed(self):
        return self.is_snoop_rsp_in_snoop_responses("RspFlushed") and self.snoop_sent()

    def core_still_has_data_after_snoop(self):
        #In case of using CBs that will cause us to snoop all cores + using the Wb2MMIOFix we can get to situation that
        #We got RspSI from one core and RspIFwdMO from another while we will convert it to RspIHitI (due to Wb2MMIOFix)
        #In that case we will consider RspSI as S even that we know that only one core had the data (Since it was modified).
        Wb2MMIOFix_exception = self.should_snoop_to_all_cores() and self.original_snoop_is_rsp_IFwdM()
        return (not Wb2MMIOFix_exception) and \
                ((self.is_snoop_rsp_in_snoop_responses("RspS") and not self.is_snoop_rsp_in_snoop_responses("RspStopDone") and not self.is_snoop_rsp_in_snoop_responses("RspStartDone")) or self.is_snoop_rsp_in_snoop_responses("RspFE") or
                self.is_snoop_rsp_in_snoop_responses("RspVFwdV") or self.is_snoop_rsp_in_snoop_responses("RspVHitV")) and self.snoop_sent()

    def core_still_has_data_in_s(self):
        #If we got RspSI and RspFwdMO become RspIHitI in MMIO the final snoop response will be RspSI.
        #But that not mean the core in Shared mode since RspSI can be both I or S, but the existence of RspIFwdMO
        return (self.is_snoop_rsp_in_snoop_responses("RspS") and not self.original_snoop_is_rsp_IFwdM() and self.snoop_sent())

    def is_self_snoop_dont_care_idi_opcode(self):
        self_snoop_dont_care_idi_opcode = {"LLCInv", "LLCWB", "LLCWBInv"} #See IDI HAS table 25
        return self.opcode.lower().strip() in (string.lower() for string in self_snoop_dont_care_idi_opcode)


    def read_data_from_mem(self):
        return (len(self.ufi_uxi_rd_data) > 1)

    def wrote_data_to_upi(self):
        return len(self.ufi_uxi_wr_data) > 1

    #TODO meirlevy: This function is not accurate any more since we have Data_* as a response for snoops
    def wrote_data_to_mem(self):
        return self.wrote_data_to_upi()

    def wrote_full_cache_line_to_mem(self):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH")
        for rec in write_recs:
            if ("Wb" in rec.rec_opcode and not "Ptl" in rec.rec_opcode) or (rec.rec_opcode in ["Data_M", "Data_E", "Data_SI"]):
                return True
        return False

    def got_snoop_rsp_fwd_data(self, exp_data_type):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH")
        for rec in write_recs:
            if rec.rec_opcode.lower() == exp_data_type.lower():
                return True
        return False

    def is_santa_dirty_wb(self):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH")
        for rec in write_recs:
            if rec.is_upi_dirty_wb():
                return True
        return False

    def is_santa_wbmtoi(self):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA",uxi_type="COH")
        for rec in write_recs:
            if rec.rec_opcode =="WbMtoI":
                return True
        return False

    def is_santa_wbmtoe(self):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH")
        for rec in write_recs:
            if rec.rec_opcode =="WbMtoE":
                return True
        return False

    def is_santa_RspIWb(self):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH")
        for rec in write_recs:
            if rec.rec_opcode =="RspIWb":
                return True
        return False

    def is_santa_clean_wb(self):
        write_recs = self.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH")
        for rec in write_recs:
            if rec.is_upi_clean_wb():
                return True
        return False

    def req_core_initial_cv_bit_is_one(self):
        if self.initial_cv is not None:
            flipped_cv = self.initial_cv[::-1]
            return self.requestor_logic_id is not None and flipped_cv[self.requestor_logic_id] == "1"

    def req_core_initial_cv_bit_is_zero(self):
        if self.initial_cv is not None:
            flipped_cv = self.initial_cv[::-1]
            return self.requestor_logic_id is not None and flipped_cv[self.requestor_logic_id] == "0"

    def try_do_selfsnoop_force(self):
        if ccf_registers.get_pointer().get_force_selfsnoop_all_field(self.cbo_id_phys, self.initial_time_stamp) == 1:
            return True
        if (self.is_drd() and not self.is_drd_pref()) or (self.is_drd_shared_opt() and not self.is_drd_shared_opt_pref()):
            return ccf_registers.get_pointer().get_force_selfsnoop_drd_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if self.is_drd_pref() or self.is_drd_shared_opt_pref():
            return ccf_registers.get_pointer().get_force_selfsnoop_drd_prefetch_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if (self.is_crd() and not self.is_crd_pref()) or self.is_monitor(): #monitor is CRD at pipe
            return ccf_registers.get_pointer().get_force_selfsnoop_crd_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if self.is_crd_pref():
            return ccf_registers.get_pointer().get_force_selfsnoop_crd_prefetch_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if self.is_rfo() and not self.is_rfo_pref():
            return ccf_registers.get_pointer().get_force_selfsnoop_rfo_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if self.is_rfo_pref():
            return ccf_registers.get_pointer().get_force_selfsnoop_rfo_prefetch_field(self.cbo_id_phys, self.initial_time_stamp) == 1

        return False
    def is_always_selfsnoop(self):
        if (ccf_registers.get_pointer().get_force_selfsnoop_snoopfilter_field(self.cbo_id_phys, self.initial_time_stamp) == 1):
            return self.initial_map_sf() and self.try_do_selfsnoop_force()
        else:
            return self.try_do_selfsnoop_force()

    def is_selfsnoop(self):
        if self.is_always_selfsnoop():
            return True
        else:
            return self.selfsnoop == "1"

    def is_selfsnoop_and_req_cv(self):
        # According IDI Spec Table 25 we should consider selfsnoop=0 for those wb exception opcodes.
        wb_exception = self.is_wbeftoi() or self.is_wbeftoe() or self.is_wbstoi()
        return self.is_selfsnoop() and self.req_core_initial_cv_bit_is_one() and not wb_exception

    def need_to_selfsnoop_req_core(self):
        return self.is_selfsnoop_and_req_cv() or (self.is_self_snoop_dont_care_idi_opcode() and self.req_core_initial_cv_bit_is_one())

    def is_cache_near(self):
        return self.get_effective_cache_near_value() == "1"

    def get_effective_cache_near_value(self):
        #If we are using LLC special opcode we are not doing LookUp and therefore YMM is not manipulate the CN value.
        if self.is_yens_magic_msr() and not self.is_llc_special_opcode():
            return "1"
        elif self.is_always_cache_near():
            return "1"
        elif self.is_llcpref():
            return "1"
        else:
            return self.cache_near

    def is_always_cache_near(self):
        if self.is_drd() or self.is_drd_shared_opt() or self.is_drd_shared_opt_pref():
            return ccf_registers.get_pointer().get_drd_always_cachenear_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if self.is_crd():
            return ccf_registers.get_pointer().get_crd_always_cachenear_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        if self.is_rfo():
            return ccf_registers.get_pointer().get_rfo_always_cachenear_field(self.cbo_id_phys, self.initial_time_stamp) == 1
        return 0

    #Important! that mean we have candidate for victim if we will need it
    def is_data_way_available(self):
        return self.data_ways_available == "1"

    def is_go_s_opt(self):
        return self.go_s_opt == "1"

    def is_go_s_counter_above_th(self):
        return self.go_s_counter_above_th

    def is_go_s_counter_below_th(self):
        return (self.go_s_counter_above_th is not None) and (not self.go_s_counter_above_th)

    def is_srp_en(self):
        return self.srp_en == "1"

    def is_data_vulnerable(self):
        return self.data_vulnerable == "1"

    def is_data_vulnerable_feature_disable(self):
        return (ccf_registers.get_pointer().disable_data_vulnerable[self.cbo_id_phys] == 1)

    def is_data_vulnerable_feature_enable(self):
        return not self.is_data_vulnerable_feature_disable()

    def is_flow_promoted(self):
        cbo_phy_id = self.cbo_id_phys if self.cbo_id_phys is not None else 0
        return self.flow_promoted and (ccf_registers.get_pointer().enable_prefetch_promotion[cbo_phy_id] == 1)

    def is_prefetch(self):
        pref_opcode_list = ["LlcPrefRFO", "LlcPrefData", "LlcPrefCode"]
        return any([True for pref_opcode in pref_opcode_list if self.opcode.lower().strip() == pref_opcode.lower().strip()])

    def is_prefetch_elimination_flow(self):
        cbo_phy_id = self.cbo_id_phys if self.cbo_id_phys is not None else 0
        return self.prefetch_elimination_flow and (ccf_registers.get_pointer().prefetch_elimination_en[cbo_phy_id] == 1)

    #AvailData definiton = Can allocate (Map = Data or can create victim or Invalid Data way)
    #Note: if we are being reject due to RejectDueAllDataWaysAreReserved the next time we will not consider ourself as having data way
    #this is to avoid deadlock in case all data ways are allocated for one Tag way array.
    #removing is_free_data_way() indication since if data_way_available == 1, data_way_available == 1
    #(unless we force data_way_available to 0 due to tag bit zero feture - and then free_data_way is irrelevant)
    def force_non_avilable_data_way(self):
        for reject in self.rejected_reasons:
            if "RejectDueAllDataWaysAreReserved" == reject.reject_reason:
                if ccf_registers.get_pointer().enable_force_noavaildataway_in_any_reject[self.cbo_id_phys] or reject.llc_state == "LLC_I":

                    return True
        return False

    def is_available_data(self):
        data_way_available = self.is_data_way_available()
        initial_map_dway = self.initial_map_dway()
        free_data_way = self.is_free_data_way()
        force_noavaildataway = self.force_non_avilable_data_way()
        return ((data_way_available or free_data_way) and (not force_noavaildataway)) or initial_map_dway

    def is_dead_dbp(self):
        return self.dead_dbp == 1

    def is_dead_dbp_from_core(self):
        return self.dead_dbp_from_idi == 1

    def is_bypass_llc_to_mufasa(self):
        return self.dbpinfo == "0"

    def is_bypass_llc_to_dram(self):
        return self.dbpinfo == "2"

    def is_core_clean(self):
        return self.is_wbeftoi() and not self.core_sent_bogus_data()


    def is_core_modified(self):
        return self.is_wbmtoi() and not self.core_sent_bogus_data()


    def is_llc_clean(self):
        return self.is_victim() and not self.initial_state_llc_m() and not self.snoop_rsp_m()


    def is_llc_modified(self):
        return self.is_victim() and (self.initial_state_llc_m() or self.snoop_rsp_m())

    def is_initial_stale_data(self):
        return not self.initial_state_llc_i() and self.initial_map_sf() and self.initial_cv_zero()

    def is_final_stale_data(self):
        return not self.final_state_llc_i() and self.final_map_sf() and self.final_cv_zero()

    # This mean we have some data ways that was not being allocated to no one.
    # when we have CV_ERROR this indication is always 0 - due to rtl implementation
    def is_free_data_way(self):
        return self.found_free_data_way == 1 and not self.has_cv_err()

    # This is what Leon calling FreeInvWay (map=Data or invalid_data_way)
    # Note: if we are being reject due to RejectDueAllDataWaysAreReserved the next time we will not consider ourself as having data way
    # this is to avoid deadlock in case all data ways are allocated for one Tag way array.
    def is_free_inv_way(self):
        return (self.is_free_data_way() and all([reject.reject_reason != "RejectDueAllDataWaysAreReserved" for reject in self.rejected_reasons])) or self.initial_map_dway()

    def is_idi_flow_origin(self):
        return "IDI" in self.flow_origin

    def is_cfi_flow_origin(self):
        return "CFI" in self.flow_origin

    def is_uxi_flow_origin(self):
        return "UXI" in self.flow_origin

    def is_cfi_NcMsgS_flow_origin(self):
        return "CFI NcMsgS" in self.flow_origin

    def is_uxi_NcMsgS_flow_origin(self):
        return "UXI NcMsgS" in self.flow_origin

    def is_flow_origin_uxi_snp(self):
        return self.opcode in UXI_UTILS.uxi_coh_snp_opcodes

    def cbo_sent_go(self):
        return not (not self.go_type) # when doing not on empty string ("") the result is true

    def cbo_sent_go_e(self):
        return self.cbo_sent_go() and "GO_E" in self.go_type and not self.cbo_sent_fast_go_extcmp()
    def cbo_sent_go_m(self):
        return self.cbo_sent_go() and "GO_M" in self.go_type
    def cbo_sent_go_s(self):
        return self.cbo_sent_go() and "GO_S" in self.go_type
    def cbo_sent_go_f(self):
        return self.cbo_sent_go() and "GO_F" in self.go_type
    def cbo_sent_go_s_or_f(self):
        return self.cbo_sent_go_s() or self.cbo_sent_go_f()
    def cbo_sent_go_i(self):
        return self.cbo_sent_go() and "GO_I" in self.go_type
    def cbo_sent_go_nogo(self):
        return self.cbo_sent_go() and "GO_NO" in self.go_type
    def cbo_sent_go_mesif(self):
        return self.cbo_sent_go_e() or self.cbo_sent_go_m() or self.cbo_sent_go_f() or self.cbo_sent_go_s_or_f() or self.cbo_sent_go_i()
    def cbo_sent_go_mesf(self):
        return self.cbo_sent_go_e() or self.cbo_sent_go_m() or self.cbo_sent_go_s_or_f()
    def cbo_sent_fast_go_wr_pull(self):
        return self.cbo_sent_go() and "FAST_GO_WRITEPULL" in self.go_type
    def cbo_sent_fast_go(self):
        return self.cbo_sent_go() and "FAST_GO" in self.go_type
    def cbo_sent_fast_go_extcmp(self):
        return self.cbo_sent_go() and "FASTGO_EXTCMP" in self.go_type
    def cbo_sent_go_wr_pull(self):
        return self.cbo_sent_go() and "GO_WRITEPULL" in self.go_type and not self.cbo_sent_fast_go_wr_pull() and not self.cbo_sent_go_wr_pull_drop()
    def cbo_sent_go_wr_pull_drop(self):
        return self.cbo_sent_go() and "GO_WRITEPULL_DROP" in self.go_type and not self.cbo_sent_fast_go_wr_pull()
    def cbo_got_ufi_uxi_cmpo_si(self):
        return self.ufi_uxi_cmpo is not None and 'SI' in self.ufi_uxi_cmpo
    def cbo_got_ufi_uxi_cmpo_m(self):
        return self.ufi_uxi_cmpo is not None and 'M' in self.ufi_uxi_cmpo
    def cbo_got_ufi_uxi_cmpo_e(self):
        return self.ufi_uxi_cmpo is not None and 'E' in self.ufi_uxi_cmpo
    def cbo_got_ufi_uxi_cmpo(self):
        return self.cbo_got_ufi_uxi_cmpo_m() or self.cbo_got_ufi_uxi_cmpo_e() or self.cbo_got_ufi_uxi_cmpo_si()
    #TODO: need to replace this with seach in flow_progress
    def cbo_got_upi_cmpu(self):
        return self.cfi_or_ufi_uxi_cmpu is not None and "CmpU" in self.cfi_or_ufi_uxi_cmpu
    # TODO: need to replace this with seach in flow_progress
    def cbo_got_upi_NCmpu(self):
        return self.cfi_or_ufi_uxi_cmpu is not None and "NCCmpU" in self.cfi_or_ufi_uxi_cmpu

    def santa_got_upi_rd_data(self):
        return self.ufi_uxi_rd_data != ""
    def cbo_got_upi_fwdcnflto(self):
        return self.got_fwdcnflto

    #is Opcode questions
    def is_read_opcode(self):
        return self.is_drd() or self.is_crd() or self.is_rfo() or self.is_partial_or_uncachable_rd() or self.is_llcpref()
    def is_pref_read(self):
        self.is_drd_pref() or self.is_crd_pref() or self.is_rfo_pref()
    def is_drd(self):
        return (self.opcode is not None) and ("DRD" in self.opcode) and not (self.is_drd_shared_opt() or self.is_drd_shared_opt_pref())
    def is_drd_shared_opt(self):
        return (self.opcode is not None) and ("DRD_SHARED_OPT" in self.opcode)
    def is_drd_shared_opt_pref(self):
        return (self.opcode is not None) and ("DRD_SHARED_PREF" in self.opcode)
    def is_drd_pref(self):
        return self.opcode is not None and ("DRD_PREF" in self.opcode or "DRD_OPT_PREF" in self.opcode)
    def is_crd(self):
        return self.opcode is not None and "CRD" in self.opcode and not "CRD_UC" in self.opcode and not "UCRDF" in self.opcode
    def is_crd_pref(self):
        return self.opcode is not None and "CRD_PREF" in self.opcode
    def is_prd(self):
        return self.opcode is not None and "PRD" in self.opcode
    def is_partial_or_uncachable_rd(self):
        return self.opcode is not None and ("PRD" in self.opcode or "CRD_UC" in self.opcode or "UCRDF" in self.opcode)
    def is_ucrdf_or_crd_uc(self):
        return self.opcode is not None and ("CRD_UC" in self.opcode or "UCRDF" in self.opcode)
    def is_rfo(self):
        return self.opcode is not None and "RFO" in self.opcode and not "WR" in self.opcode and "LLCPREF" not in self.opcode
    def is_rfo_pref(self):
        return self.opcode is not None and "RFO_PREF" in self.opcode
    def is_itom(self):
        return self.opcode is not None and "ITOM" in self.opcode and not "WR" in self.opcode and not "SPEC" in self.opcode
    def is_llcwb(self):
        return self.opcode is not None and "LLCWB" in self.opcode and not "INV" in self.opcode
    def is_llcwbinv(self):
        return self.opcode is not None and self.opcode in ["LLCWBINV"]
    def is_llcinv(self):
        return self.opcode is not None and "LLCINV" in self.opcode
    def is_llc_special_opcode(self):
        return self.is_llcwbinv() or self.is_llcwb() or self.is_llcinv()
    def is_addressless_opcode(self):
        return self.opcode is not None and (self.opcode in CCF_FLOW_UTILS.idi_addressless_opcodes)
    def is_wcilf_or_itomwr_wt(self):
        return self.opcode is not None and "WCILF" in self.opcode or "ITOMWR_WT" in self.opcode
    def is_itomwr(self):
        return self.opcode is not None and "ITOMWR" in self.opcode and not self.is_wcilf_or_itomwr_wt()
    def is_itomwr_wt(self):
        return self.opcode is not None and "ITOMWR_WT" in self.opcode
    def is_wcil(self):
        return self.opcode is not None and "WCIL" in self.opcode and not "WCILF" in self.opcode
    def is_wcilf(self):
        return self.opcode is not None and "WCILF" in self.opcode
    def is_llcpref(self):
        return self.is_llcprefdata() or self.is_llcprefcode() or self.is_llcprefrfo()
    def is_llcprefdata(self):
        return self.opcode is not None and "LLCPREFDATA" in self.opcode
    def is_llcprefcode(self):
        return self.opcode is not None and "LLCPREFCODE" in self.opcode
    def is_llcprefrfo(self):
        return self.opcode is not None and "LLCPREFRFO" in self.opcode
    def is_specitom(self):
        return self.opcode is not None and "SPEC_ITOM" in self.opcode
    def is_clflush(self):
        return self.opcode is not None and "CLFLUSH" in self.opcode and not "CLFLUSHOPT" in self.opcode
    def is_clflush_opt(self):
        return self.opcode is not None and "CLFLUSHOPT" in self.opcode
    def is_mempushwr(self):
        return self.opcode is not None and "MEMPUSHWR" in self.opcode
    def is_wil(self):
        return self.opcode is not None and "WIL" in self.opcode and not "WiLF" in self.opcode
    def is_wilf(self):
        return self.opcode is not None and "WILF" in self.opcode
    def is_wbmtoi(self):
        return self.opcode is not None and "WBMTOI" in self.opcode
    def is_wbmtoe(self):
        return self.opcode is not None and "WBMTOE" in self.opcode
    def is_wbeftoe(self):
        return self.opcode is not None and "WBEFTOE" in self.opcode
    def is_wbeftoi(self):
        return self.opcode is not None and "WBEFTOI" in self.opcode
    def is_wbstoi(self):
        return self.opcode is not None and "WBSTOI" in self.opcode
    def is_wb_flow(self):
        return self.is_wbstoi() or self.is_wbmtoi() or self.is_wbmtoe() or self.is_wbeftoi() or self.is_wbeftoe()
    def is_snpinv(self):
        return self.opcode is not None and self.opcode in ['SNPINV', 'SnpLInv']
    def is_snpLDrop(self):
        return self.opcode is not None and self.opcode in ['SNPLDROP', 'SnpLDrop']
    def is_snpinvmig(self):
        return self.opcode is not None and self.opcode in ['SNPINVMIG', 'SnpInvMig']
    def is_snpinvown(self):
        return self.opcode is not None and self.opcode in ['SnpInvOwn']
    def is_snpflush(self):
        return self.opcode is not None and self.opcode in ['SnpLFlush']
    def is_interrupt(self):
        return self.opcode is not None and self.opcode in ['INTPHY', 'INTLOG', 'INTPRIUP', 'EOI', 'INTA']
    def is_ipi_interrupt(self):
        return self.opcode is not None and self.opcode in ['INTPHY', 'INTLOG']
    def is_vlw(self):
        return self.is_cfi_flow_origin() and self.opcode is not None and ("NcMsgB" == self.opcode)
    def is_doorbell(self):
        return self.is_cfi_flow_origin() and self.opcode is not None and ("NcLTWr" == self.opcode)
    def is_enqueue(self):
        return self.opcode is not None and "ENQUEUE" in self.opcode
    def is_flusher(self):
        return self.opcode is not None and "FLUSHER" in self.opcode
    def is_flusher_origin(self):
        return "CBo FlushReadSet Flow" == self.flow_origin
    def is_u2c_cfi_uxi_nc_interrupt(self):
        return self.is_cfi_flow_origin() and self.opcode is not None and self.opcode in ["IntPhysical", "IntLogical", "NcLTWr", "NcMsgB"]

    def is_u2c_upi_nc_ipi_interrupt(self):
        return self.is_cfi_flow_origin() and self.opcode is not None and self.opcode in ["IntPhysical", "IntLogical"]

    def is_u2c_upi_nc_ltdoorbell(self):
        return self.is_cfi_flow_origin() and self.opcode is not None and self.opcode in ["NcLTWr"]

    def is_u2c_cfi_uxi_nc_req_opcode(self):
        return self.is_cfi_flow_origin() and self.opcode is not None and ("NcMsgS" == self.opcode)

    def is_u2c_ufi_uxi_nc_req_opcode(self):
        return self.is_uxi_flow_origin() and self.opcode is not None and ("NcMsgS" == self.opcode)

    def is_u2c_dpt_req(self):
        return self.flow_origin == "DPT REQ" and self.opcode is not None and self.opcode == "DPTEV"
    def is_portin(self):
        return self.opcode is not None and 'PORT_IN' == self.opcode
    def is_portout(self):
        return self.opcode is not None and 'PORT_OUT' == self.opcode
    def is_victim(self):
        return self.opcode is not None and "VICTIM" == self.opcode
    def is_snpdatamig(self):
        return self.opcode is not None and self.opcode in ["SnpDataMig", "SnpLDataMig"]
    def is_snpdata(self):
        return self.opcode is not None and self.opcode in ["SnpData"]
    def is_snpldata(self):
        return self.opcode is not None and self.opcode == "SnpLData"
    def is_snpcode(self):
        return self.opcode is not None and self.opcode == "SnpCode"
    def is_snplcode(self):
        return self.opcode is not None and self.opcode == "SnpLCode"
    def is_snpdata_or_snpcode(self):
        return self.is_snpdata() or self.is_snpcode() or self.is_snpldata() or self.is_snplcode() or self.is_snpdatamig()
    def is_snpcurr(self):
        return self.opcode is not None and self.opcode in ["SnpCur"]
    def is_snplcurr(self):
        return self.opcode is not None and self.opcode in ["SnpLCur"]
    def is_snoop_opcode(self):
        return self.is_snpdata_or_snpcode() or self.is_snpinv() or self.is_snpLDrop() or self.is_snpinvmig() \
               or self.is_snpinvown() or self.is_snpcurr() or self.is_snplcurr() or self.is_snpflush()
    def is_monitor(self):
        return self.opcode is not None and 'MONITOR' == self.opcode and not 'CLRMONITOR' == self.opcode
    def is_clrmonitor(self):
        return self.opcode is not None and 'CLRMONITOR' == self.opcode
    def is_nop(self):
        return self.opcode is not None and 'NOP' == self.opcode
    def is_lock_or_unlock(self):
        return self.opcode is not None and self.opcode in ["LOCK", "SPLITLOCK", "UNLOCK"]
    def is_lock_or_splitlock(self):
        return self.opcode is not None and self.opcode in ["LOCK", "SPLITLOCK"]
    def is_spcyc(self):
        return self.opcode is not None and 'SPCYC' == self.opcode
    def is_cldemote(self):
        return self.opcode is not None and "CLDEMOTE" in self.opcode
    def is_clwb(self):
        return self.opcode is not None and "CLWB" in self.opcode
    def is_non_prefetch_read(self):
        return (self.is_crd() or self.is_drd or self.is_rfo()) and not self.is_pref_read()

    def is_fsrdcurr(self):
        return (("RDCURR" in self.opcode and "IDI.C REQ" in self.flow_origin) or "FSRDCURR" in self.opcode)

    def is_rdcurr(self):
        return "RDCURR" in self.opcode and not "IDI.C REQ" in self.flow_origin

    def is_promotable_opcode(self):
        return self.is_crd() or self.is_drd() or self.is_rfo() or self.is_monitor()

    def is_full_line_c2u_data_write_flow(self):
        return self.is_wilf() or self.is_wcilf() or self.is_wbmtoi() or self.is_wbmtoe() or self.is_wbeftoe()  or self.is_wbeftoi() \
               or self.is_mempushwr() or self.is_clwb() or self.is_clflush_opt() or self.is_clflush() or self.is_llcwbinv() or self.is_llcwb()

    def is_partial_c2u_data_write_flow(self):
        return self.is_wil() or self.is_wcil()

    def is_wr_and_inv_flow(self):
        return self.is_partial_c2u_data_write_flow() or self.is_wilf() or self.is_wcilf() or self.is_mempushwr()

    def is_c2u_data_write_flow_opcode(self):
        return self.is_full_line_c2u_data_write_flow() or self.is_partial_c2u_data_write_flow() or self.is_specitom()

    def is_possible_evict_in_read_flow(self):
        return self.is_drd() or self.is_partial_or_uncachable_rd() or self.is_crd() or self.is_monitor() or self.is_crd_pref() or self.is_rfo() or self.is_victim() or self.is_specitom()

    #These flows check monitor hit indication and cannot gurantee that there will be no false data writes to sf entry
    def flow_should_ignore_false_data_wr_to_sf(self):
        return self.is_drd() or self.is_rfo() or self.is_specitom() or self.is_snpinv() or self.is_snpinvown()

    def core_sent_bogus_data(self):
        return self.core_flow_is_bogus

    def flow_is_a_finished_pref(self):
        return self.is_llcpref() and not self.pref_used_for_promotion



    #Get expected value functions
    ###############################
    def get_clean_evict_for_victim(self, victim_parent):
         #If we are in Victim flow, SF, LLC_E we will check the clean evict in the first pipe pass - RTL implementation
        sample_clean_evict_for_victim_on_second_pass = self.is_victim() and not (self.initial_map_sf() and self.initial_state_llc_e())
        #If we are candidate for Silent Evict we are using the clean evict indication from the parent transaction.
        sample_clean_evict_for_victim_on_parent_trans = self.is_victim() and self.initial_state_llc_e_or_s() and self.initial_cv_zero()

        if sample_clean_evict_for_victim_on_second_pass and self.snoop_sent():
            return self.get_clean_evict_value("SNP_RSP")
        elif sample_clean_evict_for_victim_on_parent_trans:
            return victim_parent.victim_clean_evict
        else:
            return self.get_clean_evict_value()

    def get_evict_clean_throttle_value(self, pipe_pass="first"):
        if len(self.pipe_passes_information) > 0:
            if pipe_pass == "first":
                #In case of victim with reject we will have FakeCycle that we need to ignore.
                if self.is_victim() and self.is_in_arbcommands("FakeCycle"):
                    return self.get_pipe_pass_item("FakeCycle").get_evict_clean_throttle_value()
                else:
                    return self.pipe_passes_information[0].get_evict_clean_throttle_value()
            elif pipe_pass == "SNP_RSP":
                for item in self.pipe_passes_information:
                    if item.get_pipe_arbcommand() in CCF_FLOW_UTILS.SNP_RSP_arbcommand:
                        return item.get_evict_clean_throttle_value()
                #in case we don't have SNP_RSP cycle we assume we will take the value from pipe pass "first"
                return self.pipe_passes_information[0].get_evict_clean_throttle_value()
            else:
                for item in self.pipe_passes_information:
                    if item.get_pipe_arbcommand() == pipe_pass:
                        return item.get_evict_clean_throttle_value()

            err_msg = "Something went wrong we should get some value here please check your code"
            VAL_UTDB_ERROR(time=0, msg=err_msg)
            return None
        else:
            return None

    def is_evict_clean_throttle(self, pipe_pass="first"):
        return self.get_evict_clean_throttle_value(pipe_pass) == "1"


    def get_clean_evict_value(self, pipe_pass="first"):
        if len(self.pipe_passes_information) > 0:
            if pipe_pass == "first":
                #In case of victim with reject we will have FakeCycle that we need to ignore.
                if self.is_victim() and self.is_in_arbcommands("FakeCycle"):
                    return self.get_pipe_pass_item("FakeCycle").get_clean_evict_value()
                else:
                    return self.pipe_passes_information[0].get_clean_evict_value()
            elif pipe_pass == "SNP_RSP":
                for item in self.pipe_passes_information:
                    if item.get_pipe_arbcommand() in CCF_FLOW_UTILS.SNP_RSP_arbcommand:
                        return item.get_clean_evict_value()
            else:
                for item in self.pipe_passes_information:
                    if item.get_pipe_arbcommand() == pipe_pass:
                        return item.get_clean_evict_value()

            err_msg = "Something went wrong we should get some value here please check your code"
            VAL_UTDB_ERROR(time=0, msg=err_msg)
            return None
        else:
            return None

    def is_clean_evict(self, pipe_pass="first"):
        return self.get_clean_evict_value(pipe_pass) == "1"

    def get_monitor_hit_value(self, pipe_pass="first"):
        if len(self.pipe_passes_information) > 0:
            if pipe_pass == "first":
                return self.pipe_passes_information[0].get_monitor_hit_value()
            elif pipe_pass == "go_sent":
                for item in self.pipe_passes_information:
                    if item.is_sent_go_in_pipe_pass():
                        return item.get_monitor_hit_value()
                #If we didn't found any GO we assuming we should use the first pass monitor hit indication
                return self.pipe_passes_information[0].get_monitor_hit_value()
            elif pipe_pass == "SNP_RSP":
                for item in self.pipe_passes_information:
                    if item.get_pipe_arbcommand() in CCF_FLOW_UTILS.SNP_RSP_arbcommand:
                        return item.get_monitor_hit_value()
                # If we didn't found any SNP_RSP we assuming we should use the first pass monitor hit indication
                return self.pipe_passes_information[0].get_monitor_hit_value()
            else:
                for item in self.pipe_passes_information:
                    if item.get_pipe_arbcommand() == pipe_pass:
                        return item.get_monitor_hit_value()

            err_msg = "(get_monitor_hit_value): User expected to get MonHit indication for TID-{} at pipe pass {} but we don't have this pipe pass in the flow".format(self.uri['TID'], pipe_pass)
            VAL_UTDB_ERROR(time=0, msg=err_msg)
            return None
        else:
            err_msg = "(get_monitor_hit_value): Something went wrong user asked for monitor hit value but we didn't find any pipe pass"
            VAL_UTDB_ERROR(time=0, msg=err_msg)
            return None

    def is_monitor_hit(self, pipe_pass="first"):
        return self.get_monitor_hit_value(pipe_pass) == "1"

    def is_monitor_hit_for_upi_snoop_flow(self):
        if self.is_conflict_flow():
            #first_pipe_stage = "FwdCnfltO"
            first_pipe_stage = "FakeCycle"
        else:
            first_pipe_stage = "first"

        if self.is_snpflush():
            return self.is_monitor_hit(first_pipe_stage)
        elif self.is_snpdata_or_snpcode() or self.is_snplcode() or self.is_snpcurr() or self.is_snplcurr():
            if self.snoop_sent():
                return self.is_monitor_hit("SNP_RSP")
            else:
                return self.is_monitor_hit(first_pipe_stage)
        elif self.is_snpinv() or self.is_snpinvown() or self.is_snpLDrop() or self.is_snpinvmig():
            return False #snoopinv is clearing the monitor indication
        else:
            err_msg = "(is_monitor_hit_for_upi_snoop_flow): User ask for monitor hit indication for snoop flow " \
                      "({}, URI-{}) that the function wasn't programed to handle.".format(self.opcode, self.uri['TID'])
            VAL_UTDB_ERROR(time=self.initial_time_stamp, msg=err_msg)
            return self.is_monitor_hit()

    def get_exp_uqid(self, tor_qid=-1, cbo_id_in=-1):
        if tor_qid == -1:
            tor_id = bint(int(self.cbo_tor_qid))
        else:
            tor_id = bint(int(tor_qid))
        if cbo_id_in == -1:
            cbo_id = bint(int(self.cbo_id_log))
        else:
            cbo_id = bint(int(cbo_id_in))
        uqid = bint(int(0))
        uqid[5:0] = tor_id[5:0]
        uqid[9:6] = cbo_id[3:0]
        return hex(uqid)[2:]


    #Sometime we have several victim flows in one parent flow (because of partial hit) therefore we need to find the right information for it according to time.
    #When Victim time is bigger the the time of the parent that had the victim information we know this is the right parent
    #please notice we are sorting this list in a reverse order.
    def get_victim_flow_info(self, vic_time):
        #for time, info in sorted(list(self.victim_flow.items()), key=lambda x: x[0].lower(), reverse=True):
        #ordered_victim_flow = OrderedDict(sorted(self.victim_flow.items(), reverse=True))
        ordered_victim_flow = sorted(self.victim_flow.items(), reverse=True)
        for time, info in ordered_victim_flow:
            if vic_time > time:
                return info
        return None

    def get_flow_victim_map(self):
        victim_item = self.get_victim_flow_info(self.first_accept_time)
        return victim_item["MAP"]

    def get_victim_tag_way(self):
        victim_item = self.get_victim_flow_info(self.first_accept_time)
        return victim_item["TAG_WAY"]

    #CBs functions
    ###############
    def is_force_snoop_effect_opcode(self):
        return not (self.is_wbeftoi() or self.is_wbmtoe() or self.is_wbmtoi() or self.is_wbeftoe())

    def is_force_snoop_all_cb_en(self):
        force_snoop_all = (ccf_registers.get_pointer().ccf_ral_agent_ptr.read_reg_field("ingress_" + str(self.cbo_id_phys), "flow_cntrl", "force_snoop_all", self.first_accept_time) == 1)
        return force_snoop_all and self.is_force_snoop_effect_opcode()

    def is_dis_spec_snoop(self):
        return (ccf_registers.get_pointer().ccf_ral_agent_ptr.read_reg_field("ingress_" + str(self.cbo_id_phys),"flow_cntrl", "dis_spec_snoop", self.first_accept_time) == 1)

    def cb_force_snoop_to_all_cores(self):
        force_snoop_all = (ccf_registers.get_pointer().ccf_ral_agent_ptr.read_reg_field("ingress_" + str(self.cbo_id_phys), "flow_cntrl", "force_snoop_all", self.first_accept_time) == 1)
        always_snoop_all_ia = (ccf_registers.get_pointer().ccf_ral_agent_ptr.read_reg_field("ingress_" + str(self.cbo_id_phys), "flow_cntrl", "always_snoop_all_ia", self.first_accept_time) == 1)
        if force_snoop_all and not always_snoop_all_ia:
            err_msg = "(cb_force_snoop_to_all_cores): if force_snoop_all cb enable then always_snoop_all_ia most be enable as well." \
                      "force_snoop_all={}, always_snoop_all_ia={}".format(force_snoop_all, always_snoop_all_ia)
            VAL_UTDB_ERROR(time=self.initial_time_stamp, msg=err_msg)
        return (force_snoop_all or always_snoop_all_ia) and self.is_force_snoop_effect_opcode()

    def should_snoop_to_all_cores(self):
        return self.cb_force_snoop_to_all_cores() or (self.has_cv_err() and not self.is_cldemote())

    #Pipe Pass functions
    #####################
    def is_in_arbcommands(self, arbcommand):
        return any([True for pipe_pass in self.pipe_passes_information if pipe_pass.arbcommand_opcode.lower().strip() == arbcommand.lower().strip()])

    def get_list_of_arbcommand_opcodes(self):
        arbcommand_list = []
        for pipe_pass in self.pipe_passes_information:
            arbcommand_list.append(pipe_pass.arbcommand_opcode)
        return arbcommand_list

    def get_pipe_pass_item(self, arbcommand):
        for pipe_pass in self.pipe_passes_information:
            if pipe_pass.arbcommand_opcode.lower().strip() == arbcommand.lower().strip():
                return pipe_pass
        return None

    def get_arbcommand_time(self, arbcommand_name):
        if arbcommand_name == "SNP_RSP":
            for pipe_pass in self.pipe_passes_information:
                if pipe_pass.arbcommand_opcode in CCF_FLOW_UTILS.SNP_RSP_arbcommand:
                    return pipe_pass.get_pipe_arbcommand_time()
        else:
            for pipe_pass in self.pipe_passes_information:
                if arbcommand_name in pipe_pass.arbcommand_opcode:
                    return pipe_pass.get_pipe_arbcommand_time()
        return None

    #Flow progress functions
    #########################
    def add_flow_point_to_flow_progress(self,ccf_coherency_analyzer):
        self.flow_progress.append(ccf_coherency_analyzer)

    def does_flow_contain_uxi_req(self):
        for trans in self.flow_progress:
            if (type(trans) is ccf_ufi_record_info) and (trans.is_uxi_req()):
                return True
        return False

    @property
    def _first_llc_trans(self):
        for trans in self.flow_progress:
            if type(trans) is ccf_llc_record_info:
                return trans
        return None

    #This funciton will get diffrent kinds of conditions and return the right transactions from flow progress
    def check_record_is_valid(self, record_type):
        return record_type in [ccf_idi_record_info, ccf_llc_record_info, ccf_cbo_record_info, ccf_ufi_record_info, ccf_cfi_record_info]

    def is_opcode_as_requested(self, trans, requested_opcode):
        return trans.rec_opcode.lower() == requested_opcode.lower()

    def is_direction_as_requested(self, trans, requested_direction):
        if type(trans) is ccf_idi_record_info:
            return ((requested_direction == "C2U") and trans.is_c2u_dir()) or ((requested_direction == "U2C") and trans.is_u2c_dir())
        elif type(trans) in [ccf_ufi_record_info, ccf_cfi_record_info]:
            return ((requested_direction == "C2S") and trans.is_c2u_dir()) or ((requested_direction == "S2C") and trans.is_u2c_dir())
        elif type(trans) in [ccf_llc_record_info, ccf_cbo_record_info]:
            return True
        else:
            VAL_UTDB_ERROR(time=0, msg="(is_direction_as_requested): transaction type {} wasn't expected".format(str(type(trans))))

    def is_channel_as_requested(self, trans, requested_channel):
        if type(trans) in [ccf_ufi_record_info, ccf_cfi_record_info]:
            return ((requested_channel == "REQ") and trans.is_req_channel()) \
                   or \
                   ((requested_channel == "RSP") and trans.is_rsp_channel()) \
                   or \
                   ((requested_channel == "DATA") and trans.is_data_channel())
        elif type(trans) in [ccf_idi_record_info]:
            return ((requested_channel == "REQ") and trans.is_req_if()) \
                   or \
                   ((requested_channel == "RSP") and trans.is_rsp_if()) \
                   or \
                   ((requested_channel == "DATA") and trans.is_data_if())
        elif type(trans) in [ccf_llc_record_info, ccf_cbo_record_info]:
            return True
        else:
            VAL_UTDB_ERROR(time=0, msg="(is_channel_as_requested): transaction type {} wasn't expected".format(str(type(trans))))

    def is_traffic_type_as_requested(self, requested_traffic_type):
        if requested_traffic_type == "COH":
            return self.is_coherent_flow()
        elif requested_traffic_type == "NC":
            return self.is_non_coherent_flow()
        else:
            VAL_UTDB_ERROR(time=0, msg="(is_traffic_type_as_requested): requested_traffic_type {} wasn't expected".format(requested_traffic_type))

    def is_pkt_type_as_requested(self, trans, requested_pkt_type):
        if type(trans) in [ccf_ufi_record_info, ccf_cfi_record_info]:
            return requested_pkt_type.lower() == trans.pkt_type.lower()
        else:
            return True

    def get_flow_progress(self, **kwargs):
        actual_trans = []
        args_key = kwargs.keys()

        if not self.check_record_is_valid(kwargs["record_type"]):
            VAL_UTDB_ERROR(time=0, msg="User try to get non supported record type from flow progress")

        for trans in self.flow_progress:
            add_transaction = True
            if ("record_type" in args_key) and (type(trans) is not kwargs["record_type"]):
                add_transaction = False
            if ("direction" in args_key) and not self.is_direction_as_requested(trans, kwargs["direction"]):
                add_transaction = False
            if ("channel" in args_key) and not self.is_channel_as_requested(trans, kwargs["channel"]):
                add_transaction = False
            if ("opcode" in args_key) and not self.is_opcode_as_requested(trans, kwargs["opcode"]):
                add_transaction = False
            if ("traffic_type" in args_key) and not self.is_traffic_type_as_requested(kwargs["traffic_type"]):
                add_transaction = False
            if ("pkt_type" in args_key) and not self.is_pkt_type_as_requested(trans, kwargs["pkt_type"]):
                add_transaction = False
            if ("start_time" in args_key) and not (trans.rec_time >= kwargs["start_time"]):
                add_transaction = False
            if ("end_time" in args_key) and (kwargs["end_time"] is not None) and not (trans.rec_time < kwargs["end_time"]):
                add_transaction = False
            if ("cache2cache" in args_key) and (kwargs["cache2cache"] is True) and (trans.rec_opcode not in ["Data_SI", "Data_E"]):
                add_transaction = False
            if ("cache2ha" in args_key) and (kwargs["cache2ha"] is True) and (trans.rec_opcode in ["Data_SI", "Data_E"]):
                add_transaction = False

            if add_transaction:
                actual_trans.append(trans)
        return actual_trans


    #SANTA functions
    #################
    def get_rd_santa_id(self):
        santa_id = self.santa_id
        for trans in self.flow_progress:
            if (type(trans) is ccf_cfi_record_info) and trans.is_upi_c_c2u_req():
                santa_id = trans.rec_unit
        return santa_id

    def get_wr_santa_id(self):
        santa_id = self.santa_id
        for trans in self.flow_progress:
            if (type(trans) is ccf_cfi_record_info) and trans.is_upi_c_c2u_data():
                santa_id = trans.rec_unit
        return santa_id

    def get_rx_req_santa_id(self):
        santa_id = self.santa_id
        for trans in self.flow_progress:
            if (type(trans) is ccf_cfi_record_info) and trans.is_upi_c_u2c_req():
                santa_id = trans.rec_unit
        return santa_id

    def get_num_of_cmp_per_santa_id(self, santa_id):
        count = 0
        for trans in self.flow_progress:
            if (type(trans) is ccf_cfi_record_info) and trans.is_upi_c_u2c_rsp():
                if str(santa_id) in trans.rec_unit:
                    count = count + 1
        return count



    #UPI functions
    #################
    def get_upi_expected_protocol(self):
        if self.is_coherent_flow():
            return "UPI.C"
        else:
            return "UPI.NC"

    def final_state_dosent_macth_upi_cmp(self):
        if self.cbo_got_ufi_uxi_cmpo_e():
            return not self.final_state_llc_e()
        elif self.cbo_got_ufi_uxi_cmpo_m():
            return not self.final_state_llc_m()
        elif self.cbo_got_ufi_uxi_cmpo_si():
            return not self.final_state_llc_s()
        else:
            return True

    #In case we have several QW that are full and in a row we will put them in the same 2 pumps WB message.
    #else we will take each QW and give it separated message
    def get_num_of_data_chunk_exp_on_upi_nc(self):
        num_of_chunks = 0
        all_data = self.get_all_write_data_from_idi()
        full_QW_accumulating = False

        if "-" in all_data:
            chunk_QW = all_data.split(" ")
            for QW in chunk_QW:
                QW_dont_care_count = QW.count('-')
                partial_QW = (QW_dont_care_count != 16) and (QW_dont_care_count != 0)
                full_QW = (QW_dont_care_count == 0)

                if partial_QW:
                    num_of_chunks = num_of_chunks + 2
                    full_QW_accumulating = False
                elif full_QW and not full_QW_accumulating:
                    num_of_chunks = num_of_chunks + 2
                    full_QW_accumulating = True
                else:
                    full_QW_accumulating = False

            return num_of_chunks
        else:
            return ccf_systeminit.get_pointer().num_of_cfi_data_chunk

    def cbo_got_upi_NCretry(self):
        return self.cfi_upi_retry is not None and "NcRetry" in self.cfi_upi_retry



