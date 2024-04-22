    #!/usr/bin/env python3.6.3

#################################################################################################
# ccf_snoop_chk.py
#
# Owner:              kmoses1
# Creation Date:      05.2021
#
# ###############################################
#
# Description:
#   This file containts the content of the snoop checker
#   The checker chekcs the correctness of snoops sent to core
#   It bases it's decisions on the ccf_flows data base
#################################################################################################
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_common_base import snoop_response
from agents.ccf_common_base.ccf_common_base import snoop_request
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from val_utdb_report import VAL_UTDB_ERROR
from agents.ccf_common_base.ccf_registers import ccf_registers

class ccf_snoop_chk(ccf_coherency_base_chk):

    def __init__(self):
        super().__init__()
        self.checker_name = "ccf_snoop_chk"
        self.ccf_registers = ccf_registers.get_pointer()

    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow) and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_u2c_dpt_req()

    def check_and_report_all_snoop_req_opcodes(self, flow: ccf_flow, opcodes):
        msg = ""
        for snoop in flow.snoop_requests:
            if not any([True for string in opcodes if (string.lower() == snoop.snoop_req_opcode.lower() or \
                    ((snoop.get_req_core() == flow.requestor_physical_id) and ("self"+string.lower() == snoop.snoop_req_opcode.lower())) or \
                    ((snoop.get_req_core() == flow.requestor_physical_id) and (string.lower() == "cdfsnpinv" and snoop.snoop_req_opcode.lower() == "cdfselfsnpinv")))]):
                act_snoops = ""
                exp_snoops = ""
                for snp in opcodes:
                    exp_snoops = exp_snoops + ", " + str(snp)
                for snp in flow.snoop_requests:
                    act_snoops = act_snoops + ", " + str(snp.snoop_req_opcode)
                msg += "sent snoops is/are" + act_snoops + " but allowed snoops is" + exp_snoops + "\n"
        if len(msg) > 0:
            msg = "Rule 1: " + msg
        return msg


    def check_and_report_snoop_req(self, flow: ccf_flow):
        msg = ""
        local_snp_req = flow.snoop_requests.copy()
        while (local_snp_req):
            req = local_snp_req.pop()
            if not any([True for opcode, reqs in CCF_FLOW_UTILS.u2c_allowed_req.items() for string in reqs if flow.opcode.lower() == opcode.lower() and req.snoop_req_opcode.lower() == string.lower()]):
                msg += "snoop req " + str(req.snoop_req_opcode) + " is not expected for " + str(flow.opcode) + "\n"

        if len(msg) > 0:
            msg = "Rule 2: " + msg
        return msg

    def check_and_report_snoop_rsp(self, flow: ccf_flow):
        msg = ""
        local_snp_req = flow.snoop_requests.copy()
        local_snp_rsp = flow.snoop_responses.copy()

        local_snp_req.sort(
            key=snoop_request.get_req_core)  # sort list according to core id in case response wont come in the same order of requests
        local_snp_rsp.sort(
            key=snoop_response.get_rsp_core)  # sort list according to core id in case response wont come in the same order of requests

        while (local_snp_req):
            req = local_snp_req.pop()
            rsp = local_snp_rsp.pop()

            if not any([True for snoop, resp in CCF_FLOW_UTILS.u2c_snp_and_rsp.items() for string in resp if
                        (req.snoop_req_opcode.lower() == snoop.lower() and rsp.snoop_rsp_opcode.lower() == string.lower())]):
                msg += "snoop rsp " + str(rsp.snoop_rsp_opcode) + " is not expected for " + str(
                    req.snoop_req_opcode) + "\n"
        if len(msg) > 0:
            msg = "Rule 3: " + msg
        return msg

    def check_and_report_snoop_cv_bit(self, flow: ccf_flow):
        msg = ""
        local_snp_req = flow.snoop_requests.copy()
        local_snp_rsp = flow.snoop_responses.copy()

        local_snp_req.sort(
            key=snoop_request.get_req_core)  # sort list according to core id in case response wont come in the same order of requests
        local_snp_rsp.sort(
            key=snoop_response.get_rsp_core)  # sort list according to core id in case response wont come in the same order of requests

        while (local_snp_req):
            req = local_snp_req.pop()
            rsp = local_snp_rsp.pop()
            req_core = int(req.snoop_req_core)
            #req_core_st_physical = req_core.split("_")[-1]
            xbar_id = req_core // CCF_COH_DEFINES.num_of_ccf_clusters
            req_core_int_logical = CCF_UTILS.get_logical_id_by_physical_id(xbar_id) * CCF_COH_DEFINES.num_of_ccf_clusters + req_core%CCF_COH_DEFINES.num_of_ccf_clusters
            #req_core_int_logical = CCF_UTILS.get_logical_id_by_physical_id(int(req_core_st_physical))
            #If initial CV bit was 0 for this core and we are using always_snoop_all_ia CB we may get RspSI from core that don't have the data.
            #in that case we will consider it as RspI since we can assume the core doesn't have the data.
            consider_RspSI_as_RspI = (flow.get_initial_cv_bit_by_index(req_core_int_logical) == '0') and \
                                     (self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("ingress_"+ str(flow.cbo_id_phys), "flow_cntrl", "always_snoop_all_ia", flow.first_accept_time) == 1)
            if ("RspI" not in rsp.snoop_rsp_opcode) and ("RspFlushed" not in rsp.snoop_rsp_opcode) and ("RspSI" not in rsp.snoop_rsp_opcode and not consider_RspSI_as_RspI):
                if (not (flow.is_cv_err_injection() or flow.has_cv_err())) and flow.get_final_cv_bit_by_index(req_core_int_logical) == '0':
                    msg = "Rule 4: core still has data but final CV bit of core " + req_core + " is 0\n"
        return msg

    def check_snpRsp_vs_llc_map_cv_state(self, flow: ccf_flow):
        msg = ""
        local_snp_rsp = flow.snoop_responses.copy()
        num_of_fwd_data = 0
        num_of_fwdM_data = 0
        num_of_not_rspI = 0
        num_of_not_rspSI = 0
        num_of_rsp_s = 0
        num_of_fwdMFE_data = 0
        num_of_rspV = 0
        snoop_to_monitor_core_in_buriedM_case = flow.is_idi_flow_origin() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and not flow.is_selfsnoop() \
                   and flow.initial_map_sf() and flow.initial_state_llc_m_or_e() and \
                   not (flow.is_partial_c2u_data_write_flow() or flow.is_partial_or_uncachable_rd()) \
                   and flow.is_monitor_hit("first")

        #When CLDEMOTE gets a cv parity error a GO-I is send to the requested core to close the flow without doing anything
        CLDemote_exception = flow.has_cv_err() and flow.is_cldemote()

        for rsp in local_snp_rsp:
            if "Fwd" in rsp.snoop_rsp_opcode:
                num_of_fwd_data = num_of_fwd_data + 1
            if "FwdM" in rsp.snoop_rsp_opcode or (rsp.original_snoop_rsp_opcode is not None and "FwdM" in rsp.original_snoop_rsp_opcode):
                num_of_fwdM_data = num_of_fwdM_data + 1
            if "FwdFE" in rsp.snoop_rsp_opcode:
                num_of_fwdMFE_data = num_of_fwdMFE_data + 1
            if rsp.snoop_rsp_opcode not in ["RspIHitI", "RspIHitFSE", "RspSI", "RspFlushed"]:
                num_of_not_rspI = num_of_not_rspI + 1
            if rsp.snoop_rsp_opcode not in ["RspSHitFSE", "RspIHitI", "RspIHitFSE", "RspSI", "RspFlushed"]:
                num_of_not_rspSI = num_of_not_rspSI + 1
            if rsp.snoop_rsp_opcode in ["RspSHitFSE", "RspSFwdMO", "RspSI", "RspSFwdFE"]:
                num_of_rsp_s = num_of_rsp_s + 1
            if rsp.snoop_rsp_opcode == "RspVFwdV":
                num_of_rspV = num_of_rspV + 1



        if num_of_fwd_data > 1:
            msg += "Rule 5: ccf gets data from more than 1 core\n"
        if flow.initial_state_llc_m() or (num_of_fwdM_data > 0):
            if (num_of_not_rspSI > 1):
                msg += "Rule 6: ccf didn't get only one rsp that is not rspI when initial llc state was M or MLC state was M\n"
        if flow.initial_state_llc_i():
            if num_of_not_rspI > 0:
                msg += "Rule 7: ccf didn't get only rspI when initial llc state was I\n"
        if flow.initial_state_llc_s():
            if num_of_fwdM_data > 0:
                msg += "Rule 8: ccf can't get fwdM data when initial state is S\n"
        if flow.initial_cv_more_than_one() and not flow.has_cv_err():
            if num_of_fwdM_data > 0:
                msg += "Rule 9: ccf can't get fwdM data when CV is more then 1\n"
        if flow.initial_map_sf() and flow.initial_state_llc_m() and not (snoop_to_monitor_core_in_buriedM_case or CLDemote_exception):
            if num_of_fwdM_data == 0 and num_of_rspV == 0:
                msg += "Rule 10: If LLC_M and SF then Rsp must have FwdM\n"
        if flow.initial_map_dway():
            if num_of_fwdMFE_data > 0:
                msg += "Rule 11: If initial map = DWAY then no RspXFwdFE is expected\n"
        return msg



    def check_flow(self,flow: ccf_flow):
        err_msg = ""
        if len(flow.snoop_requests) != len(flow.snoop_responses):
            err_msg = "Rule 5: snp requests size is " + len(flow.snoop_requests) + "while snoop responses size is " + len(flow.snoop_responses) + "\n"

        if flow.snoop_requests:
            err_msg+= self.check_and_report_snoop_req(flow)
            err_msg+= self.check_and_report_snoop_rsp(flow)
            err_msg+= self.check_and_report_snoop_cv_bit(flow)
            err_msg+= self.check_snpRsp_vs_llc_map_cv_state(flow)

            if flow.is_rdcurr() or flow.is_fsrdcurr():
                if flow.flow_is_hom():
                    if flow.initial_map_sf():
                        err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["CDFSnpCurr"])
                    else: err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpCurr"])
                else: err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])

            elif flow.is_partial_or_uncachable_rd() or flow.is_clflush() or flow.is_clflush_opt():
                if flow.flow_is_hom():
                    err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
                else: err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])

            elif flow.is_wil() or flow.is_wilf():
                err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
            elif flow.is_mempushwr():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
            elif flow.is_wcil():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
            elif flow.is_wcilf_or_itomwr_wt():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])

            elif flow.is_specitom():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
            elif flow.is_itomwr() or flow.is_itom():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
            elif flow.is_drd():
                if flow.flow_is_hom():
                    snp_opcode = self.drd_snoop_opcode(flow)
                else:
                    snp_opcode = self.nc_drd_snoop_opcode(flow)
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, [snp_opcode])
            elif flow.is_drd_shared_opt() or flow.is_drd_shared_opt_pref():
                if flow.flow_is_hom():
                    snp_opcode = self.drd_shared_opt_snoop_opcode(flow)
                else:
                    snp_opcode = self.nc_drd_shared_opt_snoop_opcode(flow)
                err_msg += self.check_and_report_all_snoop_req_opcodes(flow, [snp_opcode])

            elif flow.is_crd() or flow.is_monitor():
                if flow.flow_is_hom():
                    snp_opcode = self.crd_snoop_opcode(flow)
                else:
                    snp_opcode = self.nc_crd_snoop_opcode(flow)
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, [snp_opcode])
            elif flow.is_snpinv():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])

            elif flow.is_snpLDrop():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])

            elif flow.is_snpinvmig():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])

            elif flow.is_snpinvown():
                if flow.initial_map_dway() or flow.is_monitor_hit():
                    err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["SnpInv"])
                else:
                    err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["CDFSnpInv"])

            elif flow.is_snpflush():
                err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])

            elif flow.is_snpdata():
                if flow.initial_map_sf():
                    err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["CDFSnpData"])
                else:
                    err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["SnpData"])

            elif flow.is_snpldata():
                err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["SnpData"])

            elif flow.is_snpdatamig():
                if flow.initial_map_sf():
                    err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["CDFSnpData"])
                else:
                    err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["SnpData"])

            elif flow.is_snplcode():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpCode"])

            elif flow.is_snpcode():
                if flow.initial_map_sf():
                    err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["CDFSnpCode"])
                else:
                    err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpCode"])

            elif flow.is_snpcurr():
                snp_opcode = self.snpcurr_opcode(flow)
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, [snp_opcode])
            elif flow.is_snplcurr():
                snp_opcode = self.snpcurr_opcode(flow)
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, [snp_opcode])
            elif flow.is_rfo():
                snp_opcode = self.rfo_snoop_opcode(flow)
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, [snp_opcode])
            elif flow.is_llcwbinv():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])
            elif flow.is_llcwb():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpData"])
            elif flow.is_cldemote():
                if flow.initial_map_sf():
                    err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["CDFBackInv"])
                elif flow.initial_map_dway():
                    err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])
            elif flow.is_clwb():
                err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["SnpData"])
            elif flow.is_llcinv():
                err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])
            elif flow.is_victim():
                err_msg += self.check_and_report_all_snoop_req_opcodes(flow, ["BackInv"])
            elif flow.is_lock_or_unlock():
                 err_msg+= self.check_and_report_all_snoop_req_opcodes(flow, ["STOPREQ", "STARTREQ"])
            else:
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg="We didn't found any snoop check for opcode: {}".format(flow.opcode))
        if len(err_msg) > 0:
            out_err_msg="TID "+flow.uri["TID"]+" with opcode "+flow.opcode+" is violating the following rules:\n"+err_msg+"\n"+flow.get_flow_info_str()
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=out_err_msg)
        elif self.si.ccf_cov_en:
            self.collect_coverage()

    def drd_snoop_opcode(self, flow):
        if not flow.need_to_selfsnoop_req_core() and flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "SnpData")
        elif flow.need_to_selfsnoop_req_core() and flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "BackInv")
        elif not flow.need_to_selfsnoop_req_core() and flow.initial_map_sf():
            return self.covert_to_spec_snoop_if_needed(flow, "CDFSnpData")
        elif flow.need_to_selfsnoop_req_core() and flow.initial_map_sf():
            return self.covert_to_spec_snoop_if_needed(flow, "CDFBackInv")

    def drd_shared_opt_snoop_opcode(self, flow):
        if not flow.need_to_selfsnoop_req_core() and flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "SnpCode")
        elif flow.need_to_selfsnoop_req_core() and flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "BackInv")
        elif not flow.need_to_selfsnoop_req_core() and flow.initial_map_sf():
            return self.covert_to_spec_snoop_if_needed(flow, "CDFSnpCode")
        elif flow.need_to_selfsnoop_req_core() and flow.initial_map_sf():
            return self.covert_to_spec_snoop_if_needed(flow, "CDFBackInv")

    def nc_drd_shared_opt_snoop_opcode(self, flow):
        if flow.initial_map_dway():
            return "SnpCode"
        else:
            return "CDFSnpCode"

    def nc_drd_snoop_opcode(self, flow):
        if flow.initial_map_dway():
            return "SnpData"
        else:
            return "CDFSnpData"
     
                 
    def crd_snoop_opcode(self, flow):
        if not flow.need_to_selfsnoop_req_core() and flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "SnpCode")
        elif flow.need_to_selfsnoop_req_core() and flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "BackInv")
        elif not flow.need_to_selfsnoop_req_core() and flow.initial_map_sf():
            return self.covert_to_spec_snoop_if_needed(flow, "CDFSnpCode")
        elif flow.need_to_selfsnoop_req_core() and flow.initial_map_sf():
            return self.covert_to_spec_snoop_if_needed(flow, "CDFBackInv")

    def nc_crd_snoop_opcode(self, flow):
        if flow.initial_map_dway():
            return "SnpCode"
        else:
            return "CDFSnpCode" 
        
    def rfo_snoop_opcode(self, flow: ccf_flow):
        if flow.initial_state_llc_i() or flow.initial_map_dway():
            return self.covert_to_spec_snoop_if_needed(flow, "SnpInv")
        else:
            return self.covert_to_spec_snoop_if_needed(flow, "CDFSnpInv")


    def snpcurr_opcode(self, flow):
        if flow.initial_map_sf():
            return "CDFSnpCurr"
        else:
            return "SnpCurr"

    def should_send_speculative_snoop(self, flow: ccf_flow):
        return (flow.is_rfo_pref() or flow.is_drd_pref() or flow.is_crd_pref() or flow.is_drd_shared_opt_pref()) and not flow.is_dis_spec_snoop()

    def covert_to_spec_snoop_if_needed(self, flow, snoop_str):
        if self.should_send_speculative_snoop(flow):
            return "Spec" + snoop_str
        else:
            return snoop_str
