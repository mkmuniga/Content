#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG, EOT
from val_utdb_ral import val_utdb_ral, val_utdb_chk
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES


class ccf_bw_counter_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.checker_name = "ccf_bw_counter_chk"
        self.dic_write = {}
        self.dic_read = {}
        self.ccf_ral_agent_i = ccf_ral_agent.create()

    def reset(self):
        self.dic_write = {}
        self.dic_read = {}
    def initialize_dict(self):
        for i in range(self.si.num_of_cbo):
            self.dic_write["cbo" + str(i)] = 0
            self.dic_read["cbo" + str(i)] = 0

    def is_write_opode(self,opcode):
        return opcode in ['ITOMWR','ITOMWR_NS','ITOMWR_WT_NS','ITOMWR_WT','WBMTOI','WBMTOE','WBEFTOI','WBEFTOE','WBOTOI','WBOTOE','WBSTOI']

    def is_read_opcode(self,opcode):
        return opcode in ["CRD","CRD_PREF", "DRD", "DRD_SHARED_OPT", "DRD_SHARED_PREF", "DRD_PREF", "DRD_OPT", "DRD_NS", "DRD_OPT_PREF", "DRDPTE", "MONITOR", "RFO", "RFO_PREF", 'PRD', 'UCRDF']

    def is_pref_opcode(self,opcode):
        return opcode in ['LLCPREFCODE', 'LLCPREFDATA', 'LLCPREFRFO']

    def is_prefetch_enable(self,xbar_id):
        prefetch_cb = 0
        prefetch_cb = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i,
                                                      "egress_" + str(xbar_id), "egr_misc_cfg",
                                                      "bw_read_counter_with_pref")
        return prefetch_cb

    def get_cbo_id_for_core_requestor(self,requestor_phy_id):
        xbar_id = requestor_phy_id//CCF_COH_DEFINES.num_of_ccf_clusters
        return xbar_id
    def check_flow(self, flow: ccf_flow):
        if flow.is_idi_flow_origin():
            xbar_id = flow.requestor_physical_id // CCF_COH_DEFINES.num_of_ccf_clusters
            if self.is_write_opode(flow.opcode):
                self.dic_write["cbo" + str(xbar_id)] += 1
            if self.is_read_opcode(flow.opcode) or (self.is_pref_opcode(flow.opcode) and self.is_prefetch_enable(xbar_id)):

                self.dic_read["cbo" + str(xbar_id)] += 1



    def should_check_flow(self, flow : ccf_flow):
        return super().should_check_flow(flow)

    def ccf_bw_ral_check(self):
        write_dic = self.dic_write
        read_dic = self.dic_read
        for i in range(self.si.num_of_cbo):
            end_value_write = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,"egress_" + str(i), "ccf_input_write_counter", "count", COH_GLOBAL.global_vars["END_OF_TEST"])
            end_value_read = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "egress_" + str(i),"ccf_input_read_counter", "count",COH_GLOBAL.global_vars["END_OF_TEST"])
            if write_dic["cbo"+str(i)] != end_value_write:
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=f'(ccf_bw_counter_chk_write_error) CBO: '+str(i) +' actual: '+str(end_value_write) + ' and expected '+ str(write_dic["cbo"+str(i)]))
            if read_dic["cbo" + str(i)] != end_value_read:
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=f'(ccf_bw_counter_chk_read_error) CBO: '+str(i) +' actual: '+str(end_value_read) + ' and expected '+ str(read_dic["cbo"+str(i)]))
        self.collect_coverage()

