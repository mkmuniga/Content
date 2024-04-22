from val_utdb_report import VAL_UTDB_MSG

from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import CCF_MONITOR_CG
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cg, ccf_cp
from agents.ccf_csv_flows_db.ccf_csv_flow_db import ccf_csv_flow_db
from agents.ccf_csv_flows_db.flow_routes_analyzer import flow_routes_analyzer


class CCF_FLOW_TABLE_ROW_CG(ccf_cg):
    def __init__(self):
        self.ccf_csv_flow_db = ccf_csv_flow_db.get_pointer().csv_db
        super().__init__()

    def coverpoints(self):
        # Define the coverpoints to be included in this covergroup
        self.PRd__CRd_UC__UcRdF_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("PRd/CRd_UC/UcRdF"))
        self.NC__Prd__CRd_UC__UcRdF_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/Prd/CRd_UC/UcRdF"))
        self.ItoMWr__ItoMWtr_NS_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("ItoMWr/ItoMWtr_NS"))
        self.WCiLF__WCiLF_NS__ItoMWr_WT__ItoMWr_WT_NS_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WCiLF/WCiLF_NS/ItoMWr_WT/ItoMWr_WT_NS"))
        self.CLFlush_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("CLFlush"))
        self.CLFlushOPT_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("CLFlushOPT"))
        self.NC__WiL__WiLF_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/WiL/WiLF"))
        self.Port_In_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Port_In"))
        self.Port_Out_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Port_Out"))
        self.WciL__WciL_NS_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WciL/WciL_NS"))
        self.WiL_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WiL"))
        self.WiLF_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WiLF"))
        self.INTA_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("INTA"))
        self.Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Drd/Drd_NS/Drd_Opt/DRd_Pref/DRd_Opt_Pref/DRdPTE"))
        self.Crd__Crd_Pref_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Crd/Crd_Pref/Monitor"))
        self.NC__Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE__Crd__Crd_Pref_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/Drd/Drd_NS/Drd_Opt/Drd_Pref/Crd/Crd_Pref/Drd_Opt_Pref/DrdPTE/monitor"))
        self.RFO__RFO_PRef_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("RFO/RFO_PRef"))
        self.NC__RFO__RFO_PRef_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/RFO/RFO_Pref"))
        self.SnpLDataMig_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpLDataMig"))
        self.SnpCode_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpCode"))
        self.SnpLCode_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpLCode"))
        self.SnpDataMig_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpDataMig"))
        self.SnpData_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpData"))
        self.SnpLData_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpLData"))
        self.SnpLCur_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpLCur"))
        self.SnpCur_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpCur"))
        self.SnpLInv_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpLInv"))
        self.SnpInvOwn_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SnpInvOwn"))
        self.IntPriUp_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("IntPriUp"))
        self.IntPhy_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("IntPhy"))
        self.IntLog_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("IntLog"))
        self.EOI_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("EOI"))
        self.ENQUEUE_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Enqueue"))
        self.SPCYC_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("SpCyc"))
        self.Victim_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Victim"))
        self.ItoM_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("ItoM"))
        self.ClrMonitor__Nop_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("ClrMonitor/Nop"))
        self.WbMtoI__WbMtoE_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WbMtoI/WbMtoE"))
        self.LLCWBInv_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("LLCWBInv"))
        self.LLCWB_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("LLCWB"))
        self.LLCInv_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("LLCInv"))
        self.CLWB_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("CLWB"))
        self.CLDemote_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("CLDemote"))
        self.LLCPrefData__LLCPrefCode__LLCPrefRFO_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("LLCPrefData/LLCPrefCode/LLCPrefRFO"))
        self.WciL__WciL_NS_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WciL/WciL_NS"))
        self.WiL_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WiL"))
        self.WiLF_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WiLF"))
        self.Spec_ItoM_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("Spec_ItoM"))
        self.MemPushWr__MemPushWr_NS_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("MemPushWr/MemPushWr_NS"))
        self.WbEFtoE_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WbEFtoE"))
        self.WbEFtoI_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WbEFtoI"))
        self.CLWB_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("CLWB"))
        self.WbStoI_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("WbStoI"))
        self.NC__LLCPrefData__LLCPrefCode__LLCPrefRFO_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/LLCPrefData/LLCPrefCode/LLCPrefRFO"))
        self.NC__ItoM__Spec_ItoM_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/ItoM/Spec_ItoM"))
        self.NC__WciL__WciL_Ns__WciLF__WciLF_NS_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/WciL/WciL_Ns/WciLF/WciLF_NS"))
        self.NC__CLFlush_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/CLFlush"))
        self.NC__CLFlushOPT_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/CLFlushOPT"))
        self.NC__CLWB_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/CLWB"))
        self.NC__CLDemote_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/CLDemote"))
        self.NC__WbEFtoI__WbEFtoE_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/WbEFtoI/WbEFtoE"))
        self.NC__MemPushWr__MemPushWr_NS__WbMtoI__WbMtoE_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("NC_/MemPushWr/MemPushWr_NS/WbMtoI/WbMtoE"))
        self.LOCK__SPLITLOCK__UNLOCK_table_row_cp = ccf_cp(self.build_flow_table_enable_row_span("LOCK/SPLITLOCK/UNLOCK"))

    def build_flow_table_enable_row_span(self, key):
        return list(
            self.ccf_csv_flow_db[key].loc[self.ccf_csv_flow_db[key]['Row Enable'] == "1"].loc[:, "Row Number"].values)



class CCF_FLOW_ROUTES_CG(ccf_cg):
    def __init__(self):
        self.flow_path_analyzer_i = flow_routes_analyzer()
        self.ccf_csv_flow_db = ccf_csv_flow_db.get_pointer().csv_db
        super().__init__()

    def build_flow_routes_span(self, key):
        return_list = []
        list_of_routes = self.flow_path_analyzer_i.get_all_possible_flow_routes_from_df(self.ccf_csv_flow_db[key])
        for route in list_of_routes:
            return_list.append("->".join(route))
        return return_list

    def coverpoints(self):
        # Define the coverpoints to be included in this covergroup
        # Need to see how we can coverage each of those opcode sperated
        self.PRd__CRd_UC__UcRdF_flow_routes_cp = ccf_cp(self.build_flow_routes_span("PRd/CRd_UC/UcRdF"))
        self.NC__Prd__CRd_UC__UcRdF_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/Prd/CRd_UC/UcRdF"))
        self.ItoMWr__ItoMWtr_NS_flow_routes_cp = ccf_cp(self.build_flow_routes_span("ItoMWr/ItoMWtr_NS"))
        self.WCiLF__WCiLF_NS__ItoMWr_WT__ItoMWr_WT_NS_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WCiLF/WCiLF_NS/ItoMWr_WT/ItoMWr_WT_NS"))
        self.CLFlush_flow_routes_cp = ccf_cp(self.build_flow_routes_span("CLFlush"))
        self.CLFlushOPT_flow_routes_cp = ccf_cp(self.build_flow_routes_span("CLFlushOPT"))
        self.NC__WiL__WiLF_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/WiL/WiLF"))
        self.Port_In_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Port_In"))
        self.Port_Out_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Port_Out"))
        self.WciL__WciL_NS_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WciL/WciL_NS"))
        self.WiL_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WiL"))
        self.WiLF_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WiLF"))
        self.INTA_flow_routes_cp = ccf_cp(self.build_flow_routes_span("INTA"))
        self.Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Drd/Drd_NS/Drd_Opt/DRd_Pref/DRd_Opt_Pref/DRdPTE"))
        self.Crd__Crd_Pref_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Crd/Crd_Pref/Monitor"))
        self.NC__Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE__Crd__Crd_Pref_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/Drd/Drd_NS/Drd_Opt/Drd_Pref/Crd/Crd_Pref/Drd_Opt_Pref/DrdPTE/monitor"))
        self.RFO__RFO_PRef_flow_routes_cp = ccf_cp(self.build_flow_routes_span("RFO/RFO_PRef"))
        self.NC__RFO__RFO_PRef_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/RFO/RFO_Pref"))
        self.SnpLDataMig_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpLDataMig"))
        self.SnpCode_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpCode"))
        self.SnpLCode_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpLCode"))
        self.SnpDataMig_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpDataMig"))
        self.SnpData_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpData"))
        self.SnpLData_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpLData"))
        self.SnpLCur_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpLCur"))
        self.SnpCur_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpCur"))
        self.SnpLInv_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpLInv"))
        self.SnpInvOwn_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SnpInvOwn"))
        self.IntPriUp_flow_routes_cp = ccf_cp(self.build_flow_routes_span("IntPriUp"))
        self.IntPhy_flow_routes_cp = ccf_cp(self.build_flow_routes_span("IntPhy"))
        self.IntLog_flow_routes_cp = ccf_cp(self.build_flow_routes_span("IntLog"))
        self.EOI_flow_routes_cp = ccf_cp(self.build_flow_routes_span("EOI"))
        self.ENQUEUE_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Enqueue"))
        self.SPCYC_flow_routes_cp = ccf_cp(self.build_flow_routes_span("SpCyc"))
        self.Victim_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Victim"))
        self.ItoM_flow_routes_cp = ccf_cp(self.build_flow_routes_span("ItoM"))
        self.ClrMonitor__Nop_flow_routes_cp = ccf_cp(self.build_flow_routes_span("ClrMonitor/Nop"))
        self.WbMtoI__WbMtoE_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WbMtoI/WbMtoE"))
        self.LLCWBInv_flow_routes_cp = ccf_cp(self.build_flow_routes_span("LLCWBInv"))
        self.LLCWB_flow_routes_cp = ccf_cp(self.build_flow_routes_span("LLCWB"))
        self.LLCInv_flow_routes_cp = ccf_cp(self.build_flow_routes_span("LLCInv"))
        self.CLWB_flow_routes_cp = ccf_cp(self.build_flow_routes_span("CLWB"))
        self.CLDemote_flow_routes_cp = ccf_cp(self.build_flow_routes_span("CLDemote"))
        self.LLCPrefData__LLCPrefCode__LLCPrefRFO_flow_routes_cp = ccf_cp(self.build_flow_routes_span("LLCPrefData/LLCPrefCode/LLCPrefRFO"))
        self.WciL__WciL_NS_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WciL/WciL_NS"))
        self.WiL_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WiL"))
        self.WiLF_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WiLF"))
        self.Spec_ItoM_flow_routes_cp = ccf_cp(self.build_flow_routes_span("Spec_ItoM"))
        self.MemPushWr__MemPushWr_NS_flow_routes_cp = ccf_cp(self.build_flow_routes_span("MemPushWr/MemPushWr_NS"))
        self.WbEFtoE_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WbEFtoE"))
        self.WbEFtoI_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WbEFtoI"))
        self.CLWB_flow_routes_cp = ccf_cp(self.build_flow_routes_span("CLWB"))
        self.WbStoI_flow_routes_cp = ccf_cp(self.build_flow_routes_span("WbStoI"))
        self.NC__LLCPrefData__LLCPrefCode__LLCPrefRFO_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/LLCPrefData/LLCPrefCode/LLCPrefRFO"))
        self.NC__ItoM__Spec_ItoM_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/ItoM/Spec_ItoM"))
        self.NC__WciL__WciL_Ns__WciLF__WciLF_NS_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/WciL/WciL_Ns/WciLF/WciLF_NS"))
        self.NC__CLFlush_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/CLFlush"))
        self.NC__CLFlushOPT_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/CLFlushOPT"))
        self.NC__CLWB_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/CLWB"))
        self.NC__CLDemote_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/CLDemote"))
        self.NC__WbEFtoI__WbEFtoE_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/WbEFtoI/WbEFtoE"))
        self.NC__MemPushWr__MemPushWr_NS__WbMtoI__WbMtoE_flow_routes_cp = ccf_cp(self.build_flow_routes_span("NC_/MemPushWr/MemPushWr_NS/WbMtoI/WbMtoE"))
        self.LOCK__SPLITLOCK__UNLOCK_flow_routes_cp = ccf_cp(self.build_flow_routes_span("LOCK/SPLITLOCK/UNLOCK"))


class ccf_flow_chk_cov_sample(ccf_base_component):

    def collect_flow_coverage(self, df_flow_name, flow_bubble_trace_msg, flow_selected_row_list):
        ccf_flow_cg = CCF_FLOW_ROUTES_CG.get_pointer()
        table_flow_row_cg = CCF_FLOW_TABLE_ROW_CG.get_pointer()

        if df_flow_name == "PRd/CRd_UC/UcRdF":
            ccf_flow_cg.sample(PRd__CRd_UC__UcRdF_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(PRd__CRd_UC__UcRdF_table_row_cp=row)

        elif df_flow_name == "NC_/Prd/CRd_UC/UcRdF":
            ccf_flow_cg.sample(NC__Prd__CRd_UC__UcRdF_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__Prd__CRd_UC__UcRdF_table_row_cp=row)

        elif df_flow_name == "ItoMWr/ItoMWtr_NS":
            ccf_flow_cg.sample(ItoMWr__ItoMWtr_NS_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WItoMWr__ItoMWtr_NS_table_row_cp=row)

        elif df_flow_name == "WCiLF/WCiLF_NS/ItoMWr_WT/ItoMWr_WT_NS":
            ccf_flow_cg.sample(WCiLF__WCiLF_NS__ItoMWr_WT__ItoMWr_WT_NS_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WCiLF__WCiLF_NS__ItoMWr_WT__ItoMWr_WT_NS_table_row_cp=row)

        elif df_flow_name == "CLFlush":
            ccf_flow_cg.sample(CLFlush_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(CLFlush_table_row_cp=row)

        elif df_flow_name == "CLFlushOPT":
            ccf_flow_cg.sample(CLFlushOPT_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(CLFlushOPT_table_row_cp=row)

        elif df_flow_name == "NC_/WiL/WiLF":
            ccf_flow_cg.sample(NC__WiL__WiLF_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__WiL__WiLF_table_row_cp=row)

        elif df_flow_name == "Port_In":
            ccf_flow_cg.sample(Port_In_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(Port_In_table_row_cp=row)

        elif df_flow_name == "Port_Out":
            ccf_flow_cg.sample(Port_Out_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(Port_Out_table_row_cp=row)

        elif df_flow_name == "WciL/WciL_NS":
            ccf_flow_cg.sample(WciL__WciL_NS_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WciL__WciL_NS_table_row_cp=row)

        elif df_flow_name == "WiL":
            ccf_flow_cg.sample(WiL_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WiL_table_row_cp=row)

        elif df_flow_name == "WiLF":
            ccf_flow_cg.sample(WiLF_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WiLF_table_row_cp=row)

        elif df_flow_name == "INTA":
            ccf_flow_cg.sample(INTA_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(INTA_table_row_cp=row)

        elif df_flow_name == "Drd/Drd_NS/Drd_Opt/DRd_Pref/DRd_Opt_Pref/DRdPTE":
            ccf_flow_cg.sample(Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE_table_row_cp=row)

        elif df_flow_name == "Crd/Crd_Pref/Monitor":
            ccf_flow_cg.sample(Crd__Crd_Pref_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(Crd__Crd_Pref_table_row_cp=row)

        elif df_flow_name == "NC_/Drd/Drd_NS/Drd_Opt/Drd_Pref/Crd/Crd_Pref/Drd_Opt_Pref/DrdPTE/monitor":
            ccf_flow_cg.sample(NC__Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE__Crd__Crd_Pref_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__Drd__Drd_NS__Drd_Opt__DRd_Pref__DRd_Opt_Pref__DRdPTE__Crd__Crd_Pref_table_row_cp=row)

        elif df_flow_name == "RFO/RFO_PRef":
            ccf_flow_cg.sample(RFO__RFO_PRef_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(RFO__RFO_PRef_table_row_cp=row)

        elif df_flow_name == "NC_/RFO/RFO_Pref":
            ccf_flow_cg.sample(NC__RFO__RFO_PRef_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__RFO__RFO_PRef_table_row_cp=row)

        elif df_flow_name == "SnpLDataMig":
            ccf_flow_cg.sample(SnpLDataMig_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpLDataMig_table_row_cp=row)

        elif df_flow_name == "SnpCur":
            ccf_flow_cg.sample(SnpCur_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpCur_table_row_cp=row)

        elif df_flow_name == "SnpDataMig":
            ccf_flow_cg.sample(SnpDataMig_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpDataMig_table_row_cp=row)

        elif df_flow_name == "SnpLCur":
            ccf_flow_cg.sample(SnpLCur_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpLCur_table_row_cp=row)

        elif df_flow_name == "SnpLCode":
            ccf_flow_cg.sample(SnpLCode_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpLCode_table_row_cp=row)

        elif df_flow_name == "SnpCode":
            ccf_flow_cg.sample(SnpCode_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpCode_table_row_cp=row)

        elif df_flow_name == "SnpData":
            ccf_flow_cg.sample(SnpData_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpData_table_row_cp=row)

        elif df_flow_name == "SnpLData":
            ccf_flow_cg.sample(SnpLData_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpLData_table_row_cp=row)

        elif df_flow_name == "SnpLInv":
            ccf_flow_cg.sample(SnpLInv_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpLInv_table_row_cp=row)

        elif df_flow_name == "SnpInvOwn":
            ccf_flow_cg.sample(SnpInvOwn_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SnpInvOwn_table_row_cp=row)

        elif df_flow_name == "IntPriUp":
            ccf_flow_cg.sample(IntPriUp_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(IntPriUp_table_row_cp=row)

        elif df_flow_name == "IntPhy":
            ccf_flow_cg.sample(IntPhy_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(IntPhy_table_row_cp=row)

        elif df_flow_name == "IntLog":
            ccf_flow_cg.sample(IntLog_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(IntLog_table_row_cp=row)

        elif df_flow_name == "EOI":
            ccf_flow_cg.sample(EOI_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(EOI_table_row_cp=row)

        elif df_flow_name == "Enqueue":
            ccf_flow_cg.sample(ENQUEUE_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(ENQUEUE_table_row_cp=row)

        elif df_flow_name == "SpCyc":
            ccf_flow_cg.sample(SPCYC_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(SPCYC_table_row_cp=row)

        elif df_flow_name == "Victim":
            ccf_flow_cg.sample(Victim_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(Victim_table_row_cp=row)

        elif df_flow_name == "ItoM":
            ccf_flow_cg.sample(ItoM_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(ItoM_table_row_cp=row)

        elif df_flow_name == "ClrMonitor/Nop":
            ccf_flow_cg.sample(ClrMonitor__Nop_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(ClrMonitor__Nop_table_row_cp=row)

        elif df_flow_name == "WbMtoI/WbMtoE":
            ccf_flow_cg.sample(WbMtoI__WbMtoE_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WbMtoI__WbMtoE_table_row_cp=row)

        elif df_flow_name == "LLCWBInv":
            ccf_flow_cg.sample(LLCWBInv_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(LLCWBInv_table_row_cp=row)

        elif df_flow_name == "LLCWB":
            ccf_flow_cg.sample(LLCWB_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(LLCWB_table_row_cp=row)

        elif df_flow_name == "LLCInv":
            ccf_flow_cg.sample(LLCInv_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(LLCInv_table_row_cp=row)

        elif df_flow_name == "LLCPrefData/LLCPrefCode/LLCPrefRFO":
            ccf_flow_cg.sample(LLCPrefData__LLCPrefCode__LLCPrefRFO_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(LLCPrefData__LLCPrefCode__LLCPrefRFO_table_row_cp=row)

        elif df_flow_name == "WciL/WciL_NS":
            ccf_flow_cg.sample(WciL__WciL_NS_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WciL__WciL_NS_table_row_cp=row)

        elif df_flow_name == "WiL":
            ccf_flow_cg.sample(WiL_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WiL_table_row_cp=row)

        elif df_flow_name == "Spec_ItoM":
            ccf_flow_cg.sample(Spec_ItoM_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(Spec_ItoM_table_row_cp=row)

        elif df_flow_name == "MemPushWr/MemPushWr_NS":
            ccf_flow_cg.sample(MemPushWr__MemPushWr_NS_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(MemPushWr__MemPushWr_NS_table_row_cp=row)

        elif df_flow_name == "WbEFtoE":
            ccf_flow_cg.sample(WbEFtoE_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WbEFtoE_table_row_cp=row)

        elif df_flow_name == "WbEFtoI":
            ccf_flow_cg.sample(WbEFtoI_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WbEFtoI_table_row_cp=row)

        elif df_flow_name == "CLWB":
            ccf_flow_cg.sample(CLWB_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(CLWB_table_row_cp=row)

        elif df_flow_name == "WbStoI":
            ccf_flow_cg.sample(WbStoI_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(WbStoI_table_row_cp=row)

        elif df_flow_name == "NC_/LLCPrefData/LLCPrefCode/LLCPrefRFO":
            ccf_flow_cg.sample(NC__LLCPrefData__LLCPrefCode__LLCPrefRFO_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__LLCPrefData__LLCPrefCode__LLCPrefRFO_table_row_cp=row)

        elif df_flow_name == "NC_/ItoM/Spec_ItoM":
            ccf_flow_cg.sample(NC__ItoM__Spec_ItoM_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__ItoM__Spec_ItoM_table_row_cp=row)

        elif df_flow_name == "NC_/WciL/WciL_Ns/WciLF/WciLF_NS":
            ccf_flow_cg.sample(NC__WciL__WciL_Ns__WciLF__WciLF_NS_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__WciL__WciL_Ns__WciLF__WciLF_NS_table_row_cp=row)

        elif df_flow_name == "NC_/CLFlush":
            ccf_flow_cg.sample(NC__CLFlush_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__CLFlush_table_row_cp=row)

        elif df_flow_name == "NC_/CLFlushOPT":
            ccf_flow_cg.sample(NC__CLFlushOPT_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__CLFlushOPT_table_row_cp=row)

        elif df_flow_name == "NC_/CLWB":
            ccf_flow_cg.sample(NC__CLWB_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__CLWB_table_row_cp=row)

        elif df_flow_name == "CLDemote":
            ccf_flow_cg.sample(CLDemote_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(CLDemote_table_row_cp=row)

        elif df_flow_name == "NC_/CLDemote":
            ccf_flow_cg.sample(NC__CLDemote_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__CLDemote_table_row_cp=row)

        elif df_flow_name == "NC_/WbEFtoI/WbEFtoE":
            ccf_flow_cg.sample(NC__WbEFtoI__WbEFtoE_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__WbEFtoI__WbEFtoE_table_row_cp=row)

        elif df_flow_name == "NC_/MemPushWr/MemPushWr_NS/WbMtoI/WbMtoE":
            ccf_flow_cg.sample(NC__MemPushWr__MemPushWr_NS__WbMtoI__WbMtoE_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(NC__MemPushWr__MemPushWr_NS__WbMtoI__WbMtoE_table_row_cp=row)

        elif df_flow_name == "LOCK/SPLITLOCK/UNLOCK":
            ccf_flow_cg.sample(LOCK__SPLITLOCK__UNLOCK_flow_routes_cp=flow_bubble_trace_msg)
            for row in flow_selected_row_list:
                table_flow_row_cg.sample(LOCK__SPLITLOCK__UNLOCK_table_row_cp=row)

        else:
            VAL_UTDB_MSG(time=0, msg="COVERAGE INFO - Couldn't sample the flow since the df_flow_name is unknown - {}".format(df_flow_name))

    def collect_mon_hit_coverage(self, monitor_vector_size):
        ccf_monitor_cg = CCF_MONITOR_CG.get_pointer()
        ccf_monitor_cg.sample(num_of_cores_with_monitor_in_monitor_hit=monitor_vector_size)

class PRE_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.data_pre_miss_values_list = ["9|1", "9|3", "E|4", "E|5", "E|6"]

        self.data_pre_values_cp = ccf_cp(
                ["2|1", "2|2", "2|3", "2|4", "2|5", "4|1", "4|2", "4|3", "4|4", "4|5", "6|1", "6|2", "6|3", "6|4",
                 # is not valid case: "6|5" -> LLC S cannot get RspFwdM
                 "E|7", "0|7",
                 "B|4",
                 "E|1", "9|1", "9|3", "E|4", "E|5", "E|6"])

        self.data_pre_miss_values_cp = ccf_cp(self.data_pre_miss_values_list)
        self.pcls_values_cp = ccf_cp(["2", "3", "8", "10", "1a", "1b"])
        self.rsp_pre_cp = ccf_cp(["0", "1"])

        self.data_pre_miss_values_cp_CROSS_pcls_values_cp = self.cross(self.data_pre_miss_values_cp,
                                                                           self.pcls_values_cp)

class ccf_flow_chk_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.flow_cg: CCF_FLOW_ROUTES_CG = CCF_FLOW_ROUTES_CG.get_pointer()
        self.table_flow_row_cg: CCF_FLOW_TABLE_ROW_CG = CCF_FLOW_TABLE_ROW_CG.get_pointer()
        self.ccf_monitor_cg: CCF_MONITOR_CG = CCF_MONITOR_CG.get_pointer()
        self.pre_cg: PRE_CG = PRE_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        VAL_UTDB_MSG(time=0, msg="End of flow chk coverage Run..")
