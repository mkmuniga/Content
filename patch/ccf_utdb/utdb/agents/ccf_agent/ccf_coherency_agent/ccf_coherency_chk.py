#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_coherency_agent.ccf_conflict_checker import conflict_checker, only_single_conflict_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_vulnerable_chk import ccf_vulnerable_chk
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_lfc_chk import ccf_lfc_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_go_chk import ccf_go_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_snoop_chk import ccf_snoop_chk
from agents.ccf_agent.ccf_coherency_agent.mem_hash_chk import mem_hash_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_sad_mca_chk import ccf_sad_mca_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import ccf_flow_cov
from agents.ccf_agent.ccf_coherency_agent.ccf_window_chk import ccf_windows_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_general_flow_chk import ccf_general_flow_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_mini_features_chk import ccf_mini_features_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_dbp_utils import ccf_dbp_chk_and_update
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_data_bases.ccf_dbs import ccf_dbs

from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_coherency_agent.ccf_clos_chk import ccf_clos_chk



class ccf_coherency_chk(ccf_coherency_base_chk):
    coherency_flow_checkers = {}
    global_ccf_checkers = {}

    ccf_dbp_chk_and_update = None

    #Global checker
    def get_global_checkers(self):
        self.global_ccf_checkers["ccf_window_chk"] = ccf_windows_chk.get_pointer()
        self.global_ccf_checkers["only_single_conflict_chk"] = only_single_conflict_chk.get_pointer()
        #self.global_ccf_checkers["santa_id_is_eq_to_hbo_id_when_send_reqfwdcnflt_chk"] = santa_id_is_eq_to_hbo_id_when_send_reqfwdcnflt_chk.get_pointer()
        self.global_ccf_checkers["ccf_vulnerable_chk"] = ccf_vulnerable_chk.get_pointer()
        self.global_ccf_checkers["ccf_mini_features_chk"] = ccf_mini_features_chk.get_pointer()

    def set_en_for_global_checkers(self):
        self.global_ccf_checkers["ccf_window_chk"].checker_enable = self.si.ccf_window_chk_en
        self.global_ccf_checkers["only_single_conflict_chk"].checker_enable = self.si.ccf_only_single_conflict_chk_en
        #self.global_ccf_checkers["santa_id_is_eq_to_hbo_id_when_send_reqfwdcnflt_chk"].checker_enable = self.si.ccf_reqfwdcnflt_chk_en
        self.global_ccf_checkers["ccf_vulnerable_chk"].checker_enable = self.si.ccf_vulnerable_chk_en

    #Flow checker
    def get_coherency_flow_checkers_ptr(self):
        self.coherency_flow_checkers["ccf_lfc_chk"] = ccf_lfc_chk.get_pointer()
        self.coherency_flow_checkers["ccf_dbp_chk_and_update"] = ccf_dbp_chk_and_update.get_pointer()
        self.coherency_flow_checkers["ccf_go_chk"] = ccf_go_chk.get_pointer()
        self.coherency_flow_checkers["ccf_snoop_chk"] = ccf_snoop_chk.get_pointer()
        self.coherency_flow_checkers["mem_hash_chk"] = mem_hash_chk.get_pointer()
        self.coherency_flow_checkers["ccf_sad_mca_chk"] = ccf_sad_mca_chk.get_pointer()
        self.coherency_flow_checkers["ccf_general_flow_chk"] = ccf_general_flow_chk.get_pointer()
        self.coherency_flow_checkers["ccf_clos_chk"] = ccf_clos_chk.get_pointer()
        self.coherency_flow_checkers["conflict_checker"] = conflict_checker.get_pointer()

    def set_en_for_coherency_flow_checkers(self):
        self.coherency_flow_checkers["ccf_lfc_chk"].checker_enable = self.si.ccf_lfc_chk_en
        self.coherency_flow_checkers["ccf_go_chk"].checker_enable = self.si.ccf_go_chk_en
        self.coherency_flow_checkers["ccf_snoop_chk"].checker_enable = self.si.ccf_snoop_chk_en
        self.coherency_flow_checkers["mem_hash_chk"].checker_enable = self.si.mem_hash_chk_en
        self.coherency_flow_checkers["ccf_sad_mca_chk"].checker_enable = self.si.ccf_sad_mca_chk_en
        self.coherency_flow_checkers["ccf_general_flow_chk"].checker_enable = self.si.ccf_general_flow_chk_en
        self.coherency_flow_checkers["ccf_clos_chk"].checker_enable = self.si.ccf_clos_chk_en
        self.coherency_flow_checkers["ccf_dbp_chk_and_update"].checker_enable = self.si.dbp_en
        self.coherency_flow_checkers["conflict_checker"].checker_enable = self.si.conflict_chk_en

    def get_coherency_coverage_ptr(self):
        self.coherency_coverage = ccf_flow_cov.get_pointer()
    def set_en_for_coverage(self):
        self.coherency_coverage.cov_en = self.si.ccf_cov_en

    def pre_flow_requirements_for_pp_checking(self, flow: ccf_flow):
        time = flow.initial_time_stamp
        err_msg = ""
        if flow.initial_time_stamp is None:
            time = 0
            err_msg += "(pre_flow_requirements_for_pp_checking): initial_time_stamp is None we cannot check this flow - TID {}\n".format(flow.uri['TID'])
        if flow.flow_is_hom() and flow.first_accept_time is None:
            err_msg += "(pre_flow_requirements_for_pp_checking): it seems that the follow trasnaction (TID {}) wasn't accepted in the pipe till EOT\n".format(flow.uri['TID'])
        #BDADON  had stiching isses  - URI related? keep and try to clean
        if flow.first_accept_time is None:
            err_msg += "(pre_flow_requirements_for_pp_checking): it seems that the follow trasnaction (TID {}) wasn't accepted in the pipe till EOT\n".format(flow.uri['TID'])
        #BDADON End of patch  
        if(err_msg != ""):
            err_msg += "We will skip the checking of the transaction TID -{} because of the errors that was found in the pre checking stage".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=time, msg=err_msg)
            return False
        else:
            return True

    def run_all_flow_checkers(self, flow: ccf_flow):
        flow_pass_initial_checking = self.pre_flow_requirements_for_pp_checking(self.ccf_flows[flow])
        if flow_pass_initial_checking:

            for checker in self.coherency_flow_checkers:
                if self.coherency_flow_checkers[checker].should_check_flow(self.ccf_flows[flow]):
                    self.coherency_flow_checkers[checker].check_flow(self.ccf_flows[flow])

            if self.coherency_coverage.cov_en:
                self.coherency_coverage.collect_end_of_flow_coverage(self.ccf_flows[flow])

    def run(self):
        self.get_global_checkers()
        self.set_en_for_global_checkers()

        self.get_coherency_flow_checkers_ptr()
        self.set_en_for_coherency_flow_checkers()

        self.coherency_flow_checkers["ccf_sad_mca_chk"].read_cb_reg() #checker need to initilize itself with registers values
        self.coherency_flow_checkers["ccf_dbp_chk_and_update"].config_dbp_initial_hits()
        self.ccf_coherency_qry = ccf_coherency_qry.get_pointer()

        self.get_coherency_coverage_ptr()
        self.set_en_for_coverage()

        #CCF global checkers will not iterate on each flow but will do global checking.
        for checker in self.global_ccf_checkers:
            if self.global_ccf_checkers[checker].is_checker_enable():
                self.global_ccf_checkers[checker].do_check()

        #Sort ccf flows according to order.
        ccf_dbs.sort_ccf_flows()
        self.coherency_flow_checkers["ccf_sad_mca_chk"].last_uri = list(self.ccf_flows.keys())[-1]
        self.coherency_flow_checkers["mem_hash_chk"].last_uri = list(self.ccf_flows.keys())[-1]

        for flow in self.ccf_flows:
            self.run_all_flow_checkers(flow)

        self.coherency_flow_checkers["ccf_dbp_chk_and_update"].eot_check()
