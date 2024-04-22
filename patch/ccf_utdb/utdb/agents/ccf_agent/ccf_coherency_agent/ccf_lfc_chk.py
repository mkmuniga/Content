#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from val_utdb_report import VAL_UTDB_ERROR
from val_utdb_bint import bint

from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_systeminit.ccf_systeminit import ccf_systeminit


class ccf_lfc_chk(ccf_coherency_base_chk):
    """LLC Flow Checker (LFC)

    Owner: asaffeld
    Creation Date: 11.20

    Desctiption:
    This checker validates the cache control's final decisions for every flow
    It should check LLC Final State, LLC Final CV and LLC Final MAP for different scenarios of each flow
    The checker doens't validate the flow it self rather checks the end only

    Each flow has a case in the checker
    """

    exluded_opcodes_from_llc_m_check = ["ITOM", "LLCINV"]
    exluded_opcodes_from_lfc_check = ["PORT_OUT", "PORT_IN", "INTPRIUP", "STOPREQ", "INTA", "EOI", "INTPHY", "INTLOG", "CLRMONITOR", "NOP", "LOCK", "UNLOCK", "SPLITLOCK", "ENQUEUE", "SPCYC"]

    def __init__(self):
        self.checker_name = "ccf_lfc_chk"
        self.ccf_registers = ccf_registers.get_pointer()
        self.force_snoop_all_cb_en = None


    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow) and not flow.core_flow_is_bogus and flow.opcode not in self.exluded_opcodes_from_lfc_check \
               and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_u2c_dpt_req()

    def should_check_general_rules(self, flow: ccf_flow):
        return not flow.flow_is_crababort()

    def is_cache_near(self, flow: ccf_flow):
        return flow.is_cache_near()

    #When force_snoop_all_cb_en we will send snoops to core even if cores CV=0 that mean RspSI doesn't say that we need to consider this as S state.
    #We will consider it as potential S state in core only if the core CV was 1 in our initial CV
    def consider_RspSI_as_RspI_core_do_not_has_data(self, flow: ccf_flow):
        all_RspSI_was_with_cv_zero = True
        if flow.final_snp_rsp == "RspSI":
            for snoop_rsp in flow.snoop_responses:
                if (snoop_rsp.snoop_rsp_opcode == "RspSI") and (flow.get_initial_cv_bit_by_index(int(snoop_rsp.snoop_rsp_core)) != "0"):
                    all_RspSI_was_with_cv_zero = False
            return self.force_snoop_all_cb_en and flow.final_snp_rsp == "RspSI" and all_RspSI_was_with_cv_zero
        else:
            return False
    def check_flow(self, flow: ccf_flow):
        err_msg = ""

        # in case of buried M we will go to take the data from te memory and we will end with E_CmpO
        # (since we are going to the memory we will consider it as miss)
        buried_m = flow.is_idi_flow_origin() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and not flow.is_selfsnoop() \
                   and flow.initial_map_sf() and flow.initial_state_llc_m_or_e() and \
                   not (flow.is_partial_c2u_data_write_flow() or flow.is_partial_or_uncachable_rd())

        if (flow.cbo_id_phys is not None) and (flow.first_accept_time is not None):
            self.force_snoop_all_cb_en = (self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("ingress_" + str(flow.cbo_id_phys), "flow_cntrl", "force_snoop_all", flow.first_accept_time) == 1)
        else:
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg="(FLOW cannot be checked): Flow TID-{} cannot be checked since is seems the flow was never being inside the CBO (please check you flow you may have a bug)".format(flow.uri['TID']))

        #treating crababort as a indepdendant flow - should not change LLC
        if flow.flow_is_crababort():
            if not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 1: Crababort flow detected LLC should not be changed\n"
        elif flow.is_rfo():
            llc_hit = flow.initial_state_llc_m_or_e() and (flow.initial_cv_with_selfsnoop_zero() and not self.force_snoop_all_cb_en) and not flow.initial_map_sf() and not flow.is_monitor_hit("go_sent")

            read_mem = ( (not flow.initial_state_llc_m_or_e() or flow.is_initial_stale_data()) and not flow.is_monitor_hit("go_sent")) or \
                       (flow.snoop_sent() and flow.initial_map_sf() and flow.snoop_rsp_i())

            #decide where to put the data
            # is case of CN=1 if there is avialable data or flow has been promoted it will use DWAY
            #is case of promotion with no CN only if we recevie cmpo_m map is DWAY
            if flow.flow_is_hom():
                expected_map_data = (self.is_cache_near(flow) and (flow.is_available_data() or flow.is_flow_promoted())) or (flow.is_flow_promoted() and flow.cbo_got_ufi_uxi_cmpo_m())
            else:
                expected_map_data = flow.is_available_data()

            if (not flow.is_cv_err_injection()) and (not flow.final_cv_one() or not flow.final_req_cv_one()):
                err_msg += "Rule1: Final CV must 1 and requestor bit only\n"
            if read_mem and not flow.cbo_got_ufi_uxi_cmpo_m() and not flow.final_state_llc_e():
                err_msg += "Rule 2: Inital state was not not M/E and UPI cmp was not M so final state must be E\n"
            if read_mem and flow.cbo_got_ufi_uxi_cmpo_m() and not flow.final_state_llc_m() :
                err_msg += "Rule 3: Inital state was not not M/E and UPI cmp was M, so final state must be M\n"
            if llc_hit and not flow.state_unchanged():
                err_msg += "Rule 4: We had a hit in cache with no need to snoop state should not change\n"
            if flow.flow_is_hom() and(flow.snoop_rsp_m() or (flow.initial_state_llc_m() and not buried_m)) and not flow.wrote_data_to_mem() and not flow.final_state_llc_m():
                err_msg += "Rule 5: Receivied RspIFwdMO or initial state is M and CBo did not write back data to mem - final state must be M\n"
            if flow.snoop_rsp_m() and flow.wrote_data_to_mem() and not flow.final_state_llc_e():
                err_msg += "Rule 6: Received RspIFwdMO and CBo wrote back data to mem - final state should be E\n"
            if expected_map_data and flow.final_map_sf():
                err_msg += "Rule 7: Expected final map is DWAY and final map is SF\n"
            if not expected_map_data and flow.final_map_dway():
                err_msg += "Rule 8: Expected final map is SF and final is DWAY\n"
            if flow.flow_is_hom() and (read_mem or flow.snoop_rsp_m() or flow.snoop_rsp_f()) and expected_map_data and (not flow.is_data_written_to_cache()):
                err_msg += "Rule 9: Flow missed in cache or received forward data. Final map is DWAY and data should be written to cache\n"
            if not flow.final_state_llc_m_or_e():
                err_msg += "Rule 10: Final state must be LLC_M or LLC_E\n"




        # FSRDCURR - CXL DEVICE
        elif flow.is_fsrdcurr():
            llc_miss = flow.initial_state_llc_i() or (flow.initial_cv_zero() and flow.initial_map_sf()) or (
                        flow.initial_map_sf() and flow.snoop_rsp_i())
            if not llc_miss and not flow.snoop_sent() and not flow.llc_unchanged():
                err_msg += "Rule 1: LLC Should not have been changed in this flow\n"

            # We are not doing optimization for CN=1 therefore when we have Rsp*Hit* && initial_map=SF and CN=1
            # We will not write the CV bits to zero or the state to LLC_E - and if a read will be done again we will snoop the cores again.
            if llc_miss and \
                    (self.is_cache_near(flow) and flow.is_available_data() and flow.is_cxm_rd()) \
                    and ((not flow.final_state_llc_e() and not (flow.snoop_rsp_hit() and flow.initial_map_sf())) or (
            not flow.is_data_written_to_cache()) or (not flow.final_map_dway())):
                err_msg += "Rule 2: On LLC Miss and CXM, CN=1 and DataWayAvail - Data should have been cahced in LLC at E state with Map=Data and Data should have been written to cache\n"

            if (
                    flow.snoop_rsp_m() or flow.snoop_rsp_f()) and flow.is_available_data() and not flow.is_data_written_to_cache():
                err_msg += "Rule 4: Core sent forward data to LLC with data ways available and data was not written to cache\n"
            if flow.snoop_rsp_m() and flow.is_available_data() and not flow.final_state_llc_m():
                err_msg += "Rule 5: Core Sent Rsp*FwdM with modified data and final state is not LLC_M\n"
            # TODO: Same todo as above rule 3 - asaffeld - not relevant for LNL-M
            # if flow.snoop_rsp_i() and flow.data_ways_available and (not flow.final_cv_zero() or not flow.state_unchanged()):
            #    err_msg+="Rule 6: All cores responded RspI* when data is in the cache and final CV is not zero or final state has been changed\n"
            if flow.snoop_rsp_m() and flow.core_still_has_data_after_snoop() and not flow.is_data_way_available() and not flow.final_state_llc_e():
                err_msg += "Rule 7: Core Sent RspSFwdM, LLC has no available data ways and data should have been writen back to memory with final state LLC_E\n"
            if flow.snoop_rsp_m() and not flow.core_still_has_data_after_snoop() and not flow.is_available_data() and not flow.final_state_llc_i():
                err_msg += "Rule 8: Core Sent RspIFwdM, LLC has no available data ways and data should have been writen back to memory with final state LLC_I\n"



        # Uncacheable Reads PRD/UCRDF/PRD
        elif "CRD_UC" in flow.opcode or "UCRDF" in flow.opcode or "PRD" in flow.opcode:
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        #ITOMWR_WT
        elif flow.is_itomwr_wt():
            if flow.flow_is_hom():
                    if not flow.final_state_llc_i():
                        err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"
            elif not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged():
                err_msg+= "Rule 2: Non Coherenet ItoM_Wr_WT should not change anything in cache \n"

        #WCILF
        elif flow.is_wcilf():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"


        elif flow.is_mempushwr():
            if flow.flow_is_hom():
                if not flow.final_state_llc_i():
                    err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"
            elif not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged():
                err_msg+= "Rule 2: Non Coherenet MemPushWr should not change anything in cache \n"

        elif "WCIL" in flow.opcode and not flow.is_wcilf_or_itomwr_wt():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        # CLFLUSH and CLFLUSHOPT
        elif flow.is_clflush() or flow.is_clflush_opt():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        # WIL and WILF
        elif "WIL" in flow.opcode:
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        elif flow.is_itomwr():
            if flow.flow_is_hom():
                if flow.is_available_data() and (
                        not flow.final_state_llc_m() or not flow.is_data_written_to_cache() or not flow.final_map_dway() or not flow.final_cv_zero()):
                    err_msg += "Rule 1: For ItoMWr with data ways available final state should be LLC_M with data written to cache and Map=Data and CV=0\n"
                elif not flow.is_available_data() and flow.initial_map_sf() and not flow.final_state_llc_i():
                    err_msg += "Rule 2: For ItoMWr with no data ways available final state must be LLC_I as data must be written back to memory\n"
            elif not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged():
                err_msg+= "Rule 3: Non Coherenet ItoM_Wr should not change anything in cache \n"

        # CRd Coherent
        elif flow.is_crd() and flow.flow_is_hom():
            flow_promoted_not_by_code_pref = flow.flow_promoted and \
                                            (self.ccf_flows[flow.promotion_flow_orig_pref_uri].is_llcprefdata() or self.ccf_flows[flow.promotion_flow_orig_pref_uri].is_llcprefrfo())
            llc_miss = flow.initial_state_llc_i() or (flow.initial_cv_zero() and flow.initial_map_sf()) or (
                        flow.initial_map_sf() and (flow.snoop_rsp_i() or flow.snoop_rsp_s())) or (buried_m)
            llc_hit = not llc_miss and not flow.snoop_sent()

            expected_map_data = (self.is_cache_near(flow) and (flow.is_available_data() or flow.is_flow_promoted())) or \
                                (not self.is_cache_near(flow) and flow.is_available_data() and (flow.snoop_rsp_m() or (
                                            flow.initial_state_llc_m() and flow.initial_map_dway()))) or \
                                (flow.is_available_data() and (flow.initial_cv_with_selfsnoop_more_than_zero() or self.force_snoop_all_cb_en) and (
                                            llc_hit or flow.core_still_has_data_after_snoop())) or \
                                (flow.is_flow_promoted() and flow.cbo_got_ufi_uxi_cmpo_m())

            if llc_miss and not flow_promoted_not_by_code_pref and not flow.initial_state_llc_m_or_e() and \
                    ( flow.is_selfsnoop_and_req_cv() or not flow.req_core_initial_cv_bit_is_one()) and not flow.final_state_llc_s():
                err_msg += "Rule 1: For CRd that misses in LLC or gets RspI with Map=SF final cache state must be LLC_S\n"
            if flow.final_state_llc_i():
                err_msg += "Rule 2: For CRd should not finish in LLC_I\n"
            if llc_miss and not flow.snoop_rsp_s() and not (flow.final_cv_one() or flow.final_req_cv_one()) and (not flow.is_cv_err_injection()):
                err_msg += "Rule 3: For CRd that misses in LLC or gets RspI with Map=SF final CV must be 1\n"
            if (not flow.is_cv_err_injection()) and (flow.final_cv_zero() or not flow.final_req_cv_one()):
                err_msg += "Rule 4: In CRd expected CV cannot be zero and requestor cv must be 1\n"
            # checking that we don't remove cv bits and add the requestor CV
            if (not flow.is_cv_err_injection()) and flow.initial_cv_more_than_zero() and flow.core_still_has_data_after_snoop() and not flow.is_initial_cv_exist_in_final_cv():
                err_msg += "Rule 5: Initial CV was more than 0, and snoop response was not RspI* and there was not miss in llc. Final CV should add new requestor to it an not loose the old ones\n"
            if expected_map_data and not flow.final_map_dway():
                err_msg += "Rule 6: Expected map is DWAY while final map is not\n"
            if not expected_map_data and not flow.final_map_sf():
                err_msg += "Rule 7: Expected map is SF while final map is not\n"
            if llc_miss and flow.is_data_way_available() and self.is_cache_near(flow) and not flow.is_data_written_to_cache():
                err_msg += "Rule 8: After miss with CN=1 and Data Way Available data was not written to cache\n"
            if flow.snoop_rsp_m() and flow.is_available_data() and not flow.is_data_written_to_cache():
                err_msg += "Rule 9: After Rsp*FwdM with Available Data data should be written to chache regardless of Cache Near\n"
            if flow.snoop_rsp_f() and flow.is_available_data() and flow.core_still_has_data_after_snoop() and not flow.is_data_written_to_cache():
                err_msg += "Rule 10: After RspSFwdFE with Available Data and data should be written to chache\n"
            if flow.initial_state_llc_e() and flow.snoop_sent() and not flow.snoop_rsp_m() and not flow.snoop_rsp_s() and not flow.cbo_got_ufi_uxi_cmpo_si() and not flow.is_initial_stale_data() and not flow.final_state_llc_e():
                err_msg += "Rule 11: Inital state was LLC_E with not modified data from snoop and final state is not LLC_E\n"
            if ((flow.initial_state_llc_m() and not buried_m) or flow.snoop_rsp_m()) and not flow.wrote_data_to_upi() and not flow.final_state_llc_m():
                err_msg += "Rule 12: CRd has modified data in LLC or from Snp that was not written back to UPI and final state is not LLC_M\n"
            if (
                    flow.snoop_rsp_m() and not flow.is_available_data()) and flow.wrote_data_to_upi() and not flow.final_state_llc_s():
                err_msg += "Rule 13: CRd got Snp with modified data that was written back to UPI and final state is not LLC_S\n"
            if not flow.initial_state_llc_m_or_e() and not flow_promoted_not_by_code_pref and not flow.final_state_llc_s():
                err_msg += "Rule 14: Initial state was not M/E so final state of CRD must be LLC_S\n"
            if not llc_miss and not flow.snoop_sent() and not flow.state_unchanged():
                err_msg += "Rule 15: In case of LLC Hit with not Snoop State should be the unchnaged\n"
            if flow.snoop_rsp_nack() and (
                    not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged()):
                err_msg += "Rule 16: In Case of RspNack LLC should be unchanged\n"
            if flow.wrote_data_to_upi() and not flow.final_map_sf():
                err_msg += "Rule 17: When CRd wrties back data to memory it means it had no available data and final map must be SF\n"
            if flow.initial_state_llc_m() and not (
                    flow.snoop_rsp_m() and not flow.is_available_data()) and flow.final_state_llc_s():
                err_msg += "Rule 18: For CRd with initial state of LLC_M or LLC_E, final state must be M or E and not downgrade to to LLC_S\n"
            if flow.initial_state_llc_s() and not llc_miss and not flow.final_state_llc_s():
                err_msg += "Rule 19: For CRd with inital state of LLC_S with data in cache, final state must be LLC_S\n"
            #In case of force_snoop_all CB we can get to a situation that in normal mode we wouldn't do snoop to cores but we do the snoop and have Buried M data.
            force_snoop_all_cb_exception = self.force_snoop_all_cb_en and (flow.initial_cv_with_selfsnoop_zero() and flow.initial_cv_one() and flow.req_core_initial_cv_bit_is_one()) and flow.snoop_rsp_m()

            if flow.initial_state_llc_e_or_s() and (flow.initial_cv_more_than_one() or flow.initial_cv_with_selfsnoop_zero()) and (flow.initial_map_dway() or flow.snoop_rsp_f()) \
                and not force_snoop_all_cb_exception\
                and not flow.has_cv_err()\
                and not flow.state_unchanged():
                err_msg += "Rule 20: cores are sharing or LLC has non modified data, final state should not change\n"


        # DRD Coherent
        elif flow.is_drd() and flow.flow_is_hom():
            #Notie that force_snoop_all_cb_en mean that we are CV=1 With ReqCV=0
            llc_miss = flow.initial_state_llc_i() or (
                    (flow.initial_cv_with_selfsnoop_zero() and not self.force_snoop_all_cb_en) and flow.initial_map_sf()) or (
                                   flow.initial_map_sf() and (flow.snoop_rsp_i() or flow.snoop_rsp_s()))

            llc_hit_no_snp = not llc_miss and not flow.snoop_sent()

            #Dedicated calculation for monitor hit for DRD
            drd_mon_hit = flow.is_monitor_hit() if flow.snoop_sent() else flow.is_monitor_hit()


            #based on visio - there are 4 cases
            #hit is based on (cache near or CV > 0 or monitor hit or is_go_S_opt or data is vulnerable)
            #miss is based on cache near or monitor hit (when flow is not promoted) - even if we got the miss through a snoop that recevies RspS with Map=SF - Review this
            #snoop has 3 sub cases:
                #1 cache near or monitor hit
                #2 no CN and not Mon hit and CV>0 and RspSHit* meaning more cores would like to continue reading the data later
                #3 no CN and no Mon hit but we found modified and other cores hold a copy we cannot send GO_M and must have dway
            #Flow is promoted with prefetch and get M_CmpO we will save the data in MAP Data
            #Flow is promoted with cache near =1 because cache near is taken from the flow and not the prefetch
            #Finally this is in the condition that we have available data

            if flow.is_flow_promoted() and (flow.cbo_got_ufi_uxi_cmpo_m() or self.is_cache_near(flow)):
                expected_map_data = True
            
            else:
                expected_map_data = (llc_hit_no_snp and (self.is_cache_near(flow) or drd_mon_hit or (flow.initial_cv_with_selfsnoop_more_than_zero() or self.force_snoop_all_cb_en) or flow.is_go_s_opt() or flow.is_data_vulnerable())) or \
                                 (flow.read_data_from_mem() and ((drd_mon_hit and not flow.is_flow_promoted()) or self.is_cache_near(flow))) or \
                                 (flow.snoop_sent() and (drd_mon_hit or self.is_cache_near(flow)) ) or \
                                 (
                                     flow.snoop_sent() and not self.is_cache_near(flow) and not drd_mon_hit and not flow.read_data_from_mem() and \
                                         (
                                          ( (flow.initial_cv_with_selfsnoop_more_than_zero() or self.force_snoop_all_cb_en) and flow.core_still_has_data_after_snoop() ) or \
                                          ( (flow.initial_state_llc_m() or flow.snoop_rsp_m() ) and flow.core_still_has_data_after_snoop() )or \
                                            flow.snoop_rsp_IFwdM() 
                                         )
                                 )
                #All depends if we have available data or we have a promotion wit cmp_e or cmp_m where cbo for sure has available data
                expected_map_data &= flow.is_available_data()

            if llc_miss and not flow.initial_state_llc_m_or_e() and flow.final_state_dosent_macth_upi_cmp():
                err_msg += "Rule 1: DRd missed or recevied no data from snooped cores and did not update final state according to UPI CmpO\n"
            if flow.final_state_llc_i():
                err_msg += "Rule 2: For DRd should not finish in LLC_I\n"
            if (llc_miss and not flow.snoop_rsp_s() and (not flow.final_cv_one() or not flow.final_req_cv_one())) and not flow.is_cv_err_injection():
                err_msg += "Rule 3: For DRd that misses in LLC or gets RspI final CV must be 1\n"
            if (not flow.is_cv_err_injection()) and (flow.final_cv_zero() or not flow.final_req_cv_one()):
                err_msg += "Rule 4: In DRd expected CV cannot be zero and requestor cv must be 1\n"
            # checking that we don't remove cv bits and add the requestor CV
            if (flow.initial_cv_more_than_zero() and flow.core_still_has_data_after_snoop() and not llc_miss and not flow.is_initial_cv_exist_in_final_cv()) and not (flow.has_cv_err() or flow.is_cv_err_injection()):
                err_msg += "Rule 5: Initial CV was more than 0, and snoop response was not RspI* and there was not miss in llc. Final CV should have kept the original cv bits and adding the requestor cv to it\n"
            if expected_map_data and not flow.final_map_dway():
                err_msg += "Rule 6: Expected map is DWAY while final map is not\n"
            if not expected_map_data and not flow.final_map_sf():
                err_msg += "Rule 7: Expected map is SF while final map is not\n"
            if llc_miss and flow.is_data_way_available() and self.is_cache_near(flow) and not flow.is_data_written_to_cache():
                err_msg += "Rule 8: After miss with CN=1 and Data Way Available data was not written to cache\n"
            if ((flow.snoop_rsp_f() or flow.snoop_rsp_m()) and flow.is_available_data()) and (
                    self.is_cache_near(flow) or flow.is_monitor_hit()) and not flow.is_data_written_to_cache():
                err_msg += "Rule 9: After Rsp*FwdFE with Available Data and (CN or MonHit) data should be written to chache\n"
            # according to visios we should not write to catch in this situation because it sends GO_M
            # known issue, rtl get monitor inidication after llc opcode decision
            # if (flow.snoop_rsp_i_fwd_x() or (flow.snoop_rsp_f() and flow.core_still_has_data_after_snoop()) or (not flow.snoop_rsp_with_data() and flow.initial_map_dway())) \
            #     and not self.is_cache_near(flow) and not flow.is_monitor_hit("go_sent") and flow.is_data_written_to_cache():
            #      err_msg+="Rule 10: During CN=0 and MonHit=0 We have the data a do require to write it to cache - CBo wrote data to cache\n"
            if flow.initial_state_llc_e() and not flow.snoop_rsp_m() and not flow.is_initial_stale_data() and flow.cbo_got_ufi_uxi_cmpo_e() and not flow.final_state_llc_e():
                err_msg += "Rule 11.1: Inital state was LLC_E with not modified data from snoop and we didn't got CmpO_SI/M and final state is not LLC_E\n"

            #11.2 and 11.3 are from Leon Visio
            if flow.initial_state_llc_m_or_e() and not flow.snoop_sent() and (flow.cbo_got_ufi_uxi_cmpo_si() or flow.final_state_llc_s()):
                err_msg += "Rule 11.2: Inital state was LLC_E/M and no snoop was sent we supposed to get the DATA back with M/E state\n"
            if flow.initial_state_llc_e() and flow.snoop_rsp_s() and flow.initial_map_sf() and (flow.cbo_got_ufi_uxi_cmpo_m() or flow.final_state_llc_m()):
                err_msg += "Rule 11.3: Inital state was LLC_E and snoop RspS we shouldn't get data back in M state\n"

            if flow.initial_state_llc_e() and not flow.read_data_from_mem() and not flow.snoop_rsp_m() and not flow.final_state_llc_e():
                err_msg += "Rule 11.4: Initial state was LLC_E snoop response is not Rsp_M final state shold be LLC_E\n"
            if (
                    flow.initial_state_llc_m() or flow.snoop_rsp_m()) and not flow.wrote_data_to_upi() and not buried_m and not flow.final_state_llc_m():
                err_msg += "Rule 12: DRd has modified data in LLC or from Snp that was not written back to UPI and final state is not LLC_M\n"
            if (
                    flow.initial_state_llc_m() or flow.snoop_rsp_m()) and flow.wrote_data_to_upi() and not flow.final_state_llc_e():
                err_msg += "Rule 13: CRd has modified data in LLC or from Snp that was written back to UPI and final state is not LLC_E\n"
            if not llc_miss and not flow.snoop_sent() and not flow.state_unchanged():
                err_msg += "Rule 14: In case of LLC Hit with not Snoop State should be the unchnaged\n"
            if flow.snoop_rsp_nack() and (
                    not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged()):
                err_msg += "Rule 15: In Case of RspNack LLC should be unchanged\n"
            if flow.wrote_data_to_upi() and not flow.final_map_sf():
                err_msg += "Rule 16: When DRd wrties back data to memory it means it had no available data and final map must be SF\n"
            if flow.initial_state_llc_m() and not flow.final_state_llc_m_or_e():
                err_msg += "Rule 17: For DRd with initial state of LLC_C M, final state must be M or E\n"
            if flow.initial_state_llc_s() and not llc_miss and not flow.final_state_llc_s():
                err_msg += "Rule 18: For DRd with inital state of LLC_S with data in cache, final state must be LLC_S\n"

            if flow.is_flow_promoted() and flow.cbo_got_ufi_uxi_cmpo_e() and not flow.is_cache_near() and flow.is_data_vulnerable():
               err_msg += "Rule 19: Since CBB for promoted DRd that got E_cmpO and CN=0 data should not be saved as vulnerable data in the LLC \n"

        #DRD_Shared_Opt Coherent
        elif flow.is_drd_shared_opt() and flow.flow_is_hom():
            llc_hit = flow.initial_map_dway() and (not flow.is_selfsnoop_and_req_cv()) and \
                      (flow.initial_state_llc_s() or
                       (flow.initial_state_llc_m_or_e() and not flow.initial_cv_one()))

            need_to_snoop = (flow.initial_state_llc_m_or_e() and flow.initial_cv_one() and not flow.initial_cv_is_shared()) or \
                            (not flow.initial_state_llc_i() and flow.initial_cv_more_than_zero() and flow.initial_map_sf()) or \
                            (flow.is_selfsnoop_and_req_cv())

            need_to_snoop_and_evict = need_to_snoop and not flow.is_available_data() and flow.snoop_rsp_m()

            llc_miss = flow.initial_state_llc_i() or (flow.initial_map_sf() and flow.initial_cv_zero()) or \
                       (need_to_snoop and not flow.snoop_rsp_with_data() and flow.initial_map_sf())

            promotion_that_got_modified_data_from_uxi = flow.is_flow_promoted() and flow.cbo_got_ufi_uxi_cmpo_m()

            uxi_read_allocated_in_llc = (flow.is_data_way_available() and (flow.is_cache_near() or (flow.snoop_rsp_s() and not flow.snoop_rsp_with_data()))) or promotion_that_got_modified_data_from_uxi



            #Final state rules:
            if llc_miss and not flow.initial_state_llc_m_or_e() and flow.final_state_dosent_macth_upi_cmp():
                err_msg += "Rule 1: DRd_Shared_Opt missed or recevied no data from snooped cores and did not update final state according to UXI CmpO\n"

            if llc_miss and promotion_that_got_modified_data_from_uxi and not flow.final_state_llc_m():
                err_msg += "Rule 1.1: DRd_Shared_Opt did promotion and got modified data from memory final state in LLC is not LLC_M."

            if flow.final_state_llc_i():
                err_msg += "Rule 1.2: For DRd_Shared_Opt should not finish in LLC_I\n"

            if not (llc_miss or need_to_snoop_and_evict or (flow.snoop_rsp_m() and not flow.initial_state_llc_m())) and not flow.state_unchanged():
                err_msg += "Rule 1.3: For DRd_Shared_Opt in it hit case we didn't expect to see State change\n"

            #TODO: final state should be LLC_E according to Leon we need to make sure visio is fixed.
            if need_to_snoop_and_evict and not (flow.final_state_llc_e() and flow.final_map_sf()):
                err_msg += "Rule 1.4: For DRd_Shared_Opt when doing evict and WBMtoS final LLC state need to be LLC_S and map SF\n"


            #Final map rules:
            if llc_miss:
                if uxi_read_allocated_in_llc and not flow.final_map_dway():
                    if promotion_that_got_modified_data_from_uxi:
                        err_msg += "Rule 2.1: DRd_Shared_Opt should have been allocated in the LLC and the final map should be Dway - since flow was promoted and got M_CmpO\n"
                    else:
                        err_msg += "Rule 2.1: DRd_Shared_Opt should have been allocated in the LLC and the final map should be Dway\n"
                if not uxi_read_allocated_in_llc and not flow.final_map_sf():
                    err_msg += "Rule 2.2: DRd_Shared_Opt is miss or didn't got back data from snoop - we don't have DwayAvail or CN=0 and no core hold the data in S state and MAP != SF\n"


            if llc_hit:
                if flow.is_cache_near():
                    if not flow.final_map_dway():
                        err_msg += "Rule 2.3: DRd_Shared_Opt in hit case with CN=1 and MAP isn't Dway\n"
                # GO_S_OPT condition is not part of Leon flows but in case we will want to enable it.
                # The meanning of it is that we know that probebly another core will want the data so we prefer to keep it in Dway
                elif (flow.initial_state_llc_m() or flow.initial_cv_with_selfsnoop_more_than_zero() or flow.is_go_s_opt()):
                    if not flow.final_map_dway():
                        err_msg += "Rule 2.4: DRd_Shared_Opt in hit case with CN=0 and (LLC_M or CV>0) and final MAP isn't Dway\n"
                elif not flow.is_data_vulnerable() and not flow.final_map_sf():
                    err_msg += "Rule 2.5: DRd_Shared_Opt in hit case with CN=0 and not (LLC_M or CV>0) and not data_vulnerable and final MAP isn't SF\n"

            if need_to_snoop:
                have_modified_data_no_need_to_evict = (flow.initial_state_llc_m() and flow.initial_map_dway()) or (flow.is_data_way_available() and flow.snoop_rsp_m())
                if have_modified_data_no_need_to_evict:
                    if not flow.final_map_dway():
                        err_msg += "Rule 2.6: DRd_Shared_Opt in case of available data way or initial Dway final map should be Dway\n"
                    if not flow.final_state_llc_m():
                        err_msg += "Rule 2.7: DRd_Shared_Opt we have initial state LLC_M or Rsp*FwdMO we must finish the flow with LLC_M\n"
                if (flow.is_data_way_available() or flow.initial_map_dway()) and flow.snoop_rsp_m():
                    if not flow.is_data_written_to_cache():
                        err_msg += "Rule 2.8: DRd_Shared_Opt in case of available data way or initial Dway final map should be Dway\n"
                if not (have_modified_data_no_need_to_evict or need_to_snoop_and_evict or llc_miss):
                    #got_s_data_by_snoop = flow.initial_cv_more_than_zero() and flow.snoop_rsp_s() and flow.is_available_data()
                    #m_state_and_rsps = flow.initial_state_llc_m() and flow.snoop_rsp_s()
                    #rspm_and_avilable_data = flow.snoop_rsp_IFwdM() and flow.is_available_data()
                    #if (got_s_data_by_snoop or m_state_and_rsps or rspm_and_avilable_data or flow.snoop_rsp_s_fwd_m()) and flow.final_map_dway():
                    if (flow.snoop_rsp_s() or flow.snoop_rsp_s_fwd() or flow.is_cache_near())and flow.is_data_way_available():
                        if not flow.final_map_dway():
                            err_msg += "Rule 2.9: DRd_Shared_Opt in case of Non modified data from snoop and AvialData=1 and (CN=1 or core hold data in S state) MAP should be Dway\n"
                    elif not flow.final_map_sf():
                        err_msg += "Rule 2.10: DRd_Shared_Opt in case of Non modified data from snoop and AvialData=0 or CN=0 and core hold data in S state MAP should be SF\n"

            #Final cv rules:
            if llc_miss and not flow.snoop_rsp_s() and (not flow.final_cv_one() or not flow.final_req_cv_one()):
                err_msg += "Rule 3.1: For DRd_Shared_Opt that misses in LLC or gets RspI with Map=SF final CV must be 1\n"
            if flow.final_cv_zero() or not flow.final_req_cv_one():
                err_msg += "Rule 3.2: In DRd_Shared_Opt expected CV cannot be zero and requestor cv must be 1\n"
            # checking that while we are adding the ReqCV we don't remove the original CV bits
            if flow.initial_cv_more_than_zero() and flow.core_still_has_data_after_snoop() and not llc_miss and not flow.is_initial_cv_exist_in_final_cv():
                err_msg += "Rule 3.3: Initial CV was more than 0, and snoop response was not RspI* and there was not miss in llc. Final CV should have kept the original cv bits and adding the requestor cv to it\n"

            #Data written to cache:
            if llc_miss:
                if uxi_read_allocated_in_llc and not flow.is_data_written_to_cache():
                    err_msg += "Rule 4.1: In DRd_Shared_Opt created UXI read and need to write the CL to the cache but we didn't saw the write happen.\n"
                if not uxi_read_allocated_in_llc and flow.is_data_written_to_cache():
                    err_msg += "Rule 4.2: In DRd_Shared_Opt created UXI read and need to finish in SF without writeing to the cache but we see the cache is written in the flow.\n"
            if llc_hit and flow.initial_map_dway() and flow.is_data_written_to_cache():
                err_msg += "Rule 4.3: In DRd_Shared_Opt is HIT in the cache therefore we didn't expect to see any write to cache\n"



        #CRD and DRD Non-Coherent
        elif (flow.is_crd() or flow.is_drd()) and not flow.flow_is_hom():
            if flow.is_mmio():
                snp_sent = (not flow.initial_state_llc_i() and not flow.initial_cv_with_selfsnoop_zero()) or self.force_snoop_all_cb_en
                llc_miss = flow.initial_state_llc_i() or (flow.initial_state_llc_s() and flow.initial_cv_with_selfsnoop_zero() and not self.force_snoop_all_cb_en) or \
                           (flow.initial_state_llc_m_or_e() and flow.initial_map_sf() and flow.initial_cv_with_selfsnoop_zero() and not self.force_snoop_all_cb_en) or \
                           (snp_sent and not flow.snoop_rsp_with_data() and flow.initial_map_sf())
                llc_hit_no_snp = flow.initial_state_llc_m_or_e() and flow.initial_map_dway() and flow.initial_cv_with_selfsnoop_zero() and not self.force_snoop_all_cb_en

                expected_map_data = (llc_miss and flow.is_available_data()) or llc_hit_no_snp or (snp_sent and not llc_miss and flow.is_available_data())

                if llc_miss:
                    #If we sent snoop and we are in CRd we expect LLC_E too.
                    if flow.is_drd() and not flow.final_state_llc_e():
                        err_msg += "NC Rule 1.1: DRD that misses in LLC must have final state LLC_E\n"

                    #IF we had snoop we will expect to be LLC_E -
                    # since this is Non-coherent we don't have real state therefore we can move to LLC_E since we have the ownership
                    if flow.is_crd() and not flow.snoop_sent() and not flow.initial_state_llc_m_or_e() and not flow.final_state_llc_s():
                        err_msg += "NC Rule 1.2.1: CRD that misses in LLC or sending snoop with LLC_S must have final state LLC_S\n"
                    elif flow.is_crd() and not flow.snoop_sent() and flow.initial_state_llc_e() and not flow.final_state_llc_e():
                        err_msg += "NC Rule 1.2.2: CRD that misses in LLC_E and CV=0 or sending snoop with LLC_E receving RspI must have final state LLC_E - Should not downgrade state\n"

                    #If snoop sent and we got RspS we will have two cores that have the CL in shared state.
                    if not (flow.snoop_sent() and flow.snoop_rsp_s()) and (not flow.is_cv_err_injection()) and not (flow.final_req_cv_one() and flow.final_cv_one()):
                        err_msg += "NC Rule 2: DRD/CRD that misses in LLC must finish with CV=1 and ReqCV=1\n"
                elif llc_hit_no_snp:
                    if not flow.state_unchanged() or not flow.final_req_cv_one() or not flow.final_cv_one():
                        err_msg += "NC Rule 3: DRD/CRD that hits in LLC must have final state LLC_E/LLC_M (not changed) with CV=1 and ReqCV=1\n"

                #Snoop sent and received response with data or map is dway
                else:
                    if not flow.snoop_sent():
                        if not flow.state_unchanged():
                            err_msg += "NC Rule 4: CRD/DRD is hit and didn't sent any snoop therefore state should be the same. initial state {} final_state {}\n".format(flow.initial_cache_state, flow.final_cache_state)
                    
                    if (flow.initial_state_llc_m() or flow.snoop_rsp_m()):
                        if not flow.final_map_sf() and not flow.final_state_llc_m():
                            err_msg += "NC Rule 5: CRD/DRD sent snoop with initial map DWAY final state should remain LLC_M\n"
                    elif flow.initial_state_llc_e() and not flow.final_state_llc_e():
                        err_msg += "NC Rule 6: CRD/DRD that started in LLC_E or received Rsp*FwdFE should have final state LLC_E\n"
                    elif not flow.snoop_sent() and not (flow.initial_state_llc_e() or flow.initial_state_llc_m()) and not flow.final_state_llc_s():
                        err_msg += "NC Rule 7: CRD/DRD that started in LLC_S should have final state LLC_S\n"
                    
                    elif flow.snoop_sent() and flow.snoop_rsp_m():
                        #This Rule is coming in order to prevent a case of LLC_M, SF, GO_S - and at this case the core can response to our snoop without data and we can be stuck.
                        if flow.final_map_sf() and not flow.final_state_llc_e():
                            err_msg += "NC Rule 8.1: CRD/DRD is hit and we sent snoop and got RspFwdM and out final map is SF, we had to finish in LLC_E.\n"
                        elif flow.final_map_dway() and not flow.final_state_llc_m():
                            err_msg += "NC Rule 9.2: CRD/DRD is hit and we sent snoop and got RspFwdM and out final map is DWAY, we had to finish in LLC_M.\n"
                    elif flow.snoop_sent() and flow.snoop_rsp_f():
                        if (flow.initial_state_llc_e() or flow.is_drd()) and not flow.final_state_llc_e():
                            err_msg += "NC Rule 10.1: DRD is hit or CRD with LLC_E and we sent snoop and got Rsp*wdFE, we had to finish in LLC_E.\n"
                        elif flow.initial_state_llc_s() and flow.is_crd() and not flow.final_state_llc_s():
                            err_msg += "NC Rule 10.2: CRD is hit and we sent snoop and got Rsp*wdFE, we had to finish in LLC_S.\n"
                    elif flow.snoop_sent() and flow.snoop_rsp_si() and flow.final_map_sf() and not self.force_snoop_all_cb_en and not flow.initial_state_llc_m_or_e() and not flow.final_state_llc_s():
                        err_msg += "NC Rule 11: CRD/DRD is hit and we sent snoop and got RspSI, we had to finish in LLC_S.\n"
                    elif flow.snoop_sent() and not flow.snoop_rsp_with_data() and flow.initial_map_dway() and not flow.state_unchanged():
                        err_msg += "NC Rule 12: CRD/DRD is hit and we sent snoop and got Snoop response without data, we had to finish with the same state as we begin with.\n"

                    #CV Checks in Snoop
                    elif flow.initial_cv_with_selfsnoop_more_than_zero() and flow.core_still_has_data_after_snoop() and (not flow.is_initial_cv_exist_in_final_cv() or not flow.final_req_cv_one()):
                        err_msg += "NC Rule 13: CRD/DRD started with CV>0 must finish with ReqCV=1 and keep inital CV\n"
                    elif flow.initial_cv_with_selfsnoop_more_than_zero() and not flow.core_still_has_data_after_snoop() and (not flow.final_cv_one() or not flow.final_req_cv_one()):
                        err_msg += "NC Rule 14: CRD/DRD started with CV>0 must finish with ReqCV=1 and final CV=1\n"

                #Map Check
                if expected_map_data and flow.final_map_sf():
                    err_msg += "NC Rule 15.1: Expected map is DWAY final map is SF\n"

                elif not expected_map_data and flow.final_map_dway():
                    err_msg += "NC Rule 15.2 Expected map is SF and final map is DWAY\n"

            #CRABABORT
            elif not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 10: Non-Coherenet CRD/DRD that CRABABORT should not change anything in cache\n"



        elif flow.is_victim():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        # SnoopInv/SnpInvOwn/SnpFlush
        elif flow.is_snpinvown() or flow.is_snpinv() or flow.is_snpflush():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        elif flow.is_snpinvmig():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"
            if (flow.initial_state_llc_m() or flow.snoop_rsp_IFwdM()) and not flow.got_snoop_rsp_fwd_data("Data_M"):
                err_msg += "Rule 2: snpInvMig and LLC_M or got RspIFwdMO you should write the modified data to the memory \n"

        elif flow.is_snpLDrop():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"
            if flow.wrote_data_to_mem():
                err_msg += "Rule 2: snpLDrop should not write to the memory \n"

        elif flow.is_snpcurr() or flow.is_snplcurr():
            #in this flow we either have a cahce hit of we send snoop
            snp_sent = flow.initial_state_llc_m_or_e() and (flow.initial_cv_one() or flow.has_cv_err())

            found_m_data = flow.initial_state_llc_m() or flow.snoop_rsp_m()

            #Calculate expected_map_data
            expected_map_data = flow.initial_map_dway() or \
                                (snp_sent and flow.initial_map_sf() and flow.is_free_inv_way() and not flow.is_conflict_flow() and flow.snoop_rsp_with_data() and not flow.snoop_rsp_v_fwd())

            expected_state_llc_i = flow.initial_state_llc_i() or \
                                   (flow.initial_state_llc_e() and snp_sent and (flow.snoop_rsp_i_hit() or flow.snoop_rsp_flushed()) and flow.initial_map_sf() ) or \
                                   (snp_sent and flow.snoop_rsp_i_fwd_x() and not expected_map_data)

            expected_state_llc_m = found_m_data and (expected_map_data or (not expected_map_data and flow.snoop_sent() and flow.snoop_rsp_v_fwd()))

            expected_state_llc_s = flow.initial_state_llc_s() or \
                                   (snp_sent and flow.core_still_has_data_in_s() and flow.snoop_rsp_m() and not expected_map_data)
                                   #(snp_sent and flow.initial_state_llc_e() and flow.core_still_has_data_in_s() and not flow.snoop_rsp_with_data() ) or \

            expected_state_llc_e = not expected_state_llc_i and not expected_state_llc_m and not expected_state_llc_s

            #No Snoop
            if not snp_sent and not flow.llc_unchanged() and not flow.has_cv_err_with_no_fix():
                err_msg += "Rule 1: No snoop is sent, LLC state/map/cv should not change\n"
            #Snoop
            elif snp_sent:
                #Map check
                if expected_map_data and not flow.final_map_dway():
                    err_msg += "Rule 2: Snoop is sent and expceted map is DWAY, final map is SF\n"
                #CV Check
                if flow.core_still_has_data_after_snoop() and ((not flow.cv_unchanged() and not flow.has_cv_err_with_no_fix) or flow.final_state_llc_i()):
                    err_msg += "Rule 3: Snoop was sent and core has data after snoop - final cv should should not change and LLC cannot be in I state\n"
                if not flow.core_still_has_data_after_snoop() and not flow.final_state_llc_i() and (not flow.is_cv_err_injection()) and (not flow.final_cv_zero()):
                    err_msg += "Rule 4: Snoop was sent and core doesn't have data after the snoop. Line is kept in LLC - final CV should be 0\n"
                #RspV* Checks
                if (flow.snoop_rsp_v_fwd() or flow.snoop_rsp_v_hit()) and (not flow.state_unchanged() or (not flow.cv_unchanged() and not flow.has_cv_err_with_no_fix())):
                    err_msg += "Rule 5.1: In case of RspVFwdV or RspVHitV state and cv should not change\n"
                if flow.snoop_rsp_v_hit() and not flow.map_unchanged():
                    err_msg += "Rule 5.2 In case of RspVHitV map should not change\n"
                #Data Write Check
                if flow.initial_map_sf()  and expected_map_data and not flow.is_data_written_to_cache():
                    err_msg += "Rule 6: Initial map is SF and expecting a final map to be DWAY - missing a data write\n"
            #Final State check
            if expected_state_llc_m and not flow.final_state_llc_m():
                    err_msg += "Rule 7: Expected state is LLC_M final state is "+str(flow.final_cache_state)+"\n"
            if expected_state_llc_i and not flow.final_state_llc_i():
                    err_msg += "Rule 8: Expected state is LLC_I final state is "+str(flow.final_cache_state)+"\n"
            if expected_state_llc_s and not flow.final_state_llc_s():
                    err_msg += "Rule 9: Expected state is LLC_S final state is "+str(flow.final_cache_state)+"\n"
            if expected_state_llc_e and not flow.final_state_llc_e():
                    err_msg += "Rule 10: Expected state is LLC_E final state is "+str(flow.final_cache_state)+"\n"

        if flow.is_snpdata():
            snoop_needed = flow.initial_state_llc_m_or_e() and flow.initial_cv_one()


            if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                err_msg += "Rule 0: For LLC_I final state must be LLC_I\n"

            if not snoop_needed:
                if not flow.cv_unchanged():
                    err_msg += "Rule 1: We didn't had any snoop therefore CV bits need to be unchanged.\n"

                if flow.initial_state_llc_m():
                    if flow.initial_state_llc_m() and flow.initial_map_sf():
                        err_msg += "Rule 2: We have LLC_M with Map=SF and we didn't done any snoop.\n"

                    if (flow.is_monitor_hit() or flow.initial_cv_more_than_one()):
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 3.1: We have modified data with MonHit or CV>1, final state should be LLC_S.\n"
                        if (not flow.cv_unchanged()) or (not flow.map_unchanged()):
                            err_msg += "Rule 3.2: We have modified data with MonHit or CV>1 and we didn't do snoop, final CV and map should be unchanged.\n"
                    else:
                        if (not flow.final_state_llc_i()) or (not flow.final_map_sf()) or (not flow.final_cv_zero()):
                            err_msg += "Rule 3.3: We have modified data without (MonHit or CV>1),  final state should be LLC_I with SF and CV=0.\n"

                elif flow.initial_state_llc_e() and flow.initial_map_dway():
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 4.1: We have clean exclusive data with MAP=DATA, final state should be LLC_S.\n"

                else:
                    if flow.initial_state_llc_e() and flow.initial_map_sf():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 5.1: We have clean exclusive line and no data with MAP=SF, final state should be LLC_S.\n"
                    elif flow.initial_state_llc_s():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 5.1: We don't have data and initial state is LLC_S, final state should be LLC_S.\n"
                    else:
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 5.1: We don't have data and intial state is LLC_I final state should be LLC_I.\n"

            else: #should snoop
                have_modified_data = flow.initial_state_llc_m() or flow.snoop_rsp_m()
                keep_modified_data_in_LLC = (flow.snoop_rsp_s_fwd_x() or flow.snoop_rsp_s()) and (flow.initial_map_dway() or flow.is_free_inv_way())
                have_clean_data = flow.initial_state_llc_e() and (flow.initial_map_dway() or flow.snoop_rsp_f())

                if have_modified_data and not keep_modified_data_in_LLC:
                    if flow.is_data_written_to_cache():
                        err_msg += "Rule 6.1: We should not write data to LLC as we are not supposed to keep the data in the LLC.\n"

                    if flow.snoop_rsp_s_fwd_m():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 6.3: We got RspS* as snoop response final state should be LLC_S.\n"
                        if not flow.cv_unchanged():
                            err_msg += "Rule 6.4: We got RspS* CV should be stay unchanged.\n"
                        if not flow.final_map_sf():
                            err_msg += "Rule 6.2: We got RspS* as snoop response and we cannot keep the line in LLC - final map should be SF.\n"
                    else:
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 6.5: We got RspI with modified data and we don't keep the line in LLC so final state should be LLC_I.\n"
                elif have_modified_data and keep_modified_data_in_LLC:
                    if flow.snoop_rsp_m() and not flow.is_data_written_to_cache():
                        err_msg += "Rule 7.1: We should write data to LLC as we are supposed to keep the data in the LLC.\n"
                    if not flow.final_map_dway():
                        err_msg += "Rule 7.2: We should write data to LLC so we should finish with MAP=DATA.\n"
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 7.2: We should finish the flow with LLC_S.\n"
                elif have_clean_data:
                    if flow.is_free_inv_way() and flow.initial_map_sf():
                        if not flow.is_data_written_to_cache():
                            err_msg += "Rule 8.1: Data should be write to LLC.\n"
                        if not flow.final_map_dway():
                            err_msg += "Rule 8.2: We should write data to LLC so we should finish with MAP=DATA.\n"

                    if flow.core_still_has_data_after_snoop():
                        if not flow.cv_unchanged():
                            err_msg += "Rule 8.2: Since cores still have the data after snoop CV should be unchanged.\n"
                    else:
                        if not flow.final_cv_zero():
                            err_msg += "Rule 8.2: Since cores don't have the data after snoop CV should be zero.\n"

                    if flow.snoop_rsp_i_fwd() and flow.initial_map_sf() and not flow.is_free_inv_way() and not flow.is_monitor_hit():
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 8.3: We cannot keep clean data in the LLC we should finish the flow with LLC_I.\n"
                    else:
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 8.4: We should finish the flow with LLC_S.\n"
                else:
                    if flow.initial_state_llc_e() and flow.snoop_rsp_s():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 9.1: We should finish the flow with LLC_S.\n"
                        if not flow.cv_unchanged():
                            err_msg += "Rule 9.2: Core still have the data CV should be unchanged.\n"
                        if (not flow.map_unchanged()) or (not flow.final_map_sf()):
                            err_msg += "Rule 9.3: Core didn't return any data map slhould still be SF.\n"
                    else:
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 9.4: We should finish the flow with LLC_I, SF and CV=0.\n"


        elif flow.is_snpcode():
            snoop_needed = flow.initial_state_llc_m_or_e() and flow.initial_cv_one()
            local_cv_unchanged = flow.cv_unchanged() and not flow.has_cv_err()
            if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                err_msg += "Rule 1: For LLC_I final state must be LLC_I\n"

            #No snoop is needed
            if not snoop_needed:
                #Data to evict
                if flow.initial_state_llc_m():
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 2: In case there is no snoop needed and we have initial state of LLC_M and data should be evict final cache state should be LLC_S.\n"
                    if not (local_cv_unchanged and flow.map_unchanged()):
                        err_msg += "Rule 2.1: In case there is no snoop needed and we have initial state of LLC_M and data should be evict and CV and map shouldn't be changed.\n"
                    #TODO: need to fix wrote data to mem function.
                    #if flow.wrote_data_to_mem():
                    #    err_msg += "Rule 2.2: In case there is no snoop needed and we have initial state of LLC_M and data should be evict we should see RspFwdWB to HA.\n"

                #Clean data FwD
                elif flow.initial_state_llc_e() and flow.initial_map_dway():
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 3: In case there is no snoop needed and we have initial state of LLC_E and Dway data should be Fwd and final cache state should be LLC_S.\n"
                    if not (local_cv_unchanged and flow.map_unchanged()):
                        err_msg += "Rule 3.1: In case there is no snoop needed and we have initial state of LLC_E and data should be Fwd Dway and CV and map shouldn't be changed.\n"
                #No data
                else:
                    if flow.initial_state_llc_e() and flow.initial_map_sf():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 4.1: In case there is no data available in the CA and initial state is LLC_E we should finish the flow with LLC_S.\n"
                    elif flow.initial_state_llc_s():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 4.2: In case there is no data available in the CA and initial state is LLC_S we should stay with LLC_S.\n"
                    else:
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 4.2: In case there is no data available in the CA and we started with LLC_I we should finish with LLC_I.\n"

                    if not (local_cv_unchanged and flow.map_unchanged()):
                        err_msg += "Rule 4.3: We are not expecting any change in CV and MAP.\n"

            #Snoop is needed
            else:
                have_modified_data = flow.initial_state_llc_m() or flow.snoop_rsp_m()
                dont_keep_data_in_llc = have_modified_data and (not flow.is_free_inv_way() and flow.initial_map_sf())
                keep_modified_line_in_llc = have_modified_data and (flow.is_free_inv_way() or flow.initial_map_dway())
                have_clean_data = flow.initial_state_llc_e() and (flow.initial_map_dway() or flow.snoop_rsp_f())

                if dont_keep_data_in_llc:

                    # TODO: need to fix wrote data to mem function.
                    # if flow.wrote_data_to_mem():
                    #    err_msg += "Rule 4: In case we are in M state and core have the data (SF) or we got Rsp*FwdM data should be written to HA.\n"

                    if flow.snoop_rsp_IFwdM():
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 4.2: In case we got snoop response of RspIFwdMO and we are not keeping the line in the LLC - We expect to finish the flow with LLC_I state.\n"
                        if not flow.final_map_sf():
                            err_msg += "Rule 4.3: In case we got snoop response of RspIFwdMO and we are not keeping the line in the LLC - We expect to finish the flow with MAP=SF.\n"
                    else: #RspSFwdMO
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 4.4: In case we got snoop response of RspSFwdMO and we are not keeping the line in the LLC - We expect to finish the flow with LLC_S state.\n"
                        if not flow.final_map_sf():
                            err_msg += "Rule 4.5: In case we got snoop response of RspSFwdMO and we are not keeping the line in the LLC - We expect to finish the flow with MAP=SF.\n"
                        if not local_cv_unchanged:
                            err_msg += "Rule 4.6: In case we got snoop response of RspSFwdMO and we are not keeping the line in the LLC - We expect to finish with CV unchanged since cores still hold the data.\n"

                elif keep_modified_line_in_llc:
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 5: In case we got snoop response of Rsp*FwdMO or we are in LLC_M and Dway and we should keep the CL in the LLC - We expect to finish the flow with LLC_S state.\n"

                    if (flow.snoop_rsp_IFwdM() or flow.snoop_rsp_s_fwd_m()) and not flow.is_data_written_to_cache():
                        err_msg += "Rule 5.1: In case we got snoop response of Rsp*FwdMO and we should keep the CL in the LLC - We expect to write the new data we got from the cores to the cache.\n"

                    if flow.snoop_rsp_IFwdM():
                        if not flow.final_cv_zero():
                            err_msg += "Rule 5.2: In case we got snoop response of RspIFwdMO and we should keep the CL in the LLC - We expect to finish with CV=0.\n"
                    else:
                        #CV should be CV=1 since before core downgrade itself to S state core had the data in M state.
                        if not (local_cv_unchanged and flow.final_cv_one()):
                            err_msg += "Rule 5.3: In case we got snoop response of RspSFwdMO and we should keep the CL in the LLC - We expect to finish with the same CV=1 as the core still hold the data .\n"

                elif have_clean_data:
                    #We got Fwd of clean data and we do have free location to save the CL in the LLC
                    if flow.is_free_inv_way() and flow.initial_map_sf() and not flow.is_data_written_to_cache():
                        err_msg += "Rule 6: We got clean Fwd data and we do have free inv way to keep it in the LLC but we didn't detect write to the LLC.\n"

                    if (flow.is_free_inv_way() and flow.initial_map_sf()) or flow.snoop_rsp_s_fwd() or flow.is_monitor_hit("SNP_RSP") or flow.initial_map_dway():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 6.1: We got clean Fwd data and we had all the conditions to finish in LLC_S state but we didn't finish at LLC_S.\n"
                    else:
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 6.2: We got clean Fwd data and we had all the conditions to finish in LLC_I state but we didn't finish at LLC_I.\n"

                    if flow.snoop_rsp_i():
                        if not flow.final_cv_zero():
                            err_msg += "Rule 6.2: When we are getting clean Fwd data with RspIFwd final CV should be CV=0.\n"
                    else:
                        if (not flow.final_state_llc_i()) and not local_cv_unchanged:
                            err_msg += "Rule 6.2: When we are getting clean Fwd data without RspIFwd final CV should be uncahnged .\n"

                #No data
                else:
                    if flow.is_data_written_to_cache():
                        err_msg += "Rule 7: We didn't got any data we shouldn't write anything to cache.\n"

                    if flow.initial_state_llc_e() and (flow.snoop_rsp_s_hit() or flow.snoop_rsp_si()):
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 7.2: Initial state is LLC_E and snoop response is RspSHit* we expect final state to be in LLC_S.\n"
                        if not local_cv_unchanged:
                            err_msg += "Rule 7.3: Initial state is LLC_E and snoop response is RspSHit* we expect to have CV unchanged.\n"
                    else:
                        if not (flow.final_state_llc_i() and flow.final_map_sf()):
                            err_msg += "Rule 7.4: We expect final state to be LLC_I and final map is SF.\n"



        elif flow.is_snplcode():
            # We will send snoop in this flow in case of CV=1 or we have CV error and our real CV can be CV=1
            # In case of CV_SHARED indication we will consider the CV as CV>1 as describe in Leon visios.
            snoop_needed = flow.initial_state_llc_m_or_e() and ((flow.initial_cv_one() and not flow.initial_cv_is_shared()) or flow.has_cv_err())
            have_modified_data = flow.initial_state_llc_m() or flow.snoop_rsp_m()
            keep_modified_line_in_llc = have_modified_data and (flow.is_free_inv_way() or flow.initial_map_dway())

            if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                err_msg += "Rule 1: For LLC_I final state must be LLC_I\n"

            if snoop_needed:
                if have_modified_data and not keep_modified_line_in_llc:
                    if flow.snoop_rsp_s_fwd_m():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 2.1: For modified data that cannot be saved in LLC and core still have the data in S state final LLC state should be LLC_S\n"
                        if not flow.cv_unchanged():
                            err_msg += "Rule 2.2: Cores return RspSFwdMO as snoop response, that mean they still keep the CL in S state, CV should not be changed.\n"
                        if not flow.final_map_sf():
                            err_msg += "Rule 2.3: Cores return RspSFwdMO as snoop response, that mean they still keep the CL in S state, since we don't allocate Dway final map should be SF.\n"
                    else:
                        if (not flow.final_state_llc_i()) or (not flow.final_map_sf()):
                            err_msg += "Rule 2.4: For modified data that cannot be saved in LLC and core don't have the data anymore final LLC state should be LLC_I and CV=0 and map=SF\n"

                elif have_modified_data and keep_modified_line_in_llc:
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 3.1: For modified data and we can allocated Dway in LLC, final LLC state should be LLC_S\n"
                    if (flow.snoop_rsp_m() and not flow.is_data_written_to_cache()):
                        err_msg += "Rule 3.2: For modified data that come from snoop and we can allocated Dway or use existing one in LLC, we should write the data to the cache and final map should be Dway.\n"
                    if not flow.final_map_dway():
                        err_msg += "Rule 3.2: For modified data and we can allocated Dway in LLC, final map should be Dway.\n"
                    if flow.core_still_has_data_after_snoop() and not flow.cv_unchanged():
                        err_msg += "Rule 3.3: Core still have the data after snoop CV should be unchanged.\n"
                    if not flow.core_still_has_data_after_snoop() and not flow.final_cv_zero():
                        err_msg += "Rule 3.4: Core don't have data after snoop CV bit should be zero.\n"

                else: #not have_modified_data
                    if flow.core_still_has_data_after_snoop() or flow.initial_map_dway():
                        if flow.core_still_has_data_after_snoop() and not flow.cv_unchanged():
                            err_msg += "Rule 4.1: Core still have data CV should be unchanged.\n"
                        #TODO: is it really CV unchanged?? can we remove part of the CV?
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 4.1: Core still have data or we already have Dway allocated final state should be LLC_S.\n"
                    if not flow.core_still_has_data_after_snoop() and flow.initial_map_sf():
                        if (not flow.final_state_llc_i()) or (not flow.final_map_sf()):
                            err_msg += "Rule 4.2: Core don't have data after snoop, final LLC state should be LLC_I, CV=0, MAP=SF.\n"


            else: #not snoop_needed:
                if not flow.cv_unchanged():
                    err_msg += "Rule 5.1: Since we don't need to send snoop CV bits shouldn't be changed.\n"

                if flow.initial_state_llc_m():
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 5.2: We don't need to send snoop and we are in LLC_M state, final state should be LLC_S.\n"
                    #TODO: check this funciton.
                    if not flow.wrote_data_to_mem():
                        err_msg += "Rule 5.3: We don't need to send snoop and we are in LLC_M state modified data need to be written to the memory.\n"
                else:
                    if flow.wrote_data_to_mem():
                        err_msg += "Rule 5.3: We don't need to send snoop and we are in LLC_E/S/I state data don't need to be written to the memory.\n"

                    if flow.initial_state_llc_e_or_s():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 5.4: We don't need to send snoop and we are in LLC_E/S final state need to be LLC_S.\n"
                    else:
                        if (not flow.final_state_llc_i()) or (not flow.final_map_sf()):
                            err_msg += "Rule 5.4: We are in LLC_I final state need to be LLC_I, CV=0, MAP=SF.\n"




        elif flow.is_snpldata():
            # We will send snoop in this flow in case of CV=1 or we have CV error and our real CV can be CV=1
            # In case of CV_SHARED indication we will consider the CV as CV>1 as describe in Leon visios.
            snp_sent = flow.initial_state_llc_m_or_e() and ( (flow.initial_cv_one() and not flow.initial_cv_is_shared()) or flow.has_cv_err())

            #snoop_conditions
            have_modified_data = flow.initial_state_llc_m() or flow.snoop_rsp_m()
            keep_modified_data_in_LLC = flow.snoop_rsp_s_fwd_x() and (flow.initial_map_dway() or flow.is_free_inv_way())

            if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                err_msg += "Rule 1: For LLC_I final state must be LLC_I\n"

            if snp_sent:
                if have_modified_data and keep_modified_data_in_LLC:
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 2.1: IO snoop found modified data and we are keeping the data in the LLC final state must be LLC_S.\n"
                    if not flow.final_map_dway():
                        err_msg += "Rule 2.2: Modified data should be kept in the LLC so Map should be Dway.\n"
                    if not flow.cv_unchanged():
                        err_msg += "Rule 2.3: Modified data is being kept in the LLC only if core still have the data (RspS) therefore we are not expecting any CV change in the flow.\n"
                elif have_modified_data and not keep_modified_data_in_LLC:
                    if flow.snoop_rsp_s_fwd_m():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 3.1: IO snoop found modified data and we are not keeping the data in the LLC but core still have the data in shared (RspSFwdMO) - final state must be LLC_S.\n"
                        if not flow.final_map_sf():
                            err_msg += "Rule 3.2: IO snoop found modified data and we are not keeping the data in the LLC but core still have the data in shared (RspSFwdMO) - final map should be SF.\n"
                    if flow.snoop_rsp_i() and not flow.final_state_llc_i():
                        err_msg += "Rule 3.3: IO snoop found modified data and we are not keeping the data in the LLC since core don't have the data (RspI*) - final state must be LLC_I.\n"
                else: #No modified data
                    if flow.initial_state_llc_e() and (flow.snoop_rsp_s() or flow.initial_map_dway()):
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 2.1: Snoop found non modified data, snoop got RspS* or Map=Dway, LLC final state must be LLC_S.\n"
                    if flow.initial_state_llc_e() and flow.snoop_rsp_i() and flow.initial_map_sf():
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 2.2: Snoop found non modified data, snoop got RspI* and  Map=SF, LLC final state must be LLC_I.\n"

            else: #no snoop sent
                if flow.initial_state_llc_m():
                    if flow.initial_cv_zero():
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 3.1: IO snoop found modified data with CV=0 - final state must be LLC_I.\n"
                    else: #CV>1 since for CV=1 we are doing snoop
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 3.1: IO snoop found modified data with CV>0 - final state must be LLC_S.\n"
                        if not flow.cv_unchanged():
                            err_msg += "Rule 3.1: IO snoop found modified data with CV>0 - CV bits shouldn't be changed since all cores still hold the data.\n"
                else: #LLC_E/S/I
                    #TODO: what will happen in case of stale data LLC_E CV=0 map=SF?
                    if flow.initial_state_llc_e_or_s() and not flow.final_state_llc_s():
                        err_msg += "Rule 3.1: IO snoop found CL in LLC_E with CV!=1 or LLC_S - we should downgrade to or stay at LLC_S state\n"

        elif flow.is_snpdatamig():
            #TODO: need to complete the rules.
            # Snoop with Modified Data
            snp_sent = flow.initial_state_llc_m_or_e() and (flow.initial_cv_one() or flow.has_cv_err())

            if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                err_msg += "Rule 1: For LLC_I final state must be LLC_I\n"

            if not snp_sent:
                if not snp_sent and (not flow.cv_unchanged() and not flow.has_cv_err()):
                    err_msg += "Rule 2.3: In case there is no snoop needed, we should have unchanged CV and unchanged map\n"

                if (flow.initial_state_llc_s() or (flow.initial_state_llc_e() and flow.initial_map_sf())):
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 2.1: For LLC_S or LLC_E without any changed data in the cores (CV=0 or CV>0 and map is SF) final state must be LLC_S\n"
                    if not flow.cv_unchanged() or not flow.map_unchanged():
                        err_msg += "Rule 2.2: For LLC_S or LLC_E without any changed data in the cores (CV=0 or CV>0 and map is SF) CV and map should be unchanged \n"

                if flow.initial_state_llc_e() and flow.initial_map_dway():
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 3.1: For LLC_E and map=Data we are doing clean data forwarding and therefore final state must be LLC_S\n"
                    if not flow.cv_unchanged() or not flow.map_unchanged():
                        err_msg += "Rule 3.2: For LLC_E and map=Data without any snoop to the cores CV and map should be unchanged \n"

                if flow.initial_state_llc_m() and flow.initial_cv_zero() and not flow.is_monitor_hit():
                    if not flow.final_state_llc_i():
                        err_msg += "Rule 4.1: For LLC_M with CV=0 (no core have the data) and no monitor hit we should send the data to HA and final state should be LLC_I\n"

                if flow.initial_state_llc_m() and (flow.initial_cv_more_than_one() or flow.is_monitor_hit()):
                    if not flow.final_state_llc_s():
                        err_msg += "Rule 5.1: For LLC_M with CV>0 (core have the data in shared state) or MonHit=1 we should send the data to HA and final state should be LLC_S\n"
                    if not flow.cv_unchanged() or not flow.map_unchanged():
                        err_msg += "Rule 5.2: For LLC_E and map=Data without any snoop to the cores CV and map should be unchanged \n"
                    #TODO: need to fix the below function.
                    #if not flow.wrote_data_to_mem():
                        #err_msg += "Rule 5.3: For LLC_M with CV>0 (core have the data in shared state) or MonHit=1 we should send the data to HA and to the CA that ask the data\n"

            elif snp_sent:
                update_modified_data_in_llc = flow.snoop_rsp_s_fwd_m() and (flow.is_free_inv_way() or flow.initial_map_dway())
                if flow.snoop_rsp_m() or flow.initial_state_llc_m():
                    if flow.snoop_rsp_i() and not flow.is_monitor_hit("SNP_RSP"):
                        if not flow.final_state_llc_i():
                            err_msg += "Rule 6.1: in case of RspI* and not MonHit we are expecting to finish the flow with LLC_I state\n"

                    if flow.snoop_rsp_i() and flow.is_monitor_hit("SNP_RSP"):
                        err_msg += "Rule 6.2: in case of RspI* with monitor hit we are expecting to finish the flow with LLC_I state\n"

                    if flow.snoop_rsp_s():
                        if not flow.final_state_llc_s():
                            err_msg += "Rule 6.2: in case of RspS* or RspI* with monitor hit we are expecting to finish the flow with LLC_S state\n"
                        if not flow.cv_unchanged():
                            err_msg += "Rule 6.3: Snp started from LLC_M and received RspS* therefore CV bit should be unchanged \n"

                    if update_modified_data_in_llc:
                        if flow.final_map_sf():
                            err_msg += "Rule 6.4: Snp received RspSFwdM, line should have been kept in LLC with map=DWAY\n"
                        if not flow.is_data_written_to_cache():
                            err_msg += "Rule 6.5: Snp received RspSFwdM, line should have been kept in LLC data should have been written to cache\n"
                        if not flow.cv_unchanged():
                            err_msg += "Rule 6.6: Snp received RspSFwdM therefore CV bit should be unchanged \n"


                elif flow.initial_state_llc_e() and (flow.initial_map_dway() or flow.snoop_rsp_f()):
                    if flow.initial_map_dway():
                        if (not flow.final_state_llc_s()) or (not flow.final_map_dway()):
                            err_msg += "Rule 7.1: LLC_E with MAP=DATA, line should have been kept in LLC therfore MAP should keep being Dway and final state should be LLC_S\n"

                    if flow.core_still_has_data_after_snoop():
                        if not flow.cv_unchanged():
                            err_msg += "Rule 7.2: We got RspSFwdFE there fore core still have the data and CV bit should stay unchanged\n"

                    if flow.is_free_inv_way() and flow.initial_map_sf() and flow.snoop_rsp_f():
                        if not flow.is_data_written_to_cache():
                            err_msg += "Rule 7.3: LLC_E with Dway or snp rsp received Rsp*FwdFE, line should have been kept in LLC data should have been written to cache\n"
                        if not flow.final_map_dway():
                            err_msg += "Rule 7.4: LLC_E with Dway or snp rsp received Rsp*FwdFE, we should have map=data\n"
                        if not flow.core_still_has_data_after_snoop() and not flow.final_cv_zero():
                            err_msg += "Rule 7.5: Snp received RspIFwdFE, line should have been kept in LLC with final CV=0\n"

                    else:
                        if flow.is_data_written_to_cache():
                            err_msg += "Rule 7.6: LLC_E without snp rsp received Rsp*FwdFE and FreeInvWay, line should not have been kept in LLC we should send the clean data to HA\n"
                        # TODO: need to fix the below function.
                        # if not flow.wrote_data_to_mem():
                        # err_msg += "Rule 7.7: For LLC_M with CV>0 (core have the data in shared state) or MonHit=1 we should send the data to HA and to the CA that ask the data\n"
                        if flow.snoop_rsp_i_fwd() and not flow.is_monitor_hit("SNP_RSP"):
                            if not flow.final_state_llc_i():
                                err_msg += "Rule 7.8: in case of LLC_E with RspIFwdFE and not MonHit we are expecting to finish the flow with LLC_I state\n"
                        else:
                            if not flow.final_state_llc_s():
                                err_msg += "Rule 7.9: in case of LLC_E with RspSFwdFE or MonHit we are expecting to finish the flow with LLC_S state\n"
                            if flow.snoop_rsp_i_fwd() and not flow.final_cv_zero():
                                err_msg += "Rule 7.10: in case of LLC_E with RspIFwdFE with MonHit that cause us to finish in S state final CV bit should be 0.\n"

                else:
                    if not ((flow.snoop_rsp_hit() or flow.snoop_rsp_s() or flow.snoop_rsp_flushed()) and flow.initial_state_llc_e() and flow.initial_map_sf()):
                        err_msg += "Rule 8.0: We got to this Rule even that the case is not fitted - check the rules.\n"

                    if flow.initial_state_llc_e() and (flow.snoop_rsp_s() or flow.initial_map_dway()) and not flow.final_state_llc_s():
                        err_msg += "Rule 8.1: LLC_E with RspS* or map Dway (we have Dway to keep the data or cores still keep the data in shared state) and final state is not LLC_S.\n"

                    if flow.initial_state_llc_e() and flow.snoop_rsp_i() and flow.initial_map_sf() and not flow.final_state_llc_i():
                        err_msg += "Rule 8.1: LLC_E with RspI* and map SF (we don't have the data in the cores or in the LLC) and final state is not LLC_I.\n"
            else:
                err_msg += "Val_Assert (SNPDATAMIG): we shouldn't get here please check your code\n"

        elif flow.is_llcwbinv() or flow.is_llcinv():
            if not flow.final_state_llc_i():
                err_msg += "Rule 1: Final cache state in not LLC_I, final state is: " + flow.final_cache_state + "\n"

        elif flow.is_llcwb() or flow.is_clwb():
            if flow.flow_is_hom():
                llc_miss = flow.initial_state_llc_i()
                if flow.final_state_llc_m():
                    err_msg += "Rule 1: Flow cannot finish with final state LLC_M\n"
                
                if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                    err_msg += "Rule 2.1: If initial state is LLC_I final state should be LLC_I\n"
                
                if flow.initial_state_llc_s() or (flow.initial_state_llc_e() and not flow.snoop_sent()):
                    if  (flow.is_llcwb() or (flow.is_clwb() and not flow.is_initial_stale_data())) and (not flow.state_unchanged() or ((not flow.cv_unchanged()) and (not flow.has_cv_err())) or not flow.map_unchanged()):
                        err_msg += "Rule 2.2: If initial state is of LLCWB LLC_S/E or CLWB is LLC_E/S with stale data, final, LLC should remain unchanged\n"
                    elif flow.is_clwb() and flow.is_initial_stale_data() and not flow.final_state_llc_i():
                        err_msg += "Rule 2.3: If initial state is of CLWB LLC_S and we have stale data final, final state should be LLC_I\n"

                if not flow.snoop_sent() and flow.initial_state_llc_m() and not flow.final_state_llc_e():
                    err_msg += "Rule 3: Initial state was LLC_M with no snoop final state should be LLC_E\n"
                if flow.is_initial_stale_data() and flow.is_clwb() and not flow.final_state_llc_i():
                    err_msg += "Rule 4: Stale data CV=0 and Map=SF should end with LLC_I\n"
                if flow.snoop_rsp_m() and not flow.is_available_data() and not flow.core_still_has_data_after_snoop() and not flow.final_state_llc_i():
                    err_msg += "Rule 5: Received modified data with no available data and core does not hold a copy of the line, expected state is LLC_I\n"
                if flow.snoop_rsp_m() and (flow.is_available_data() or flow.core_still_has_data_after_snoop()) and not flow.final_state_llc_e():
                    err_msg += "Rule 6: Received modified data with available data or core holds a copy of the line, expected state is LLC_E\n"
                if flow.snoop_sent() and not flow.snoop_rsp_m() and not flow.core_still_has_data_after_snoop() and not flow.initial_state_llc_m()\
                        and flow.initial_map_sf() and not flow.final_state_llc_i():
                    err_msg += "Rule 7: No modified data with RspI* that is not RspIFwdM and initial map SF should finish with LLC_I\n"
                if flow.snoop_sent() and not flow.core_still_has_data_after_snoop() and flow.initial_map_dway() and not flow.final_cv_zero() and (not flow.is_cv_err_injection()):
                    err_msg += "Rule 8: Core responded RspI* and initial map Data should finish with CV=0\n"
                if (not flow.final_state_llc_i() and (not flow.snoop_sent() or flow.core_still_has_data_after_snoop()) and not flow.cv_unchanged()) and not flow.has_cv_err():
                    err_msg += "Rule 9: Snoop not sent or core responded with RspS*, final CV should not change\n"
                if flow.snoop_rsp_m() and flow.is_available_data() and not flow.is_data_written_to_cache():
                    err_msg += "Rule 10: Received modified data with data_way_available and data was not written to cache\n"
                if (not flow.initial_state_llc_m_or_e()) and not flow.state_unchanged():
                    err_msg += "Rule 11: Initial state was LLC_I so we are expecting to finish with LLC_I\n"
                if not flow.initial_state_llc_i() and flow.initial_map_sf() and flow.snoop_sent() and flow.core_still_has_data_after_snoop() and not flow.snoop_rsp_m() and not flow.final_map_sf():
                    err_msg += "Rule 12: No modified data found, core still hold a copy of the data, final map should be SF\n"
            elif not flow.is_llcwb() and (not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged()):
                err_msg+= "Rule 13: Non Coherenet CLWB/LLCWB should not change anything in cache \n"

        elif flow.is_llcpref() and not flow.pref_used_for_promotion:
                if flow.flow_is_hom():
                    if flow.initial_state_llc_i() and flow.is_available_data() and not flow.is_tor_occup_above_threshold() and not flow.is_prefetch_elimination_flow():
                        if not flow.final_map_dway():
                            err_msg+="Rule 1: Miss in cache, final map should be DWAY\n"
                        if (not flow.is_cv_err_injection()) and not flow.final_cv_zero():
                            err_msg+="Rule 2: Miss in cache, final CV should be 0\n"
                        #In PTL mode when we are
                        if  (not flow.is_cv_err_injection()) and not flow.is_data_marked_as_brought_by_llc_prefetch():
                            err_msg += "Rule 3: Data that brought by prefetch should be marked as so in CV bit 4\n"
                        if "RFO" in flow.opcode and not flow.final_state_llc_m_or_e():
                            err_msg+="Rule 4: Miss in cache with RFOPREF final state should be state m or e according to UPI cmp\n"
                        #TODO: llcprefcode right now down grades E_CmpO to LLC_S - other wise Sate should match Cmp from UPI - RTL is expected to change this behavior - rule 4.1
                        if flow.flow_is_a_finished_pref() and not (flow.is_llcprefcode() and flow.cbo_got_ufi_uxi_cmpo_e()) and flow.final_state_dosent_macth_upi_cmp():
                            err_msg+="Rule 5: Miss in cache, final state should be determined by UPI cmp\n"
                        if flow.flow_is_a_finished_pref() and flow.is_llcprefcode() and flow.cbo_got_ufi_uxi_cmpo_e() and not flow.final_state_llc_s():
                            err_msg+="Rule 5.1: Miss in cache for LLCPREFCODE with E_CmpO writes LLC_S for perforamnce reasons\n"
                    elif (not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged()) and (not flow.has_cv_err()):
                        err_msg+="Rule 6: Hit in cache, LLC should remain unchanged\n"
                elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                    err_msg+="Rule 7: NC LLCPREF, LLC should remain unchanged\n"

        elif flow.is_itom():
            if flow.flow_is_hom():
                expected_map_data = flow.initial_state_llc_m_or_e() and flow.is_cache_near() and flow.initial_map_dway()
                if (not flow.final_cv_one() or not flow.final_req_cv_one()) and not flow.is_cv_err_injection():
                    err_msg+="Rule 1: Final CV must be 1 and req cv must be set\n"
                #If we write state we write E, in case of Hit no Snoop and M we leave it at M - looking at monitor hit only in the first pass in ItoM because Map is always SF and GO_E
                #In case we have force_snoop_all_cb_en we will consider ourself as having CV=1 that is not requestor core.
                if flow.initial_state_llc_m() and flow.initial_map_dway() and (flow.initial_cv_with_selfsnoop_zero() and not self.force_snoop_all_cb_en) and not flow.is_monitor_hit():
                    if not flow.final_state_llc_m():
                        err_msg+="Rule 2: Final state must be LLC_M (unchanged)\n"
                elif not flow.final_state_llc_e():
                    err_msg+="Rule 2: Final state must be LLC_E\n"
                if expected_map_data and flow.final_map_sf():
                    err_msg+="Rule 3: expected map is DWAY but final map is SF\n"
                elif not expected_map_data and not flow.final_map_sf():
                    err_msg+="Rule 4: expected map is SF but final map is DWAY\n"
                if flow.is_data_written_to_cache():
                    err_msg+="Rule 6: ITOM is not supposed to write data to cache\n"
            elif flow.is_mmio():
                #In ItoM we will not allocate Data way if CN=1 - this is how design implement it
                #and it also make sense since if we want to cache the data we can senf the next write with CN=1 (ItoM perpose is to have ownership)
                expected_map_data = flow.initial_map_dway()
                if not (flow.final_req_cv_one() and flow.final_cv_one()) or not flow.final_state_llc_e():
                    err_msg += "Rule 7: NC ItoM to MMIO, final cv should be 1 with final state LLC_E\n"
                if expected_map_data and flow.final_map_sf():
                    err_msg+="Rule 8.1: MMIO - expected map is DWAY but final map is SF\n"
                elif not expected_map_data and not flow.final_map_sf():
                    err_msg+="Rule 8.2: MMIO - expected map is SF but final map is DWAY\n"
            #not MMIO meaning CRABABORT
            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 7: NC ItoM, LLC should remain unchanged\n"


        elif flow.is_specitom():
            if flow.flow_is_hom():
                llc_hit_no_snp = flow.initial_state_llc_m_or_e() and flow.initial_cv_with_selfsnoop_zero() and not flow.is_monitor_hit("go_sent")
                read_from_mem = flow.initial_state_llc_s() or flow.initial_state_llc_i()

                expected_map_data = flow.is_available_data() and (flow.snoop_rsp_m() or flow.initial_map_dway()) and not flow.flow_is_hom()

                if not read_from_mem and llc_hit_no_snp and flow.initial_map_dway():
                    expected_map_data = True
                elif not read_from_mem and flow.snoop_sent():
                    #Monitor hit RTL optimization
                    if flow.snoop_rsp_m() and flow.is_monitor_hit("go_sent") and flow.initial_cv_zero():
                        expected_map_data = flow.initial_map_dway()
                    else:
                        expected_map_data =  (flow.snoop_rsp_m() and flow.is_available_data() ) or flow.initial_map_dway()

                    if (not flow.is_cv_err_injection()) and (not flow.final_cv_one() or not flow.final_req_cv_one()):
                        err_msg+="Rule 1: Final CV must be 1 and req cv must be set\n"
                    elif expected_map_data and flow.final_map_sf():
                        err_msg += "Rule 2: expected map is DWAY but final map is SF\n"
                    elif not expected_map_data and not flow.final_map_sf():
                        err_msg += "Rule 3: expected map is SF but final map is DWAY\n"
                    if llc_hit_no_snp and not flow.state_unchanged():
                        err_msg += "Rule 4: For cache hit final state should not change"
                    if not flow.initial_state_llc_m_or_e() and not flow.final_state_llc_e():
                        err_msg += "Rule 5: For LLC state S/I final state must be LLC_E\n"
                    if flow.initial_state_llc_e() and not flow.snoop_rsp_m() and not flow.final_state_llc_e():
                        err_msg += "Rule 6: For LLC state E and no modifed data in snoop response final state must be  LLC_E\n"
                    if (flow.initial_state_llc_m() or flow.snoop_rsp_m()) and not flow.wrote_data_to_mem() and not flow.final_state_llc_m():
                        err_msg += "Rule 7: Modified data was found and not written to memory, final state must be LLC_M\n"
                    if flow.snoop_rsp_m() and flow.wrote_data_to_mem() and not flow.final_state_llc_e():
                        err_msg += "Rule 8: Modified data from snoop was written to memory - final state should be LLC_E\n"
                    if flow.snoop_rsp_m() and flow.is_available_data() and not flow.data_written_to_cache:
                        err_msg += "Rule 9: Modified data from snoop should have been written to cache\n"
            #NC SPEC ITOM
            elif flow.is_mmio():
                expected_map_data = (flow.initial_map_dway() and not flow.initial_state_llc_i()) or (flow.snoop_rsp_m() and flow.is_available_data())
                if not (flow.final_req_cv_one() and flow.final_cv_one()):
                    err_msg += "Rule 10.1: NC ItoM to MMIO, final cv should be 1\n"

                #If we have map Dway or we should allocate Data way we can save the data the come with M state as modified.
                if expected_map_data and flow.snoop_rsp_m():
                    if not flow.final_state_llc_m():
                        err_msg += "Rule 11.1: Final state should be LLC_M\n"
                elif not flow.final_state_llc_e():
                    err_msg += "Rule 11.2: Final state should be LLC_E\n"

                if expected_map_data and flow.final_map_sf():
                    err_msg+="Rule 12.1: MMIO - expected map is DWAY but final map is SF\n"
                elif not expected_map_data and not flow.final_map_sf():
                    err_msg+="Rule 12.2: MMIO - expected map is SF but final map is DWAY\n"
            #not MMIO meaning CRABABORT
            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 13: NC Spec_ItoM, LLC should remain unchanged\n"

        elif flow.is_wbmtoe():
            if flow.flow_is_hom():
                if flow.core_sent_bogus_data() and not flow.llc_unchanged():
                    err_msg+="Rule 1: Bogus data should not update any information in cache\n"
                if flow.wrote_data_to_mem() and not flow.final_state_llc_e():
                    err_msg+="Rule 2: CBo wrote data to mem final state should be LLC_E\n"
                if not flow.core_sent_bogus_data() and not flow.wrote_data_to_mem():
                    if not flow.final_state_llc_m():
                        err_msg+="Rule 3.1: CBo did not write data to memory final state should be LLC_M\n"
                    if not flow.data_written_to_cache:
                        err_msg+="Rule 3.2: CBo did not write data to memory data should have been written to cache\n"
                #In case of WBMTOE we are not writing the CV bit at the end of the flow since we starting from M and finish at E state.
                #Therefore in case of an error we will not fix the CV bit and it will be fixed in the next flow.
                if (not flow.core_sent_bogus_data() and (not flow.final_cv_one() or not flow.final_req_cv_one())) and not flow.has_cv_err():
                    err_msg+="Rule 4: No bogus data, Final CV must have only req cv set\n"
            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 5: NC WbMtoE, LLC should remain unchanged\n"

        elif flow.is_wbmtoi():
            if flow.flow_is_hom():
                if flow.core_sent_bogus_data() and not flow.llc_unchanged():
                    err_msg += "Rule 1: Bogus data should not update any information in cache\n"
                if flow.wrote_data_to_mem() and not flow.final_state_llc_i():
                    err_msg+="Rule 2: CBo wrote data to mem final state should be LLC_I\n"
                if not flow.core_sent_bogus_data() and not flow.wrote_data_to_mem():
                    if not flow.final_state_llc_m():
                        err_msg+="Rule 3.1: No bogus data, CBo did not write data to memory final state should be LLC_M\n"
                    if not flow.data_written_to_cache:
                        err_msg+="Rule 3.2: No bogus data, CBo did not write data to memory data should have been written to cache\n"
                    #In case we had cv_err we cannot expect that final CV == 0. since at the end of WBMTOI we are not cleanning the CV bits(we will not do the append CV in case of an err).
                    #Therfore we can find that at the end of the flow we will not have CV=0.
                    if not flow.final_cv_zero() and not (flow.has_cv_err() or flow.is_cv_err_injection()):
                        err_msg+="Rule 3.3: No bogus data, Final CV should be 0\n"
                    if not flow.final_map_dway():
                        err_msg+="Rule 3.4: No bogus data, Final map should be data\n"
            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 4: NC WbMtoI, LLC should remain unchanged\n"

        #Note: This flow can get an initial state of LLC_I due to a conflict with a UPI Snoop
        elif flow.is_wbeftoe():
            if flow.flow_is_hom():
                #Important: Assumption that Core will send WbEF* only when MLC is in E/F state in case of MLC=M core will send WbM*
                if (not flow.state_unchanged() or not flow.cv_unchanged()) and not flow.has_cv_err():
                    err_msg+= "Rule 1: WbEFtoE should not change State or CV\n"

                if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                    err_msg+= "Rule 2: For inital state LLC_I , probably CBo has been snooped and final state should LLC_I\n"

                #Relying on flow checker to determine if a correct wr pull has been sent - if so we expect to write the data
                if flow.cbo_sent_go_wr_pull() and not flow.core_sent_bogus_data() and not flow.is_data_written_to_cache():
                    err_msg+= "Rule 6: CBo sent GO_WrPull to core because it can allocate a dway for this data but no data has been written to cache\n"

                if (flow.cbo_sent_go_wr_pull_drop() or flow.core_sent_bogus_data()) and flow.is_data_written_to_cache():
                    err_msg+= "Rule 7: CBo sent GO_WrPullDrop to core because it cannot allocate a dway or core has sent bogus data - and garbage data has been written to cache\n"

            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 8: NC WbEFtoE, LLC should remain unchanged\n"

        elif flow.is_wbeftoi():
            if flow.flow_is_hom():
                #Important: Assumption that Core will send WbEF* only when MLC is in E/F state in case of MLC=M core will send WbM*
                if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                    err_msg+= "Rule 2: For inital state LLC_I , probably CBo has been snooped and final state should LLC_I\n"

                #Relying on flow checker to determine if a correct wr pull has been sent - if so we expect to write the data
                if flow.cbo_sent_go_wr_pull_drop():
                    if not flow.initial_state_llc_i() and flow.initial_cv_more_than_one() and not flow.state_unchanged():
                        err_msg+= "Rule 3.1: CBo sent GO_WrPullDrop and other cores hold a copy of the line, State should not change\n"
                    if flow.initial_state_llc_e_or_s() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and flow.initial_map_sf() and not flow.final_state_llc_i():
                        err_msg+= "Rule 3.2: CBo sent GO_WrPullDrop and only req cv is 1 with no modified data and initial map was SF - final state must be LLC_I\n"

                #We are asking if CV>2 since according to CV decoding we cannot recognize if we have more the one core that have the line unless we have more the two CV bits on
                #In case we have 2 cores or less that hold the data we will not use decoding of mode=0 and therefore we will know if we have only one core or we have two that hold the data.
                #if not flow.initial_cv_more_than_value(value=2) and not flow.final_state_llc_i() and not flow.final_req_cv_zero() and not (flow.is_cv_err_injection() or flow.has_cv_err()):
                if flow.initial_cv_one() and not flow.final_state_llc_i() and not flow.final_req_cv_zero() and not (flow.is_cv_err_injection() or flow.has_cv_err()):
                    err_msg+="Rule 4: After WbEFtoI when we have only one CV bit and it is ReqCV, final state is not LLC_I - req cv needs to be zero\n"
                #if not flow.initial_cv_more_than_value(value=2) and not (flow.has_cv_err() or flow.is_cv_err_injection()) and flow.cbo_sent_go_wr_pull() and not flow.core_sent_bogus_data() and not flow.final_req_cv_zero():
                if flow.initial_cv_one() and not (flow.has_cv_err() or flow.is_cv_err_injection()) and flow.cbo_sent_go_wr_pull() and not flow.core_sent_bogus_data() and not flow.final_req_cv_zero():
                    err_msg += "Rule 5: CBo sent GO_WrPull to core because it can allocate a dway, data is not bogus, final ReqCV should be 0\n"
                if flow.cbo_sent_go_wr_pull() and not flow.core_sent_bogus_data() and not flow.is_data_written_to_cache():
                    err_msg+= "Rule 6: CBo sent GO_WrPull to core because it can allocate a dway for this data but no data has been written to cache\n"
                if (flow.cbo_sent_go_wr_pull_drop() or flow.core_sent_bogus_data()) and flow.is_data_written_to_cache():
                    err_msg+= "Rule 7: CBo sent GO_WrPullDrop to core because it cannot allocate a dway or core has sent bogus data - and garbage data has been written to cache\n"
            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 8: NC WbEFtoI, LLC should remain unchanged\n"

        elif flow.is_wbstoi():
            if flow.flow_is_hom():
                if not flow.initial_state_llc_i() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and flow.initial_map_sf():
                    if not flow.final_state_llc_i():
                        err_msg+="Rule 1: Initial State is not LLC_I and only ReqCV is set with initial map SF - Final state should be LLC_I to avoid stale data\n"
                elif not flow.state_unchanged() or not flow.map_unchanged():
                    err_msg+= " Rule 2: LLC should not changed due to this flow\n"
                if not flow.final_state_llc_i() and ((flow.final_cv != flow.get_exp_final_cv_with_req_cv_zero()) and not (flow.is_cv_err_injection() or flow.has_cv_err())):
                    err_msg+= "Rule 3: Final state is not LLC_I and Final CV is incorrect, initial cv bits should have been kept and reqcv should be 0\n"
            elif not flow.cv_unchanged() or not flow.state_unchanged() or not flow.map_unchanged():
                err_msg += "Rule 4: NC WbStoI, LLC should remain unchanged\n"


        elif flow.is_cldemote():
            if flow.flow_is_hom():
                snp_sent = flow.req_core_initial_cv_bit_is_one() and flow.is_available_data() and not flow.initial_state_llc_i()
                allocate = flow.snoop_rsp_m() or (flow.snoop_rsp_f() and flow.initial_map_sf())
                #if not snoop is sent LLC should remain unchanged
                if not snp_sent and (not flow.state_unchanged() or (not flow.cv_unchanged() and not flow.has_cv_err()) or not flow.map_unchanged()):
                    err_msg+= "Rule 1: Snoop not sent because LLC cannot allocate dway or ReqCV = 0 or initital state is LLC_I, LLC should not be changed\n"
                if (not (flow.has_cv_err() or flow.is_cv_err_injection())) and (snp_sent and not flow.final_state_llc_i() \
                                                                                and (flow.final_cv != flow.get_exp_final_cv_with_req_cv_zero())):
                    err_msg+= "Rule 2: Final CV is incorrect, it should contain initial CV without the requesting core CV bit\n"
                if snp_sent and allocate and flow.final_map_sf():
                    err_msg+= "Rule 3: Snoop was sent and final map is not dway\n"
                if flow.initial_state_llc_i() and not flow.final_state_llc_i():
                    err_msg+= "Rule 4: Initial state is LLC_I, final state should be LLC_I\n"
                if snp_sent and flow.initial_cv_more_than_one() and not flow.state_unchanged():
                    err_msg+= "Rule 5: Snoop was sent and iniitial CV was more than 1, final state should not change\n"
                if (flow.initial_state_llc_m() or (snp_sent and flow.snoop_rsp_m()) ) and not flow.final_state_llc_m():
                    err_msg+= "Rule 6: Modified data was found, final state must be LLC_M\n"
                if snp_sent and flow.snoop_rsp_f() and not flow.state_unchanged():
                    err_msg+= "Rule 7: core sent forwarded un modified data after a snoop - state should not change\n"
                if snp_sent and flow.snoop_rsp_i_hit() and flow.initial_cv_one() and flow.initial_map_sf() and not flow.initial_state_llc_m() and not flow.initial_state_llc_i() and not flow.final_state_llc_i():
                    err_msg+= "Rule 8: Initial map was SF, There is no modified data in the system, initial CV was 1 and core responded RspIHit*, final state should be LLC_I to avoid stale data\n"
                if snp_sent and allocate and not flow.is_data_written_to_cache():
                    err_msg+= "Rule 9: Snoop was sent and CBo should allocate dway and write data to LLC\n"
            elif not flow.state_unchanged() or not flow.cv_unchanged() or not flow.map_unchanged():
                err_msg+= "Rule 10: Non Coherenet CLDEMOTE should not change anything in cache \n"


        # General Rules that apply to all flows
        if self.should_check_general_rules(flow):
            # if flow.final_state_llc_i() and not flow.final_map_sf():
            #    err_msg+="General Rule 101: Final cache state is LLC_I but final map is not SF, final map is: "+flow.final_map+"\n"
            if ( (flow.initial_map_sf() and not flow.final_state_llc_i()) or flow.initial_state_llc_i()) and not flow.final_state_llc_i() and flow.final_map_dway() and not flow.is_data_written_to_cache():
                err_msg += "General Rule 101: Data was moved from SF to DWAY or final map is DWAY after a miss and data was not written to cache\n"
            # known issue, rtl get monitor inidication after llc opcode decision
            if flow.final_map_sf() and flow.is_data_written_to_cache() and not flow.flow_should_ignore_false_data_wr_to_sf():
                err_msg += "General Rule 102: Data was written to cache when final map is SF\n"

            rule_103_exceptions = flow.is_prefetch_elimination_flow()
            rule_103_cv_error_exception = flow.is_cv_err_injection() or (flow.is_llcpref and flow.has_cv_err())
            if flow.final_state_llc_m() and flow.final_map_sf() and not flow.final_cv_one() and not rule_103_cv_error_exception and not rule_103_exceptions:
                err_msg += "General Rule 103: Final map is SF with LLC_M - Final CV must be 1\n"

            #TODO PTL: instead of not flow.flow_is_hom -this will apply when we are in NEM mode also and in NC - asaffeld 2/2022
            rule_104_exceptions = flow.is_itom() or flow.is_llcinv() or flow.is_snpLDrop() or buried_m or not flow.flow_is_hom()
            if (flow.initial_state_llc_m() or flow.snoop_rsp_m()) and not flow.wrote_full_cache_line_to_mem() and not rule_104_exceptions and not flow.final_state_llc_m():
                err_msg += "General Rule 104: For LLC_M or Snp Rsp with FwdM and not writeback to mem final state must be LLC_M, except for ItoM, snpLDrop and LLCINV flow and buried_m\n"

            rule_105_exceptions = flow.is_llc_special_opcode() or flow.is_wcil() or flow.is_mempushwr() or flow.is_wcilf() or flow.is_wbeftoi() or flow.is_wbstoi() or flow.is_wbmtoi()
            if buried_m and not rule_105_exceptions and not  (flow.final_state_llc_m_or_e() or flow.final_cv_one() or flow.final_req_cv_one()):
                err_msg += "General Rule 105: We have buried_m condition but we lost our ReqCV bit or CV is not 1 or LLC state is not M/E - potential lost of M data"
            if (flow.final_state_llc_m_or_e_or_s() and not flow.is_llcwb() and (
                    int(flow.final_tag_way) >= (CCF_COH_DEFINES.max_num_of_tag_ways / 2)) and not flow.is_tag_bit_zero()):
                err_msg += "General Rule 106: line with tag bit 0 can be allocate only in the first 16 ways\n"
            if (flow.final_state_llc_m_or_e_or_s() and not flow.is_llcwb() and (
                    int(flow.final_tag_way) < (CCF_COH_DEFINES.max_num_of_tag_ways / 2)) and flow.is_tag_bit_zero()):
                err_msg += "General Rule 107: line with tag bit 1 can be allocate only in the last 16 ways \n" + "is tag bit zero: " + str(
                    flow.is_tag_bit_zero()) + "\n"
            rule_108_exceptions = flow.is_clwb() and flow.core_still_has_data_after_snoop() and flow.initial_cv_zero() #clwb does not update cv and therefore if core sends rspS due to monitor and initial CV was zero final cv with remain 0 
            if ((flow.core_still_has_data_after_snoop() and not self.consider_RspSI_as_RspI_core_do_not_has_data(flow)) or flow.cbo_sent_go_mesf()) \
               and ((flow.final_cv_zero() and not (flow.has_cv_err() or flow.is_cv_err_injection())) or flow.final_state_llc_i()) and not rule_108_exceptions:
                err_msg += "General Rule 108: Sent snoop and recevied RspS* or Sent GO_M/E/F/S, final state is LLC_I or CV is zero\n"
            #This rule is more like a valid assertion if we entered it something is wrong in validation - because go_i flows don't keep initial CV
            if not flow.initial_state_llc_i() and not flow.final_state_llc_i() and flow.initial_cv_more_than_zero() \
                    and flow.cbo_sent_go_i() and flow.core_still_has_data_after_snoop() \
                    and (not flow.is_initial_cv_exist_in_final_cv() or flow.final_req_cv_one()):
                err_msg+="General Rule 109: Initial and final state are not LLC_I, a GO_I has been sent to requestor and other cores may still have data" \
                         "CBo should have kept original CV bits\n"
            if not flow.initial_state_llc_i() and not flow.final_state_llc_i() and flow.initial_cv_more_than_zero() \
                    and flow.cbo_sent_go_s_or_f() and flow.core_still_has_data_after_snoop() \
                    and (not flow.is_initial_cv_exist_in_final_cv() or not flow.final_req_cv_one()) and (not flow.is_cv_err_injection()):
                err_msg+="General Rule 110: Initial and final state are not LLC_I, a GO_S has been sent to requestor and other cores may still have data" \
                         "CBo should have kept original CV bits and add the requestor CV bit also\n"

            #A prefetch that didn't finish does not write the final state
            #Un chachable reads that finish with LLC_I
            #Wr and inv flows that finish with state LLC_I
            rule_111_exceptions = not flow.flow_is_a_finished_pref() or \
                                  (flow.is_partial_or_uncachable_rd() and flow.read_data_from_mem() and flow.cbo_got_ufi_uxi_cmpo_e()) or \
                                  (flow.is_wr_and_inv_flow() and flow.cbo_got_ufi_uxi_cmpo_e())

            if not rule_111_exceptions and flow.cbo_got_ufi_uxi_cmpo() and flow.final_state_dosent_macth_upi_cmp():
                err_msg+="General Rule 111: CBo received CmpO from UPI and final state does not match it\n"


            #if we have snoop response RSPI* and CV=1 we are expecting to have CV=0 in case of write and CV=1 in case of another core that getting the data.
            #if the flow was snoop that coming from UPI we will expect to have CV=0 else we will expec CV=1 if ReqCV=1 and CV=0 elsewhere
            if (not flow.is_cv_err_injection()) and ((flow.snoop_rsp_i_hit() or flow.snoop_rsp_i_fwd_x() or flow.snoop_rsp_flushed()) and flow.initial_cv_one() \
                                                     and not ((flow.is_idi_flow_origin() and flow.final_req_cv_one() and flow.final_cv_one()) or flow.final_cv_zero() or flow.final_state_llc_i())):
                err_msg+="General Rule 112: In case we got snoop RSPI* and CV=1 we are expecting to finish with CV=0 or ReqCV=1\n"

            if (not flow.is_cv_err_injection()) and ((flow.cbo_sent_go_m() or flow.cbo_sent_go_e()) and (not flow.final_cv_one() or not flow.final_req_cv_one() or not flow.final_state_llc_m_or_e())):
                err_msg+="General Rule 113: CBO sent GO_M/GO_E - final state must be LLC_M/E with CV=1 and ReqCV=1\n"
            #
            if (not flow.is_cv_err_injection()) and (flow.cbo_sent_go_s_or_f() and not flow.initial_state_llc_i() and ((not flow.initial_cv_zero() and not flow.snoop_sent()) or flow.core_still_has_data_after_snoop()) and (not flow.is_initial_cv_exist_in_final_cv() or not flow.final_req_cv_one())):
                err_msg+="General Rule 114: CBO sent GO_S/GO_F - initial CV should have been kept and only requestor bit should have been added\n"

            if (not flow.is_cv_err_injection()) and (((flow.initial_cv_zero() and not flow.initial_state_llc_i()) or flow.initial_state_llc_i() or not flow.core_still_has_data_after_snoop()) and flow.cbo_sent_go_mesf() and not (flow.final_cv_one() or flow.final_req_cv_one())):
                err_msg+="General Rule 115: Inital CV was 0 or LLC was in LLC_I state or snoop was sent and core sent RspI*, and non GO_I was sent to core - final reqCV=1 and CV=1\n"

            if flow.cbo_sent_go_mesf() and flow.final_state_llc_i():
                err_msg+="General Rule 116: a GO_M/E/S/F was sent to core and final state is LLC_I\n"

            if flow.is_flow_origin_uxi_snp() and flow.snoop_sent() and flow.snoop_rsp_i() and (not flow.is_cv_err_injection()) and (not flow.final_state_llc_i()) and (not flow.final_cv_zero()):
                err_msg += "General Rule 117: UPI snooop received RspI* final state is not LLC_I, excpecting final CV to be 0\n"

            if flow.is_flow_origin_uxi_snp() and flow.snoop_sent() and flow.core_still_has_data_after_snoop() and not flow.final_state_llc_i() and (not flow.cv_unchanged() and not flow.has_cv_err()):
                err_msg += "General Rule 118: UPI snooop sent a snoop to core, core still has data - cv should not change\n"

            if not flow.is_cldemote() and flow.snoop_sent() and flow.snoop_rsp_i() and flow.cbo_sent_go_i() and not flow.final_state_llc_i() and not flow.final_cv_zero():
                err_msg += "General Rule 119: Flow sent snoop, recevied RspI* and Sent GO_I, final state is not LLC_I, Final CV - must be 0\n"

            if flow.snoop_sent() and flow.snoop_rsp_i() and flow.cbo_sent_go_mesif() and not flow.cbo_sent_go_i() and not flow.is_cv_err_injection() and (not flow.final_cv_one()):
                err_msg += "General Rule 120: Flow sent snoop, recevied RspI* and Sent GO_S/M/E/F, Final CV - must be 1\n"

            if (flow.initial_cv_more_than_zero() and not (flow.has_cv_err() or flow.is_cv_err_injection())) and flow.snoop_sent() and flow.core_still_has_data_after_snoop() and not flow.is_initial_cv_exist_in_final_cv():
                err_msg += "General Rule 121: Initial CV was more than 0, and snoop response was not RspI*, Initial CV should have been kept\n"

            if flow.is_flow_origin_uxi_snp() and flow.initial_state_llc_m() and flow.initial_cv_zero() and flow.initial_map_sf():
                err_msg += "General Rule 122: UPI Snoop hits LLC_M with CV=0 and Map=SF - this is a forbidden scenario\n"

            rule_123_exceptions = flow.is_llcprefcode() or flow.is_llcprefdata() or flow.is_llcprefrfo() or (flow.is_cldemote() and flow.initial_cv_with_selfsnoop_zero())
            #In case of opcode WBSTOI or CLDEMote with CV bit error the flow does not take any action about the CV bits and the error remains,
            #This is why in this case the final CV bits can be zero (as a result of initial CV bits zero with error)
            # with map=SF and final state of LLC not I so this opcode is excluded in this rule.
            rule_123_cv_err_exception = flow.is_cv_err_injection() or ((flow.is_wbstoi() or flow.is_wbeftoi() or flow.is_wbeftoe() or flow.is_wbmtoe() or flow.is_clwb() or flow.is_cldemote() or flow.is_llcwb() or flow.is_snpcode()) and flow.has_cv_err_with_no_fix())
            if not flow.final_state_llc_i() and (flow.final_cv_zero() and not rule_123_cv_err_exception) and flow.final_map_sf() and not rule_123_exceptions:
                err_msg+="General Rule 123: LLC Reached stale Data\n"

            is_promoted_DRd_flow = flow.is_drd() and flow.is_flow_promoted()
            if (not flow.is_prefetch() and not is_promoted_DRd_flow) or flow.prefetch_elimination_flow or (flow.is_llcpref() and flow.pref_used_for_promotion):
                if flow.is_data_marked_as_brought_by_llc_prefetch():
                    err_msg += "General Rule 124: CL marked as brought by prefetch with no reason.\n"

            is_snpcur_exceptions = (flow.is_snpcurr() or flow.is_snplcurr()) and (flow.santa_snoop_response in ["RspCurData", "RspE"])
            list_of_snoop_rsp_that_allow_with_monitor_hit = ["RspS", "RspFwdS", "RspFwd"]
            got_snoop_rsp_s = (flow.santa_snoop_response is not None) and (any([True for legal_rsp in list_of_snoop_rsp_that_allow_with_monitor_hit if legal_rsp in flow.santa_snoop_response]))
            #got_snoop_rsp_s = (flow.santa_snoop_response is not None) and (("RspS" in flow.santa_snoop_response) or ("RspFwdS" in flow.santa_snoop_response) or ("RspFwd"))
            if flow.is_snoop_opcode() and flow.is_monitor_hit_for_upi_snoop_flow() and not (got_snoop_rsp_s or is_snpcur_exceptions):
                err_msg += "General Rule 125.1: UPI SnoopFlush with monitor hit didn't return RspS.\n"

            #When the opcode is drd or crd and there was hit in the LLC and the cbo sent GO_S and at least one core kept the data it means that we need to append new CV bit to the CV array,
            # but if it is a case of CV bit error then all the relevant bits in the cv (according to the enabled cbo's)
            # should get 1 since we are doing append operation and don't know which CV bits are correct (Exeption -> unless it is the case of injection error to the CV array).
            if (flow.is_drd() or flow.is_crd()) and flow.hit_in_cache() and flow.cbo_sent_go_s() and flow.has_cv_err() and flow.core_still_has_data_after_snoop() \
                and (not flow.final_cv_is_all_one()) and (not flow.is_cv_err_injection()):
                err_msg += "General Rule 126: Flow that supposed to append new CV bit to the CV array and has a CV bit error - the final CV should be all one.\n"

            # In case of CV_ERR we will snoop all cores and the fullCV bits that was reflected in the CBO TRK will be all 1's
            #if(flow.has_cv_err() and flow.get_num_of_valid_cores_in_final_cv()!= self.si.num_of_cbo):
            #    err_msg += "General Rule 126: CV bit error occured but cv vector is not full.\n"

        if len(err_msg) > 0:
            out_err_msg = "Opcode {}: of TID {} is violating the following rules\n{} \n{}".format(flow.opcode, flow.uri["TID"],err_msg, flow.get_flow_info_str())
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=out_err_msg)
        else:
            self.collect_coverage()
