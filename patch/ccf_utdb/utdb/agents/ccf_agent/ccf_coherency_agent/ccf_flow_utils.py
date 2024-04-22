#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_flow_utils.py
#
# Owner:              meirlevy
# Creation Date:      03.2021
#
# ###############################################
#
# Description:
#
#################################################################################################
from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

class CCF_FLOW_UTILS:
    #According to Table 33 in IDI HAS.
    u2c_request_opcode = {"SnpCode"    : {"SnpCode":        ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI"],
                                          "CDFSnpCode":     ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE"],
                                          "SpecSnpCode":    ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspNack"],
                                          "SpecCDFSnpCode": ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE", "RspNack"]
                                         },
                          "SnpData"    : {"SnpData":        ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI"],
                                          "CDFSnpData":     ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE"],
                                          "SpecSnpData":    ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspNack"],
                                          "SpecCDFSnpData": ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE", "RspNack"],
                                         },
                          "SnpInv"     : {"SnpInv":        ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed"],
                                          "CDFSnpInv":     ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE"],
                                          "SpecSnpInv":    ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspNack"],
                                          "SpecCDFSnpInv": ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE", "RspNack"]
                                          },
                          "SelfSnpInv" : {"SelfSnpInv":         ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed"],
                                          "CDFSelfSnpInv" :     ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE"],
                                          "SelfSpecSnpInv" :    ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspNack"],
                                          "SelfSpecCDFSnpInv" : ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE", "RspNack"]
                                          },
                          "BackInv"    : {"BackInv":        ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed"],
                                          "CDFBackInv":     ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE"],
                                          "SpecBackInv":    ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspNack"],
                                          "SpecCDFBackInv": ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE", "RspNack"],
                                          }
                          }

    u2c_snp_and_rsp = {"SnpCode":        ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI"],
                       "CDFSnpCode":     ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE"],
                       "SpecSnpCode":    ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspNack"],
                       "SpecCDFSnpCode": ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE", "RspNack"],
                       "SnpData":        ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI"],
                       "CDFSnpData":     ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE"],
                       "SpecSnpData":    ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspNack"],
                       "SpecCDFSnpData": ["RspIHitI", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspFlushed", "RspSI", "RspSFwdFE", "RspNack"],
                       "SnpInv":        ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed"],
                       "CDFSnpInv":     ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE"],
                       "SpecSnpInv":    ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspNack"],
                       "SpecCDFSnpInv": ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE", "RspNack"],
                       "SelfSnpInv":         ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed"],
                       "CDFSelfSnpInv" :     ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE"],
                       "SelfSpecSnpInv" :    ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspNack"],
                       "SelfSpecCDFSnpInv" : ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE", "RspNack"],
                       "BackInv":        ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed"],
                       "CDFBackInv":     ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE"],
                       "SpecBackInv":    ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspNack"],
                       "SpecCDFBackInv": ["RspIHitI", "RspIHitFSE", "RspIFwdMO", "RspFlushed", "RspIFwdFE", "RspNack"],
                       "SnpCurr": ["RspIHitI","RspVhitV", "RspFlushed", "RspVFwdV", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspSI"] , #"RspSHitFSE", "RspSFwdMO", "RspIFwdMO" ,"RspSI"
                       "CDFSnpCurr": ["RspIHitI","RspVhitV", "RspFlushed", "RspVFwdV", "RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspSFwdFE", "RspSI"], #"RspSHitFSE", "RspSFwdMO", "RspIFwdMO", "RspSFwdFE", "RspSI"
                       "SnpClean": ["RspIHitI","RspVhitV", "RspFlushed", "RspEFFFwdMO"],
                       "INTPHY": ["RspIHitI"], #for INTPHY NC flows that configure to inner loop in NCU
                       "INTLOG": ["RspIHitI"], #for INTLOG NC flows that configure to inner loop in NCU
                       "STOPREQ": ["RspStopDone"],
                       "STARTREQ": ["RspStartDone"]
                       }

    #TODO: need to add DRD_SHARED_OPT_PREF once Dmitry will add it to the BFM
    flow_opcodes = ['ATOMICWR', 'ATOMICRDWR', 'ATOMICRD', 'CLDEMOTE', 'CLFLUSH', 'CLFLUSHOPT', 'CLRMONITOR', 'CLWB', 'CRD', 'CRD_PREF', 'CRD_UC', 'DRD', 'DRD_NS', 'DRD_OPT', 'DRD_OPT_PREF', 'DRD_PREF', 'DRDPTE', 'DRD_SHARED_OPT', 'DRD_SHARED_PREF', 'ITOM', 'ITOMWR', 'ITOMWR_NS', 'ITOMWR_WT', 'ITOMWR_WT_NS',
                       'LLCINV', 'LLCPREFCODE', 'LLCPREFDATA', 'LLCPREFRFO', 'LLCWB', 'LLCWBINV', 'LOCK', 'MEMPUSHWR', 'MEMPUSHWR_NS', 'PRD', 'RDCURR', 'RFO', 'RFO_PREF', 'RFOWR', 'MONITOR', 'SPEC_ITOM', 'SPLITLOCK', 'UCRDF', 'UNLOCK', 'WCIL', 'WCILF', 'WCIL_NS', 'WCILF_NS',
                       'WILF', 'WIL', 'FLOWN', 'PORT_IN', 'PORT_OUT', 'FSRDCURR', 'FSRDCURRPTL', 'RDCURRPTL', 'WILPTL', 'INTPHY', 'INTLOG', 'INTA', 'VICTIM', 'SNPCUR', 'SNPLCUR', 'SNPINV', 'SNPLINV', 'SNPLDROP', 'SNPINVMIG','SNPINVOWN', 'SNPCODE', 'SNPLCODE', 'SNPLFLUSH', 'SNPDATA', 'SNPLDATA', 'SNPDATAMIG', 'SNPLDATAMIG', 'NOP',
                       'NCMSGB', 'NCLTWR', 'INTLOGICAL', 'EOI', 'INTPHYSICAL', 'INTPRIUP', 'WBMTOE', 'WBMTOI', 'WBEFTOI', 'WBEFTOE', 'FLUSHER']

    u2c_allowed_req = {"AtomicWr":        ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "AtomicRdWr":      ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "AtomicRd":        ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "CLDemote":        ["SnpInv", "CDFSnpInv","SpecSnpInv", "CDFSelfSnpInv", "SelfSnpInv", "SpecCDFSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "CLFlush":         ["SnpInv", "SelfSnpInv", "BackInv"],
                       "CLFlushOPT":      ["SnpInv", "SelfSnpInv", "BackInv"],
                       "ClrMonitor":      [],
                       "CLWB":            ["SnpClean", "SnpData"], # SnpData is optional downgrade and we are using it.(Table 34 in IDI spec)
                       "CRd":             ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "CRD_PREF":        ["SnpCode", "CDFSnpCode","SpecSnpCode", "SpecCDFSnpCode",  "SnpData", "CDFSnpData", "SpecSnpData", "SpecCDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "SpecSnpInv", "SpecCDFSnpInv", "CDFSelfSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "CRD_UC":          ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "DRd":             ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "DRD_NS":          ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "DRD_OPT":         ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "DRD_OPT_PREF":    ["SnpCode", "CDFSnpCode","SpecSnpCode", "SpecCDFSnpCode",  "SnpData", "CDFSnpData", "SpecSnpData", "SpecCDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "SpecSnpInv", "SpecCDFSnpInv", "CDFSelfSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "DRD_PREF":        ["SnpCode", "CDFSnpCode","SpecSnpCode", "SpecCDFSnpCode",  "SnpData", "CDFSnpData", "SpecSnpData", "SpecCDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "SpecSnpInv", "SpecCDFSnpInv", "CDFSelfSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "DRdPTE":          ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "ItoM":            ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "ItoMWr":          ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "ItoMWr_NS":       ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "ItoMWr_Wt":       ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "ItoMWr_Wt_NS":    ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "LLCInv":          ["BackInv", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "LlcPrefCode":     ["SnpCode", "CDFSnpCode","SpecSnpCode", "SpecCDFSnpCode",  "SnpData", "CDFSnpData", "SpecSnpData", "SpecCDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "SpecSnpInv", "SpecCDFSnpInv", "CDFSelfSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "LlcPrefData":     ["SnpCode", "CDFSnpCode","SpecSnpCode", "SpecCDFSnpCode",  "SnpData", "CDFSnpData", "SpecSnpData", "SpecCDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "SpecSnpInv", "SpecCDFSnpInv", "CDFSelfSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "LlcPrefRFO":      ["SnpInv", "CDFSnpInv","SpecSnpInv", "CDFSelfSnpInv", "SelfSnpInv", "SpecCDFSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv"],
                       "LLCWB":           ["SnpClean", "SnpData"], # SnpData is optional downgrade and we are using it.(Table 34 in IDI spec)
                       "LLCWBInv":        ["BackInv", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "Lock":            ["StopReq"],
                       "MemPushWr":       ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "MemPushWr_NS":    ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "PRd":             ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "RdCurr":          ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "RFO":             ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "RFO_PREF":        ["SnpInv", "CDFSnpInv","SpecSnpInv", "CDFSelfSnpInv", "SelfSnpInv", "SpecCDFSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv"],
                       "RFOWr":           ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "Monitor":         ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv"],
                       "Spec_Itom":       ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "SplitLock":       ["StopReq"],
                       "UcRdF":           ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv", "BackInv"], #BackInv is not in IDI Spec (but it is the default snoop)
                       "Unlock":          ["StartReq"],
                       "WCiL":            ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "WCIL_NS":         ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "WcilF":           ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "WCILF_NS":        ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "WiLF":            ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "WiL":             ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "CLCleanse":       ["SnpInv", "CDFSnpInv","SpecSnpInv", "CDFSelfSnpInv", "SelfSnpInv", "SpecCDFSnpInv", "SelfSpecSnpInv", "SelfSpecCDFSnpInv", "BackInv", "CDFBackInv", "SpecBackInv", "SpecCDFBackInv"],
                       "Drd_Shared_Opt":  ["SnpCode", "CDFSnpCode", "BackInv", "CDFBackInv"],
                       "Drd_Shared_Pref": ["SnpCode", "CDFSnpCode", "BackInv", "CDFBackInv", "SpecSnpCode", "SpecCDFSnpCode", "SpecBackInv", "SpecCDFBackInv"],
                       "Flown":           ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "FsRdCurr":        ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv", "SnpCurr", "CDFSnpCurr"],
                       "FsRdCurrPtl":     ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv", "SnpCurr", "CDFSnpCurr"],
                       "RdCurrPtl":       ["SnpCode", "CDFSnpCode", "SnpData", "CDFSnpData", "SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv","BackInv", "CDFBackInv", "SnpCurr", "CDFSnpCurr"],
                       "WiLPtl":          ["SnpInv", "CDFSnpInv", "SelfSnpInv", "CDFSelfSnpInv"],
                       "IntPhy":          ["IntPhy"],
                       "IntLog":          ["IntLog"],
                       "VICTIM":          ["BackInv", "CDFBackInv"],
                       "SnpLInv":         ["SnpInv"],
                       "SnpLDrop":        ["SnpInv"],
                       "SnpInvMig":       ["SnpInv"],
                       "SnpInvOwn":       ["SnpInv", "CDFSnpInv"],
                       "SnpLCode":        ["SnpCode"],
                       "SnpCode":         ["SnpCode", "CDFSnpCode"],
                       "SnpLData":        ["SnpData"],
                       "SnpLDataMig":     ["SnpData"],
                       "SnpData":         ["SnpData", "CDFSnpData"],
                       "SnpDataMig":      ["SnpData", "CDFSnpData"],
                       "SnpCur":          ["SnpCurr", "CDFSnpCurr"],
                       "SnpLCur":         ["SnpCurr", "CDFSnpCurr"],
                       "SnpLFlush":       ["BackInv"]
                       }

    #table 26 in idi spec (C2U Requests & Supported U2C Responses)
    u2c_allowed_rsp = {"AtomicWr":        ["ExtCmp", "Fast_GO_WritePull", "FastGO_WritePull_Trivial", "GO_ERR_WritePull", "GO"],
                       "AtomicRdWr":      ["ExtCmp", "Fast_GO_WritePull", "FastGO_WritePull_Trivial", "GO_ERR_WritePull", "GO"],
                       "AtomicRd":        ["ExtCmp", "FastGo_ExtCmp", "fastgo", "GO_Err", "GO_I"],
                       "CLDemote":        ["GO"],
                       "CLFlush":         ["GO_Err", "GO"],
                       "CLFlushOPT":      ["ExtCmp", "FastGo_ExtCmp", "fastgo", "GO_Err"],
                       "ClrMonitor":      ["GO"],
                       "CLWB":            ["ExtCmp", "FastGo_ExtCmp", "fastgo", "GO_Err"],
                       "CRd":             ["GO_Err", "GO"],
                       "CRD_PREF":        ["GO_Err", "GO", "GO_NOGO"],
                       "CRD_UC":          ["GO_Err", "GO"],
                       "DRd":             ["LLCMiss", "GO"],
                       "DRD_NS":          ["GO"],
                       "DRD_OPT":         ["GO"],
                       "DRD_OPT_PREF":    ["GO", "GO_NOGO"],
                       "DRD_PREF":        ["LLCMiss", "GO", "GO_NOGO"],
                       "DRdPTE":          ["LLCMiss", "GO"],
                       "Enqueue":         ["WritePull", "GO"],
                       "EOI":             ["WritePull", "GO"],
                       "IntA":            ["GO"],
                       "ItoM":            ["GO"],
                       "ItoMWr":          ["GO_WritePull", "Fast_GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "ItoMWr_NS":       ["GO_WritePull", "Fast_GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "ItoMWr_Wt":       ["ExtCmp", "Fast_GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "ItoMWr_Wt_NS":    ["ExtCmp", "Fast_GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "LLCInv":          ["GO"],
                       "LlcPrefCode":     ["GO"],
                       "LlcPrefData":     ["GO"],
                       "LlcPrefRFO":      ["GO"],
                       "LLCWB":           ["ExtCmp", "FastGo_ExtCmp", "fastgo"],
                       "LLCWBInv":        ["ExtCmp", "FastGo_ExtCmp", "fastgo"],
                       "Lock":            ["GO"],
                       "MemPushWr":       ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "MemPushWr_NS":    ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "NOP":             ["GO"],
                       "Pcommit":         ["ExtCmp", "Fast_GO_WritePull"],
                       "Port_In":         ["GO"],
                       "Port_Out":        ["WritePull", "GO_Err", "GO"],
                       "PRd":             ["GO"],
                       "RdCurr":          ["GO"],
                       "RFO":             ["GO"],
                       "RFO_PREF":        ["GO", "GO_NOGO"],
                       "RFOWr":           ["GO_WritePull", "GO_ERR_WritePull"],
                       "Monitor":         ["GO"],
                       "SpCyc":           ["GO"],
                       "Spec_Itom":       ["GO"],
                       "SplitLock":       ["GO"],
                       "UcRdF":           ["GO"],
                       "Unlock":          ["GO"],
                       "WbEFtoE":         ["GO_WritePull", "GO_WritePull_Drop", "GO_WritePull_Trivial"],
                       "WbEFtoI":         ["GO_WritePull", "GO_WritePull_Drop", "GO_WritePull_Trivial"],
                       "WbMtoE":          ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WbMtoI":          ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WbOtoE":          ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WbOtoI":          ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WbStoI":          ["GO"],
                       "WCiL":            ["ExtCmp", "Fast_GO_WritePull", "FastGO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WCIL_NS":         ["ExtCmp", "Fast_GO_WritePull", "FastGO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WcilF":           ["ExtCmp", "Fast_GO_WritePull", "FastGO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WCILF_NS":        ["ExtCmp", "Fast_GO_WritePull", "FastGO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WiLF":            ["WritePull", "GO"],
                       "WiL":             ["WritePull", "GO"],
                       "CLCleanse":       ["GO"],
                       "Drd_Shared_Opt":  ["GO"],
                       "Drd_Shared_Pref": ["GO", "GO_NOGO"],
                       "Flown":           ["GO"],
                       "FsRdCurr":        [],
                       "FsRdCurrPtl":     [],
                       "RdCurrPtl":       ["GO"],
                       "WiLPtl":          ["WritePull", "GO"],
                       "IntPhy":          ["WritePull", "GO"],
                       "IntLog":          ["WritePull", "GO"],
                       "IntPriUp":        ["WritePull", "GO"],
                       "WbPushMtoI":      ["GO_WritePull", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WbPMPushMtoI":    ["GO_WritePull", "ExtCmp", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WBMtoEExtCmp":    ["GO_WritePull", "ExtCmp", "GO_WritePull_Trivial", "GO_ERR_WritePull"],
                       "WBMtoIExtCmp":    ["GO_WritePull", "ExtCmp", "GO_WritePull_Trivial", "GO_ERR_WritePull"]
                       }


    #PTL: check for new opcodes
    c2u_req_opcodes = {"read": ["FsRdCurr", "RdCurr","AtomicRd","CLDemote","CLFlush","CLFlushOPT","ClrMonitor","CLWB", "CRd","CRD_PREF",
                                "CRD_UC","DRd","DRD_NS","DRD_OPT","DRD_OPT_PREF","DRD_PREF","DRdPTE","IntA","ItoM","LLCInv","LlcPrefCode",
                                "LlcPrefData","LlcPrefRFO","LLCInv","LLCWB","LLCWBInv","Lock","NOP","PortIn","PRdRdcurr","RFO","RFO_PREF",
                                "SetMonitor","Monitor","SpCyc","SpecItoM","Spec_ItoM","SplitLock","UcRdF","Unlock", "WbStoI","CLCleanse","Drd_Shared_Opt", "DRD_SHARED_PREF", "FlOwn",
                                "RdCurPtl", "Prd"],
                       "write": ["CLFlush", "WCiLF", "WCiLF_NS", "ItoMWr_WT", "ItoMWr_WT_NS", "ItoMWr", "ItoMWr_NS","Enqueue","EOI",
                                 "IntLog","IntPhy","IntPriUp","Pcommit","PortOut","WbEFtoE","WbEFtoI","WbMtoE","WbMtoE","WbMtoI","WbOtoI","WbOtoE","WCiL",
                                 "WCIL_NS","WcilF","WCILF_NS","WiLF","WiL","WBPushMtoI","WBMtoEExtCmp","WBMtoIExtCmp","WiLPtl", "mempush_wr", "mempushwr", "mempushwr_ns", "victim"]}

    SNP_RSP_arbcommand = ["RspI", "RspS", "RspV", "RspSFwdM", "RspIFwdF", "RspSFwdF", "RspIFwdM", "RspILLCM", "RspSLLCM", "AtomicWr", "RspVFwdV", "RspNack"]

    c2u_special_addresses_req_opcodes = ["LLCWB", "WbInvd", "Invd"]
    c2u_special_addresses_req_opcodes_on_idi = ["LLCWB" , "LLCWBINV" ,"LLCINV"]


    addressless_opcodes = ["SpCyc", "Nop", "ClrMonitor","IntA","IntLog","IntPhy","IntPriUp", "CBO_EOI", "Lock", "Unlock", "SplitLock", "PortIn", "PortOut", "Enqueue", "FlushReadSet"]

    idi_addressless_opcodes = ["SPCYC", "NOP", "CLRMONITOR","INTA","INTLOG","INTPHY","INTPRIUP", "EOI", "LOCK", "UNLOCK", "SPLITLOCK", "PORT_IN", "PORT_OUT", "ENQUEUE"]

    DEMAND_READs_for_cxm_priority = ["CRD", "MONITOR", "DRD", "DRD_NS", "DRD_OPT", "DRDPTE", "RFO"] #MONITOR is there since CBO convert it to CRD opcode
    MLC_PREF_for_cxm_priority = ["CRD_PREF", "DRD_OPT_PREF", "DRD_PREF", "RFO_PREF"]



    #Note: we add SnpLFlush even that this opcode shouldn't trigger monitor according to CFI HAS.
    # This was done since design decide to send the snoop in case of monitor hit anyway and that since this snoop is from the type of BACKINV and will know wake the core if it's sleeping.
    CCF_MONITOR_TRIGGER_OPCODES_IDI_HOM_ONLY = ["ITOMWR" ,"ITOMWR_WT","ITOMWR_WT_NS","MEMPUSHWR", "MEMPUSHWR_NS", "CLFLUSH", "CLFLUSHOPT", "PRD", "CRD_UC", "UCRDF"]
    CCF_MONITOR_TRIGGER_OPCODES_IDI_HOM_AND_MMIO = ["ITOM","SPEC_ITOM","LLCPREFCODE","LLCPREFDATA","LCPREFRFO","WIL","WILF","WCIL","WCIL_NS","WCILF","WCILF_NS","PCOMMIT","RFO","RFO_PREF", "SnpLInv", "SnpLDrop", "SnpInvMig", "SnpInv", "SnpInvOwn", "SnpLFlush"]

    llc_opcodes = ["LLCGrant", "LRdsUcl", "LRsUcl", "LRdsc", "RdctWs", "RctWs", "MRdsctl",\
                   "Rdsctl", "Rsctl", "Rsct", "MRd", "Wdsct", "Wsct", "Wdsc", "Wds", "Wdc", "Wsc", "Ws", "Wc", "Wd", "Wt"]
    #MRd - in use in MBIST - currently stays in list
    #Wt - only in MBIST - currently stays in list
    #Rsctl - only in MBIST - currently stays in list
    #RdRsctl - not in use -  will be removed from list
    #NopLLCOpcode - is irrelevant to cover. there is no transaction in that case.  will be removed from list
    #Wdst - no in use - will be removed from list
    #MRdsctl -Oz might add it

    @staticmethod
    def is_arbcommand_in_SNP_RSP_arbcommand_list(opcode):
        return any([True for snp_rsp_arb in CCF_FLOW_UTILS.SNP_RSP_arbcommand if opcode.lower() == snp_rsp_arb.lower()])

    @staticmethod
    def should_trigger_monitor(opcode, sad):
        #return sad == "HOM" and (opcode in CCF_MONITOR_TRIGGER_OPCODES_IDI)
        return (opcode in CCF_FLOW_UTILS.CCF_MONITOR_TRIGGER_OPCODES_IDI_HOM_AND_MMIO) or (sad == "HOM" and opcode in CCF_FLOW_UTILS.CCF_MONITOR_TRIGGER_OPCODES_IDI_HOM_ONLY)

    @staticmethod
    def is_u2c_rsp_supported(c2u_req, u2c_rsp):
        return any([True for opcodes, responses in CCF_FLOW_UTILS.u2c_allowed_rsp.items() if (opcodes.lower() == c2u_req.lower().strip()) and (u2c_rsp.lower().strip() in (string.lower() for string in responses))])

    @staticmethod
    def is_snoop_opcode(opcode):
        return any([True for key, value in CCF_FLOW_UTILS.u2c_request_opcode.items() if opcode.lower().strip() in (string.lower() for string in value)])

    @staticmethod
    def is_snoop_response_valid(snoop_op,snoop_rsp_op):
        #for opcode_group, sub_dict in u2c_request_opcode.items():
        return any([True for opcode_group, sub_dict in CCF_FLOW_UTILS.u2c_request_opcode.items() for opcode, snoop_response in sub_dict.items() if (opcode.lower() == snoop_op.lower().strip()) and (snoop_rsp_op.lower().strip() in (string.lower() for string in snoop_response))])

    @staticmethod
    def is_write_opcode(opcode):
        return (opcode.lower().strip() in (string.lower() for string in CCF_FLOW_UTILS.c2u_req_opcodes.get("write")) or (opcode.lower().strip() == "port_out"))
  
    @staticmethod
    def get_aligned_address(address):
        int_addr = bint(int(address, 16))
        int_addr[5:0] = 0
        return str(hex(int_addr))

    @staticmethod
    def get_idi_aligned_address(address):
        aligned_addr = CCF_FLOW_UTILS.get_aligned_address(address)
        aligned_addr = '0x' + aligned_addr[2:].zfill(CCF_COH_DEFINES.address_lenth_in_hex)
        return aligned_addr

    @staticmethod
    def get_address_offset(address):
        bin_addr = bint(int(address, 16))
        return bin_addr[5:0]

    @staticmethod
    def is_read_opcode(opcode):
        return (opcode.lower().strip() in (string.lower() for string in CCF_FLOW_UTILS.c2u_req_opcodes.get("read"))) or (opcode.lower().strip()== "port_in")

    @staticmethod
    def get_only_snp_rsp_data(data_transactions):
        trans_to_return = []
        for trans in data_transactions:
            if trans.is_c2u_snoop_data_response():
                trans_to_return.append(trans)
        return trans_to_return

    @staticmethod
    def get_only_data_for_write(data_transactions):
        trans_to_return = []
        for trans in data_transactions:
            if not trans.is_c2u_snoop_data_response():
                trans_to_return.append(trans)
        return trans_to_return

    @staticmethod
    def get_distance(a ,b):
        if len(a) != len(b):
            VAL_UTDB_ERROR(time=0, msg="length mismatch of " + a + " = " + str(len(a)) + " while length of " + b + " = " + str(len(b)))
        else:
            distance = 0
            for j in range(len(a)):
                if a[j] != b[j]:
                    distance += 1
            return distance
