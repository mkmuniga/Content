#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_data_analyzer.py
#
# Owner:              asaffeld
# Creation Date:      12.2020
#
# ###############################################
#
# Description:
#   This file contain all ccf_coherency data analyzing from UTDB
#   It build the ccf_flows data based on the UTDB queires
#################################################################################################
from agents.ccf_analyzers.ccf_ufi_analyzer import ccf_ufi_analyzer
from agents.ccf_common_base.uxi_utils import UXI_UTILS
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_queries.ccf_window_qry import ccf_window_qry
from agents.ccf_analyzers.ccf_idi_analyzer import ccf_idi_analyzer
from agents.ccf_analyzers.ccf_llc_analyzer import ccf_llc_analyzer
from agents.ccf_analyzers.ccf_cbo_analyzer import ccf_cbo_analyzer
from agents.ccf_analyzers.ccf_cfi_analyzer import ccf_cfi_analyzer
from agents.ccf_analyzers.ccf_cpipe_windows_analyzer import ccf_cpipe_windows_analyzer
from agents.ccf_common_base.ccf_common_base_class import ccf_base_chk
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from agents.ccf_queries.ccf_llc_coherency_qry import ccf_llc_coherency_qry
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_monitor_agent import ref_monitor_array
from val_utdb_report import VAL_UTDB_ERROR

class ccf_coherency_db_constructor(ccf_base_chk):
    def __init__(self):
        self.ref_monitor_array = ref_monitor_array.get_pointer()
        self.ccf_window_db = None
        self.ccf_cpipe_window_utils = ccf_cpipe_window_utils.get_pointer()
        self.ccf_addressless_db = ccf_addressless_db.get_pointer()
        self.ccf_llc_db_agent = ccf_llc_db_agent.get_pointer()
        self.ccf_llc_coherency_qry = ccf_llc_coherency_qry.get_pointer()
        self.ccf_coherency_qry = ccf_coherency_qry.get_pointer()


    def end_of_data_analysis_update_flow_current_monitor_array(self, flow: ccf_flow):
        # Note: we add SnpLFlush even that this opcode shouldn't trigger monitor according to CFI HAS.
        # This was done since design decide to send the snoop in case of monitor hit anyway
        # and that since this snoop is from the type of BACKINV and will know wake the core if it's sleeping.
        flow_data_is_corrupted = (flow.initial_time_stamp is None) or (flow.flow_is_hom() and flow.first_accept_time is None)
        is_nc_opcodes_to_ignore = flow.is_non_coherent_flow() and flow.is_uxi_NcMsgS_flow_origin()
        should_update_current_monitor_array = (flow.is_victim() or flow.is_idi_flow_origin() or flow.is_uxi_flow_origin()) and not flow.is_clrmonitor() and not is_nc_opcodes_to_ignore

        if (not flow_data_is_corrupted) and should_update_current_monitor_array:
            if flow.first_accept_time is not None:
                if flow.is_monitor():
                    flow.current_monitor_array = self.ref_monitor_array.get_current_monitor_array(flow.first_accept_time, flow.cbo_id_log)
                elif flow.is_conflict_flow():
                    flow.current_monitor_array = self.ref_monitor_array.get_current_monitor_array(flow.get_arbcommand_time("FakeCycle"), flow.cbo_id_log)
                else:
                    #For LLC special opcode we are doing the same flow for COH and NC and there isn't any FakeCycle there
                    # wbstoi is same flow for COH/NC
                    if flow.flow_is_hom() or flow.is_llc_special_opcode() or flow.is_wbstoi():
                        flow.current_monitor_array = self.ref_monitor_array.get_current_monitor_array(flow.first_accept_time, flow.cbo_id_log)
                    else:
                        flow.current_monitor_array = self.ref_monitor_array.get_current_monitor_array(flow.get_arbcommand_time("FakeCycle"), flow.cbo_id_log)
                flow.go_monitor_array = self.ref_monitor_array.get_current_monitor_array(flow.go_accept_time, flow.cbo_id_log)
            else:
                err_msg = "(end_of_data_analysis_update_flow_current_monitor_array): We tried to use transaction accepted_time in pipe but it seems that it's None, " \
                          "the reason is probably since this trx wasn't accepted in the pipe till EOT (TID - {})".format(flow.uri['TID'])
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif flow_data_is_corrupted:
            VAL_UTDB_ERROR(time=0, msg="(end_of_data_analysis_update_flow_current_monitor_array): We didn't update monitor array flow is corrupted")


    def end_of_data_analysis_update_flow_promoted(self, flow: ccf_flow):
        if flow.flow_promoted is None:
            flow.flow_promoted = False
        elif flow.is_flow_promoted():
            status, orig_prefetch_uri_tid = self.ccf_cpipe_window_utils.can_promote(flow.address, flow.flow_promoted_time, flow.is_monitor_hit(), flow)
            if status:
                flow.promotion_flow_orig_pref_uri = orig_prefetch_uri_tid
                self.ccf_flows[orig_prefetch_uri_tid].pref_used_for_promotion = True
                self.ccf_flows[orig_prefetch_uri_tid].promoted_uri = flow.uri["TID"]
                orig_prefetch_flow = self.ccf_flows[orig_prefetch_uri_tid]
                flow.initial_cache_state = orig_prefetch_flow.initial_cache_state
                flow.sad_results = orig_prefetch_flow.sad_results
                flow.ufi_uxi_cmpo = orig_prefetch_flow.ufi_uxi_cmpo
                flow.ufi_uxi_rd_data = orig_prefetch_flow.ufi_uxi_rd_data
                flow.data_ways_available = orig_prefetch_flow.data_ways_available
                flow.dbp_params = orig_prefetch_flow.dbp_params
                flow.dbpinfo = orig_prefetch_flow.dbpinfo

                flow.allocated_tag_way = self.ccf_flows[orig_prefetch_uri_tid].allocated_tag_way
                flow.allocated_data_way = self.ccf_flows[orig_prefetch_uri_tid].allocated_data_way

                if orig_prefetch_flow.ufi_uxi_rd_data != "":
                    flow.ufi_uxi_rd_data = orig_prefetch_flow.ufi_uxi_rd_data
                else:
                    err_msg = "Val_Assert (end_of_data_analysis_update_flow_promoted): it appear that you don't have data in UPI and in CXM that cannot be in a flow that did promotion."
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            else:
                err_msg = "The transaction TID {} should not be promoted since the promotion windows was not open".format(flow.uri['TID'])
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def end_of_data_analysis_update_flow_is_prefetch_elimination(self, flow: ccf_flow):
        if flow.prefetch_elimination_flow is None:
            flow.prefetch_elimination_flow = False

    def end_of_data_analysis_update_conflict_flow(self, flow: ccf_flow):
        if flow.is_snoop_opcode():
            snoop_alloc_entry = self.ccf_cpipe_window_utils.get_transaction_allocation_entry(flow.address, flow.uri['TID'], flow.uri['LID'])

            if snoop_alloc_entry is not None:
                if snoop_alloc_entry.snoop_conflict_allocated == 1:
                    flow.had_conflict = True
                    flow.conflict_with_uri = snoop_alloc_entry.conflict_with_uri
                else:
                    flow.had_conflict = False
            else:
                err_msg = "(end_of_data_analysis_update_conflict_flow): We didn't found allocation entry for transaction TID {}".format(flow.uri['TID'])
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def end_of_data_analysis_add_info_from_cpipe_window_db(self, flow: ccf_flow):
        if len(flow.pipe_passes_information) > 0:
            entry = self.ccf_cpipe_window_utils.get_transaction_allocation_entry(flow.address, flow.uri['TID'], flow.uri['LID'])
            if entry is not None:
                flow.tor_occupancy = entry.Occupancy

    def initialize_llc_db(self):
        all_tids = self.ccf_llc_coherency_qry.flow_by_tid()
        for tid in all_tids:
            for record in tid.EVENTS:
                event = self.ccf_llc_coherency_qry.rec(record)
                if (int(event.r.TIME) >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (
                        int(event.r.TIME) < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    self.ccf_addressless_db.populate_addressless_db(event.r)
                    self.ccf_llc_db_agent.update_llc_rtl_db(event.r)



    def run_windows_analyzer(self):
        self.ccf_window_db = ccf_window_qry.get_pointer()
        self.ccf_cpipe_windows_analyzer = ccf_cpipe_windows_analyzer.get_pointer()

        all_addresses = self.ccf_window_db.address_sorting()

        for window_rec in all_addresses:
            for address_entry in window_rec.EVENTS:
                if (int(address_entry.TIME) >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (
                        int(address_entry.TIME) < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    address_event = self.ccf_window_db.rec(address_entry)
                    self.ccf_cpipe_windows_analyzer.analyze_record(address_event.r)


    def run_flow_analyzers(self):
        self.all_tids = self.ccf_coherency_qry.flow_by_tid()
        for tid in self.all_tids:
            # print("tid flow")
            for record in tid.EVENTS:
                # print(record)
                if (record.TIME >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (record.TIME < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    event = self.ccf_coherency_qry.rec(record)
                    for analyzer in self.analyzers:
                        self.analyzers[analyzer].analyze_record(event.r)

    def analyzer_declaration(self):
        self.analyzers = {"ccf_idi_analyzer": ccf_idi_analyzer.get_pointer(),
                          "ccf_llc_analyzer": ccf_llc_analyzer.get_pointer(),
                          "ccf_cbo_analyzer": ccf_cbo_analyzer.get_pointer(),
                          "ccf_cfi_analyzer": ccf_cfi_analyzer.get_pointer(),
                          "ccf_ufi_analyzer": ccf_ufi_analyzer.get_pointer()}

        self.analyzers["ccf_cbo_analyzer"].ref_monitor_array = self.ref_monitor_array

    def end_of_data_analysis_modification_to_cpipe_window_db(self):
        self.ccf_cpipe_window_utils.sort_ccf_addr_flow_db()
        self.ccf_cpipe_window_utils.update_db()

    def end_of_data_analysis_modification_to_ref_monitor_array(self):
        self.ref_monitor_array.sort_db()
        self.ref_monitor_array.arrange_db()

    def end_of_data_analysis_modification_to_ccf_flow_objects(self):
        for flow in self.ccf_flows:
            self.ccf_flows[flow].end_of_data_analysis_tasks()
            self.end_of_data_analysis_update_flow_promoted(self.ccf_flows[flow])
            self.end_of_data_analysis_update_flow_is_prefetch_elimination(self.ccf_flows[flow])
            self.end_of_data_analysis_update_conflict_flow(self.ccf_flows[flow])
            self.end_of_data_analysis_update_flow_current_monitor_array(self.ccf_flows[flow])
            self.end_of_data_analysis_add_info_from_cpipe_window_db(self.ccf_flows[flow])


    def run(self):

        #In here we will declare our flow analyzers
        self.analyzer_declaration()

        #LLC DB initialization
        self.initialize_llc_db()

        #Windows analyzer:
        self.run_windows_analyzer()

        #Flow analyzers
        self.run_flow_analyzers()

        #After all analyzers finish there some final tasks the flow runs
        self.end_of_data_analysis_modification_to_cpipe_window_db()
        self.end_of_data_analysis_modification_to_ref_monitor_array()

        #End of ccf_flows updates
        self.end_of_data_analysis_modification_to_ccf_flow_objects()
