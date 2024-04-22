from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_common_base import ccf_ufi_record_info
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from agents.ccf_common_base.ccf_monitor_agent import monitor_array_snapshot
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import ccf_flow_cov
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR

class ccf_general_flow_chk(ccf_coherency_base_chk):
    def __init__(self):
        super().__init__()
        self.checker_name = "ccf_general_flow_chk"
        self.ccf_cpipe_window_utils = ccf_cpipe_window_utils.get_pointer()
        self.ccf_addressless_db = ccf_addressless_db.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.ccf_sm_db = SM_DB.get_pointer()
        self.ccf_flow_cov_ptr = ccf_flow_cov.get_pointer()
        self.coverage_en = self.si.ccf_cov_en



    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow) and self.si.ccf_flow_chk_en == 1 \
               and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_flusher() and not flow.is_u2c_dpt_req()

    def should_flow_had_pa_match_reject(self, flow: ccf_flow):
        allocated_uri = None
        # check that this transaction shouldn't be rejected
        if flow.opcode not in self.ccf_cpipe_window_utils.always_allocate:
            if flow.is_llc_special_opcode():
                if flow.uri['TID'] in self.ccf_addressless_db.addressless_db.keyls() and self.ccf_addressless_db.get_addressless_state_by_uri(flow.uri['TID']) != "LLC_I":
                    flow_address = self.ccf_addressless_db.get_real_address_by_uri(flow.uri['TID'])
                    allocated_uri = self.ccf_cpipe_window_utils.check_that_no_pa_match_reject_expected_for_uri(flow_address,flow.uri, flow.initial_time_stamp)
            else:
                allocated_uri = self.ccf_cpipe_window_utils.check_that_no_pa_match_reject_expected_for_uri(flow.address, flow.uri, flow.initial_time_stamp)

            if allocated_uri is not None:
                err_msg = "The flow was accepted in CPIPE while we already have transaction with the same address active in the pipe. " \
                          "our transaction URI is: {} and the active transaction is - TID: {}. check it.".format(flow.uri['TID'], allocated_uri)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
    '''
    In this function we will check each time that we have RejectDuePaMatch if we should do promotion for this flow.
    if we will have RejectDueIRQSetMatchBlocked too we are not expecting to allow prefetch promotion(design implementation not HAS one).
    '''
    def flow_wasnt_promoted_check_that_decision_was_correct(self, flow: ccf_flow):
            if flow.uri['TID'] in self.ccf_cpipe_window_utils.ccf_reject_accurate_times.keys():
                flow_reject_time_list = self.ccf_cpipe_window_utils.ccf_reject_accurate_times[flow.uri['TID']]
                if "RejectDuePaMatch" in flow_reject_time_list.keys():
                    for pa_match_reject_info in flow_reject_time_list["RejectDuePaMatch"]:

                        if "RejectDueIRQSetMatchBlocked" not in flow_reject_time_list.keys() or \
                                (not any([True for reject_set_match_time in flow_reject_time_list["RejectDueIRQSetMatchBlocked"] if reject_set_match_time['TIME'] == pa_match_reject_info['TIME']])):
                            can_promote, prefetch_uri = self.ccf_cpipe_window_utils.can_promote(flow.address, pa_match_reject_info['TIME'], pa_match_reject_info['MonHit'], flow)
                            if can_promote:
                                rfo_prefetch_promotion = flow.is_rfo() and self.ccf_flows[prefetch_uri].is_llcprefrfo()
                                if (not flow.is_rfo()) or rfo_prefetch_promotion:
                                    err_msg = "According to the HAS this transaction should have been promoted - URI: {} by using the follow prefetch: URI: {}. " \
                                              "please check why promotion wasn't done".format(flow.uri['TID'], prefetch_uri)
                                    VAL_UTDB_ERROR(time=pa_match_reject_info['TIME'], msg=err_msg)

    '''
    This function should check that the decision to promoted the flow was a correct decision. 
    '''
    def check_promotion_decision_was_correct(self, flow: ccf_flow):
        if flow.uri['TID'] in self.ccf_cpipe_window_utils.ccf_reject_accurate_times.keys():
            flow_reject_time_list = self.ccf_cpipe_window_utils.ccf_reject_accurate_times[flow.uri['TID']]
            if ("RejectDuePaMatch" in flow_reject_time_list.keys()) and (self.ccf_cpipe_window_utils.is_flow_had_reject_on_time(flow.uri['TID'],"RejectDuePaMatch", flow.flow_promoted_time)) and \
                    ("RejectDueIRQSetMatchBlocked" not in flow_reject_time_list.keys() or (not self.ccf_cpipe_window_utils.is_flow_had_reject_on_time(flow.uri['TID'], "RejectDueIRQSetMatchBlocked", flow.flow_promoted_time))):
                can_promote, prefetch_uri = self.ccf_cpipe_window_utils.can_promote(flow.address, flow.flow_promoted_time, flow.is_monitor_hit(), flow)
                if not can_promote:
                    err_msg = "We didn't need to do promotion for transaction TID- {}".format(flow.uri['TID'])
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            else:
                err_msg = "We didn't had any RejectDuePaMatch or we didn't have the reject the fit to promotion time" \
                          " so we didn't expect to see any promotion for TID- {}".format(flow.uri['TID'])
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        else:
            err_msg = "We didn't had any Reject that fit to promotion time so we didn't expect to see any promotion for TID- {}".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    '''
    This function will check that if we are seeing RFO that was promoted the prefetch that cause it 
    had to be LLCPrefRFO.
    '''
    def check_rfo_did_prefetch_promotion_only_with_llcprefrfo(self, flow: ccf_flow):
        if flow.promotion_flow_orig_pref_uri is not None:
            if flow.is_rfo() and not self.ccf_flows[flow.promotion_flow_orig_pref_uri].is_llcprefrfo():
                err_msg = "LLCPREFRFO can be promoted only if we are getting RFO opcode but in our flow we got: {}".format(flow.opcode)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        else:
            err_msg = "Val_Assert (check_rfo_did_prefetch_promotion_only_with_llcprefrfo): something went wrong with this promotion flow since we don't have the prefetch URI."
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def check_demand_and_prefetch_torid_are_the_same(self, flow: ccf_flow):
        if flow.promotion_flow_orig_pref_uri is not None:
            if flow.cbo_tor_qid != self.ccf_flows[flow.promotion_flow_orig_pref_uri].cbo_tor_qid:
                err_msg = "The seems that the demand request is not using the same TorID like the prefetch that was promoted " \
                          "this was not expected. demand TorID: {}, prefetch TorID: {}"\
                          .format(flow.cbo_tor_qid, self.ccf_flows[flow.promotion_flow_orig_pref_uri].cbo_tor_qid)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        else:
            err_msg = "Val_Assert (check_demand_and_prefetch_torid_are_the_same): something went wrong with this promotion flow since we don't have the prefetch URI."
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def prefetch_promotion_checks(self, flow):
        #check that the flow was not promoted with a good reason
        if flow.is_promotable_opcode() and not flow.is_flow_promoted():
            self.flow_wasnt_promoted_check_that_decision_was_correct(flow)

        if flow.is_flow_promoted():
            self.check_promotion_decision_was_correct(flow)
            self.check_rfo_did_prefetch_promotion_only_with_llcprefrfo(flow)
            self.check_demand_and_prefetch_torid_are_the_same(flow)



    ####################
    ## Monitor checks
    ####################
    def get_tag_way_for_monitor_check(self, flow):
        if flow.is_victim():
            tag_way = flow.initial_tag_way
        else:
            bint_tag_way = bint(int(flow.address, 16))
            tag_way = bint_tag_way[CCF_COH_DEFINES.llc_addressless_llcway_addr_range_msb:CCF_COH_DEFINES.llc_addressless_llcway_addr_range_lsb]
        return tag_way

    def get_monitor_array(self, flow_monitor_array):
        monitor_snapshot = monitor_array_snapshot()
        if flow_monitor_array is not None:
            return flow_monitor_array
        else:
            return monitor_snapshot

    def check_actual_vs_expected_monhit_at_first_pass(self, flow):
        monitor_snapshot = self.get_monitor_array(flow_monitor_array=flow.current_monitor_array)

        # Checking actual MonHit vs expected MonHit in the first pipe pass
        ##################################################################
        # If we are using LLC special Opcode the flow should be the same in COH and NC without "FakeCycle".
        # Since WBMTOI is same flow for COH/NC (send GO_I) it easier to implement without "FakeCycle".
        if flow.flow_is_hom() or flow.is_llc_special_opcode() or flow.is_wbstoi():
            if flow.is_victim() or flow.is_llcwbinv() or flow.is_llcinv() or flow.is_llcwb():
                monitor_snapshot.is_monitor_hit_correct(flow.first_accept_time, flow.get_monitor_hit_value(),
                                                        flow.address, self.get_tag_way_for_monitor_check(flow),
                                                        flow.cbo_half_id, check_for_partial_mon_hit=True)
            else:
                monitor_snapshot.is_monitor_hit_correct(flow.first_accept_time, flow.get_monitor_hit_value(), flow.address)
        else:
            monitor_snapshot.is_monitor_hit_correct(flow.first_accept_time, flow.get_monitor_hit_value("FakeCycle"), flow.address)

    def check_actual_vs_expected_monhit_at_go_pass(self, flow):
        if flow.is_idi_flow_origin():
            monitor_snapshot = self.get_monitor_array(flow_monitor_array=flow.go_monitor_array)
            if (flow.is_victim() or flow.is_llcwbinv() or flow.is_llcinv() or flow.is_llcwb()) and (
                    flow.go_accept_time == flow.first_accept_time):
                monitor_snapshot.is_monitor_hit_correct(flow.go_accept_time, flow.get_monitor_hit_value("go_sent"),
                                                        flow.address, self.get_tag_way_for_monitor_check(flow),
                                                        flow.cbo_half_id, check_for_partial_mon_hit=True)
            else:
                monitor_snapshot.is_monitor_hit_correct(flow.go_accept_time, flow.get_monitor_hit_value("go_sent"),
                                                        flow.address)

    def check_when_monitor_hit_uxi_rsp_is_not_invalidtion(self, flow: ccf_flow):
        if not CCF_FLOW_UTILS.should_trigger_monitor(opcode=flow.opcode, sad=flow.sad_results):
            wb_pkt_sa_d = flow.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH", pkt_type="SA-D")
            wb_pkt_pw = flow.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA",uxi_type="COH", pkt_type="PW")
            wb_list = wb_pkt_sa_d + wb_pkt_pw

            if (flow.is_monitor_hit() or flow.is_monitor_hit("SNP_RSP")):
                for wb in wb_list:
                    if wb.rec_opcode not in ["WbMtoS", "WbMtoE"]:
                        err_msg = "(check_when_monitor_hit_uxi_rsp_is_not_invalidtion): Since we have Monitor Hit we are expecting from CBO to send WbMtoS to HA since we don't have monitor opcode on UXI but the actual opcode is: {}".format(wb.rec_opcode)
                        VAL_UTDB_ERROR(time=wb.rec_time, msg=err_msg)

            #Clean evict shouldn't be sent.
            can_be_clean_evict = flow.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="REQ", uxi_type="COH", pkt_type="SA")
            if (flow.is_monitor_hit() or flow.is_monitor_hit("SNP_RSP")):
                for tran in can_be_clean_evict:
                    if tran.rec_opcode == "EvctCln":
                        err_msg = "(check_when_monitor_hit_uxi_rsp_is_not_invalidtion): Since we have Monitor Hit we are expecting from CBO to not send EvctCln to HA since we don't have monitor opcode on UXI but the actual opcode is: {}".format(tran.rec_opcode)
                        VAL_UTDB_ERROR(time=tran.rec_time, msg=err_msg)

            #Check snoop response:
            if not flow.snoop_sent():
                monitor_hit = flow.is_monitor_hit()
            else:
                monitor_hit = flow.is_monitor_hit("SNP_RSP")


            snoop_rsp_with_data_list = flow.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="DATA", uxi_type="COH", pkt_type="SR-HD")
            for snoop_rsp in snoop_rsp_with_data_list:
                if monitor_hit and snoop_rsp.rec_opcode not in ["RspFwdSWb", "RspSWb", "RspCurData"]:
                    err_msg = "(check_when_monitor_hit_uxi_rsp_is_not_invalidtion): Since we have Monitor Hit we are expecting from CBO to send RspS to HA since we don't have monitor opcode on UXI but the actual opcode is: {}".format(snoop_rsp.rec_opcode)
                    VAL_UTDB_ERROR(time=snoop_rsp.rec_time, msg=err_msg)

            snoop_rsp_without_data_list = flow.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="RSP", uxi_type="COH", pkt_type="SR-H")
            for snoop_rsp in snoop_rsp_without_data_list:
                if monitor_hit and snoop_rsp.rec_opcode not in ["RspS", "RspFwdS", "RspE"]:
                    err_msg = "(check_when_monitor_hit_uxi_rsp_is_not_invalidtion): Since we have Monitor Hit we are expecting from CBO to send RspS/RspE to HA since we don't have monitor opcode on UXI but the actual opcode is: {}".format(snoop_rsp.rec_opcode)
                    VAL_UTDB_ERROR(time=snoop_rsp.rec_time, msg=err_msg)

    def collect_monitor_array_cov(self, flow):
        monitor_snapshot = self.get_monitor_array(flow_monitor_array=flow.current_monitor_array)
        if self.coverage_en:
            self.ccf_flow_cov_ptr.collect_num_of_used_entries_in_monitor_array_coverage(monitor_snapshot.get_num_of_entries())

    def monitor_hit_chk(self, flow: ccf_flow):
        if not (flow.is_monitor() or flow.is_clrmonitor() or flow.is_nop() or flow.is_enqueue() or flow.is_spcyc()):
            self.check_actual_vs_expected_monhit_at_first_pass(flow)
            self.check_actual_vs_expected_monhit_at_go_pass(flow)
            self.check_when_monitor_hit_uxi_rsp_is_not_invalidtion(flow)
            self.collect_monitor_array_cov(flow)

    def check_flow(self, flow: ccf_flow):
        #TODO: fixme this should be part of the new window checker - self.should_flow_had_pa_match_reject(flow)
        self.prefetch_promotion_checks(flow)
        self.monitor_hit_chk(flow)
        self.collect_coverage()













