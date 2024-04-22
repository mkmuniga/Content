from val_utdb_bint import bint

from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

class UXI_UTILS:
    upi_opcodes_table_for_pkt_type = {
                        "REQ": ["RdCur","RdCode","RdData","RdDataMig","RdInvOwn","InvXtoI","RemMemSpecRd","InvItoE",
                                "InvItoEMig","InvItoMPush","RdInv","RdInvOwnPush","InvItoEMigPush","InvItoM"],
                        "SNP": ["SnpCur","SnpCode","SnpData","SnpDataMig","SnpInvOwn","SnpInvMig","UpdateM","SnpLCur",
                                "SnpLCode","SnpLData","SnpLDrop","SnpLInv","SnpFCur", "SnpFCode", "SnpFData", "SnpFInv"],
                        "RSP": ["RspI","RspS","RspFwd","RspFwdI-C","RspFwdS","RspFwdI-D","RspE","RspM","RspFwdIWb","RspFwdSWb","RspIWb","RspSWb","RspCurData",
                                "CmpU","NcCmpU","M_CmpO","E_CmpO","SI_CmpO",
                                "NcRetry","PCpl",
                                "FwdCnfltO",
                                "Data_M","Data_E","Data_SI","NcData"],
                        "WB":  ["WbMtoI","WbMtoS","WbMtoE","NonSnpWr","WbMtoIPush","WbEtoI",
                                "ReqFwdCnflt","EvctShrd","EvctCln","NonSnpRd",
                                "WbMtoIPtl", "WbMtoEPtl", "NonSnpWrPtl"],
                        "NCB": ["NcWr", "WcWr", "NcWrPtl", "WcWrPtl", "NcMsgB"],
                        "NCS": ["NcRd", "NcRdPtl", "NcCfgRd", "NcIORd", "NcCfgWr", "NcRd", "NcEnqueue", "NcMsgS"]
    }

    #Read, write and invalidation
    uxi_coh_read_opcodes = ["RdCur","RdCode","RdData","RdDataMig","RdInvOwn","RemMemSpecRd","RdInv","RdInvOwnPush",
                            "RdDataMigLP", "RdCodeLP", "RdDataLP", "RdInvOwnLP", "RdDataHP"]
    uxi_coh_inv_req_opcodes = ["InvXtoI","InvItoE","InvItoEMig","InvItoMPush","InvItoEMigPush","InvItoM"]
    uxi_coh_write_opcodes = ["WbMtoI","WbMtoS","WbMtoE","NonSnpWr","WbMtoIPush","WbEtoI","WbMtoIPtl", "WbMtoEPtl", "NonSnpWrPtl"]

    #Snoops
    uxi_coh_snp_opcodes = ["SnpCur","SnpCode","SnpData","SnpDataMig","SnpInvOwn","SnpInvMig","SnpLCur",
                           "SnpLCode","SnpLData","SnpLDrop","SnpLInv","SnpFCur", "SnpFCode", "SnpFData", "SnpFInv"]
    uxi_coh_snp_rsp_with_data_opcodes = ["RspFwd", "RspFwdI-C", "RspFwdS", "RspFwdI-D", "RspFwdIWb", "RspFwdSWb","RspIWb", "RspSWb", "RspCurData"]
    uxi_coh_snp_rsp_without_data_opcodes = ["RspI", "RspS", "RspE", "RspM"]
    uxi_coh_snp_rsp_opcodes = uxi_coh_snp_rsp_without_data_opcodes + uxi_coh_snp_rsp_with_data_opcodes

    #Snoops that can generate snpinv to IDI interface
    uxi_coh_snp_can_generate_idi_snpinv = ["SnpLInv", "SnpInvOwn", "SnpInvMig", "SnpLDrop"]

    #DDIO flow
    uxi_ddio_opcodes = ["UpdateM"]

    #Data and CMP
    uxi_coh_data_rtn_opcodes = ["Data_M", "Data_E", "Data_SI"]
    uxi_coh_cmp_opcodes = ["SI_CmpO", "E_CmpO", "M_CmpO", "CmpU"]

    #NC opcodes
    uxi_nc_read_opcodes = ["NcRd", "NcRdPtl", "NcCfgRd", "NcIORd", "NcRd"]
    uxi_nc_write_opcdes = ["NcWr", "WcWr", "NcWrPtl", "WcWrPtl"]
    uxi_nc_data_rtn_opcodes = ["NcData"]
    uxi_nc_cmp_opcodes = ["NcCmpU"]

    @staticmethod
    def is_exist_in_uxi_utils_list(uxi_list: list, item):
        return any([True for list_item in uxi_list if list_item.lower() == item.lower()])

    @staticmethod
    def is_in_coh_read_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_read_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_inv_req_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_inv_req_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_write_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_write_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_snp_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_snp_opcodes, item=opcode)

    @staticmethod
    def is_snp_can_generate_snpinv_on_idi(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_snp_can_generate_idi_snpinv, item=opcode)

    @staticmethod
    def is_in_coh_snp_rsp_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_snp_rsp_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_snp_rsp_without_data_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_snp_rsp_without_data_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_snp_rsp_with_data_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_snp_rsp_with_data_opcodes, item=opcode)

    @staticmethod
    def is_in_ddio_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_ddio_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_data_rtn_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_data_rtn_opcodes, item=opcode)

    @staticmethod
    def is_in_coh_cmp_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_coh_cmp_opcodes, item=opcode)

    @staticmethod
    def is_in_nc_read_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_nc_read_opcodes, item=opcode)

    @staticmethod
    def is_in_nc_write_opcdes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_nc_write_opcdes, item=opcode)

    @staticmethod
    def is_in_nc_data_rtn_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_nc_data_rtn_opcodes, item=opcode)

    @staticmethod
    def is_in_nc_cmp_opcodes(opcode):
        return UXI_UTILS.is_exist_in_uxi_utils_list(uxi_list=UXI_UTILS.uxi_nc_cmp_opcodes, item=opcode)

    @staticmethod
    def is_uxi_reqfwdcnflt(opcode):
        return opcode == "ReqFwdCnflt"

    @staticmethod
    def is_uxi_fwdcnflto(opcode):
        return opcode == "FwdCnfltO"