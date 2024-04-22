#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_chk.py 
#
# Owner:              asaffeld
# Creation Date:      11.2020
#
# ###############################################
#
# Description:
#   This file contain all ccf_coherency coverage
#################################################################################################
from py_ral_cov import *
from agents.ccf_agent.ccf_coherency_agent.ccf_sad_mca_cov import SAD_MCA_CG
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cp, ccf_cg
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_MSG, val_utdb_component
from agents.ccf_systeminit.ccf_systeminit import ccf_systeminit
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.uxi_utils import UXI_UTILS

class DBP_TO_MSCACHE_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.dbp_info_cp = ccf_cp(["obserever_dead_bx0",
                                   "obserever_bx1",
                                   "obserever_not_dead",
                                   "follower_dead_bin0_downgrade0",
                                   "follower_dead_bin0_dropped",
                                   "follower_dead_bin0_downgrade1",
                                   "follower_not_dead_bin0",
                                   "follower_bin1_downgrade0",
                                   "follower_bin1_dropped",
                                   "follower_bin1_downgrade1"])

class SAD_CHANGE_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.lock_opcodes_cp = ccf_cp(["LOCK", "UNLOCK", "SPLITLOCK", "SPCYC"])
        self.lock_sad_results = ccf_cp(["CRABABORT", "NA"])
        self.origin_region = ccf_cp(["PAM", "LT", "PCIE_MMCFG", "SMM","VGAGSA", "ISA"])
        self.final_region = ccf_cp(["MMIOPTL","MMIO",  "CFG", "DRAM", "CRABABORT"])
        self.flow_opcode = ccf_cp(['CLDEMOTE', 'CLFLUSH', 'CLFLUSHOPT', 'CLRMONITOR',
                                   'CLWB', 'CRD', 'CRD_PREF', 'CRD_UC', 'DRD', 'DRD_NS', 'DRD_OPT', 'DRD_OPT_PREF', 'DRD_PREF',
                                   'DRDPTE', 'ITOM',  'LLCPREFCODE',
                                   'LLCPREFDATA', 'LLCPREFRFO',  'MEMPUSHWR', 'MEMPUSHWR_NS', 'PRD',
                                   'RDCURR', 'RFO', 'RFO_PREF', 'RFOWR', 'MONITOR', 'SPEC_ITOM', 'UCRDF',
                                   'WCIL', 'WCILF', 'WCIL_NS', 'WCILF_NS', 'WILF', 'WIL',
                                    'VICTIM', 'WBMTOE','WBEFTOE', 'WBMTOI', "WBEFTOI","WBSTOI" 
                                   #'ITOMWR', 'ITOMWR_NS', 'ITOMWR_WT', 'ITOMWR_WT_NS','LLCINV','LLCWB', 'LLCWBINV', 'LOCK', 'PORT_IN', 'PORT_OUT', 'FSRDCURR',, 'SPLITLOCK''FSRDCURRPTL', 'RDCURRPTL', 'WILPTL','FLOWN',
                                   ])

        #CROSS:
        self.sad_lock_change_cp = self.cross(self.lock_opcodes_cp, self.lock_sad_results)
        self.sad_region_change_cp = self.cross(self.origin_region,self.final_region,self.flow_opcode)

class CCF_CLKS_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):

        self.ring_pll_ratio_cp = ccf_cp(self.build_range_span(minimum=int(self.si.ring_min_pll_ratio),
                                                              maximum=int(self.si.ring_max_pll_ratio)))


class SPECIAL_ACCESS_OPCODE_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def get_set_span_string(self, set_num):
        for range in self.numeric_ranges_l:
            if (range[0] < set_num) and (range[1] > set_num):
                return self.create_set_span_string_from_start_end(range[0], range[1])
        return None

    def create_set_span_string_from_start_end(self, start, end):
        return "{}-{}".format(start, end)

    def create_span_of_set_ranges(self, num_of_set_in_each_range):
        total_num_of_set = CCF_COH_DEFINES.num_of_sets
        num_of_region = round(total_num_of_set / num_of_set_in_each_range)
        last_region = total_num_of_set % num_of_set_in_each_range

        span_list = []
        start = 0
        for i in range(num_of_region):
            end = start + num_of_set_in_each_range - 1
            self.numeric_ranges_l.append([start, end])
            span_list.append(self.create_set_span_string_from_start_end(start, end))
            start = end
        if last_region > 0:
            self.numeric_ranges_l.append([start, total_num_of_set - 1])
            span_list.append(self.create_set_span_string_from_start_end(start, total_num_of_set - 1))

        return span_list

    def coverpoints(self):
        self.numeric_ranges_l = []
        self.set_span_list = self.create_span_of_set_ranges(512)

        self.way_map_type_cp = ccf_cp(["SF", "DATA"])
        self.special_address_got_pa_match_cp = ccf_cp([0, 1])
        self.llc_set_ranges_cp = ccf_cp(self.set_span_list)
        self.llc_tag_way_cp = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_tag_ways)))
        self.llc_data_way_cp = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_data_ways)))
        self.special_access_opcodes_cp = ccf_cp(CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes_on_idi)

        self.special_access_opcodes_CROSS_special_address_got_pa_match_cp = self.cross(self.special_access_opcodes_cp, self.special_address_got_pa_match_cp)
        self.special_access_opcodes_CROSS_way_map_type_cp = self.cross(self.special_access_opcodes_cp, self.way_map_type_cp)


class CONFLICT_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.had_conflict_cp = ccf_cp([0, 1])
        self.snoop_opcodes_cp = ccf_cp(UXI_UTILS.uxi_coh_snp_opcodes)
        self.request_with_conflict_cp = ccf_cp(CCF_FLOW_UTILS.flow_opcodes)
        self.snoop_reject_due_to_no_allow_snoop_cp = ccf_cp([0, 1])
        self.conflict_type_cp = ccf_cp(["Early Conflict", "Late Conflict"])
        self.snoop_conflict_with_prefetch_promotion_cp = ccf_cp(["Trigger"])

        self.had_conflict_cp_CROSS_snoop_opcodes_cp = self.cross(self.had_conflict_cp, self.snoop_opcodes_cp)
        self.had_conflict_cp_CROSS_snoop_opcodes_cp.ignore(had_conflict_cp=0)
        self.request_with_conflicts_cp_CROSS_conflict_type_cp = self.cross(self.conflict_type_cp, self.request_with_conflict_cp)
        self.snoop_reject_due_to_no_allow_snoop_cp_CROSS_snoop_opcodes_cp = self.cross(self.snoop_reject_due_to_no_allow_snoop_cp, self.snoop_opcodes_cp)

class PREFETCH_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.prefetch_opcode_cp = ccf_cp(["LLCPREFDATA", "LLCPREFCODE", "LLCPREFRFO"])
        self.prefetch_hit_miss_cp = ccf_cp(["Hit", "Miss"])
        self.prefetch_avilable_data_way_cp = ccf_cp(["AvailData", "NoAvailData"])
        self.TOR_OccupancyTh_cp = ccf_cp(self.build_range_span(int(CCF_COH_DEFINES.num_of_tor_entries) + 1)) #Current TOR half is 19 entries (therefore TOOccupancy is between 0-20) if TOR total entry will be 64 this should be 31.
        self.TOR_Occupancy_cp = ccf_cp(self.build_range_span(int(CCF_COH_DEFINES.num_of_tor_entries) + 1))  # Current TOR half is 19 entries (therefore TOOccupancy is between 0-20) if TOR total entry will be 64 this should be 31.

        #General CROSS:
        self.prefetch_opcode_CROSS_prefetch_hit_miss_cp = self.cross(self.prefetch_opcode_cp, self.prefetch_hit_miss_cp)
        self.prefetch_opcode_CROSS_prefetch_avilable_data_way_cp = self.cross(self.prefetch_opcode_cp, self.prefetch_avilable_data_way_cp)
        self.prefetch_opcode_CROSS_TOR_OccupancyTh_CROSS_TOR_Occupancy_cp = self.cross(self.prefetch_opcode_cp, self.TOR_Occupancy_cp)


class PREFETCH_PROMOTION_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.promoted_opcode_cp = ccf_cp(["DRD", "DRD_NS", "DRD_OPT", "DRD_PREF", "DRD_OPT_PREF", "DRDPTE", "DRD_SHARED_OPT", "DRD_SHARED_PREF", "CRD", "CRD_PREF", "RFO", "RFO_PREF","MONITOR"])
        self.prefetch_opcode_cp = ccf_cp(["LLCPREFDATA", "LLCPREFCODE", "LLCPREFRFO"])
        self.prefetch_hit_miss_cp = ccf_cp(["Hit", "Miss"])
        self.prefetch_avilable_data_way_cp = ccf_cp(["AvailData", "NoAvailData"])

        self.prefetch_promotion_cp = ccf_cp([0, 1])
        self.TOR_Occupancy_cp = ccf_cp(self.build_range_span(int(CCF_COH_DEFINES.num_of_tor_entries) + 1))  # Current TOR half is 19 entries (therefore TOOccupancy is between 0-20) if TOR total entry will be 64 this should be 31.
        self.TOR_OccupancyTh_cp = ccf_cp(self.build_range_span(int(CCF_COH_DEFINES.num_of_tor_entries) + 1))  # Current TOR half is 19 entries (therefore TOOccupancy is between 0-20) if TOR total entry will be 64 this should be 31.

        #Prefetch elimination
        self.prefetch_elimination_cp = ccf_cp([0, 1])

        #General CROSS:
        self.prefetch_opcode_CROSS_prefetch_hit_miss_cp = self.cross(self.prefetch_opcode_cp, self.prefetch_hit_miss_cp)
        self.prefetch_opcode_CROSS_prefetch_avilable_data_way_cp = self.cross(self.prefetch_opcode_cp, self.prefetch_avilable_data_way_cp)
        self.prefetch_opcode_CROSS_prefetch_promotion_cp = self.cross(self.prefetch_opcode_cp, self.prefetch_promotion_cp)
        self.prefetch_opcode_CROSS_TOR_OccupancyTh_CROSS_TOR_Occupancy_cp = self.cross(self.prefetch_opcode_cp, self.TOR_OccupancyTh_cp)

        #promotion CROSS
        self.promoted_opcode_CROSS_prefetch_opcode_cp = self.cross(self.promoted_opcode_cp, self.prefetch_opcode_cp, self.prefetch_promotion_cp)
        self.promoted_opcode_CROSS_prefetch_opcode_cp.ignore(prefetch_promotion_cp=0)

        #elimination CROSS
        self.prefetch_elimination_CROSS_prefetch_opcode_cp = self.cross(self.prefetch_opcode_cp,self.prefetch_elimination_cp)


class HASH_AND_REMAP_CG(ccf_cg):
    def __init__(self):
        self.hash_type_list = ["Read", "Write", "ReqFwdCnflt", "SnpRsp", "C2U_data", "NC"]
        self.half_id_list = ["0", "1"]
        super().__init__()

    def coverpoints(self):
        self.Santa_Hash = ccf_cp(["Santa0", "Santa1"])
        self.HBO_Hash = ccf_cp(["HBO0", "HBO1"])
        self.InsideCBOID = ccf_cp(self.half_id_list) #Half ID for WR Santa hashing
        self.hash_type = ccf_cp(self.hash_type_list)

        self.hash_type_CROOS_Santa_Hash = self.cross(self.hash_type, self.Santa_Hash)
        self.hash_type_CROSS_HBO_Hash = self.cross(self.hash_type, self.HBO_Hash)

class CCF_GENERAL_FLOW_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def address_bit_cov_span(self, opcode_list, address_msb_bit):
        #The follow opcodes are not relevant in LNL-M
        opcode_exclude_list = ['ATOMICWR', 'ATOMICRDWR', 'ATOMICRD', 'ITOMWR', 'ITOMWR_NS', 'ITOMWR_WT', 'ITOMWR_WT_NS', 'RDCURR', 'RFOWR', 'FLOWN', 'FSRDCURR', 'FSRDCURRPTL', 'RDCURRPTL', 'WILPTL']
        span_list = list()
        for opcode in opcode_list:
            if opcode not in opcode_exclude_list:
                for i in range(address_msb_bit):
                    span_list.append("{}_bit_{}".format(opcode, i))
        return span_list

    def opcode_cross_bit_cov_span(self, opcode_list, bit_name, exclude_hbo_snoops=False, exclude_flusher=False):
        #The follow opcodes are not relevant in LNL-M
        opcode_exclude_list = ['ATOMICWR', 'ATOMICRDWR', 'ATOMICRD', 'ITOMWR', 'ITOMWR_NS', 'ITOMWR_WT', 'ITOMWR_WT_NS', 'RDCURR', 'RFOWR', 'FLOWN', 'FSRDCURR', 'FSRDCURRPTL', 'RDCURRPTL', 'WILPTL', 'VICTIM']

        span_list = list()
        for opcode in opcode_list:
            if (opcode not in opcode_exclude_list) and not (exclude_hbo_snoops and UXI_UTILS.is_in_coh_snp_opcodes(opcode)) and not (exclude_flusher and opcode == "FLUSHER"):
                span_list.append("{}_{}_{}".format(opcode, bit_name, "0"))
                span_list.append("{}_{}_{}".format(opcode, bit_name, "1"))
        return span_list

    def data_way_cov_span(self):
        data_way_span = []
        for data_way_index in range(CCF_COH_DEFINES.max_num_of_data_ways):
            data_way_span.append("DWAY_{}".format(data_way_index))
        data_way_span.append("SF_ENTRY")
        return data_way_span

    def coverpoints(self):
        self.Opcode = ccf_cp(CCF_FLOW_UTILS.flow_opcodes) #add all opcodes
        self.address_bits = ccf_cp(self.address_bit_cov_span(CCF_FLOW_UTILS.flow_opcodes, CCF_COH_DEFINES.mktme_msb))
        self.selfsnoop_per_opcode = ccf_cp(self.opcode_cross_bit_cov_span(CCF_FLOW_UTILS.flow_opcodes, "selfsnoop", exclude_hbo_snoops=True, exclude_flusher=True))
        self.cachenear_per_opcode = ccf_cp(self.opcode_cross_bit_cov_span(CCF_FLOW_UTILS.flow_opcodes, "cachenear", exclude_hbo_snoops=True, exclude_flusher=True))
        self.GO_S_OPT = ccf_cp([0, 1])
        self.force_no_avilable_data_due_to_AllDataWaysAreReserved_reject = ccf_cp(["Trigger"])
        self.CN_from_idi = ccf_cp([0, 1])
        self.CN_ynn = ccf_cp([0, 1])
        self.CN_register_force = ccf_cp([0, 1])
        self.CN_effective = ccf_cp([0, 1])
        self.CROSS_CN_DRIVERS = self.cross(self.CN_effective, self.CN_from_idi, self.CN_ynn, self.CN_register_force)
        self.CROSS_CN_DRIVERS.ignore(CN_effective='0')
        self.sad_result = ccf_cp(['HOM', 'MMIO', 'MMIOPTL', 'CFG', 'IO', 'CRABABORT', 'LT', 'NA', None])
        self.mktme_crababort = ccf_cp([True, False])
        self.legal_mktme_sad = ccf_cp(['DRAM', 'MMIO', 'MMIOPTL', 'CFG', 'IO', 'CRABABORT', 'NA'])
        self.data_way = ccf_cp(self.data_way_cov_span())
        self.tag_way = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_tag_ways)))
        self.victim_data_way = ccf_cp(self.data_way_cov_span())
        self.victim_tag_way = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_tag_ways)))
        self.CROSS_tag_way = self.cross(self.data_way, self.tag_way)
        self.core_dbp_params = ccf_cp([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 21, 23, 25, 27, 29, 30, 31]) #TODO: this is looks weird please check why the values are not 0-31 and we have missing numbers.
        self.GO_NOGO = ccf_cp(["Trigger"])
        self.no_data_avail_due_to_all_data_way_reserved = ccf_cp(["trigger when LLC_I", "trigger when cb is set"])
        self.cv_err = ccf_cp([True, False])
        self.cv_err_legacy_mode = ccf_cp([0, 1])
        self.CROSS_cv_err_x_cv_err_legacy_mode = self.cross(self.cv_err , self.cv_err_legacy_mode)

class CCF_REGISTERS_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def span_register_per_cbo(self, optional_values: list):
        cbo_name_list = list()
        for cbo_id in range(0, self.si.num_of_cbo):
            for reg_val in optional_values:
                cbo_name_list.append("CBO_{}:Val_{}".format(cbo_id, reg_val))
        return cbo_name_list

    def coverpoints(self):
        self.YMM_MASK = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_data_ways)))
        self.MKTME_MASK = ccf_cp([i for i in range(0, pow(2, 11))]) #11 bits; Python range() do not include last value
        self.DIS_WB2MMIOFIX = ccf_cp([0, 1])
        self.PAM_DRAM = ccf_cp([0,1,2,3]) # 1 and 2 are not relevant for LNLM, 0 is the default
        self.PREFETCH_ELIMINATION = ccf_cp([0, 1])
        self.ENABLE_PREFERTCH_PROMOTION = ccf_cp([0, 1])
        self.LLC_PREFETCH_TOR_OCCUPENCY_TH = ccf_cp(self.build_range_span(int(CCF_COH_DEFINES.num_of_tor_entries/2)))
        self.FORCE_SELFSNOOP_ALL = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_SNOOPFILTER_ONLY = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_DRD = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_DRD_PREFETCH = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_CRD = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_CRD_PREFETCH = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_RFO = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.FORCE_SELFSNOOP_RFO_PREFETCH = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.DRD_ALWAYS_CACHENEAR = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.CRD_ALWAYS_CACHENEAR = ccf_cp(self.span_register_per_cbo([0, 1]))
        self.RFO_ALWAYS_CACHENEAR = ccf_cp(self.span_register_per_cbo([0, 1]))

class CCF_MONITOR_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.num_of_cores_with_monitor_in_monitor_hit = ccf_cp(list(range(0, self.si.num_of_cbo * 2 + 1))) # 2 threads per core
        self.num_of_used_entries = ccf_cp(list(range(0, CCF_COH_DEFINES.num_of_monitor_entries + 1)))
        self.setmonitor_hit_region = ccf_cp(["DRAM", "CRABABORT"]) ##monitor to non hom region is MMIO
        self.copy_monitor_num_of_expected = ccf_cp(list(range(CCF_COH_DEFINES.num_of_monitor_copy_addresses + 1)))
        self.copy_monitor_addr = ccf_cp(["with mktme","no mktme", "addr 0x0"])

class CCF_VULNERABLE_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.hit_cl_that_marked_as_vulnerable = ccf_cp([1])
        self.dway_marked_with_data_vulnerable = ccf_cp(self.build_range_span(CCF_COH_DEFINES.max_num_of_data_ways))

class CCF_CLOS_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def span_num_of_cbo(self):
        cbo_name_list = list()
        for cbo_id in range(0, self.si.num_of_cbo):
            cbo_name_list.append("CBO_{}".format(cbo_id))
        return cbo_name_list

    def span_clos_tag_way_reg(self):
        clos_tag_way_reg = list()
        for cbo_id in range(0, self.si.num_of_cbo):
            for clos in range(0, CCF_COH_DEFINES.num_of_clos_supported):
                for tag_way in range(0, CCF_COH_DEFINES.clos_reg_tag_way_size):
                    clos_tag_way_reg.append("[CBO_{}][clos_{}][tag_way_{}][policy:0]".format(cbo_id, clos, tag_way))
                    clos_tag_way_reg.append("[CBO_{}][clos_{}][tag_way_{}][policy:1]".format(cbo_id, clos, tag_way))
        return clos_tag_way_reg
    def span_clos_data_way_reg(self):
        clos_data_way_reg = list()
        for cbo_id in range(0, self.si.num_of_cbo):
            for clos in range(0, CCF_COH_DEFINES.num_of_clos_supported):
                for data_way in range(0, CCF_COH_DEFINES.max_num_of_data_ways):
                    clos_data_way_reg.append("[CBO_{}][clos_{}][data_way_{}][policy:0]".format(cbo_id, clos, data_way))
                    clos_data_way_reg.append("[CBO_{}][clos_{}][data_way_{}][policy:1]".format(cbo_id, clos, data_way))
        return clos_data_way_reg

    def coverpoints(self):
        #CBO CLOS
        self.clos = ccf_cp(list(range(0, CCF_COH_DEFINES.num_of_clos_supported)))
        self.tag_way = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_tag_ways)))
        self.data_way = ccf_cp(list(range(0, CCF_COH_DEFINES.max_num_of_data_ways)) + ["SF_ENTRY"])

        #CXM CLOS
        self.cxm_req_priority_demand_qos = ccf_cp([0, 1, 2, 3])
        self.cxm_req_priority_pref_qos = ccf_cp([0, 1, 2, 3])
        self.tc = ccf_cp([0, 1, 2, 3])
        self.llc_prefetch_opcode = ccf_cp(["LLCPREFCODE", "LLCPREFDATA", "LLCPREFRFO"])
        self.mlc_prefetch_opcode = ccf_cp(CCF_FLOW_UTILS.MLC_PREF_for_cxm_priority)
        self.demand_read_opcode = ccf_cp(CCF_FLOW_UTILS.DEMAND_READs_for_cxm_priority)
        self.clos_to_tc_mlc_pref_is_demand = ccf_cp([0, 1])

        #CBO Cross
        self.tag_way_CROSS_clos_CROSS_clos_policy_cp = self.cross(self.tag_way, self.clos)
        self.data_way_CROSS_clos_CROSS_clos_policy_cp = self.cross(self.data_way, self.clos)

        #CXM CROSS
        self.cxm_req_priority_demand_qos_CROSS_clos = self.cross(self.cxm_req_priority_demand_qos, self.clos)
        self.cxm_req_priority_pref_qos_CROSS_clos = self.cross(self.cxm_req_priority_pref_qos, self.clos)
        self.tc_CROSS_clos_CROSS_llc_prefetch_opcode = self.cross(self.tc, self.clos, self.llc_prefetch_opcode)
        self.tc_CROSS_clos_CROSS_mlc_prefetch_opcode = self.cross(self.tc, self.clos, self.mlc_prefetch_opcode)
        self.tc_CROSS_clos_CROSS_demand_read_opcode = self.cross(self.tc, self.clos, self.demand_read_opcode)
        self.clos_to_tc_mlc_pref_is_demand_CROSS_mlc_prefetch_opcode = self.cross(self.clos_to_tc_mlc_pref_is_demand, self.mlc_prefetch_opcode)

        # Events
        self.cbo_data_way_clos_policy_are_zero = ccf_cp(self.span_num_of_cbo())
        self.all_data_way_clos_policy_are_zero = ccf_cp([1])
        #self.only_one_tag_way_avil_for_each_clos_policy = ccf_cp([1])

        self.tag_way_policy_reg = ccf_cp(self.span_clos_tag_way_reg())
        self.data_way_policy_reg = ccf_cp(self.span_clos_data_way_reg())


class CCF_CHECKER_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.checker = ccf_cp(["ccf_lfc_chk", "ccf_go_chk", "ccf_snoop_chk", "ccf_data_chk", "ccf_llc_chk",
                               "ccf_bw_counter_chk", "ccf_pmon_chk", "ccf_sad_mca_chk", "ccf_transition_chk", "ccf_prefetch_dpt_chk",
                               "conflict_checker", "mem_hash_chk", "ccf_general_flow_chk", "ccf_dbp_chk_and_update"])

class CCF_CFI_ORDER_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.data_pkt_and_cmp_pkt_order = ccf_cp(["CMP_BEFORE_DATA", "CMP_AFTER_DATA", "CMP_BETWEEN_DATA_CHUNKS"])



class CCF_SYSTEMINIT_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):

        self.NUM_OF_CBO = ccf_cp(list(range(0, 13))) #max 12 cores?
        self.CBO_DISABLE_MASK = ccf_cp([i for i in range(0,2 ** self.si.num_of_cbo)])
        self.MODULE_DISABLE_MASK = ccf_cp(list(range(0, 2 ** self.si.num_of_cbo)))
        self.CCF_MKTME_MASK = ccf_cp(list(range(0, 16))) #4 bits;
        self.CCF_PCIEXBAR_EN = ccf_cp([0, 1])


class end_of_test_collect_cov(val_utdb_component):
    def __init__(self):
        self.set_si(ccf_systeminit.get_pointer())
        self.ccf_clos_cg = CCF_CLOS_CG.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        
        if not self.si.ccf_soc_mode:
            self.ccf_clks_cg = CCF_CLKS_CG.get_pointer()

    def collect_clks_cov(self):
        #if self.si.ccf_soc_mode:

            if self.ccf_clks_cg.is_bin_in_cp_span("ring_pll_ratio_cp", str(self.si.ccf_ring_pll_ratio), True):
                self.ccf_clks_cg.sample(ring_pll_ratio_cp=str(self.si.ccf_ring_pll_ratio))

    def collect_reg_clos_cov(self):
        all_data_way_are_zero = True

        for cbo_id in range(0, self.si.num_of_cbo):
            cbo_data_way_are_zero=True
            for clos in range(0, CCF_COH_DEFINES.num_of_clos_supported):
                for data_way in range(0, CCF_COH_DEFINES.max_num_of_data_ways):
                    clos_policy = self.ccf_registers.ia_cos_ways__closways[cbo_id][clos][data_way]

                    if clos_policy == 1:
                        all_data_way_are_zero=False
                        cbo_data_way_are_zero=False

                    self.ccf_clos_cg.sample(data_way_policy_reg="[CBO_{}][clos_{}][data_way_{}][policy:{}]".format(cbo_id, clos, data_way, clos_policy))
            
            if cbo_data_way_are_zero:
                self.ccf_clos_cg.sample(cbo_data_way_clos_policy_are_zero="CBO_{}".format(cbo_id))

        if all_data_way_are_zero:
            self.ccf_clos_cg.sample(all_data_way_clos_policy_are_zero=1)

        for cbo_id in range(0, self.si.num_of_cbo):
            for clos in range(0, CCF_COH_DEFINES.num_of_clos_supported):
                for tag_way in range(0, CCF_COH_DEFINES.clos_reg_tag_way_size):
                    clos_policy = self.ccf_registers.ia_cos_ways__closways[cbo_id][clos][tag_way]
                    self.ccf_clos_cg.sample(tag_way_policy_reg="[CBO_{}][clos_{}][tag_way_{}][policy:{}]".format(cbo_id, clos, tag_way, clos_policy))

    def collect_register_coverage(self):
        ccf_register_cg = CCF_REGISTERS_CG.get_pointer()

        for i_phy in self.ccf_registers.cbo_phy_id_list:
            ccf_register_cg.sample(PREFETCH_ELIMINATION=self.ccf_registers.prefetch_elimination_en[i_phy])
            ccf_register_cg.sample(ENABLE_PREFERTCH_PROMOTION=self.ccf_registers.enable_prefetch_promotion[i_phy])

            ymm_mask_bint = bint(self.ccf_registers.ymm_mask[i_phy])
            for way_id in range(CCF_COH_DEFINES.max_num_of_data_ways):
                if ymm_mask_bint[way_id] == 1:
                    ccf_register_cg.sample(YMM_MASK=way_id)

            ccf_register_cg.sample(MKTME_MASK=self.ccf_registers.mktme_mask[i_phy])
            ccf_register_cg.sample(DIS_WB2MMIOFIX=self.ccf_registers.dis_wb2mmio_fix[i_phy])
            ccf_register_cg.sample(LLC_PREFETCH_TOR_OCCUPENCY_TH=str(self.ccf_registers.tor_occupency_th[i_phy]))
            #NI_CONTROL register fields
            ccf_register_cg.sample(FORCE_SELFSNOOP_ALL="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_all[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_SNOOPFILTER_ONLY="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_snoopfilter_only[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_DRD="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_drd[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_DRD_PREFETCH="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_drd_prefetch[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_CRD="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_crd[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_CRD_PREFETCH="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_crd_prefetch[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_RFO="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_rfo[i_phy]))
            ccf_register_cg.sample(FORCE_SELFSNOOP_RFO_PREFETCH="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.force_selfsnoop_rfo_prefetch[i_phy]))
            ccf_register_cg.sample(DRD_ALWAYS_CACHENEAR="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.drd_always_cachenear[i_phy]))
            ccf_register_cg.sample(CRD_ALWAYS_CACHENEAR="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.crd_always_cachenear[i_phy]))
            ccf_register_cg.sample(RFO_ALWAYS_CACHENEAR="CBO_{}:Val_{}".format(i_phy, self.ccf_registers.rfo_always_cachenear[i_phy]))


            #For PAM
            #for j in range(0, 7):
            #    if j != 0:
            #        ccf_register_cg.sample(PAM_DRAM=self.ccf_registers.pam_normal_dram_operation[i_phy][j][0])
            #    ccf_register_cg.sample(PAM_DRAM=self.ccf_registers.pam_normal_dram_operation[i_phy][j][1])

    def collect_end_of_test_coverage(self):
        self.collect_register_coverage()
        self.collect_reg_clos_cov()
        if not self.si.ccf_soc_mode:
            self.collect_clks_cov()

class ccf_coherency_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.ccf_general_flow_cg: CCF_GENERAL_FLOW_CG = CCF_GENERAL_FLOW_CG.get_pointer()
        self.hash_and_remap_cg: HASH_AND_REMAP_CG = HASH_AND_REMAP_CG.get_pointer()
        self.prefetch_promotion: PREFETCH_PROMOTION_CG = PREFETCH_PROMOTION_CG.get_pointer()
        self.prefetch_cg: PREFETCH_CG = PREFETCH_CG.get_pointer()
        self.conflict_cg: CONFLICT_CG = CONFLICT_CG.get_pointer()
        self.special_access_opcode_cg: SPECIAL_ACCESS_OPCODE_CG = SPECIAL_ACCESS_OPCODE_CG.get_pointer()
        self.sad_mca_cg: SAD_MCA_CG = SAD_MCA_CG.get_pointer()
        self.ccf_registers_cg: CCF_REGISTERS_CG = CCF_REGISTERS_CG.get_pointer()
        self.ccf_systeminit_cg: CCF_SYSTEMINIT_CG = CCF_SYSTEMINIT_CG.get_pointer()
        self.sad_change_cg: SAD_CHANGE_CG =SAD_CHANGE_CG.get_pointer()
        self.ccf_dbp_to_mscache_cg: DBP_TO_MSCACHE_CG = DBP_TO_MSCACHE_CG.get_pointer()
        self.ccf_monitor_cg: CCF_MONITOR_CG = CCF_MONITOR_CG.get_pointer()
        self.ccf_vulnerable_cg: CCF_VULNERABLE_CG = CCF_VULNERABLE_CG.get_pointer()
        self.ccf_clos_cg: CCF_CLOS_CG = CCF_CLOS_CG.get_pointer()
        self.ccf_chk_cg: CCF_CHECKER_CG = CCF_CHECKER_CG.get_pointer()
        self.ccf_cfi_order_cg: CCF_CFI_ORDER_CG = CCF_CFI_ORDER_CG.get_pointer()
        if not self.si.ccf_soc_mode:
            self.ccf_clks_cg: CCF_CLKS_CG = CCF_CLKS_CG.get_pointer()
        self.initial_reg_cov_config()

    def initial_reg_cov_config(self):
        ral = PyRalDb()
        top_block = ral.get_regmodel()

        params = PyRalCovParams()
        params.minimal_time_start_collect = 100
        params.field_size_for_full_range_span = 5
        params.cov_result_type = "UNICOV"
        params.cg_name_format = "REG_INSTANCE"
        params.cov_module_name = "CCF_REGISTER_COV"

        self.saola_reg_cov = PyRalCov(top_block, params)


    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        self.ccf_coherency_qry: ccf_coherency_qry = ccf_coherency_qry.get_pointer()
        end_of_test_collect_cov.get_pointer().collect_end_of_test_coverage()
        if not self.si.ccf_soc_mode:
            self.saola_reg_cov.collect_coverage()
        VAL_UTDB_MSG(time=0, msg='Hello World :)')




