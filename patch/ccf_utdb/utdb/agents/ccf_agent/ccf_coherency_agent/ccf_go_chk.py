    #!/usr/bin/env python3.6.3

#################################################################################################
# ccf_go_chk.py
#
# Owner:              asaffeld
# Creation Date:      11.2020
#
# ###############################################
#
# Description:
#   This file containts the content of the GO checker
#   The checker chekcs the correctness of GO sent to core
#   It bases it's decisions on the ccf_flows data base
#################################################################################################
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from val_utdb_report import VAL_UTDB_ERROR


class ccf_go_chk(ccf_coherency_base_chk):
    def __init__(self):
        super().__init__()
        self.checker_name = "ccf_go_chk"
        #The list "temp_excluded_opcodes" should be empty this is only for opcodes that wasn't done yet
        self.temp_excluded_opcodes = []

        self.excluded_opcodes_from_go_check = ["OPCODE_A", "OPCODE_B"]
        self.excluded_opcodes_from_go_check.extend(self.temp_excluded_opcodes)


    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow) and flow.opcode not in self.excluded_opcodes_from_go_check \
               and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_flusher_origin() and not flow.is_u2c_dpt_req()

    #Function will return false in case the flow should return GO.
    def is_go_expected_in_flow(self, flow):
        return not (flow.is_snoop_opcode() or flow.is_fsrdcurr() or flow.is_victim())

    def check_flow(self,flow: ccf_flow):
        err_msg = ""

        #General Rules that apply to all flows
        # general checks
        if flow.snoop_rsp_s() and flow.cbo_sent_go() and not (flow.cbo_sent_fast_go() or flow.cbo_sent_fast_go_extcmp()) and not flow.cbo_sent_go_s_or_f():
            err_msg += "General Rule 101: CBo did not send GO_S after RspS*. GO sent was: " + flow.go_type + "\n"

        if not flow.cbo_sent_go() and self.is_go_expected_in_flow(flow):
            err_msg+="General Rule 102: No GO was found for this flow \n"

        if flow.final_state_llc_m() and flow.final_map_sf() and (flow.cbo_sent_go_f() or flow.cbo_sent_go_s()):
            err_msg+="General Rule 103: Final state is LLC_M and final map is SF but we still sent GO_F/S." \
                     "(we can lost M data since core can drop the data even after GO_F therefore we had to send GO_M/E)"

        if flow.cbo_sent_go_s() and flow.final_map_sf():
            err_msg+="General Rule 104: map is SF, need to send GO_F instead of GO_S\n"

        if flow.cbo_sent_go_f() and flow.final_map_dway():
            err_msg+="General Rule 105: map is DATA, need to send GO_S instead of GO_F\n"

        if flow.is_cache_near() and flow.cbo_sent_go() and flow.cbo_sent_go_m():
            err_msg+="General Rule 106: if cn = 1 ccf must not return GO-M (idi rule 29)\n"


        got_monitor_hit_only_in_go_pass = (flow.is_monitor_hit("go_sent") and (flow.is_flow_promoted() or not flow.is_monitor_hit("first")))
        go_m_or_e_execption = flow.core_still_has_data_in_s() or (((flow.snoop_rsp_i() and flow.initial_map_sf()) or flow.initial_state_llc_i()) and not flow.cbo_got_ufi_uxi_cmpo_m())
        must_get_go_m_or_e_in_monitor_hit = ((flow.final_state_llc_m() or (flow.initial_state_llc_e() and not flow.read_data_from_mem())) and (not flow.is_cache_near()) or flow.cbo_got_ufi_uxi_cmpo_m()) and got_monitor_hit_only_in_go_pass and (not flow.wrote_data_to_mem()) and not go_m_or_e_execption

        if flow.is_monitor_hit("go_sent") and not (flow.snoop_sent and flow.all_snoops_where_snpinv()) and (not must_get_go_m_or_e_in_monitor_hit) and (flow.cbo_sent_go_m() or flow.cbo_sent_go_e()):
            err_msg+="General Rule 107: flow is monitor_hit (On GO pipe pass) but GO sent was GO_E or GO_M\n"

        if flow.cbo_sent_go_m() and not (flow.final_state_llc_m() or (flow.final_state_llc_e() and flow.final_map_sf())):
            err_msg+="General Rule 108_a: CCF sent GO_M to core but LLC state is not M\n"

        rule_108_b_exceptions = flow.is_itom() or \
                                (flow.initial_state_llc_m() and (flow.is_llcpref() or \
                                                                 flow.core_sent_bogus_data() or \
                                                                 (flow.is_cldemote() and (flow.req_core_initial_cv_bit_is_zero() or flow.has_cv_err())) or \
                                                                 (flow.cv_unchanged() and flow.final_state_llc_m()))) or \
                                (flow.is_wbstoi() and flow.initial_state_llc_m() and flow.initial_map_sf() and (flow.cv_unchanged() or flow.is_cv_err_injection() or flow.has_cv_err()))

        if flow.cbo_sent_go() and flow.final_map_sf() and flow.final_state_llc_m() and not rule_108_b_exceptions and not flow.cbo_sent_go_m():
            err_msg+="General Rule 108_b: CCF have data in M state but it didn't send GO_M when map is SF -  we lost M data\n"

        if flow.flow_is_crababort() and not (flow.is_wcil() or flow.is_wcilf() or flow.is_mempushwr() or flow.is_wb_flow() or flow.is_enqueue()):
            if flow.is_clflush_opt() or flow.is_clwb():
                if not flow.cbo_sent_fast_go_extcmp():
                    err_msg += "General Rule 0: clflush_opt and clwb to CRABABORT should rsp with fastgo_extcmp, the GO sent was: " + flow.go_type+ "\n"
            else:
                if not flow.cbo_sent_go_i():
                    GO = "NONE"
                    if flow.go_type is not None:
                        GO = flow.go_type
                    err_msg += "General Rule 0: flow is CRABABORT but CBo did not send GO_I, the GO sent was: " + GO + "\n"

        elif flow.is_snoop_opcode():
            if flow.cbo_sent_go():
                err_msg+="Rule 1: CBo sent unexpected GO in snoop flow. the GO sent was: "+flow.go_type+"\n"

        #Uncacheable Reads PRD/UCRDF/PRD
        elif "CRD_UC" in flow.opcode or "UCRDF" in flow.opcode or "PRD" in flow.opcode:
            if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not send GO_I, the GO sent was: "+flow.go_type+"\n"

        #RdCurr
        elif flow.is_rdcurr():
            if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not send GO_I, the GO sent was: "+flow.go_type+"\n"

        #WCILF/ITOMWR_WT
        elif flow.is_wcilf_or_itomwr_wt():
            if not flow.cbo_sent_fast_go_wr_pull():
                err_msg+="Rule 1: CBo did not send FAST_GO_WRITEPULL, GO sent is: "+flow.go_type+"\n"

        #WCiL/WCiL_NS
        elif flow.is_wcil():
            if not flow.cbo_sent_fast_go_wr_pull():
                err_msg+="Rule 1: CBo did not send FAST_GO_WRITEPULL, GO sent is: "+flow.go_type+"\n"

        #ITOMWR/ITOMWR_NS
        elif flow.is_itomwr():
            if not flow.cbo_sent_go_wr_pull():
                err_msg+="Rule 1: CBo did not send GO_WRITEPULL, GO sent is: "+flow.go_type+"\n"

        #ITOM
        elif flow.is_itom():
            if not flow.cbo_sent_go_e():
                    err_msg+="Rule 1: CBo did not send GO_E, GO sent is: "+flow.go_type+"\n"

        #SpecItoM
        elif flow.is_specitom():
            if not flow.cbo_sent_go_e():
                err_msg+="Rule 1: CBo did not send GO_E, GO sent is: "+flow.go_type+"\n"

        #LLCPrefData/LLCPrefCode/LLCPrefRFO
        elif flow.is_llcpref():
           if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not send GO_I, the GO sent was: "+flow.go_type+"\n"

        #CLFLUSH
        elif flow.is_clflush():
           if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not send GO_I, the GO sent was: "+flow.go_type+"\n"
        #CLFLUSHOPT
        elif flow.is_clflush_opt():
            if flow.flow_is_hom() and (flow.is_llc_miss() or (flow.initial_state_llc_s() and flow.initial_cv_zero())) and not flow.is_monitor_hit():
                if not flow.cbo_sent_fast_go():
                    err_msg+="Rule 1: CBo did not send FAST_GO, the GO sent was: "+flow.go_type+"\n"
            elif flow.flow_is_hom() and (flow.snoop_rsp_m() or flow.initial_state_llc_m() or (flow.snoop_rsp_i() and (flow.initial_state_llc_s() or flow.initial_state_llc_i()))):
                if not flow.cbo_sent_fast_go():
                    err_msg+="Rule 1: CBo did not send FAST_GO, the GO sent was: "+flow.go_type+"\n"
            else:
                if not flow.cbo_sent_fast_go_extcmp():
                    err_msg+="Rule 1: CBo did not sent fast_go_extCmp, GO sent is: "+flow.go_type+"\n"
        
        #MemPushWr
        elif flow.is_mempushwr():
            if not flow.cbo_sent_go_wr_pull():
                err_msg+="Rule 1: CBo did not send GO_WRITEPULL, GO sent is: "+flow.go_type+"\n"
        #WiL/WiLF
        elif flow.is_wil() or flow.is_wilf():
           if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not send GO_I, the GO sent was: "+flow.go_type+"\n"

        #INTA/IntPhy/IntLog/IntPriUp
        elif flow.is_interrupt():
           if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not send GO_I, the GO sent was: "+flow.go_type+"\n"

                # INTA/IntPhy/IntLog/IntPriUp
        elif flow.is_portin() or flow.is_portout():
               if not flow.cbo_sent_go_i():
                   err_msg += "Rule 1: CBo did not send GO_I, the GO sent was: " + flow.go_type + "\n"
        elif flow.is_enqueue():
                if flow.cbo_got_upi_NCmpu():
                    if not flow.cbo_sent_go_i():
                        err_msg += "Rule 1: CBo did not send GO_I, the GO sent was: " + flow.go_type + "\n"
                elif flow.cbo_got_upi_NCretry():
                    if not flow.cbo_sent_go_nogo():
                        err_msg += "Rule 2: CBo did not send GO_NoGo, the GO sent was: " + flow.go_type + "\n"
                else:
                    err_msg += "Rule 3: CBo did not get expected GO. GO sent was: " + flow.go_type + "\n"
        #WbMtoI/WbMtoE
        elif flow.is_wbmtoe() or flow.is_wbmtoi():
            if not flow.cbo_sent_go_wr_pull():
                err_msg+="Rule 1: CBo did not send GO_WRITEPULL, GO sent is: "+flow.go_type+"\n"

        elif flow.is_wbeftoe():
            should_return_go_write_pull_drop = not flow.flow_is_hom() or flow.initial_state_llc_i() or \
                                               (not flow.initial_state_llc_i() and (flow.initial_map_dway() or
                                                                      (not flow.is_free_inv_way() and (not flow.is_available_data() or flow.is_dead_dbp()))))
            if should_return_go_write_pull_drop:
                if not flow.cbo_sent_go_wr_pull_drop():
                    err_msg+="Rule 1: CBo did not send GO_WRITEPULL_DROP, GO sent is: "+flow.go_type+"\n"
            else:
                if not flow.cbo_sent_go_wr_pull():
                    err_msg+="Rule 2: CBo did not send GO_WRITEPULL, GO sent is: "+flow.go_type+"\n"

        elif flow.is_wbeftoi():
            should_return_go_write_pull_drop = not flow.flow_is_hom() or flow.initial_state_llc_i() or \
                (not flow.initial_state_llc_i() and
                    (flow.initial_map_dway() or
                    ((not flow.is_available_data() or (flow.is_dead_dbp() and not flow.is_free_inv_way()))
                     and (flow.is_evict_clean_throttle() or flow.is_monitor_hit() or flow.initial_cv_more_than_zero()))))
            if should_return_go_write_pull_drop:
                if not flow.cbo_sent_go_wr_pull_drop():
                    err_msg += "Rule 1: CBo did not send GO_WRITEPULL_DROP, GO sent is: " + flow.go_type + "\n"
            else:
                if not flow.cbo_sent_go_wr_pull():
                    err_msg += "Rule 2: CBo did not send GO_WRITEPULL, GO sent is: " + flow.go_type + "\n"

        #WbStoI
        elif flow.is_wbstoi():
            if not flow.cbo_sent_go_i():
                err_msg+="Rule 1: CBo did not sent GO_I, GO sent is: "+flow.go_type+"\n"

        #LLCWbInv
        elif flow.is_llcwbinv():
            if flow.initial_state_llc_m() or flow.snoop_rsp_m():
                if not flow.cbo_sent_fast_go():
                    err_msg+="Rule 1: CBo did not sent fast_go, GO sent is: "+flow.go_type+"\n"
            else:
                if not flow.cbo_sent_fast_go_extcmp():
                    err_msg+="Rule 1: CBo did not sent fast_go_extCmp, GO sent is: "+flow.go_type+"\n"
        #LLCInv
        elif flow.is_llcinv():
            if not flow.cbo_sent_go_i():
                err_msg += "Rule 1: CBo did not sent GO_I, GO sent is: " + flow.go_type + "\n"

        #LLCWb
        elif flow.is_llcwb():
            if flow.initial_state_llc_m() or flow.snoop_rsp_m():
                if not flow.cbo_sent_fast_go():
                    err_msg+="Rule 1: CBo did not sent fast_go, GO sent is: "+flow.go_type+"\n"
            else:
                if not flow.cbo_sent_fast_go_extcmp():
                    err_msg+="Rule 2: CBo did not sent fast_go_extCmp, GO sent is: "+flow.go_type+"\n"

        #CLDemote
        elif flow.is_cldemote():
            if not flow.cbo_sent_go_i():
                err_msg += "Rule 1: CBo did not sent GO_I, GO sent is: " + flow.go_type + "\n"

        #CLWB
        elif flow.is_clwb():
            if flow.flow_is_hom():
                #Diffrent cases that will case
                have_ownership_no_snoop = flow.initial_state_llc_m() and (not flow.initial_cv_one()) #TODO: Need to add flow.has_cv_err()
                have_ownership_snoop_needed = (flow.initial_state_llc_m() or (flow.initial_state_llc_e() and flow.snoop_rsp_m())) and flow.initial_cv_with_selfsnoop_one()
                miss_case = flow.initial_state_llc_i() and not flow.is_monitor_hit("first")
                all_cbo_send_fast_go_cases = have_ownership_no_snoop or have_ownership_snoop_needed or miss_case

                if all_cbo_send_fast_go_cases:
                    if not flow.cbo_sent_fast_go():
                        err_msg += "Rule 1: CBo did not sent fast_go, GO sent is: " + flow.go_type + "\n"
                else:
                    if not flow.cbo_sent_fast_go_extcmp():
                        err_msg += "Rule 2: CBo did not sent fast_go_extCmp, GO sent is: " + flow.go_type + "\n"
            else:
                if not flow.cbo_sent_fast_go_extcmp():
                    err_msg += "Rule 2: CBo did not sent fast_go_extCmp, GO sent is: " + flow.go_type + "\n"
        #CRD
        elif flow.is_crd() or flow.is_monitor():
            if flow.is_crd_pref() and flow.snoop_sent() and flow.snoop_rsp_nack():
                    if not flow.cbo_sent_go_nogo():
                        err_msg += "Rule 1: CBo did not send GO_NoGo after RspNack, the GO sent was: " + flow.go_type + "\n"
            else:
                if not flow.cbo_sent_go_s_or_f():
                    err_msg+="Rule 2: CBo did not send GO_F/S, the GO sent was: "+flow.go_type+"\n"



        #DRD
        elif flow.is_drd():
            #Please remove - DRD_MLC_M_exeption = flow.initial_map_sf() and flow.initial_state_llc_m() and flow.req_core_initial_cv_bit_is_one() and not flow.selfsnoop and flow.is_drd()
            #Please remove - DRD_MLC_E_exeption = flow.initial_map_sf() and flow.initial_state_llc_m() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and not flow.selfsnoop and flow.is_drd()
            # when HBO answers with M_CmpO, and we get set_monitor during that flow, for the same address, we will have mon_hit in the "GO cpipe pass",
            # but it is "fake monitor hit" since the monitor wasn't accept yet (due to pa match, we know for sure that the core didn't get GO for the set monitor flow)
            #If we did promotion we know that we didn't have monitor hit (We are not doing promotion if we have monitor hit in DRd) therefore if we will get M_CmpO we will send GO_M/E and not S/F.
            buried_m = flow.is_idi_flow_origin() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and not flow.is_selfsnoop() \
                       and flow.initial_map_sf() and flow.initial_state_llc_m_or_e()


            if flow.cbo_sent_go_i():
               err_msg += "Rule 1: DRD flow can't end with GO_I" + "\n"

            #If our final state is LLC_M and we are in Map=SF and we don't have monitor hit on the first pass if we will send GO_S/F we can lose our M data.
            #In that case if: 1) CN=1 (shouldn't sent GO_M according to IDI HAS) and CV=1 and ReqCV=1 and not slefsnoop to request core send GO_E (buried_m - the request core will keep it's M data)
            #                 2) any other case we will send GO_M so the receive core will know it got M data
            if buried_m and flow.final_state_llc_m() and flow.final_map_sf() and not flow.is_monitor_hit("first") and not flow.wrote_data_to_mem() and flow.is_cache_near() and not flow.cbo_sent_go_e():
                # IDI HAS demend that CN=1 will not get GO_M
                err_msg += "Rule 2.1: flow with CN=1, monitor hit in GO pass but not in first pass and final status is: LLC_M, SF (Core have M data in MLC) but GO was not GO_E, the GO sent was: " + flow.go_type + "\n"
            elif flow.final_state_llc_m() and flow.final_map_sf() and not flow.wrote_data_to_mem() and not flow.cbo_sent_go_m():
                err_msg += "Rule 2.2: flow with CN=0, monitor hit in GO pass but not in first pass and final status is: LLC_M, SF (Core have M data in MLC) but GO was not GO_M, the GO sent was: " + flow.go_type + "\n"

            # if ((flow.initial_map_sf() and flow.initial_state_llc_m()) or flow.snoop_rsp_m()) and flow.req_core_initial_cv_bit_is_one():
            #     if not flow.cbo_sent_go_e() and not flow.cbo_sent_go_m() and not flow.cbo_sent_go_s_or_f():
            #         err_msg += "Rule 00: MLC have data in M state, so CBO can send any GO (except GO_I), the core will keep the original data in M state: " + flow.go_type + "\n"
            if must_get_go_m_or_e_in_monitor_hit:
                if flow.final_map_sf() and (flow.cbo_got_ufi_uxi_cmpo_m() or flow.snoop_rsp_m() or flow.initial_state_llc_m()) and not flow.is_cache_near(): #In CN=1 we cannot sent GO_M
                    if not flow.cbo_sent_go_m():
                        err_msg += "Rule 3.1: monitor hit in GO pass but not in first pass, hbo answers with m_cmpo and final map is SF but GO was not GO_M, the GO sent was: " + flow.go_type + "\n"
                else:
                    if not flow.cbo_sent_go_e():
                        err_msg += "Rule 3.2: monitor hit in GO pass but not in first pass, hbo answers with m_cmpo and final map is DATA_WAY but GO was not GO_E, the GO sent was: " + flow.go_type + "\n"


            if flow.is_llc_miss():
                err_msg+=self.drd_llc_miss_check(flow, must_get_go_m_or_e_in_monitor_hit)
            elif flow.snoop_sent():
                err_msg+=self.drd_snoop_check(flow, must_get_go_m_or_e_in_monitor_hit)
            else:
                err_msg+=self.drd_llc_hit_check(flow, must_get_go_m_or_e_in_monitor_hit)

        # DRD_Shared_opt
        elif flow.is_drd_shared_opt() or flow.is_drd_shared_opt_pref():
            err_msg += self.drd_shared_opt_check(flow)



        elif flow.is_victim():
            if flow.cbo_sent_go():
                err_msg+="Rule 1: We are not expecting to see any GO at Victim flow."

        elif flow.is_rfo():
            if flow.is_rfo_pref() and flow.snoop_rsp_nack():
                if not flow.cbo_sent_go_nogo():
                    err_msg += "Rule 2: CBo did not send GO_NoGo after RspNack, the GO sent was: " + flow.go_type + "\n"
            if (flow.cbo_got_ufi_uxi_cmpo_m() or flow.snoop_rsp_m()) and flow.final_map_sf():
                if not flow.cbo_sent_go_m():
                    return "Rule 1: cbo sent modified data to the core with SF, but CBo did not send it with GO_M, the GO sent was: " + flow.go_type + "\n"
            else:
                if not flow.cbo_sent_go_e():
                    return "Rule 2: in rfo, when read from memory and m conditions didn't met - need to send data with GO_E. the GO sent was: " + flow.go_type + "\n"

        elif flow.is_clrmonitor() or flow.is_nop():
            if not flow.cbo_sent_go_i():
                err_msg += "Rule 1: CBo did not send GO_I, the GO sent was: " + flow.go_type + "\n"

        elif flow.is_lock_or_unlock() or flow.is_spcyc():
            if not flow.cbo_sent_go_i():
                err_msg += "Rule 1: CBo did not send GO_I, the GO sent was: " + flow.go_type + "\n"
        else:
            err_msg+="Rule 103: transaction ends without GO CHK. the GO sent was: "+flow.go_type+"\n"



        if len(err_msg) > 0:
            out_err_msg="TID "+flow.uri["TID"]+" with opcode "+flow.opcode+" is violating the following rules:\n"+err_msg+"\n"+flow.get_flow_info_str()
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=out_err_msg)
        else:
            self.collect_coverage()

    def drd_llc_miss_check(self,flow, must_get_go_m_or_e_in_monitor_hit):
        if flow.flow_is_hom():
            if ((flow.is_monitor_hit("go_sent") and not must_get_go_m_or_e_in_monitor_hit) or flow.snoop_rsp_s() or flow.cbo_got_ufi_uxi_cmpo_si()):
                if not flow.cbo_sent_go_s_or_f():
                    return "Rule 11: monitor hit or ccf have data with LLC_S but CBO didn't send GO_S, the GO sent was: " + flow.go_type + "\n"
            elif flow.cbo_got_ufi_uxi_cmpo_m() and flow.final_map_sf():
                if not flow.cbo_sent_go_m():
                    return "Rule 12: cbo sent modified data to the core with SF, but CBo did not send it with GO_M, the GO sent was: " + flow.go_type + "\n"
            else:
                if not flow.cbo_sent_go_e():
                    return "Rule 13: in drd, when read from memory and m or s conditions didn't met - need to send data with GO_E. the GO sent was: " + flow.go_type + "\n"
            return ""
        elif flow.is_mmio():
            if (flow.final_map_sf() and flow.final_cv_one()):
                if not flow.cbo_sent_go_f() and not flow.cbo_sent_go_e():
                    return "Rule 14: For NC Drd that end in SF after a miss we expect GO_F or GO_E, CBO sent " + flow.go_type + "\n"
            #DWAY
            elif (flow.final_cv_more_than_one() or flow.final_state_llc_s() or flow.initial_state_llc_s()):
                if not flow.cbo_sent_go_s():
                    return "Rule 15: For NC Drd that missed and that eneded with CV > 1 or !LLC_S and Map=Dway we expect GO_S, CBO sent - " + flow.go_type + "\n"
            elif not flow.cbo_sent_go_e():
                return "Rule 16: For NC Drd that missed and that eneded with CV = 1 and LLC_E and Map=DWAY we expect GO_E, CBO sent - " + flow.go_type + "\n"
        elif not flow.cbo_sent_go_i():
            return "Rule 17: For NC Drd that get a CRABABORT we expect GO_I, CBO sent - " + flow.go_type + "\n"

        return ""

    def drd_snoop_check(self,flow, must_get_go_m_or_e_in_monitor_hit):
        err_msg = ""
        if flow.is_drd_pref() and flow.snoop_rsp_nack():
            if not flow.cbo_sent_go_nogo():
                err_msg += "Rule 4: CBo did not send GO_NoGo after RspNack, the GO sent was: " + flow.go_type + "\n"
        elif flow.core_still_has_data_in_s() or (flow.is_monitor_hit("go_sent") and not must_get_go_m_or_e_in_monitor_hit) or (flow.initial_state_llc_s() and flow.initial_map_dway()):
            if not flow.cbo_sent_go_s_or_f():
                err_msg+="Rule 5: monitor hit or ccf have data with LLC_S or core still have data in S state but CBO didn't send GO_S, the GO sent was:"+flow.go_type+"\n"
        elif flow.snoop_rsp_f() or flow.snoop_rsp_m() or ((flow.snoop_rsp_i() or flow.snoop_rsp_s()) and flow.initial_map_dway()): #LLC have data to send to the core
            #if flow.is_snoop_rsp_in_snoop_responses("RspSFwdFE") or flow.snoop_rsp_s():
            #    if not flow.cbo_sent_go_s_or_f():
            #        err_msg+="Rule 5.1: CBo did not send GO_S, the GO sent was: "+flow.go_type+"\n"
            if flow.snoop_rsp_m() and flow.final_map_dway():
                if not flow.cbo_sent_go_e():
                    err_msg+="Rule 6.1: CBO have data in map data and LLC_M, it should send GO_E, the GO sent was: "+flow.go_type+"\n"
            elif (flow.initial_state_llc_m() or flow.snoop_rsp_m()) and flow.final_map_sf() and not flow.wrote_data_to_mem():
                if ( (not flow.is_cache_near() and not flow.flow_is_hom()) or flow.flow_is_hom() ) and not flow.cbo_sent_go_m():    #when flow is not hom and CN=1 CBo may not send GO_M and drop the data
                    err_msg+="Rule 6.2: CBO send modified data and final map is SF, it should send GO_M, the GO sent was: "+flow.go_type+"\n"
            elif flow.is_snoop_rsp_in_snoop_responses("RspIFwd") and flow.snoop_rsp_f() and flow.initial_state_llc_e() and flow.initial_map_sf():
                if not flow.cbo_sent_go_e() or not flow.final_state_llc_e():
                    err_msg+="Rule 6.3: CBo did not send GO_E, but initial map was SF, and initial state was E and the snp resp is fwdFE from the requestor. the state need to stay the same, the GO sent was: "+flow.go_type+"\n"
            elif flow.initial_state_llc_s():
                if not flow.cbo_sent_go_s_or_f():
                    err_msg+="Rule 6.4: CBo did not send GO_S/F, the GO sent was: "+flow.go_type+"\n"
            elif flow.snoop_rsp_i() and flow.initial_state_llc_e() and flow.initial_map_dway():
                if not flow.cbo_sent_go_e():
                    err_msg+="Rule 6.5: CBo did not send GO_e, the GO sent was: "+flow.go_type+"\n"
            elif flow.snoop_rsp_i() and flow.initial_state_llc_m() and flow.final_map_dway():
                if not flow.cbo_sent_go_e():
                    err_msg+="Rule 6.6: CBo did not send GO_S, the GO sent was: "+flow.go_type+"\n"
            elif flow.wrote_data_to_mem() and flow.snoop_rsp_m() and flow.core_still_has_data_in_s():
                if not flow.cbo_sent_go_s():
                    err_msg+="Rule 6.7: CBo did not send GO_S, the GO sent was: "+flow.go_type+"\n"
            elif flow.wrote_data_to_mem() and flow.snoop_rsp_m() and not flow.core_still_has_data_in_s():
                if not flow.cbo_sent_go_e():
                    err_msg+="Rule 6.8: CBo did not send GO_E, the GO sent was: "+flow.go_type+"\n"

            else:
                err_msg+="Rule 6.9: not found in any check. the GO sent was: "+flow.go_type+"\n"
        else:
            err_msg+=self.drd_llc_miss_check(flow, must_get_go_m_or_e_in_monitor_hit)
        return err_msg

    def drd_shared_opt_check(self, flow):
        err_msg = ""
        llc_hit = flow.initial_map_dway() and not flow.is_selfsnoop_and_req_cv() and \
                  (flow.initial_state_llc_s() or
                   (flow.initial_state_llc_m_or_e() and not flow.initial_cv_with_selfsnoop_one()))

        if not (flow.is_drd_shared_opt_pref() and flow.snoop_rsp_nack()) and not flow.cbo_sent_go_s_or_f():
            err_msg += "Rule 1: DRD_Shared_Opt/DRD_Shared_Pref flow can end only with GO_S/F\n"

        # Cases that we are supposed to send GO_F
        #Note 1: In case we have vulnerable data we will keep the data in Data way and therefore will not send GO_F.
        #Note 2: GO_S_OPT condition is not part of Leon flows but in case we will want to enable it.
        # The meanning of it is that we know that probebly another core will want the data so we prefer to keep it in Dway
        hit_case_for_send_go_f = llc_hit and not flow.is_data_vulnerable() and not flow.is_cache_near() and not \
                (flow.initial_state_llc_m() or flow.initial_cv_with_selfsnoop_more_than_zero() or flow.is_go_s_opt())

        evict_case_send_go_f = flow.snoop_rsp_m() and not flow.is_data_way_available()

        non_modified_data = flow.snoop_sent() and flow.initial_state_llc_e_or_s() and not flow.snoop_rsp_m() and (flow.initial_map_dway() or flow.snoop_rsp_f())
        snp_non_modified_data_go_f = non_modified_data and not (flow.is_data_way_available() and (flow.is_snoop_rsp_in_snoop_responses("RspS") or flow.is_cache_near()))

        snp_rsp_s_no_fwd = flow.snoop_rsp_s() and not flow.snoop_rsp_s_fwd()
        llc_miss_go_f = (flow.does_flow_contain_uxi_req() or (flow.is_flow_promoted() and not flow.cbo_got_ufi_uxi_cmpo_m())) and not (flow.is_data_way_available() and (flow.is_cache_near() or snp_rsp_s_no_fwd))

        should_get_go_f = hit_case_for_send_go_f or evict_case_send_go_f or snp_non_modified_data_go_f or llc_miss_go_f

        if flow.is_drd_shared_opt_pref() and flow.snoop_rsp_nack():
            if not flow.cbo_sent_go_nogo():
                err_msg += "Rule 2: CBo did not send GO_NoGo after RspNack, the GO sent was: " + flow.go_type + "\n"
        elif should_get_go_f and not flow.cbo_sent_go_f():
            err_msg += "Rule 2: We should send GO_F to core\n"
        elif not should_get_go_f and not flow.cbo_sent_go_s():
            err_msg += "Rule 2: We should send GO_S to core\n"

        return err_msg


    def drd_llc_hit_check(self, flow, must_get_go_m_or_e_in_monitor_hit):
        #Case of Data in SF code and CV=1 but this bit is ReqCV and SelfSnp=0 - in this case we are expecting to go to memory and therefore use miss branch.
        if flow.initial_map_sf() and not flow.is_selfsnoop() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one():
            return self.drd_llc_miss_check(flow, must_get_go_m_or_e_in_monitor_hit)
        elif flow.is_monitor_hit("go_sent") or flow.initial_state_llc_s() or flow.initial_cv_with_selfsnoop_more_than_zero() or (flow.is_go_s_opt() and not flow.is_cache_near()):
            if not flow.cbo_sent_go_s_or_f():
                return "Rule 7: CBo did not send GO_S/F, the GO sent was: "+flow.go_type+"\n"
        elif (flow.initial_state_llc_e() or flow.initial_state_llc_m()) and flow.initial_map_dway() and flow.initial_cv_more_than_one():
            if not flow.cbo_sent_go_s_or_f():
                return "Rule 8: LLC have data in M state, map Data, and CV>1. in that case we don't send snoop," +\
                         "since we have data and cores have data in shared state. we need to send data to requestor with GO_S too." +\
                         " CBo did not send GO_S, the GO sent was: "+flow.go_type+"\n"
        else:
            if flow.initial_map_dway() and flow.final_map_sf() and flow.initial_state_llc_m():
                if not flow.cbo_sent_go_m():
                    return "Rule 9: CBo did not send GO_M, the GO sent was: "+flow.go_type+"\n"
            else:
                if not flow.cbo_sent_go_e():
                    return "Rule 10: CBo did not send GO_E, the GO sent was: "+flow.go_type+"\n"
        return ""
