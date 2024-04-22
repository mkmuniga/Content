from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import CCF_VULNERABLE_CG
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry


class ccf_vulnerable_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.ccf_coherency_qry = ccf_coherency_qry.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.debug_prints = False
        self.GoSDis = None
        self.ccf_vulnerable_cg = CCF_VULNERABLE_CG.get_pointer()

    def is_checker_enable(self):
        return True #We will check if we want to use this checking per CBO inside the checker loop

    def collect_vulnerable_coverage_off_chk(self, cbo_phy_id):
        self.read_vulnerable_dway = self.ccf_coherency_qry.read_vulnerable_dway(llc_id=str(cbo_phy_id))
        for drd_line in self.vulnerable_flow:
            for record in drd_line.EVENTS:
                if self.is_record_in_current_test_scope(record):
                    if self.debug_prints:
                        print(record)
                    if (record.CV_RD != "-"):
                        # Data Vulnerable is when: (Vul/pref bit == 1) and CV=1
                        cv_is_zero = (bin(int(record.CV_RD, 16))[2:].count("1") == 1)
                        is_vulnerable_or_prefecth = record.PFVL_RD
                        if cv_is_zero and is_vulnerable_or_prefecth:
                            self.ccf_vulnerable_cg.sample(hit_cl_that_marked_as_vulnerable=1)

    def collect_vulnerable_coverage_during_chk(self, record):
        #self.ccf_vulnerable_cg.sample(hit_cl_that_marked_as_vulnerable=1)
        vul_dway = str(int(record.MAP))
        if self.ccf_vulnerable_cg.is_bin_in_cp_span(cp_name="dway_marked_with_data_vulnerable", bin_name=vul_dway):
            self.ccf_vulnerable_cg.sample(dway_marked_with_data_vulnerable=vul_dway)
        else:
            err_msg = "Val_Assert (collect_vulnerable_coverage_during_chk): The follow data map-{} is not part of the span".format(record.MAP)
            VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)

    def is_record_in_current_test_scope(self, record):
        return (record.TIME >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (record.TIME < COH_GLOBAL.global_vars["END_OF_TEST"])

    def is_go_s_opt_feature_disable(self, cbo_phy_id):
        return self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("ingress_" + str(cbo_phy_id), "ni_control", "disable_go_s_for_drd_hit", COH_GLOBAL.global_vars["END_OF_TEST"]) == 1

    def should_be_marked_as_vulnerble(self, flow: ccf_flow):
        basic_condition = flow.is_coherent_flow() and \
                          flow.is_data_vulnerable_feature_enable() and \
                          (flow.initial_state_llc_e() and flow.initial_cv_zero() and flow.initial_map_dway()) \
                          and not flow.is_cache_near()
        return basic_condition and (self.GoSDis or flow.is_core_observer() or flow.is_go_s_counter_below_th() or flow.is_brought_by_prefetch() or flow.is_flow_promoted())

    def check_if_prefetch_vulnerable_bit_is_correct(self, record, flow: ccf_flow, cbo_phy_id):
        err_msg = ""
        prefetch_vulnerable_bit = record.PFVL_WR
        if self.should_be_marked_as_vulnerble(flow):
            if prefetch_vulnerable_bit != "1":
                err_msg = "(ccf_vulnerable_chk):We are expecting to have this CL saved as vulnerable in LLC " \
                          "but we can see LLC clean vulnerable bit indication. LLC_{}, TID-{}".format(cbo_phy_id, flow.uri['TID'])
                VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)
            if flow.data_vulnerable != "1":
                err_msg = "(ccf_vulnerable_chk):We are expecting to have this CL saved as vulnerable in LLC " \
                          "but we can see that CBO TRK don't see this line as vulnerable line. LLC_{}, TID-{}".format(cbo_phy_id, flow.uri['TID'])
                VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)
            if not flow.final_cv_one() and (not flow.is_cv_err_injection()):
                err_msg = "(ccf_vulnerable_chk):We are expecting that if we are marking data as data vulnerable " \
                          "we will have only 1 CV turn on at the end of the flow. LLC_{}, TID-{}".format(cbo_phy_id, flow.uri['TID'])
                VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)

            if self.si.ccf_cov_en and (err_msg == ""):
                self.collect_vulnerable_coverage_during_chk(record)
        else:
            if prefetch_vulnerable_bit == "1":
                err_msg = "(ccf_vulnerable_chk):We didn't expect to have prefetch/vulnerable bit == 1 in this flow. LLC_{}, TID-{}".format(cbo_phy_id, flow.uri['TID'])
                VAL_UTDB_ERROR(time=record.TIME, msg=err_msg)

    def do_check(self):
        for cbo_log_id in range(self.si.num_of_cbo):
            cbo_phy_id = CCF_UTILS.get_physical_id_by_logical_id(cbo_log_id)
            self.GoSDis = self.is_go_s_opt_feature_disable(cbo_phy_id)

            if self.debug_prints:
                print("cbo_phy_id: {}".format(str(cbo_phy_id)))
                print("Start: {}, End: {}".format(COH_GLOBAL.global_vars["START_OF_TEST"], COH_GLOBAL.global_vars["END_OF_TEST"]))

            #First we will check all flows that can effect vulnerable bit that dont include promotion.
            self.vulnerable_flow = self.ccf_coherency_qry.vulnerable_data_flow(llc_id=str(cbo_phy_id))
            for drd_line in self.vulnerable_flow:
                for record in drd_line.EVENTS:
                    if self.is_record_in_current_test_scope(record):
                        if self.debug_prints:
                            print(record)
                        self.check_if_prefetch_vulnerable_bit_is_correct(record=record,
                                                                         cbo_phy_id=cbo_phy_id,
                                                                         flow=ccf_dbs.ccf_flows[record.TID])

            #Here we will check only the flows that did promotion and check if it should had vulnerable bit on.
            list_of_promoted_key_id = self.ccf_coherency_qry.promoted_flow_uri_list(cbo_id=str(cbo_phy_id))
            for key_id in list_of_promoted_key_id:
                if ccf_dbs.ccf_flows[key_id].final_state_llc_e() and not ccf_dbs.ccf_flows[key_id].is_cache_near():
                    list_of_records = self.ccf_coherency_qry.llc_record_for_promoted_drd(tid=key_id)
                    #We are not expecting to have more the one record that fit to the record that supposed to show the write LLC is doing after promotion.
                    if len(list_of_records) != 1:
                        err_msg = "(vulnerable checker): length of list_of_records supposed to be 1 but the current list length is: {} this can happen dur to checkr/query issue".format(len(list_of_records))
                        VAL_UTDB_ERROR(time=list_of_records[0].TIME, msg= err_msg)
                    else:
                        self.check_if_prefetch_vulnerable_bit_is_correct(record=list_of_records[0],
                                                                         cbo_phy_id=cbo_phy_id,
                                                                         flow=ccf_dbs.ccf_flows[key_id])


            self.collect_vulnerable_coverage_off_chk(cbo_phy_id)
