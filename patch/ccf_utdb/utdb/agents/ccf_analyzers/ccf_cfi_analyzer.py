#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_cfi_analyzer.py
#
# Owner:              kmoses1
# Creation Date:      02.2021
#
# ###############################################
#
# Description:
#   This file contain ccf llc anaylzer to analayze any utdb line for the coherency data base from llc TRKs
#################################################################################################
from agents.ccf_analyzers.ccf_coherency_analyzer import ccf_coherency_analyzer
from agents.ccf_common_base.ccf_common_base import ccf_cfi_record_info
from val_utdb_report import VAL_UTDB_ERROR

class ccf_cfi_analyzer(ccf_coherency_analyzer):

    def is_record_valid(self, record):
        return ("SANTA" in record.UNIT) or ("SOC_CCF_LINK" in record.UNIT)

    def get_pcls_field(self, misc):
        local_pcls = self.get_field_from_misc(misc, "pcls")

        if local_pcls is not None:
            return local_pcls.lstrip("0") or "0"
        else:
            return None


    def get_record_info(self, record):
        self.cfi_record_info = ccf_cfi_record_info()
        self.cfi_record_info.rec_time = record.TIME
        self.cfi_record_info.rec_unit = record.UNIT
        self.cfi_record_info.rec_lid = record.LID
        self.cfi_record_info.rec_tid = record.TID
        if "NA" not in record.PID:
            self.cfi_record_info.rec_pid = record.PID

        self.cfi_record_info.interface = record.INTERFACE
        self.cfi_record_info.msg_class = record.MSG_CLASS
        self.cfi_record_info.protocol_id = record.PROTOCOL_ID
        self.cfi_record_info.rec_opcode = record.OPCODE
        self.cfi_record_info.pkt_type = record.PKT_TYPE
        self.cfi_record_info.vc_id = record.VC_ID
        self.cfi_record_info.rctrl = record.RCTRL
        self.cfi_record_info.dst_id = record.DSTID
        self.cfi_record_info.rsp_id = record.RSPID
        self.cfi_record_info.address = record.ADDRESS.lstrip('0').zfill(1)
        self.cfi_record_info.rtid = record.RTID
        self.cfi_record_info.htid = record.HTID
        self.cfi_record_info.address_parity = record.PAR
        self.cfi_record_info.chunk = record.CHUNK
        if self.cfi_record_info.is_upi_rd_data() or self.cfi_record_info.is_cfi_wr_data() or self.cfi_record_info.is_upi_c_c2u_data() or self.cfi_record_info.is_upi_c_u2c_data() or self.cfi_record_info.is_upi_nc_write_opcode():
            self.cfi_record_info.data = record.DATA_3 + record.DATA_2 + record.DATA_1 + record.DATA_0
        self.cfi_record_info.paramA = self.get_field_from_misc(record.MISC, "paramA")
        self.cfi_record_info.msg_type = self.get_field_from_misc(record.MISC, "msg_type")
        self.cfi_record_info.pcls = self.get_pcls_field(record.MISC)
        if self.cfi_record_info.dbpinfo is None:
            self.cfi_record_info.dbpinfo = self.get_field_from_misc(record.MISC, "dbpinfo")
        if self.cfi_record_info.dbp_params is None:
            self.cfi_record_info.dbp_params = self.get_field_from_misc(record.MISC, "dbp_params")
        self.cfi_record_info.cachefar = self.get_field_from_misc(record.MISC, "CF")

        self.cfi_record_info.traffic_class = self.get_field_from_misc(record.MISC, "tc")
        self.cfi_record_info.is_wb = self.get_field_from_misc(record.MISC, "isWB")
        self.cfi_record_info.core_id = self.get_field_from_misc(record.MISC, "core_id")
        self.cfi_record_info.trace_pkt = record.TRACE_PKT
        self.cfi_record_info.eop = record.EOP
        self.cfi_record_info.length = self.get_field_from_misc(record.MISC, "length")


    def create_flow_point(self, record):
        flow_point = self.cfi_record_info
        return flow_point

    def update_ccf_flow(self, ccf_flow, ccf_flow_point):
        super().update_ccf_flow(ccf_flow, ccf_flow_point)
        ccf_flow.santa_id = self.cfi_record_info.rec_unit
        ccf_flow.cfi_protocol = self.cfi_record_info.protocol_id
        if "UXI" in ccf_flow.cfi_protocol:
            #In case the flow is starting from CFI and not from IDI (INTs and snoops)
            if ccf_flow.flow_origin is None:
                ccf_flow.opcode = self.cfi_record_info.rec_opcode
                ccf_flow.address = self.cfi_record_info.address
                ccf_flow.flow_origin = "CFI " + self.cfi_record_info.rec_opcode +" flow"
            if self.cfi_record_info.is_upi_snp_rsp():
                ccf_flow.santa_snoop_response = self.cfi_record_info.rec_opcode
            if self.cfi_record_info.is_cfi_wr_data() or self.cfi_record_info.is_upi_wb() or self.cfi_record_info.is_upi_snp_rsp_wb() or self.cfi_record_info.is_upi_nc_write_opcode():
                if ccf_flow.cfi_upi_wr_data is None:
                    ccf_flow.cfi_upi_wr_data = self.cfi_record_info.data
                    ccf_flow.dbpinfo = self.cfi_record_info.dbpinfo
                    ccf_flow.cfi_upi_num_of_data_chunk = 1
                else:
                    if self.cfi_record_info.chunk == "0":
                        ccf_flow.cfi_upi_wr_data = str(ccf_flow.cfi_upi_wr_data) + " " + self.cfi_record_info.data
                    else:
                        ccf_flow.cfi_upi_wr_data = self.cfi_record_info.data + " " + str(ccf_flow.cfi_upi_wr_data)
                    ccf_flow.cfi_upi_num_of_data_chunk += 1
                    if ccf_flow.dbpinfo is None:
                        ccf_flow.dbpinfo = self.cfi_record_info.dbpinfo

            elif self.cfi_record_info.is_upi_rd_data() or self.cfi_record_info.is_upi_nc_read_data_opcode():
                if self.cfi_record_info.chunk == "0":
                    ccf_flow.cfi_upi_rd_data = ccf_flow.cfi_upi_rd_data + " " + str(self.cfi_record_info.data)
                else:
                    ccf_flow.cfi_upi_rd_data = str(self.cfi_record_info.data) + " " + ccf_flow.cfi_upi_rd_data
                ccf_flow.cfi_upi_num_of_data_chunk += 1

                if ccf_flow.cfi_upi_data_pcls is None:
                    ccf_flow.cfi_upi_data_pcls = self.cfi_record_info.pcls.lstrip("0") or "0"
                else:
                    current_record_pcls = self.cfi_record_info.pcls.lstrip("0") or "0"
                    if ccf_flow.cfi_upi_data_pcls != current_record_pcls:
                        err_msg = "Val_Assert(ccf_cfi_analyzer): While collecting PCLS data we can see that we have two data chuncks with diffrent PCLS that shouldn't happen. TID- {}".format(ccf_flow.uri['TID'])
                        VAL_UTDB_ERROR(time=self.cfi_record_info.rec_time, msg=err_msg)

            elif self.cfi_record_info.is_upi_c_cmp() or self.cfi_record_info.is_upi_nc_cmp() or self.cfi_record_info.is_upi_nc_retry():
                self.update_cmp(ccf_flow)

            elif self.cfi_record_info.is_upi_c_reqfwdcnflt():
                ccf_flow.reqfwdcnflt_was_sent = True
            elif self.cfi_record_info.is_upi_c_fwdcnflto():
                ccf_flow.got_fwdcnflto = True
                ccf_flow.dbp_params = self.cfi_record_info.dbp_params

    def __init__(self):
        self.configure()

    def update_cmp(self, ccf_flow):
        if "CmpU" in self.cfi_record_info.rec_opcode:
            ccf_flow.cfi_or_ufi_uxi_cmpu = self.cfi_record_info.rec_opcode
        elif "NcRetry" in self.cfi_record_info.rec_opcode:
            ccf_flow.cfi_upi_retry = self.cfi_record_info.rec_opcode
        else:
            err_msg = "CFI Analyzer: recived an unexpected U2C UPI cmp. TID = {}, cmp opcode = {}".format(self.cfi_record_info.rec_tid, self.cfi_record_info.rec_opcode)
            VAL_UTDB_ERROR(time=self.cfi_record_info.rec_time, msg=err_msg)




