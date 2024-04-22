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
from agents.ccf_common_base.ccf_common_base import ccf_ufi_record_info
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from val_utdb_report import VAL_UTDB_ERROR

class ccf_ufi_analyzer(ccf_coherency_analyzer):
    def __init__(self):
        self.configure()
        self.valid_ufi_id_list = CCF_UTILS.get_ufi_vc_valid_ids()

    def is_record_valid(self, record):
        return (CCF_UTILS.get_ufi_name() in record.UNIT) and (int(record.UFI_ID) in self.valid_ufi_id_list)

    def get_pcls_field(self, misc):
        local_pcls = self.get_field_from_misc(misc, "pcls")

        if local_pcls is not None:
            return local_pcls.lstrip("0") or "0"
        else:
            return None


    def get_record_info(self, record):
        self.ufi_record_info = ccf_ufi_record_info()
        self.ufi_record_info.rec_time = record.TIME
        self.ufi_record_info.rec_unit = record.UNIT
        self.ufi_record_info.rec_lid = record.LID
        self.ufi_record_info.rec_tid = record.TID
        if "NA" not in record.PID:
            self.ufi_record_info.rec_pid = record.PID

        self.ufi_record_info.rec_opcode = record.OPCODE
        self.ufi_record_info.ufi_id = record.UFI_ID
        self.ufi_record_info.ifc_type = record.IFC_TYPE
        self.ufi_record_info.protocol = record.PROTOCOL
        self.ufi_record_info.channel = record.CHANNEL
        self.ufi_record_info.vc_id = record.VC_ID
        self.ufi_record_info.pkt_type = record.HEADER_TYPE
        self.ufi_record_info.address = record.ADDRESS
        self.ufi_record_info.address_parity = record.ADDRESS_PAR
        self.ufi_record_info.rtid = record.RTID
        self.ufi_record_info.htid = record.HTID
        self.ufi_record_info.crnid = record.CRNID
        self.ufi_record_info.cdnid = record.CDNID
        self.ufi_record_info.hdnid = record.HDNID
        self.ufi_record_info.hnid = record.HNID
        self.ufi_record_info.clos = record.CLOS
        self.ufi_record_info.tee = record.TEE
        self.ufi_record_info.pcls = record.PCLS
        self.ufi_record_info.memlock = record.MEMLOCK
        self.ufi_record_info.tsxabort = record.TSXABORT
        self.ufi_record_info.param_a = record.PARAM_A
        self.ufi_record_info.msg_type = record.MSG_TYPE
        self.ufi_record_info.sai = record.SAI
        self.ufi_record_info.low_address = record.LOW_ADDR
        self.ufi_record_info.length = record.LENGTH
        self.ufi_record_info.chunk = record.CHUNK
        self.ufi_record_info.data = record.PAYLOAD_DATA
        self.ufi_record_info.data_parity = record. PAYLOAD_PARITY
        self.ufi_record_info.poison = record.POISON

    def create_flow_point(self, record):
        flow_point = self.ufi_record_info
        return flow_point

    def is_this_first_trans_in_the_flow(self, ccf_flow):
        return ccf_flow.flow_origin is None

    # In case the flow is starting from CFI and not from IDI (INTs ,snoops and updateM)
    def first_transaction_in_flow_handler(self, ccf_flow, uxi_trans):
        ccf_flow.opcode = uxi_trans.rec_opcode
        ccf_flow.address = uxi_trans.address
        ccf_flow.flow_origin = "UXI {} flow".format(uxi_trans.rec_opcode)

    def uxi_snoop_response_handler(self):
        pass

    def uxi_write_handler(self, ccf_flow):
        if ccf_flow.ufi_uxi_wr_data is None:
            ccf_flow.ufi_uxi_wr_data = self.ufi_record_info.data
            #ccf_flow.dbpinfo = self.ufi_record_info.dbpinfo #TODO: meirlevy I didn't found this field in UXI excel need to check it
            ccf_flow.ufi_uxi_num_of_data_chunk = 1
        else:
            if self.ufi_record_info.chunk == "0":
                ccf_flow.ufi_uxi_wr_data = str(ccf_flow.ufi_uxi_wr_data) + " " + self.ufi_record_info.data
            else:
                ccf_flow.ufi_uxi_wr_data = self.ufi_record_info.data + " " + str(ccf_flow.ufi_uxi_wr_data)
            ccf_flow.ufi_uxi_num_of_data_chunk += 1

            # TODO: meirlevy I didn't found this field in UXI excel need to check it
            #if ccf_flow.dbpinfo is None:
            #    ccf_flow.dbpinfo = self.ufi_record_info.dbpinfo

    def uxi_read_handler(self, ccf_flow):
        if self.ufi_record_info.chunk == "0":
            ccf_flow.ufi_uxi_rd_data = ccf_flow.ufi_uxi_rd_data + " " + str(self.ufi_record_info.data)
        else:
            ccf_flow.ufi_uxi_rd_data = str(self.ufi_record_info.data) + " " + ccf_flow.ufi_uxi_rd_data
        ccf_flow.ufi_uxi_num_of_data_chunk += 1

        if ccf_flow.cfi_upi_data_pcls is None:
            ccf_flow.cfi_upi_data_pcls = self.ufi_record_info.pcls.lstrip("0") or "0"
        else:
            current_record_pcls = self.ufi_record_info.pcls.lstrip("0") or "0"
            if ccf_flow.cfi_upi_data_pcls != current_record_pcls:
                err_msg = "Val_Assert(ccf_cfi_analyzer): While collecting PCLS data we can see that we have two data chuncks with diffrent PCLS that shouldn't happen. TID- {}".format(
                    ccf_flow.uri['TID'])
                VAL_UTDB_ERROR(time=self.ufi_record_info.rec_time, msg=err_msg)

    #TODO: need to change and not save the completion as diffrent variable in the ccf_flow need to get it using function that iterate over the flow progress
    def uxi_cmp_handler(self, ccf_flow):
        if "CmpU" in self.ufi_record_info.rec_opcode:
            ccf_flow.cfi_or_ufi_uxi_cmpu = self.ufi_record_info.rec_opcode
        elif "CmpO" in self.ufi_record_info.rec_opcode:
            ccf_flow.ufi_uxi_cmpo = self.ufi_record_info.rec_opcode
        else:
            err_msg = "UFI Analyzer: got an unexpected U2C UXI cmp. TID = {}, cmp opcode = {}".format(self.ufi_record_info.rec_tid, self.ufi_record_info.rec_opcode)
            VAL_UTDB_ERROR(time=self.ufi_record_info.rec_time, msg=err_msg)

    def conflict_handler(self, current_record: ccf_ufi_record_info, ccf_flow):
        if current_record.is_uxi_reqfwdcnflt():
            ccf_flow.reqfwdcnflt_was_sent = True
        elif current_record.is_uxi_fwdcnflto():
            ccf_flow.got_fwdcnflto = True
            #ccf_flow.dbp_params = self.ufi_record_info.dbp_params #TODO: need to check if we have dbp params



    def update_ccf_flow(self, ccf_flow, ccf_flow_point):
        super().update_ccf_flow(ccf_flow, ccf_flow_point)

        if self.is_this_first_trans_in_the_flow(ccf_flow):
            self.first_transaction_in_flow_handler(ccf_flow,self.ufi_record_info)

        if self.ufi_record_info.is_uxi_snp_rsp():
            ccf_flow.santa_snoop_response = self.ufi_record_info.rec_opcode
            if self.ufi_record_info.is_uxi_snp_rsp_wb():
                self.uxi_write_handler(ccf_flow)

        if self.ufi_record_info.is_uxi_wb() or self.ufi_record_info.is_uxi_nc_write_opcode():
            self.uxi_write_handler(ccf_flow)

        if self.ufi_record_info.is_ufi_read_data() or self.ufi_record_info.is_uxi_nc_read_data_opcode():
            self.uxi_read_handler(ccf_flow)

        if self.ufi_record_info.is_uxi_cmp() or self.ufi_record_info.is_uxi_nc_cmp() or self.ufi_record_info.is_uxi_nc_retry():
            self.uxi_cmp_handler(ccf_flow)

        if self.ufi_record_info.is_conflict_related_opcode():
            self.conflict_handler(self.ufi_record_info, ccf_flow)




