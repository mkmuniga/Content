from val_utdb_bint import bint

from agents.ccf_agent.ccf_pmon_chk_agent.ccf_pmon_chk_cov import CCF_PMON_CG
from agents.ccf_common_base.ccf_common_base import ccf_llc_record_info, ccf_cfi_record_info
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import CONFLICT_CG, SPECIAL_ACCESS_OPCODE_CG, \
    PREFETCH_PROMOTION_CG, PREFETCH_CG, CCF_MONITOR_CG, CCF_CLOS_CG, CCF_CFI_ORDER_CG, CCF_GENERAL_FLOW_CG,CCF_SYSTEMINIT_CG 
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_components import val_utdb_component
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG, VAL_UTDB_DEBUG
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.uxi_utils import UXI_UTILS


class clos_coverage(val_utdb_component):
    def __init__(self):
        self.ccf_clos_cg = CCF_CLOS_CG.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()

    def collect_llc_clos_cov(self, flow: ccf_flow, collect=None):
        if collect == "TAG_WAY":
            self.ccf_clos_cg.sample(clos=flow.get_clos_value(), tag_way=int(flow.final_tag_way))
        elif collect == "DATA_WAY":
            if flow.final_map == "SF_ENTRY":
                data_way = "SF_ENTRY"
            else:
                data_way = int(flow.final_map.split("DWAY_")[1])
            self.ccf_clos_cg.sample(clos=flow.get_clos_value(), data_way=data_way)
        else:
            VAL_UTDB_MSG(time=0, msg="COVERAGE INFO - you didn't gave the coverage collect valid value: collect={}".format(str(collect)))

class conflict_coverage(val_utdb_component):
    def __init__(self):
        self.ccf_cpipe_window_utils_ptr = ccf_cpipe_window_utils.get_pointer()
        self.ccf_conflict_cg = CONFLICT_CG.get_pointer()

    def collect_cov_event__snoop_conflict_with_prefetch_promotion(self):
        self.ccf_conflict_cg.sample(snoop_conflict_with_prefetch_promotion_cp="Trigger")

    def end_of_flow_collect_conflict_cov(self, flow: ccf_flow):
        if flow.opcode in UXI_UTILS.uxi_coh_snp_opcodes:


            had_conflict_sample = 1 if flow.had_conflict else 0
            snoop_opcodes_sample = flow.opcode

            if any([True for reject in flow.rejected_reasons if reject.reject_reason == "RejectDueNotAllowSnoop"]):
                snoop_reject_due_to_no_allow_snoop_sample = 1
            else:
                snoop_reject_due_to_no_allow_snoop_sample = 0

            if flow.had_conflict:
                ccf_addr_entry = self.ccf_cpipe_window_utils_ptr.get_transaction_allocation_entry(flow.address, flow.uri['TID'], flow.uri['LID'])
                original_idi_flow = ccf_dbs.ccf_flows[ccf_addr_entry.conflict_with_uri]

                FwdCnfltO_time = flow.get_arbcommand_time("FwdCnfltO")
                CmpO_time = original_idi_flow.get_arbcommand_time("CmpO")

                if ((FwdCnfltO_time is None) or (CmpO_time is None)):
                    VAL_UTDB_MSG(time=0, msg="COVERAGE INFO - Something is wrong FwdCnfltO_time or CmpO_time is still None that cannot be in conflict senario")
                else:
                    if FwdCnfltO_time < CmpO_time:
                        self.ccf_conflict_cg.sample(conflict_type_cp="Early Conflict")
                        self.ccf_conflict_cg.sample(conflict_type_cp="Early Conflict", request_with_conflict_cp=ccf_dbs.ccf_flows[ccf_addr_entry.conflict_with_uri].opcode)
                    else:
                        self.ccf_conflict_cg.sample(conflict_type_cp="Late Conflict")
                        self.ccf_conflict_cg.sample(conflict_type_cp="Late Conflict", request_with_conflict_cp=ccf_dbs.ccf_flows[ccf_addr_entry.conflict_with_uri].opcode)

            self.ccf_conflict_cg.sample(had_conflict_cp=had_conflict_sample,
                                        snoop_opcodes_cp=snoop_opcodes_sample,
                                        snoop_reject_due_to_no_allow_snoop_cp=snoop_reject_due_to_no_allow_snoop_sample)



class ccf_flow_cov(ccf_base_component):
    def __init__(self):
        self.cov_en = 0
        self.ccf_cpipe_window_utils_ptr = ccf_cpipe_window_utils.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.conflict_coverage = conflict_coverage.get_pointer()

    def collect_special_opcode_cov(self, flow: ccf_flow):
        if flow.opcode in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes_on_idi:
            special_access_opcode_cg = SPECIAL_ACCESS_OPCODE_CG.get_pointer()

            way_map_type_sampled = "DATA" if flow.initial_map_dway() else "SF"

            if any([True for reject in flow.rejected_reasons if reject.reject_reason == "RejectDuePaMatch"]):
                special_address_got_pa_match_sample = 1
            else:
                special_address_got_pa_match_sample = 0

            llc_set_ranges_sample = None
            llc_tag_way_sample = None
            llc_data_way_sample = None

            for trans in flow.flow_progress:
                if isinstance(trans, ccf_llc_record_info) and ("R" in trans.rec_opcode):
                    llc_set_ranges_sample = special_access_opcode_cg.get_set_span_string(int(trans.rec_set, 16))
                    llc_tag_way_sample = int(trans.rec_way)
                    if (trans.rec_map != None and "-" not in trans.rec_map):
                        llc_data_way_sample =  int(trans.rec_map)

            if (llc_tag_way_sample is not None) and (llc_set_ranges_sample is not None) and (llc_data_way_sample is not None):
                if llc_data_way_sample != CCF_COH_DEFINES.SNOOP_FILTER:
                    special_access_opcode_cg.sample(way_map_type_cp=way_map_type_sampled,
                                                    special_address_got_pa_match_cp=special_address_got_pa_match_sample,
                                                    llc_set_ranges_cp=llc_set_ranges_sample,
                                                    llc_tag_way_cp=llc_tag_way_sample,
                                                    llc_data_way_cp=llc_data_way_sample,
                                                    special_access_opcodes_cp=flow.opcode)
                else:
                    special_access_opcode_cg.sample(way_map_type_cp=way_map_type_sampled,
                                                    special_address_got_pa_match_cp=special_address_got_pa_match_sample,
                                                    llc_set_ranges_cp=llc_set_ranges_sample,
                                                    llc_tag_way_cp=llc_tag_way_sample,
                                                    special_access_opcodes_cp=flow.opcode)
            else:
                VAL_UTDB_MSG(time=0, msg="COVERAGE INFO - Couldn't sample the follow opcode since we didn't found SET or WAY or DATA WAY")





    def collect_ccf_flow_cg_cov(self, flow: ccf_flow):
        ccf_general_flow_cg = CCF_GENERAL_FLOW_CG.get_pointer()
        force_no_avilable_data_sample = flow.force_non_avilable_data_way()


        cov_opcode = flow.opcode.upper()
        if cov_opcode in CCF_FLOW_UTILS.flow_opcodes:
            ccf_general_flow_cg.sample(Opcode=flow.opcode.upper())
            bint_address = bint(int(flow.address, 16))
            for i in range(CCF_COH_DEFINES.mktme_msb):
                if bint_address[i] == 1:
                    bin = "{}_bit_{}".format(cov_opcode, i)
                    ccf_general_flow_cg.sample(address_bits=bin)


            if not UXI_UTILS.is_in_coh_snp_opcodes(cov_opcode):
                # selfsnoop:
                bin = "{}_{}_{}".format(cov_opcode, "selfsnoop", flow.selfsnoop)
                if ccf_general_flow_cg.is_bin_in_cp_span("selfsnoop_per_opcode", bin):
                    ccf_general_flow_cg.sample(selfsnoop_per_opcode=bin)

                #cachenear:
                bin = "{}_{}_{}".format(cov_opcode, "cachenear", flow.cache_near)
                if ccf_general_flow_cg.is_bin_in_cp_span("cachenear_per_opcode", bin):
                    ccf_general_flow_cg.sample(cachenear_per_opcode=bin)
        else:
            VAL_UTDB_MSG(time=0, msg="COVERAGE INFO - Couldn't sample the follow opcode since it's not known opcode in span - opcode: {}".format(cov_opcode))

        ccf_general_flow_cg.sample(sad_result=flow.sad_results)
        ccf_general_flow_cg.sample(CN_from_idi=(flow.cache_near == '1'))
        ccf_general_flow_cg.sample(CN_ynn=flow.is_yens_magic_msr())
        ccf_general_flow_cg.sample(CN_register_force=flow.is_always_cache_near())
        ccf_general_flow_cg.sample(CN_effective=(flow.get_effective_cache_near_value() == '1'),
                                   CN_from_idi=(flow.cache_near == '1'),
                                   CN_ynn=flow.is_yens_magic_msr(),
                                   CN_register_force=flow.is_always_cache_near())

        if flow.cbo_id_phys is not None:
            ccf_general_flow_cg.sample(cv_err = flow.has_cv_err())
            ccf_general_flow_cg.sample(cv_err = flow.has_cv_err(), cv_err_legacy_mode= self.ccf_registers.cv_err_legacy_mode[flow.cbo_id_phys])

        if flow.idi_dbp_params is not None:
            ccf_general_flow_cg.sample(core_dbp_params=int(flow.idi_dbp_params, 16))
        if flow.is_idi_flow_origin():
            ccf_general_flow_cg.sample(GO_S_OPT=int(flow.go_s_opt))
            if force_no_avilable_data_sample:
                ccf_general_flow_cg.sample(force_no_avilable_data_due_to_AllDataWaysAreReserved_reject="Trigger")
        if (flow.final_state_llc_m_or_e_or_s()):
            ccf_general_flow_cg.sample(data_way=flow.final_map)
            ccf_general_flow_cg.sample(tag_way=int(flow.final_tag_way))
            ccf_general_flow_cg.sample(data_way=flow.final_map,tag_way=int(flow.final_tag_way))

        if flow.cbo_sent_go_nogo():
            ccf_general_flow_cg.sample(GO_NOGO="Trigger")
        if flow.is_idi_flow_origin() and flow.force_non_avilable_data_way():
            if self.ccf_registers.enable_force_noavaildataway_in_any_reject[flow.cbo_id_phys]:
                ccf_general_flow_cg.sample(no_data_avail_due_to_all_data_way_reserved="trigger when cb is set")
            else:
                ccf_general_flow_cg.sample(no_data_avail_due_to_all_data_way_reserved="trigger when LLC_I")

        if flow.is_victim_line():
            for time, vic in flow.victim_flow.items():
                ccf_general_flow_cg.sample(victim_data_way=vic['MAP'])
                ccf_general_flow_cg.sample(victim_tag_way=int(vic['TAG_WAY']))

    def collect_prefetch_promotion_cov(self, flow: ccf_flow):
        prefetch_promotion_cg = PREFETCH_PROMOTION_CG.get_pointer()

        hit_miss = "Hit" if flow.hit_in_cache() else "Miss"

        avail_data = "AvailData" if flow.is_available_data() else "NoAvailData"

        prefetch_promotion = 1 if flow.is_flow_promoted() else 0

        prefetch_elimination = 1 if flow.is_prefetch_elimination_flow() else 0

        cbo_phy_id = flow.cbo_id_phys if flow.cbo_id_phys is not None else 0

        TOR_Occupancy_value = flow.tor_occupancy

        TOR_OccupancyTh_reg_value = str(self.ccf_registers.tor_occupency_th[flow.cbo_id_phys])

        if flow.is_flow_promoted():
            if ((TOR_Occupancy_value == "-") or (TOR_Occupancy_value == None)):
                prefetch_promotion_cg.sample(promoted_opcode_cp=flow.opcode,
                                         prefetch_opcode_cp=ccf_dbs.ccf_flows[flow.promotion_flow_orig_pref_uri].opcode,
                                         prefetch_hit_miss_cp=hit_miss,
                                         prefetch_avilable_data_way_cp=avail_data,
                                         prefetch_promotion_cp=prefetch_promotion,
                                         TOR_OccupancyTh_cp=TOR_OccupancyTh_reg_value)
            else:
                prefetch_promotion_cg.sample(promoted_opcode_cp=flow.opcode,
                                         prefetch_opcode_cp=ccf_dbs.ccf_flows[flow.promotion_flow_orig_pref_uri].opcode,
                                         prefetch_hit_miss_cp=hit_miss,
                                         prefetch_avilable_data_way_cp=avail_data,
                                         prefetch_promotion_cp=prefetch_promotion,
                                         TOR_OccupancyTh_cp=TOR_OccupancyTh_reg_value,
                                         TOR_Occupancy_cp=TOR_Occupancy_value)


        if flow.is_prefetch_elimination_flow():
            prefetch_promotion_cg.sample(prefetch_opcode_cp=flow.opcode,
                                         prefetch_elimination_cp=prefetch_elimination)

    def collect_simple_prefetch_cov(self, flow: ccf_flow):
        prefetch_cg = PREFETCH_CG.get_pointer()
        prefetch_promotion_cg = PREFETCH_PROMOTION_CG.get_pointer()

        hit_miss = "Hit" if flow.hit_in_cache() else "Miss"
        avail_data = "AvailData" if flow.is_available_data() else "NoAvailData"

        TOR_Occupancy_value = flow.tor_occupancy
        TOR_OccupancyTh_reg_value = str(self.ccf_registers.tor_occupency_th[flow.cbo_id_phys])


        if ((TOR_Occupancy_value == "-") or (TOR_Occupancy_value == None)):
            prefetch_cg.sample(prefetch_opcode_cp=flow.opcode,
                           prefetch_hit_miss_cp=hit_miss,
                           prefetch_avilable_data_way_cp=avail_data,
                           TOR_OccupancyTh_cp=TOR_OccupancyTh_reg_value)
        else:
             prefetch_cg.sample(prefetch_opcode_cp=flow.opcode,
                           prefetch_hit_miss_cp=hit_miss,
                           prefetch_avilable_data_way_cp=avail_data,
                           TOR_OccupancyTh_cp=TOR_OccupancyTh_reg_value,
                           TOR_Occupancy_cp=TOR_Occupancy_value)

        prefetch_promotion_cg.sample(prefetch_promotion_cp=0,
                                     prefetch_elimination_cp=0)

    def collect_prefetch_cov(self, flow: ccf_flow):
        if flow.is_flow_promoted() or flow.is_prefetch_elimination_flow():
            self.collect_prefetch_promotion_cov(flow)
        elif flow.is_prefetch():
            self.collect_simple_prefetch_cov(flow)

    def collect_cfi_order_coverage(self, flow: ccf_flow):
        if flow.is_coherent_flow() and flow.read_data_from_mem():
            ccf_cfi_order_cg = CCF_CFI_ORDER_CG.get_pointer()
            cmp_time = list()
            data_time = list()

            if flow.is_flow_promoted():
                flow_transactions = ccf_dbs.ccf_flows[flow.promotion_flow_orig_pref_uri].flow_progress
            else:
                flow_transactions = flow.flow_progress

            for trans in flow_transactions:
                if (type(trans) == ccf_cfi_record_info) and (trans.is_upi_c() or trans.is_cxm()):
                    if trans.is_upi_CmpO():
                        cmp_time.append(trans.get_transaction_time())
                    elif trans.is_upi_rd_data():
                        data_time.append(("UPI.C", trans.get_transaction_time()))

            if len(cmp_time) != 1:
                VAL_UTDB_MSG(time=flow.initial_time_stamp,
                             msg="COVERAGE INFO - We collected {} CmpO, that was not expected please check your code.".format(len(cmp_time)))
            elif len(data_time) != 2:
                VAL_UTDB_MSG(time=flow.initial_time_stamp,
                             msg="COVERAGE INFO - We collected {} Data chunk, that was not expected please check your code.".format(len(data_time)))
            else:
                if (cmp_time[0] < data_time[0][1]) and (cmp_time[0] < data_time[1][1]):
                    ccf_cfi_order_cg.sample(data_pkt_and_cmp_pkt_order="CMP_BEFORE_DATA")
                elif (cmp_time[0] > data_time[0][1]) and (cmp_time[0] < data_time[1][1]) and (data_time[0][1] < data_time[1][1]):
                    ccf_cfi_order_cg.sample(data_pkt_and_cmp_pkt_order="CMP_BETWEEN_DATA_CHUNKS")
                elif (cmp_time[0] < data_time[0][1]) and (cmp_time[0] > data_time[1][1]) and (data_time[0][1] > data_time[1][1]):
                    ccf_cfi_order_cg.sample(data_pkt_and_cmp_pkt_order="CMP_BETWEEN_DATA_CHUNKS")
                elif (cmp_time[0] > data_time[0][1]) and (cmp_time[0] > data_time[1][1]):
                    ccf_cfi_order_cg.sample(data_pkt_and_cmp_pkt_order="CMP_AFTER_DATA")



    def collect_systeminit_coverage(self):
        ccf_systeminit_cg = CCF_SYSTEMINIT_CG.get_pointer()
        ccf_systeminit_cg.sample(NUM_OF_CBO=self.si.num_of_cbo)
        ccf_systeminit_cg.sample(CBO_DISABLE_MASK=self.si.cbo_disable_mask)
        ccf_systeminit_cg.sample(MODULE_DISABLE_MASK=self.si.module_disable_mask)
        ccf_systeminit_cg.sample(CCF_MKTME_MASK=self.si.ccf_mktme_mask)
        #ccf_systeminit_cg.sample(CCF_PCIEXBAR_EN=self.si.pciexbar_en) TODO: name was changed on CBB

    def collect_end_of_flow_coverage(self, flow: ccf_flow):
        self.collect_ccf_flow_cg_cov(flow)
        self.conflict_coverage.end_of_flow_collect_conflict_cov(flow)
        self.collect_special_opcode_cov(flow)
        self.collect_prefetch_cov(flow)
        self.collect_cfi_order_coverage(flow)

    def collect_num_of_used_entries_in_monitor_array_coverage(self, num_of_entries):
        ccf_monitor_cg = CCF_MONITOR_CG.get_pointer()
        ccf_monitor_cg.sample(num_of_used_entries=num_of_entries)

    def collect_num_of_monitors_when_copy_to_hbo(self, num_of_expected_monitiors):
        ccf_monitor_cg = CCF_MONITOR_CG.get_pointer()
        ccf_monitor_cg.sample(copy_monitor_num_of_expected=num_of_expected_monitiors)
    def collect_copy_monitor_address_when_copy_to_hbo(self, expected_monitiors):
        ccf_monitor_cg = CCF_MONITOR_CG.get_pointer()
        for addr in expected_monitiors:
            bint_addr = bint(int(addr, 16))
            if bint_addr[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.mktme_lsb] != 0:
                ccf_monitor_cg.sample(copy_monitor_addr="with mktme")
            else:
                if bint_addr == 0:
                    ccf_monitor_cg.sample(copy_monitor_addr="addr 0x0")
                ccf_monitor_cg.sample(copy_monitor_addr="no mktme")

    def collect_pmon_hit(self, event_tested):
        if self.si.ccf_cov_en:
            ccf_pmon_cg = CCF_PMON_CG.get_pointer()
            ccf_pmon_cg.sample(pmon_checked=event_tested)

    def collect_pmon_counter_for_not_checked_pmons(self, event_tested):
        if self.si.ccf_cov_en:
            ccf_pmon_cg = CCF_PMON_CG.get_pointer()
            ccf_pmon_cg.sample(pmon_not_checked=event_tested)

