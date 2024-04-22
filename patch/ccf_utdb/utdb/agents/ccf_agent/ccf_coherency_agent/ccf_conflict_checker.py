from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import conflict_coverage
from agents.ccf_common_base.ccf_common_base import ccf_cbo_record_info, ccf_llc_record_info, \
    ccf_ufi_record_info
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry


class conflict_checker(ccf_coherency_base_chk):

    def __init__(self):
        self.conflict_coverage = conflict_coverage.get_pointer()
        self.checker_name = "conflict_checker"

    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow) and flow.is_snoop_opcode() and flow.is_conflict_flow()

    def filter_only_specific_pkt_type_from_flow_progress(self, flow_progress, pkt_type_list):
        flow_progress_ret = list()
        for pkt in flow_progress:
            if type(pkt) in pkt_type_list:
                flow_progress_ret.append(pkt)
        return flow_progress_ret

    def remove_all_trans_that_not_needed_for_conflict_calc(self, flow_progress):
        ufi_valid_opcode_list = ["FwdCnfltO", "CmpO"]
        cbo_valid_opcode_list = ["FwdCnfltO", "CmpO"]
        flow_progress_ret = list()
        for tran in flow_progress:
            if (type(tran) is ccf_ufi_record_info):
                if any([True for opcode in ufi_valid_opcode_list if opcode in tran.rec_opcode]):
                    flow_progress_ret.append(tran)
            elif (type(tran) is ccf_cbo_record_info):
                if any([True for opcode in cbo_valid_opcode_list if opcode in tran.rec_opcode]):
                    flow_progress_ret.append(tran)

        return flow_progress_ret

    def get_snoop_conflict_type_on_cbo_interface(self, cbo_interface, snoop_uri, demand_uri):
        for cbo_tran in cbo_interface:
            if "CmpO" in cbo_tran.rec_opcode and cbo_tran.rec_tid == demand_uri:
                return "Late Conflict"
            if "FwdCnfltO" in cbo_tran.rec_opcode and cbo_tran.rec_tid == snoop_uri:
                return "Early Conflict"

        err_msg = "Val_Assert (get_snoop_conflict_type_on_ufi_interface): This is snoop conflict flow it's not make " \
                  "sense you didn't found any CmpO for demand or FwdCnfltO for snoop"
        VAL_UTDB_ERROR(time=cbo_interface[0].rec_time, msg=err_msg)

        return None

    def get_snoop_conflict_type_on_ufi_interface(self, ufi_interface, snoop_uri, demand_uri):
        for ufi_tran in ufi_interface:
            if "CmpO" in ufi_tran.rec_opcode and ufi_tran.rec_tid == demand_uri:
                return "Late Conflict"
            if "FwdCnfltO" in ufi_tran.rec_opcode and ufi_tran.rec_tid == snoop_uri:
                return "Early Conflict"

        err_msg = "Val_Assert (get_snoop_conflict_type_on_ufi_interface): This is snoop conflict flow it's not make " \
                  "sense you didn't found any CmpO for demand or FwdCnfltO for snoop"
        VAL_UTDB_ERROR(time=ufi_interface[0].rec_time, msg=err_msg)

        return None

    def get_snoop_conflict_type(self, flow_progress, snoop_uri, demand_uri):
        ufi_interface = self.filter_only_specific_pkt_type_from_flow_progress(flow_progress=flow_progress, pkt_type_list=[ccf_ufi_record_info])
        cbo_interface = self.filter_only_specific_pkt_type_from_flow_progress(flow_progress=flow_progress, pkt_type_list=[ccf_cbo_record_info])
        ufi_conflict_type = self.get_snoop_conflict_type_on_ufi_interface(ufi_interface, snoop_uri, demand_uri)
        cbo_conflict_type = self.get_snoop_conflict_type_on_cbo_interface(cbo_interface, snoop_uri, demand_uri)

        if ufi_conflict_type is None or cbo_conflict_type is None:
            err_msg = "Val_Assert (get_snoop_conflict_type): cfi or cbo conflict type are None check your checker/env that not make sense."
            VAL_UTDB_ERROR(time=flow_progress[0].rec_time, msg=err_msg)

        return ufi_conflict_type, cbo_conflict_type

    def get_flow_key_of_conflicted_core_flow(self, flow: ccf_flow):
        if self.ccf_flows[flow.conflict_with_uri].is_flow_promoted():
            conflict_with_uri = self.ccf_flows[flow.conflict_with_uri].promotion_flow_orig_pref_uri
            if self.si.ccf_cov_en:
                self.conflict_coverage.collect_cov_event__snoop_conflict_with_prefetch_promotion()
            return conflict_with_uri
        else:
            return flow.conflict_with_uri

    def get_flow_progress_of_core_flow(self, flow: ccf_flow):
        flow_key = self.get_flow_key_of_conflicted_core_flow(flow)
        return self.ccf_flows[flow_key].flow_progress

    def get_combine_flow_progress_of_two_conflicted_flows(self,flow: ccf_flow):
        return flow.flow_progress + self.get_flow_progress_of_core_flow(flow)


    def check_rsp_channel_order_by_analayze_conflict_type(self, flow: ccf_flow):
        conflict_flow_progress = self.get_combine_flow_progress_of_two_conflicted_flows(flow)
        conflict_flow_progress = self.remove_all_trans_that_not_needed_for_conflict_calc(conflict_flow_progress)
        conflict_flow_progress.sort(key=lambda x: x.rec_time, reverse=False)

        cfi_conflict_type, cbo_conflict_type = self.get_snoop_conflict_type(flow_progress=conflict_flow_progress,
                                                                            snoop_uri=flow.uri['TID'],
                                                                            demand_uri=self.ccf_flows[flow.conflict_with_uri].uri['TID'])

        if cfi_conflict_type != cbo_conflict_type:
            err_msg = "(conflict checker): We can see two diffrent conflict type between CFI and CBO interface.\n" \
                      "CFI: {}, CBO: {}\nthat can happen due to violation of ordering rules on RSP channel.\n" \
                      "Demand URI: {}, Snoop URI:{}" \
                .format(cfi_conflict_type, cbo_conflict_type, self.ccf_flows[flow.conflict_with_uri].uri['TID'],
                        flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    #In case of snoop conflict we want to make sure that between the time we did lookup for the core transaction
    #and the time we finished the flow we had only one write to the LLC. If we would have more then one change of the state
    #that can make our snoop act and give response to HA with wrong indication.
    #(as was with ADL bug that wrote the state to I and then when RFO completed wrote it to the correct state)
    #If this condition is correct that promise us that the snoop transaction used correct lookup data.
    def check_that_core_trans_didnt_had_more_then_one_write_to_llc(self, flow: ccf_flow):
        num_of_writes_uops = 0
        core_flow_progress = self.get_flow_progress_of_core_flow(flow)
        for trans in core_flow_progress:
            #We will not consider rejected lcc operation as access to the llc if the follow assumption are correct:
            # 1)This rejected operation is not doing any change in the llc.
            # 2)The next time we will have the exact same operation happening.
            if (type(trans) is ccf_llc_record_info) and "w" in trans.rec_opcode.lower().strip() and (trans.rejected == 0):
                num_of_writes_uops = num_of_writes_uops + 1
        if num_of_writes_uops > 1:
            err_msg = "(check_that_core_trans_didnt_had_more_then_one_write_to_llc): Core flow (flow_key-{}) wrote to LLC more then once, " \
                      "that was not expected and can cause issues when combine with snoop conflict flow".format(self.get_flow_key_of_conflicted_core_flow(flow))
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def check_no_conflict_with_write_transaction(self, flow: ccf_flow):
        key = self.get_flow_key_of_conflicted_core_flow(flow)
        conflict_timing_is_ok = False
        #if CCF_FLOW_UTILS.is_write_opcode(self.ccf_flows[key].opcode):
        if self.ccf_flows[key].cbo_got_ufi_uxi_cmpo(): #we expect conflicts only in read window
            conflict_time = flow.first_accept_time
            if self.ccf_flows[key].is_llcpref() and self.ccf_flows[key].pref_used_for_promotion:
                promoted_uri = self.ccf_flows[key].promoted_uri
                read_completion_time = self.ccf_flows[promoted_uri].get_pipe_pass_item(self.ccf_flows[promoted_uri].ufi_uxi_cmpo).arbcommand_time
            else:
                read_completion_time = self.ccf_flows[key].get_pipe_pass_item(self.ccf_flows[key].ufi_uxi_cmpo).arbcommand_time
            if conflict_time < read_completion_time:
                conflict_timing_is_ok = True
        if not conflict_timing_is_ok:
            err_msg = "(check_no_conflict_with_write_transaction): Core flow (flow_key-{}) is a write flow {}, " \
                      "that was not expected to have conflicts".format(key, self.ccf_flows[key].opcode)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def check_flow(self, flow: ccf_flow):
        self.check_rsp_channel_order_by_analayze_conflict_type(flow)
        self.check_that_core_trans_didnt_had_more_then_one_write_to_llc(flow)
        self.check_no_conflict_with_write_transaction(flow)
        self.collect_coverage()


#Not relevant to CBB
# class santa_id_is_eq_to_hbo_id_when_send_reqfwdcnflt_chk(ccf_coherency_base_chk):
#     def __init__(self):
#         self.ccf_coherency_qry = ccf_coherency_qry.get_pointer()
#
#     def is_checker_enable(self):
#         return True
#
#     def do_check(self):
#         self.ReqFwdCnflt_pass = self.ccf_coherency_qry.filter_all_ReqFwdCnflt()
#         for conflict_line in self.ReqFwdCnflt_pass:
#             for record in conflict_line.EVENTS:
#                 #For debug: print(record)
#                 for santa_id in range(CCF_COH_DEFINES.num_of_santa):
#                     err_msg = ""
#                     if (record.UNIT == CCF_UTILS.get_santa_name(santa_num=santa_id)):
#                         #We need to have SANTA_ID == HBO_ID so if transaction got out from SANTA0 it had to be sent to HBO0 and the response should go back to SANTA0.
#                         if record.RSPID != CCF_UTILS.get_santa_rsp_id_name(santa_id=santa_id):
#                             err_msg = "(santa_id_is_eq_to_hbo_id_when_send_reqfwdcnflt_chk):\nReqFwdCnflt msg is going out from SANTA {} and should have RSPID={} " \
#                                       "but the actual RSPID is={}".format(santa_id, CCF_UTILS.get_santa_rsp_id_name(santa_id=santa_id), record.RSPID)
#                         if (record.DSTID != CCF_UTILS.get_hbo_dest_id_name(hbo_id=santa_id)):
#                             err_msg += "\nReqFwdCnflt msg is going out from SANTA {} and should have DSTID={} " \
#                                       "but the actual RSPID is={}".format(santa_id, CCF_UTILS.get_hbo_dest_id_name(hbo_id=santa_id), record.DSTID)
#                         if err_msg != "":
#                             VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)


class only_single_conflict_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.ccf_coherency_qry = ccf_coherency_qry.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()

    def is_checker_enable(self):
        return True #We will check if we want to use this checking per CBO inside the checker loop

    def do_check(self):
        for cbo_log_id in range(self.si.num_of_cbo):
            cbo_phy_id = CCF_UTILS.get_physical_id_by_logical_id(cbo_log_id)
            if self.ccf_registers.allow_only_single_snoop_conflict[cbo_phy_id] == 1:
                have_active_conflict = False
                allocated_conflict_uri = None
                print("cbo_phy_id: {}".format(str(cbo_phy_id)))
                self.conflict_indication = self.ccf_coherency_qry.conflict_indication(cbo_id=str(cbo_phy_id))
                for conflict_line in self.conflict_indication:
                    for record in conflict_line.EVENTS:
                        #FOR debug: print(record)
                        if "ReqFwdCnflt" in record.MSG:
                            if(have_active_conflict):
                                err_msg = "(only_single_conflict_chk): We accepted to the pipe new snoop conflict while " \
                                          "we already have one active. active conflict-{}, new allocated conflict-{}"\
                                          .format(allocated_conflict_uri, record.TID)
                                VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)
                            else:
                                have_active_conflict = True
                                allocated_conflict_uri = record.TID

                        elif "FwdCnfltO" in record.OPCODE:
                            have_active_conflict = False
