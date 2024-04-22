#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_data_analyzer.py
#
# Owner:              meirlevy
# Creation Date:      02.2021
#
# ###############################################
#
# Description:
#   This DB will describe the CCF flows and will take it's data from the CSV files
#################################################################################################
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
from agents.ccf_csv_flows_db.ccf_csv_base_db import ccf_csv_base_db


class ccf_csv_flow_db(ccf_csv_base_db):
    def __init__(self):
        super().__init__()
        self.FlowFileFolder = ccf_pp_params.get_pointer().params["ccf_root"] + "/src/val/utdb/agents/ccf_flows_csv/"
        self.list_of_csv_flow_files = [
                                      "PRd_CRdUC_UcRdF_Tables.csv",
                                      "ItoMWr_ItoMWr_NS_Tables.csv",
                                      "WCiLF--WCiLF_NS--ItoMWr_WT--ItoMWr_WT_NS.csv",
                                      "CLFlush_Tables.csv",
                                      "CLFlush_Opt_Tables.csv",
                                      "Port_In.csv",
                                      "Port_Out.csv",
                                      "WCiL--WCiL_NS.csv",
                                      "WiL.csv",
                                      "WiLF.csv",
                                      "IntA.csv",
                                      "DRd--DRd_NS--DRd_Opt--DRd_Pref--DRd_Pref_Opt--DRd_PTE.csv",
                                      "DRd_Shared_Opt.csv",
                                      "CRd--CRd_Pref.csv",
                                      "RFO--RFO_Pref.csv",
                                      "SnpLDataMig.csv",
                                      "SnpLCode.csv",
                                      "SnpCode.csv",
                                      "SnpData.csv",
                                      "SnpDataMig.csv",
                                      "SnpLData.csv",
                                      "SnpCur.csv",
                                      "SnpLCur.csv",
                                      "SnpInvOwn.csv",
                                      "SnpLInv.csv",
                                      "SnpLDrop.csv",
                                      "SnpInvMig.csv",
                                      "Victim.csv",
                                      "ItoM.csv",
                                      "CLDemote_Tables.csv",
                                      "CLWB.csv",
                                      "LLCInv.csv",
                                      "LLCWb.csv",
                                      "WbMtoI_WbMtoE.csv",
                                      "WbEFtoE.csv",
                                      "WbEFtoI.csv",
                                      "WbStoI_Tables.csv",
                                      "LLCWbInv.csv",
                                      "LLCPrefData_LLCPrefCode_LLCPrefRFO.csv",
                                      "MemPushWr_MemPushWr_NS_Tables.csv",
                                      "SpecItoM.csv",
                                      #NC
                                      "NC_PRd_CRdUC_UcRdF_Tables.csv",
                                      "NC_CLFlush_Tables.csv",
                                      "NC_CLFlushOPT_Tables.csv",
                                      "NC_WiL_WiLF.csv",
                                      "NC_DRd--DRd_NS--DRd_Opt--DRd_Pref--DRd_Pref_Opt--CRd--CRd_Pref.csv",
                                      "NC_RFO--RFO_Pref.csv",
                                      "NC_LLCPrefData--LLCPrefCode--LLCPrefRFO.csv",
                                      "NC_CLDemote.csv",
                                      "NC_CLWB.csv",
                                      "NC_ItoM--SpecItoM.csv",
                                      "NC_MemPushWr--MemPushWr_NS--WbMtoI--WbMtoE.csv",
                                      "NC_WCiL--WCiL_Ns--WCiLF--WCiLF_NS.csv",
                                      "NC_WbEFtoI--WbEFtoE.csv",
                                      "NC_WbStoI.csv",
                                      "IntPriUp.csv",
                                      "IntPhy.csv",
                                      "IntLog.csv",
                                      "EOI.csv",
                                      "Enqueue.csv",
                                      "ClrMonitor--Nop.csv",
                                      "Lock_SplitLock_Unlock.csv",
                                      "SpCyc.csv"
                                      ]















