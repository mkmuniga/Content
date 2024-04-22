#!/usr/intel/bin/python3.6.3a
import sys
import re
import os
import json
import gzip
import subprocess

import cfi_bin2logdb_common as common

#---------------------------------------------------------
# LogDB and Table tracker definitions
#---------------------------------------------------------

def trk_header(storage_formatting={'logdb_formatting': '%x'}):
    return [
        {'name': 'TIME'         , 'header_type': 'bigint unsigned'},
        {'name': 'VC_NAME'      , 'header_type': 'text'},
        {'name': 'SUBNET_NAME'  , 'header_type': 'text'},
        {'name': 'URI_TID'      , 'header_type': 'text'},
        {'name': 'URI_LID'      , 'header_type': 'text'},
        {'name': 'URI_PID'      , 'header_type': 'text'},
        {'name': 'INTERFACE'    , 'header_type': 'text'},
        {'name': 'IS_NULL'      , 'header_type': 'bigint' },
        {'name': 'PROTOCOL_ID'  , 'header_type': 'text'},
        {'name': 'EOP'          , 'header_type': 'bigint' },
        {'name': 'RCTRL'        , 'header_type': 'bigint', **storage_formatting},
        {'name': 'TRACE_PKT'    , 'header_type': 'bigint', **storage_formatting},
        {'name': 'VC_ID'        , 'header_type': 'text'},
        {'name': 'SHARED_CREDIT', 'header_type': 'bigint unsigned', **storage_formatting},
        {'name': 'DST_ID'       , 'header_type': 'text'},
        {'name': 'HEADER'       , 'header_type': 'text'},
        {'name': 'PAYLOAD'      , 'header_type': 'text'},
    ]

trk_header_logdb = trk_header()
trk_header_text = trk_header({'text_formatting': '{0:x}'})

#---------------------------------------------------------------
def common_full_logdb_header(record_type):
    return [
        {'name': 'TIME'         , 'record_type':record_type, 'header_type': 'bigint unsigned'},
        {'name': 'VC_NAME'      , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'URI_TID'      , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'URI_LID'      , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'URI_PID'      , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'INTERFACE'    , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'PROTOCOL_ID'  , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'PKT_TYPE'     , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'VC_ID'        , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'VC_ID_VAL'    , 'record_type':record_type, 'header_type': 'bigint unsigned' },
        {'name': 'RCTRL'        , 'record_type':record_type, 'header_type': 'bigint' },
        {'name': 'TRACE_PKT'    , 'record_type':record_type, 'header_type': 'bigint' },
        {'name': 'CLK_CNT'      , 'record_type':record_type, 'header_type': 'bigint unsigned' },
        {'name': 'RSP_ID'       , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'RSP_ID_VAL'   , 'record_type':record_type, 'header_type': 'bigint unsigned' },
        {'name': 'DST_ID'       , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'DST_ID_VAL'   , 'record_type':record_type, 'header_type': 'bigint unsigned' },
        {'name': 'MSG_CLASS'    , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'MSG_CLASS_VAL', 'record_type':record_type, 'header_type': 'bigint unsigned' },
        {'name': 'OPCODE'       , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'OPCODE_VAL'   , 'record_type':record_type, 'header_type': 'bigint unsigned' },
        {'name': 'ADDRESS'      , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%012lx'},
        {'name': 'LINE_ADDR'    , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%012lx'},
        {'name': 'HEADER'       , 'record_type':record_type, 'header_type': 'text'},
        {'name': 'PAYLOAD_STR'  , 'record_type':record_type, 'header_type': 'text'},
    ]

def common_data_logdb_header(record_type):
    return [
        {'name': 'EOP'          , 'record_type':record_type, 'header_type': 'bigint'},
        {'name': 'POSION'       , 'record_type':record_type, 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'CHUNK'        , 'record_type':record_type, 'header_type': 'bigint unsigned'},
        {'name': 'BE'           , 'record_type':record_type, 'header_type': 'int unsigned',    'logdb_formatting': '%08x'},
        {'name': 'DATA3'        , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%016lx'},
        {'name': 'DATA2'        , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%016lx'},
        {'name': 'DATA1'        , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%016lx'},
        {'name': 'DATA0'        , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%016lx'},
        {'name': 'D_PAR'        , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'I_PAR'        , 'record_type':record_type, 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},

    ]

#---------------------------------------------------------------
uxi_req_logdb_header = common_full_logdb_header('uxi_req') + [
        {'name': 'PAR_ERR'      , 'record_type':'uxi_req', 'header_type': 'text'},
        {'name': 'A_PAR'        , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'RTID'         , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'HTID'         , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'HNID'         , 'record_type':'uxi_req', 'header_type': 'text'},
        {'name': 'HNID_VAL'     , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'CRNID'        , 'record_type':'uxi_req', 'header_type': 'text'},
        {'name': 'CRNID_VAL'    , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'CDNID'        , 'record_type':'uxi_req', 'header_type': 'text'},
        {'name': 'CDNID_VAL'    , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'TEE'          , 'record_type':'uxi_req', 'header_type': 'int unsigned'},
        {'name': 'CLOS'         , 'record_type':'uxi_req', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
]

uxi_rsp_logdb_header = common_full_logdb_header('uxi_rsp') + [
        {'name': 'PAR_ERR'      , 'record_type':'uxi_rsp', 'header_type': 'text'},
        {'name': 'RTID'         , 'record_type':'uxi_rsp', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'HTID'         , 'record_type':'uxi_rsp', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'HDNID'        , 'record_type':'uxi_rsp', 'header_type': 'text'},
        {'name': 'HDNID_VAL'    , 'record_type':'uxi_rsp', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'CDNID'        , 'record_type':'uxi_rsp', 'header_type': 'text'},
        {'name': 'CDNID_VAL'    , 'record_type':'uxi_rsp', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'PCLS'         , 'record_type':'uxi_rsp', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'TEE'          , 'record_type':'uxi_rsp', 'header_type': 'int unsigned'},
        {'name': 'MEM_LOC'      , 'record_type':'uxi_rsp', 'header_type': 'int unsigned'},
        {'name': 'TSX_ABORT'    , 'record_type':'uxi_rsp', 'header_type': 'int unsigned'},
]

uxi_data_logdb_header =\
        common_full_logdb_header('uxi_data') + [
        {'name': 'RTID'         , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'HTID'         , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'HNID'         , 'record_type':'uxi_data', 'header_type': 'text'},
        {'name': 'HNID_VAL'     , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'HDNID'        , 'record_type':'uxi_data', 'header_type': 'text'},
        {'name': 'HDNID_VAL'    , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'CRNID'        , 'record_type':'uxi_data', 'header_type': 'text'},
        {'name': 'CRNID_VAL'    , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'CDNID'        , 'record_type':'uxi_data', 'header_type': 'text'},
        {'name': 'CDNID_VAL'    , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        ] +\
        common_data_logdb_header('uxi_data') + [
        {'name': 'LOW_ADDR'     , 'record_type':'uxi_data', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'A_PAR'        , 'record_type':'uxi_data', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'PAR_ERR'      , 'record_type':'uxi_data', 'header_type': 'text'},
        {'name': 'PCLS'         , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'CLOS'         , 'record_type':'uxi_data', 'header_type': 'bigint unsigned',  'logdb_formatting': '%x'},
        {'name': 'LEN'          , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'SAI'          , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'PARAMA'       , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'MSG_TYPE'     , 'record_type':'uxi_data', 'header_type': 'bigint unsigned', 'logdb_formatting': '%x'},
        {'name': 'TEE'          , 'record_type':'uxi_data', 'header_type': 'int unsigned'},
        {'name': 'MEM_LOC'      , 'record_type':'uxi_data', 'header_type': 'int unsigned'},
        {'name': 'TSX_ABORT'    , 'record_type':'uxi_data', 'header_type': 'int unsigned'},

        ]

#---------------------------------------------------------------
full_logdb_header = uxi_req_logdb_header + uxi_rsp_logdb_header + uxi_data_logdb_header

#---------------------------------------------------------------
full_trk_header = [
        {'name': 'TIME'         , 'header_type': 'bigint unsigned' },
        {'name': 'VC_NAME'      , 'header_type': 'text'},]
if not os.getenv("CFI_URI_REORDER"):
    full_trk_header.extend([
        {'name': 'URI_TID'      , 'header_type': 'text'},
        {'name': 'URI_LID'      , 'header_type': 'text'},
        {'name': 'URI_PID'      , 'header_type': 'text'},
    ])
full_trk_header.extend([
        {'name': 'INTERFACE'    , 'header_type': 'text'},
        {'name': 'PROTOCOL_ID'  , 'header_type': 'text'},
        {'name': 'PKT_TYPE'     , 'header_type': 'text'},
        {'name': 'VC_ID'        , 'header_type': 'text'},
        {'name': 'RSPID'        , 'header_type': 'string', 'null_value': '-'},
        {'name': 'DSTID'        , 'header_type': 'text'},
        {'name': 'MSG_CLASS'    , 'header_type': 'text'},
        {'name': 'OPCODE'       , 'header_type': 'text'},
        {'name': 'ADDRESS'      , 'header_type': 'bigint unsigned', 'text_formatting': '{0:012x}'},
        {'name': 'RTID'         , 'header_type': 'bigint unsigned', 'text_formatting': '{0:x}',     'null_value': '-'},
        {'name': 'HTID'         , 'header_type': 'bigint unsigned', 'text_formatting': '{0:x}',     'null_value': '-'},
        {'name': 'CRNID'        , 'header_type': 'text'  , 'null_value': '-'},
        {'name': 'HNID'         , 'header_type': 'text'  , 'null_value': '-'},
        {'name': 'CDNID'        , 'header_type': 'text'  , 'null_value': '-'},
        {'name': 'HDNID'        , 'header_type': 'text'  , 'null_value': '-'},
        {'name': 'GO'           , 'header_type': 'text'  , 'null_value': '-'},
        {'name': 'EOP'          , 'header_type': 'bigint' },
        {'name': 'CHUNK'        , 'header_type': 'bigint unsigned' },
        {'name': 'DATA_3'       , 'header_type': 'text'},
        {'name': 'DATA_2'       , 'header_type': 'text'},
        {'name': 'DATA_1'       , 'header_type': 'text'},
        {'name': 'DATA_0'       , 'header_type': 'text'},
        {'name': 'A_PAR'        , 'header_type': 'bigint', 'text_formatting': '{0:x}',     'null_value': '-'},
        {'name': 'D_PAR'        , 'header_type': 'bigint', 'text_formatting': '{0:x}',     'null_value': '-'},
        {'name': 'I_PAR'        , 'header_type': 'bigint', 'text_formatting': '{0:x}',     'null_value': '-'},
        {'name': 'PAR_ERR'      , 'header_type': 'text'},
        {'name': 'POSION'       , 'header_type': 'bigint',     'null_value': '-' },
        {'name': 'RCTRL'        , 'header_type': 'bigint' },
        {'name': 'TRACE_PKT'    , 'header_type': 'bigint' },
        {'name': 'CLK_CNT'      , 'header_type': 'bigint unsigned' },
        {'name': 'MISC'         , 'header_type': 'text'},
])
if os.getenv("CFI_URI_REORDER"):
    full_trk_header.extend([
        {'name': 'URI_TID', 'header_type': 'text'},
        {'name': 'URI_LID', 'header_type': 'text'},
        {'name': 'URI_PID', 'header_type': 'text'},
    ])

###################################################################
#---------------------------------------------------------
# global vars definition
#---------------------------------------------------------

PROTOCOL_NAME = {
    1: 'UXI'
}
VC_ID_NAME = {
#protocol_id,vc_id,channel => VC_NAME
    "1,0,REQ" : "UXI_REQ",
    "1,1,REQ" : "UXI_SNP",
    "1,3,REQ" : "UXI_WBR",
    
    "1,1,DATA" : "UXI_SNPD",
    "1,2,DATA" : "VC0_DRS",
    "1,4,DATA" : "VC1_RwD",
    "1,5,DATA" : "UXI_WB",
    "1,6,DATA" : "VC0_NCB",
    "1,7,DATA" : "VC0_NCS",
    
    "1,0,RSP" : "VC0_NDR"
}


#-------------------------------------------------
# UXI
#-------------------------------------------------
UXI_MSG_CLASS = {
    0 : "REQ",
    1 : "SNP",
    2 : "RSP",
    5 : "WB",
    6 : "NCB",
    7 : "NCS"
}

UXI_NCM_MSGB_TYPE = {
 0x20 : "EOI",
 0x21 : "VLW",
 0x30 : "PMReq",
 0x31 : "IntPrioUpd",
 0x32 : "IntPhysical",
 0x33 : "IntLogical"
}

UXI_NCM_MSGS_TYPE = {
    0 : "Shutdown",
    1 : "Invd_Ack",
    2 : "WbInvd_Ack",
    3 : "Unlock",
    4 : "Lock",
    9 : "StartReq",
 0x20 : "StopReq",
 0x3C : "IntAck",
 0x3D : "LTDoorbell",
 0x3E : "VcrWr",
 0x3F : "VcrRd"
}

UXI_REQ_OPCODE = {
    0x00 : "RdCur",
    0x01 : "RdCode",
    0x02 : "RdData",
    0x03 : "RdDataMig",
    0x04 : "RdInvOwn",
    0x05 : "InvXtoI",
    0x06 : "RemMemSpecRd",
    0x07 : "InvItoE",
    0x0C : "RdInv",
    0x0F : "InvItoM",
    
}

UXI_SNP_OPCODE = {
    0x20 : "SnpCur",
    0x21 : "SnpCode",
    0x22 : "SnpData",
    0x23 : "SnpDataMig",
    0x24 : "SnpInvOwn",
    0x25 : "SnpInvMig",
    #0x2F : "UpdateM",
    0x30 : "SnpLCur",
    0x31 : "SnpLCode",
    0x32 : "SnpLData",
    0x34 : "SnpLDrop",
    0x35 : "SnpLFlush",
    0x36 : "SnpLInv",
    0x38 : "SnpFCur",
    0x39 : "SnpFCode",
    0x3A : "SnpFData",
    0x3D : "SnpFFlush",
    0x3E : "SnpFInv"
}

UXI_RSP_OPCODE = {
    0x40 : "RspI",
    0x41 : "RspS",
    0x42 : "RspFwd",
    0x43 : "RspFwdI-C",
    0x44 : "RspFwdS",
    0x45 : "RspFwdI-D",
    0x46 : "RspE",
    0x47 : "RspM",
    0x49 : "CmpU",
    0x4A : "NCCmpU",
    0x4B : "NcRetry",
    0x50 : "M_CmpO",
    0x51 : "E_CmpO",
    0x52 : "SI_CmpO",
    0x53 : "FwdCnfltO"
}

UXI_DATA_OPCODE = {
    # msg class 2 (RSP)
    0x40 : "RspFwdIWb",
    0x41 : "RspFwdSWb",
    0x42 : "RspIWb",
    0x43 : "RspSWb",
    0x44 : "RspCurData",
    0x48 : "Data_M",
    0x49 : "Data_E",
    0x4A : "Data_SI",
    0x4B : "NcData",

    # msg class 5 (WB)
    0xA0 : "WbMtoI",
    0xA1 : "WbMtoS",
    0xA2 : "WbMtoE",
    0xA3 : "NonSnpWr",
    0xA4 : "WbMtoIPush",
    0xA8 : "WbEtoI",
    0xB0 : "ReqFwdCnflt",
    0xB1 : "EvctShrd",
    0xB2 : "EvctCln",
    0xB3 : "NonSnpRd",
    0xB7 : "WbMtoIPtl",
    0xB9 : "WbMtoEPtl",
    0xBA : "NonSnpWrPtl",

    # msg class 6 (NCB)
    0xC0 : "NcWr",
    0xC1 : "WcWr",
    0xCC : "NcWrPtl",
    0xCD : "WcWrPtl",
    0xD0 : "NcMsgB",

    # msg class 7 (NCS)
    0xE0 : "NcRd",
    0xE4 : "NcRdPtl",
    0xE5 : "NcCfgRd",
    0xE7 : "NCIORd",
    0xE9 : "NcCfgWr",
    0xEB : "NcIOWr",
    0xEC : "NcEnqueue",
    0xF0 : "NcMsgS"
}

UXI_SNP_PKT_TYPE = {
    0x20 : "SA-S", # "SnpCur",
    0x21 : "SA-S", # "SnpCode",
    0x22 : "SA-S", # "SnpData",
    0x23 : "SA-S", # "SnpDataMig",
    0x24 : "SA-S", # "SnpInvOwn",
    0x25 : "SA-S", # "SnpInvMig",
    #0x2F : "SA-SLD", # "UpdateM",
    0x30 : "SA-SL", # "SnpLCur",
    0x31 : "SA-SL", # "SnpLCode",
    0x32 : "SA-SL", # "SnpLData",
    0x34 : "SA-SL", # "SnpLDrop",
    0x35 : "SA-SL", # "SnpLFlush",
    0x36 : "SA-SL", # "SnpLInv",
    0x38 : "SA-SL", # "SnpFCur",
    0x39 : "SA-SL", # "SnpFCode",
    0x3A : "SA-SL", # "SnpFData",
    0x3D : "SA-SL", # "SnpFFlush",
    0x3E : "SA-SL", # "SnpFInv",
    0xB0 : "SA", # "ReqFwdCnflt",
    0xB1 : "SA", # "EvctShrd",
    0xB2 : "SA", # "EvctCln",
    0xB3 : "SA", # "NonSnpRd",
}

UXI_RSP_PKT_TYPE = {
    0x40 : "SR-H", # "RspI",
    0x41 : "SR-H", # "RspS",
    0x42 : "SR-H", # "RspFwd",
    0x43 : "SR-H", # "RspFwdI-C",
    0x44 : "SR-H", # "RspFwdS",
    0x45 : "SR-H", # "RspFwdI-D",
    0x46 : "SR-H", # "RspE",
    0x47 : "SR-H", # "RspM",
    0x49 : "SR-U", # "CmpU",
    0x4A : "SR-U", # "NCCmpU",
    0x4B : "SR-U", # "NcRetry",
    0x50 : "SR-O", # "M_CmpO",
    0x51 : "SR-O", # "E_CmpO",
    0x52 : "SR-O", # "SI_CmpO",
    0x53 : "SR-O", # "FwdCnfltO"
}

UXI_DATA_PKT_TYPE = {
    # msg class 2 (RSP)
    0x40 : "SR-HD", # "RspFwdIWb",
    0x41 : "SR-HD", # "RspFwdSWb",
    0x42 : "SR-HD", # "RspIWb",
    0x43 : "SR-HD", # "RspSWb",
    0x44 : "SR-HD", # "RspCurData",
    0x48 : "SR-CD", # "Data_M",
    0x49 : "SR-CD", # "Data_E",
    0x4A : "SR-CD", # "Data_SI",
    0x4B : "SR-CD", # "NcData",

    # msg class 5 (WB)
    0xA0 : "SA-D", # "WbMtoI",
    0xA1 : "SA-D", # "WbMtoS",
    0xA2 : "SA-D", # "WbMtoE",
    0xA3 : "SA-D", # "NonSnpWr",
    0xA4 : "SA-D", # "WbMtoIPush",
    0xA8 : "SA-D", # "WbEtoI",
    0xB7 : "PW", # "WbMtoIPtl",
    0xB9 : "PW", # "WbMtoEPtl",
    0xBA : "PW", # "NonSnpWrPtl",

    # msg class 6 (NCB)
    0xC0 : "SA-D", # "NcWr",
    0xC1 : "SA-D", # "WcWr",
    0xCC : "PW", # "NcWrPtl",
    0xCD : "PW", # "WcWrPtl",
    0xD0 : "NCM", # "NcMsgB",

    # msg class 7 (NCS)
    0xE0 : "PR", # "NcRd",
    0xE4 : "PR", # "NcRdPtl",
    0xE5 : "PR", # "NcCfgRd",
    0xE7 : "PR", # "NCIORd",
    0xE9 : "PW", # "NcCfgWr",
    0xEB : "PW", # "NcIOWr",
    0xEC : "PW", # "NcEnqueue",
    0xF0 : "NCM", # "NcMsgS"
}

AGENT_TYPE = {
   # MEMSS
   0x00 : "MC_0",
   0x01 : "MC_1",
   0x02 : "IBECC_0",
   0x03 : "IBECC_1",
   0x04 : "CCE_0",
   0x05 : "CCE_1",
   0x10 : "CCF_0",
   0x11 : "CCF_1",
   0x12 : "CCF_0",
   0x13 : "CCF_1",
   0x08 : "HBO_0",
   0x09 : "HBO_1",
   0x0C : "HBO_0",
   0x0D : "HBO_1",
   0x14 : "IDIB",
   0x16 : "CCE_0",
   0x17 : "CCE_1",
   # Main NOC
   0x21 : "sNCU",
   0x22 : "sVTU",
   0x23 : "PUNIT",
   0x24 : "DISP_0",
   0x25 : "DISP_1",
   0x26 : "DE",
   0x28 : "VPU_0",
   0x29 : "VPU_1",
   0x2A : "VPU_2",
   0x2B : "VPU_3",
   0x2C : "MEDIA_0",
   0x2D : "MEDIA_1",
   0x2F : "IAX",
   0x30 : "GT_0",
   0x31 : "GT_1",
   0x32 : "GT_2",
   0x33 : "GT_3",
   0x34 : "IPU_0",
   0x35 : "IPU_1",
   #SOC DIE
   0x41 : "IOC_0_VTU",
   0x42 : "IOCCE",
   0x48 : "IOC_0_L0",
   0x49 : "IOC_0_L1",      # CXM writes to MEM
   0x4A : "IOC_0_L0_N1",
   0x4B : "IOC_0_L1_N1",
   # GT
   0x60 : "GT_0",
   0x61 : "GT_1",
   0x62 : "GT_2",
   0x63 : "GT_3",

   #Old encoding
   0xA0 : "CXL_0",
   0xA1 : "CXL_1"
}

HA_TYPE = {
   0 : "HBO_0",
   1 : "HBO_1"
}

MEMSS   = [
    "SOC_CFI_HBOMC0",
    "SOC_CFI_HBOMC1",
    "SOC_CFI_HBOIO0",
    "SOC_CFI_HBOIO1",
    "SOC_CFI_CCEMC0",
    "SOC_CFI_CCEMC1",
    "SOC_CFI_CCEIO0",
    "SOC_CFI_CCEIO1",
    "SOC_CFI_CCF_LINK0",
    "SOC_CFI_CCF_LINK1",
    "SOC_CFI_MEM0",
    "SOC_CFI_MEM1",
    "SOC_CFI_ICELAND",
    "SOC_CFI_MAINNOC0",
    "SOC_CFI_MAINNOC1"
]

MAINNOC = [
    "SOC_CFI_C_D2D0",
    "SOC_CFI_SNCU",
    "SOC_CFI_IAX",
    "SOC_CFI_SVTU",
    "SOC_CFI_GTC_D2D0",
    "SOC_CFI_GTC_D2D1",
    "SOC_CFI_DNC0",
    "SOC_CFI_DNC1",
    "SOC_CFI_DEIOSF",
    "SOC_CFI_PUNIT",
    "SOC_CFI_MEMSS00",
    "SOC_CFI_MEMSS10",
    "SOC_CFI_VPU0",
    "SOC_CFI_VPU1",
    "SOC_CFI_VPU2",
    "SOC_CFI_VPU3",
    "SOC_CFI_MEDIA0",
    "SOC_CFI_MEDIA1",
    "SOC_CFI_IPU0",
    "SOC_CFI_IPU1"
]

EXTERNAL = [
    "SOC_CFI_INOC_D2D",
    "SOC_CFI_GGT0_D2D",
    "SOC_CFI_GGT1_D2D",
    "SOC_CFI_GTS_D2D0",
    "SOC_CFI_GTS_D2D1",
    "GT_ICXL2CFI_INTERNAL_MUX",
    "GT_IOSF2CFI_INTERNAL_MUX",
    "MEDIA_ICXL2CFI_INTERNAL_MUX",
    "MEDIA_IOSF2CFI_INTERNAL_MUX",
    "IAX_ICXL2CFI_INTERNAL_MUX",
    "IAX_IOSF2CFI_INTERNAL_MUX"
]

EXCLUDE_CFI_PORT_LIST = [
    "cce0_cfi_req",
    "cce0_cfi_rsp",
    "cce1_cfi_req",
    "cce1_cfi_rsp"
]
#-------------------------------------------------
# override AGENT_TYPE dictionary from file (if exists)
#-------------------------------------------------
tmp = dict()
rout_id_table_path = 'rout_id_table.py'
rout_id_table_path = common.test_dir + '/' + rout_id_table_path
if (os.path.isfile(rout_id_table_path + ".gz")):
    rout_id_table_path = rout_id_table_path + ".gz"
    with gzip.open(rout_id_table_path) as f:
        tmp = json.load(f)
elif (os.path.isfile(rout_id_table_path)):
    with open(rout_id_table_path) as f:
        tmp = json.load(f)

TMP_AGENT_TYPE = dict()
TMP_HA_TYPE    = dict()

for agent_type in tmp:
    for id in tmp[agent_type]:
        if(agent_type == "AGENT_TYPE"):
            TMP_AGENT_TYPE[int(id,16)] = tmp[agent_type][id]
        elif(agent_type == "HA_TYPE"):
            TMP_HA_TYPE[int(id,16)] = tmp[agent_type][id]

if(TMP_AGENT_TYPE != {}):
    AGENT_TYPE = TMP_AGENT_TYPE
if(TMP_HA_TYPE != {}):
    HA_TYPE = TMP_HA_TYPE

#-------------------------------------------------
# CFI configuration dictionary.
# If the entry exists, this means that the interface has 522 bits DATA
# and the header_size is defined
#-------------------------------------------------
cmd = "zegrep \"CFI_TOP_PATH|DATA_HEADER_WIDTH\" " + common.test_dir + "/*_config_tracker* " + common.test_dir + "/cfi_trackers/*_config_tracker*"
output = subprocess.getoutput([cmd + " 2>/dev/null"])
CFI_config_tx = dict()
CFI_config_rx = dict()
if (output != ""):
    for line in output.split('\n'):
        match = re.search("CFI_TOP_PATH\s+\S+\s+\d+\s+(\S+)", line)
        if (match):
            cfi_top_path = match.group(1)
            cfi_top_path = re.sub('.*\.', '', cfi_top_path)
            cfi_top_path = re.sub('_CFI', '', cfi_top_path)
        match = re.search("DATA_HEADER_WIDTH_(\w+)\s+\S+\s+\d+\s+.d(\d+)", line)
        if (match):
            tx_rx       = match.group(1)
            header_size = match.group(2)
            if (tx_rx == "TX"):
                CFI_config_tx[cfi_top_path] = int(header_size)
            if (tx_rx == "RX"):
                CFI_config_rx[cfi_top_path] = int(header_size)
else:   # no cfg files in emulation, create hardcoded list
    CFI_config_rx["IOC_LINK0"] = 88
    CFI_config_rx["IOC_IOCCE_LINK0"] = 88
    CFI_config_rx["IOC_IOCCE_LINK1"] = 88
    CFI_config_rx["IOC_IOCCE_LINK2"] = 88
    CFI_config_rx["SOC_DNC0"] = 88
    CFI_config_rx["SOC_DNC1"] = 88

    CFI_config_tx["SOUTH_INST_SAF_S_IOC_N0_L0"] = 88
    CFI_config_tx["SAF_S_IOC_N0_L0"] = 88

