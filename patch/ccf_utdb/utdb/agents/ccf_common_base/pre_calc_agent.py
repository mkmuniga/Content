from agents.ccf_agent.ccf_flow_chk_agent.ccf_flow_chk_cov import PRE_CG
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from val_utdb_base_components import val_utdb_component
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from val_utdb_bint import bint

class llc_hit_case:
    def __init__(self,no_snoop_needed_pre,snoop_miss_pre,snoop_hit_no_dataPRE,snoop_hit_clean_data_fwd_pre,snoop_hit_m_data_fwd_pre):
        self.no_snoop_needed_pre = no_snoop_needed_pre
        self.snoop_miss_pre = snoop_miss_pre
        self.snoop_hit_no_dataPRE = snoop_hit_no_dataPRE
        self.snoop_hit_clean_data_fwd_pre = snoop_hit_clean_data_fwd_pre
        self.snoop_hit_m_data_fwd_pre = snoop_hit_m_data_fwd_pre

    def get_expected_dataPRE_value(self, flow: ccf_flow):
        if not flow.snoop_sent():
            return self.no_snoop_needed_pre
        elif flow.snoop_rsp_flushed() or flow.snoop_rsp_i_hit_i():
            return self.snoop_miss_pre
        elif (flow.snoop_rsp_hit() and not flow.snoop_rsp_i_hit_i()) or flow.snoop_rsp_si():
            return self.snoop_hit_no_dataPRE
        elif flow.snoop_rsp_clean_data_fwd():
            return self.snoop_hit_clean_data_fwd_pre
        elif flow.snoop_rsp_m():
            return self.snoop_hit_m_data_fwd_pre
        else:
            err_msg = "Val_Assert (get_expected_dataPRE_value): Default Answer is None Please check why did you got here in the checker, URI- {}".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return None


class pre_calc_agent(val_utdb_component):
    def __init__(self):
        self.llc_hit_m_case = llc_hit_case("2|1", "2|2", "2|3", "2|4", "2|5")
        self.llc_hit_e_case = llc_hit_case("4|1", "4|2", "4|3", "4|4", "4|5")
        self.llc_hit_s_case = llc_hit_case("6|1", "6|2", "6|3", "6|4", "6|5") #6|5 is not valid case, when LLC_S we cannot snoop hit and ge M data fwd
        #For coverage
        self.pre_cg = PRE_CG.get_pointer()
        self.collect_coverage = False
        self.pcls_for_coverage = None
        self.has_pre_for_coverage = None

    def clear_and_set_coverage_variables(self,collect_cov):
        self.collect_coverage = collect_cov and (self.si.ccf_cov_en == 1)
        self.pcls_for_coverage = None
        self.has_pre_for_coverage = None

    def collect_pre_coverage(self, flow: ccf_flow, pre_type_name):
        if pre_type_name == "DATA_PRE":
            if self.has_pre_for_coverage is not None and self.pcls_for_coverage is not None and (self.has_pre_for_coverage in self.pre_cg.data_pre_miss_values_list):
                self.pre_cg.sample(data_pre_values_cp=self.has_pre_for_coverage, data_pre_miss_values_cp=self.has_pre_for_coverage, pcls_values_cp=self.pcls_for_coverage)
            elif self.has_pre_for_coverage is not None and self.pcls_for_coverage is not None:
                self.pre_cg.sample(data_pre_values_cp=self.has_pre_for_coverage, pcls_values_cp=self.pcls_for_coverage)
            elif self.has_pre_for_coverage is not None:
                self.pre_cg.sample(data_pre_values_cp=self.has_pre_for_coverage)
            else:
                err_msg = "Val_Assert (pre_calc_agent - collect_coverage): It seems that user ask to collect coverage but no coverage could be collected please check your code."
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif pre_type_name == "RSP_PRE":
            if self.has_pre_for_coverage is not None:
                self.pre_cg.sample(rsp_pre_cp=self.has_pre_for_coverage)
            else:
                err_msg = "Val_Assert (pre_calc_agent - collect_coverage): It seems that user ask to collect coverage but no coverage could be collected please check your code."
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        else:
            err_msg = "Val_Assert (pre_calc_agent - collect_coverage): user use undefined pre_type_name please check your code."
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def convert_idi_pre_to_has_pre(self, idi_pre):
        idi_pre_bint = bint(int(idi_pre, 16))
        return "{}|{}".format(hex(idi_pre_bint[6:3]), hex(idi_pre_bint[2:0]))


    def convert_has_pre_to_idi_pre(self, has_pre):
        if has_pre is not None:
            if self.collect_coverage:
                self.has_pre_for_coverage = has_pre

            idi_pre = bint(0)
            pre_parts = has_pre.split("|")
            idi_pre[2:0] = bint(int(pre_parts[1], 16))
            idi_pre[6:3] = bint(int(pre_parts[0], 16))
            return "0x" + hex(idi_pre)[2:].zfill(2)
        else:
            return None

    def get_dataPRE_according_to_pcls_field(self, flow):
        pcls = flow.cfi_upi_data_pcls

        if self.collect_coverage:
            self.pcls_for_coverage = pcls

        if pcls == "8":
            return "9|1"
        elif pcls == "10":
            return "9|3"
        elif pcls in ["2", "3"] and (flow.cbo_got_ufi_uxi_cmpo_e() or flow.cbo_got_ufi_uxi_cmpo_si()):
            #err_msg = "Val_Assert (get_dataPRE_according_to_pcls_field): We shouldn't get PCLS 2 or 3 in LNL_M, URI- {}".format(flow.uri['TID'])
            #VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return "E|4"
        elif pcls in ["1a", "1b"] and (flow.cbo_got_ufi_uxi_cmpo_e() or flow.cbo_got_ufi_uxi_cmpo_si()):
            return "E|4"
        elif pcls == "2" and flow.cbo_got_ufi_uxi_cmpo_m():
            return "E|5"
        elif pcls == "3" and flow.cbo_got_ufi_uxi_cmpo_m():
            return "E|6"
        else:
            err_msg = "Val_Assert (get_dataPRE_according_to_pcls_field): we shouldn't got here check your code, URI- {}, PCLS- {}".format(flow.uri['TID'],pcls)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return None



    def get_dataPRE_hit_case(self, flow: ccf_flow):
        if flow.initial_state_llc_m():
            return self.convert_has_pre_to_idi_pre(self.llc_hit_m_case.get_expected_dataPRE_value(flow))
        elif flow.initial_state_llc_e():
            return self.convert_has_pre_to_idi_pre(self.llc_hit_e_case.get_expected_dataPRE_value(flow))
        elif flow.initial_state_llc_s():
            return self.convert_has_pre_to_idi_pre(self.llc_hit_s_case.get_expected_dataPRE_value(flow))
        else:
            err_msg = "Val_Assert (get_dataPRE_hit_case): Default Answer is None Please check why did you got here in the checker, URI- {}".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return None

    def get_dataPRE_miss_case(self, flow: ccf_flow):
        if flow.santa_got_cxm_rd_data():
            return self.convert_has_pre_to_idi_pre("E|1")
        elif flow.santa_got_upi_rd_data():
            return self.convert_has_pre_to_idi_pre(self.get_dataPRE_according_to_pcls_field(flow))


    def get_non_coherent_pre(self, flow: ccf_flow):
        if flow.initial_state_llc_i() or flow.initial_cache_state is None:
            return self.convert_has_pre_to_idi_pre("E|7")
        elif not flow.initial_state_llc_i():
            return self.convert_has_pre_to_idi_pre("0|7")

    def get_dataPRE(self, flow: ccf_flow, collect_cov=False):
        self.clear_and_set_coverage_variables(collect_cov)

        #1. If LLC state is LLC_I we will give PRE value according to PCLS value
        #2. If LLC state is LLC_M/E/S and we are still getting data from the memory and we are sending the data directly to core we will get PRE valueaccording to PCLS value.
        #3. If LLC state is LLC_M/E/S and CBO is sending the data to the core PRE will be according to hit Table in CCF HAS.
        #Note: DRd exception is in case we have CN but final_map is not Dway because we don't have avilable Dway but the data still goes back to CBO but stay in SF(See Leon flows)
        DRd_exception = flow.is_drd() and not flow.is_available_data() and (flow.is_cache_near() or flow.is_monitor_hit())
        data_should_got_back_to_cbo = ((not flow.final_state_llc_i() and flow.final_map_dway()) or DRd_exception) and flow.read_data_from_mem()
        hit_without_going_to_mem = ((flow.initial_cache_state is not None) and not flow.initial_state_llc_i()) and not flow.read_data_from_mem()
        hit_but_still_read_from_mem = not flow.initial_state_llc_i() and flow.read_data_from_mem()
        is_miss = ((flow.initial_cache_state is None and flow.sad_results != "HOM") or flow.initial_state_llc_i())

        data_pre = None

        if flow.is_flow_promoted():
            data_pre = self.convert_has_pre_to_idi_pre("B|4")
        elif not flow.flow_is_hom():
            data_pre = self.get_non_coherent_pre(flow)
        elif hit_without_going_to_mem or (hit_but_still_read_from_mem and data_should_got_back_to_cbo):
            data_pre = self.get_dataPRE_hit_case(flow)
        elif is_miss or (hit_but_still_read_from_mem and not data_should_got_back_to_cbo):
            data_pre = self.get_dataPRE_miss_case(flow)
        else:
            err_msg = "Val_Assert (get_dataPRE_hit_case): Default Answer is None how did you got here??, URI- {}".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return None

        if self.collect_coverage:
            self.collect_pre_coverage(flow, "DATA_PRE")

        return data_pre
        
    def get_rspPRE(self, flow: ccf_flow, collect_cov=False):
        self.clear_and_set_coverage_variables(collect_cov)

        always_miss_nc_opcode = flow.is_portin() or flow.is_portout() or flow.is_nop() or flow.is_enqueue() \
                                or flow.is_clrmonitor() or (flow.sad_results == "CRABABORT") or flow.is_interrupt() \
                                or flow.is_lock_or_unlock() or flow.is_spcyc()

        rsp_pre = None

        if flow.initial_state_llc_i() or always_miss_nc_opcode:
            rsp_pre = "0x0"
            self.has_pre_for_coverage = "0"
        else:
            rsp_pre = "0x1"
            self.has_pre_for_coverage = "1"

        if self.collect_coverage:
            self.collect_pre_coverage(flow, "RSP_PRE")

        return rsp_pre
