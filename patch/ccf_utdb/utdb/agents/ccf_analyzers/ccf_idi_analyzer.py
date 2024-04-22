#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_idi_analyzer.py
#
# Owner:              asaffeld
# Creation Date:      12.2020
#
# ###############################################
#
# Description:
#   This file contain ccf idi anaylzer to analayze any utdb line for the coherency data base from idi and idi.c from cxl log traces
#################################################################################################
from agents.ccf_analyzers.ccf_coherency_analyzer import ccf_coherency_analyzer
from agents.ccf_common_base.ccf_common_base import ccf_idi_record_info
from agents.ccf_common_base.ccf_common_base import snoop_response, snoop_request
from val_utdb_report import VAL_UTDB_ERROR
from val_utdb_bint import bint
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

from agents.ccf_common_base.ccf_utils import CCF_UTILS


class ccf_idi_analyzer(ccf_coherency_analyzer):
    def __init__(self):
        self.configure()

    def is_record_valid(self,record):
        return ("idi" in record.SELECTOR or "cxl" in record.SELECTOR) and not self.is_not_valid_unit(record.UNIT) and not "asserted" in record.TID and not "-" in record.TID

    def is_not_valid_unit(self, record_unit):
        not_valid_unit = ["GT"]
        return any([True for unit in not_valid_unit if unit in record_unit])

    def get_record_info(self,record):
        self.idi_record_info = ccf_idi_record_info()
        self.idi_record_info.rec_time = record.TIME
        self.idi_record_info.rec_unit = record.UNIT
        self.idi_record_info.rec_lid = record.LID
        self.idi_record_info.rec_pid = record.PID
        self.idi_record_info.rec_tid = record.TID
        self.idi_record_info.hash = record.HASH
        self.idi_record_info.src    = self.get_source_target(record.SRC_TGT, 0)
        self.idi_record_info.target = self.get_source_target(record.SRC_TGT, 1)

        if "NA" not in record.PID:
            self.idi_record_info.rec_pid = record.PID
        self.idi_record_info.address = record.ADDRESS.lstrip('0').zfill(1)
        self.idi_record_info.rec_opcode = record.OPCODE
        self.idi_record_info.rec_idi_interface = record.TYPE
        self.idi_record_info.rec_logic_id = self.get_core_from_src_tgt(record.SRC_TGT)
        self.idi_record_info.rec_physical_id = self.get_core_from_src_tgt(record.SRC_TGT)#should be changed when we have slice_disable
        self.idi_record_info.rec_lpid = self.get_lpid(record.LID)

        if record.CQID != "-":
            self.idi_record_info.cqid = record.CQID
        if record.UQID != "-":
            self.idi_record_info.uqid = record.UQID
        if record.LPID != "-":
            self.idi_record_info.lpid = record.LPID

        if self.idi_record_info.is_c2u_req_if() and self.idi_record_info.is_core_unit():
            self.idi_record_info.cqid = record.CQID
            self.idi_record_info.rec_cache_near = self.get_cache_near(record.ATTRIBUTES)
            self.idi_record_info.rec_selfsnoop = self.get_selfsnoop(record.DATA)
            self.idi_record_info.rec_len = self.get_len(record.DATA)
            self.idi_record_info.non_temporal = self.get_nontemporal(record.DATA)
            self.idi_record_info.clos = self.get_clos(record.DATA)
        elif self.idi_record_info.is_go():
            self.idi_record_info.rec_go_type = self.get_go_type(record.ATTRIBUTES)
            self.idi_record_info.rec_pre = self.get_pre(record.ATTRIBUTES)
            self.idi_record_info.dbp_params = self.get_dbp(record.ATTRIBUTES)
        elif self.idi_record_info.is_c2u_data_if():
            self.idi_record_info.rec_bogus = self.get_bogus(record.ATTRIBUTES)
            self.idi_record_info.rec_byteen = self.get_byteen(record.ATTRIBUTES)
            self.idi_record_info.chunk = record.CHUNK
            self.idi_record_info.data =  record.DATA
        elif self.idi_record_info.is_u2c_data_if():
            self.idi_record_info.rec_pre = self.get_pre(record.ATTRIBUTES)
            self.idi_record_info.chunk = record.CHUNK
            self.idi_record_info.data =  record.DATA
        elif self.idi_record_info.is_u2c_rsp_if():
            self.idi_record_info.rec_pre = self.get_pre(record.ATTRIBUTES)
        elif self.idi_record_info.is_u2c_req_if():
            self.idi_record_info.data =  record.DATA

    def get_cache_near(self, idi_attribute):
        return self.get_misc_info_bin(idi_attribute, "cacheNear")

    def get_bogus(self, idi_attribute):
        return self.get_misc_info_bin(idi_attribute,"bogus")

    def get_pre(self, idi_attribute):
        return "0x" + self.get_field_from_misc(idi_attribute, "pre")

    def get_byteen(self, idi_attribute):
        return idi_attribute[7:15]

    def get_selfsnoop(self, idi_data):
        return self.get_misc_info_bin(idi_data,"SlfSnp")

    def get_len(self, idi_data):
        if "len=" in idi_data:
            return idi_data.split("len=")[1].split(" ")[0]
        else:
            return '0'
    def get_nontemporal(self, idi_data):
        return self.get_misc_info_bin(idi_data, "nontemp")

    def get_clos(self, idi_data):
        return str(int(self.get_field_from_misc(idi_data, "clos"), 16))

    def get_go_type(self, idi_attribute):
        return idi_attribute[6:11]

    def get_dbp(self, idi_attribute):
        return "0x" + self.get_field_from_misc(idi_attribute, "dbp")

    def get_lpid(self, lid):
        if "COR_EMU" in lid:
            return int(lid.split("_")[2].split("T")[1])
        else:
            return -1
    def get_source_target(self, src_tgt, is_target):
        temp = (src_tgt.split("/")[is_target])
        if "CORE" in temp:
            return temp.split("CORE")[1]
        if "CBO" in temp:
            return temp.split("CBO")[1]

    def get_core_from_src_tgt(self, src_tgt):
        part0 = (src_tgt.split("/")[0])
        part1 = (src_tgt.split("/")[1])
        if "CORE" in part0:
            temp =  int(part0.split("CORE")[1])
            return self.get_logical_id(temp)
        elif "CORE" in part1:
            temp = int(part1.split("CORE")[1])
            return self.get_logical_id(temp)
        VAL_UTDB_ERROR(time=self.idi_record_info.rec_time,
                           msg=("CORE number must provided. TID = " + self.idi_record_info.rec_tid \
                                + '\n and opcode = ' + self.idi_record_info.rec_opcode))

    def get_logical_id(self,phy_unit):
        xbar_id = phy_unit // CCF_COH_DEFINES.num_of_ccf_clusters
        log_id = CCF_UTILS.get_logical_id_by_physical_id(xbar_id) * CCF_COH_DEFINES.num_of_ccf_clusters + phy_unit%CCF_COH_DEFINES.num_of_ccf_clusters
        return log_id

    def does_snoop_registerd_in_the_flow(self, snoop_obj_list):
        return [index for index, snp in enumerate(snoop_obj_list) if self.idi_record_info.is_same_uri_lid(snp.uri_lid)]

    def create_flow_point(self, record):
        flow_point = self.idi_record_info
        return flow_point

    def update_ccf_flow(self,ccf_flow,ccf_flow_point):
        super().update_ccf_flow(ccf_flow, ccf_flow_point)
        if self.idi_record_info.is_c2u_req_if() and self.idi_record_info.is_core_unit() and ccf_flow.flow_origin is None:
            ccf_flow.opcode = self.idi_record_info.rec_opcode
            ccf_flow.cache_near = self.idi_record_info.rec_cache_near
            ccf_flow.selfsnoop = self.idi_record_info.rec_selfsnoop
            if ccf_flow.clos is None and self.idi_record_info.clos is not None:
                ccf_flow.clos = self.idi_record_info.clos
            ccf_flow.requestor_logic_id = self.idi_record_info.rec_logic_id
            ccf_flow.requestor_physical_id = self.idi_record_info.rec_physical_id
            ccf_flow.lpid = self.idi_record_info.rec_lpid
            ccf_flow.cbo_id_log = int(self.idi_record_info.target)#int(float(self.idi_record_info.hash))  #we are setting it also in CBO, but we need it for analayzers before it is accepted in cbo (monitor ref building)
            ccf_flow.address = self.idi_record_info.address
            ccf_flow.flow_origin = "IDI REQ"
            observer = bint(int(self.idi_record_info.rec_len, 16))[1]
            if (int(observer) == 1):
                ccf_flow.idi_dbpinfo = bint(int(self.idi_record_info.rec_len, 16))[4:2]
            else:
                ccf_flow.dead_dbp_from_idi = bint(int(self.idi_record_info.rec_len, 16))[4]


        elif self.idi_record_info.is_u2c_req_if() and self.idi_record_info.rec_opcode in ["DPTEV"]:
            ccf_flow.opcode = self.idi_record_info.rec_opcode
            ccf_flow.data = self.idi_record_info.data
            if "CCF_DPT" in self.idi_record_info.rec_tid:
                ccf_flow.flow_origin = "DPT REQ"
            else:
                VAL_UTDB_ERROR(time=self.idi_record_info.rec_time, msg=('IDI Analyzer recevied an unexpected U2C Request. TID = '+ self.idi_record_info.rec_tid\
                                                                    +' \n Unit = '+ self.idi_record_info.rec_unit \
                                                                    +'\n and opcode = '+self.idi_record_info.rec_opcode))


        elif self.idi_record_info.is_u2c_req_if() and self.idi_record_info.is_core_unit(): # and not self.idi_record_info.is_u2c_lock_or_unlock_req():
            ccf_flow.snoop_type = self.idi_record_info.rec_opcode
            snoop_request_obj = snoop_request()
            snoop_request_obj.snoop_req_opcode = self.idi_record_info.rec_opcode
            ccf_flow.snooped_cores.append("CORE_" + self.idi_record_info.target)
            snoop_request_obj.snoop_req_core = self.idi_record_info.target
            snoop_request_obj.time_on_idi_if = self.idi_record_info.rec_time
            ccf_flow.snoop_requests.append(snoop_request_obj)

        elif self.idi_record_info.is_u2c_rsp_if() and self.idi_record_info.is_core_unit():
            if self.idi_record_info.is_go():
                ccf_flow.go_type = self.idi_record_info.rec_go_type
                ccf_flow.idi_dbp_params = self.idi_record_info.dbp_params
            elif self.idi_record_info.is_go_wr_pull():
                ccf_flow.go_type = self.idi_record_info.rec_opcode
            elif self.idi_record_info.is_fast_go() or self.idi_record_info.is_fast_go_extcmp():
                ccf_flow.go_type = self.idi_record_info.rec_opcode



        elif self.idi_record_info.is_c2u_rsp_if() and self.idi_record_info.is_core_unit(): #and not self.idi_record_info.is_c2u_lock_or_unlock_rsp():
                snoop_index = self.does_snoop_registerd_in_the_flow(ccf_flow.snoop_responses)

                if len(snoop_index) > 1:
                    err_msg = "We didn't expect to have more match then one for snoop_index"
                    VAL_UTDB_ERROR(time=self.idi_record_info.rec_time, msg=err_msg)
                elif len(snoop_index) == 1:
                    ccf_flow.snoop_responses[snoop_index[0]].snoop_rsp_opcode = self.idi_record_info.rec_opcode
                    ccf_flow.snoop_responses[snoop_index[0]].snoop_rsp_core = self.idi_record_info.src
                    ccf_flow.snoop_responses[snoop_index[0]].time_on_idi_if = self.idi_record_info.rec_time
                    #ccf_flow.snoop_responses[snoop_index].uri_lid = self.idi_record_info.rec_lid
                else:
                    snoop_response_obj = snoop_response()
                    snoop_response_obj.snoop_rsp_opcode = self.idi_record_info.rec_opcode
                    snoop_response_obj.snoop_rsp_core = self.idi_record_info.src
                    snoop_response_obj.time_on_idi_if = self.idi_record_info.rec_time
                    snoop_response_obj.uri_lid = self.idi_record_info.rec_lid
                    snoop_response_obj.num_of_data_with_snoop_rsp = 0
                    ccf_flow.snoop_responses.append(snoop_response_obj)


        elif self.idi_record_info.is_c2u_data_if() and self.idi_record_info.is_core_unit():
            if self.idi_record_info.is_c2u_snoop_data_response():

                snoop_index = self.does_snoop_registerd_in_the_flow(ccf_flow.snoop_responses)

                if len(snoop_index) > 1:
                    err_msg = "We didn't expect to have more match then one for snoop_index"
                    VAL_UTDB_ERROR(time=self.idi_record_info.rec_time, msg=err_msg)
                elif len(snoop_index) == 1:
                    ccf_flow.snoop_responses[snoop_index[0]].num_of_data_with_snoop_rsp += 1
                    if ccf_flow.snoop_responses[snoop_index[0]].last_data_time_on_idi_if is None or ccf_flow.snoop_responses[snoop_index[0]].last_data_time_on_idi_if < self.idi_record_info.rec_time:
                        ccf_flow.snoop_responses[snoop_index[0]].last_data_time_on_idi_if = self.idi_record_info.rec_time
                else:
                    snoop_response_obj = snoop_response()
                    snoop_response_obj.num_of_data_with_snoop_rsp = 1
                    snoop_response_obj.uri_lid = self.idi_record_info.rec_lid
                    snoop_response_obj.last_data_time_on_idi_if = self.idi_record_info.rec_time
                    ccf_flow.snoop_responses.append(snoop_response_obj)

            else:
                ccf_flow.received_core_write_data += 1
                ccf_flow.core_flow_is_bogus = self.idi_record_info.rec_bogus == "1"


        #elif self.is_c2u_data_if(self.idi_line_info) and self.is_idp_unit(self.idi_line_info):
        #    ccf_flow.received_idp_write_data += 1
        #    ccf_flow.uncore_flow_is_bogus = self.idi_line_info.line_bogus

        elif self.idi_record_info.is_u2c_data_if() and self.idi_record_info.is_core_unit():
            ccf_flow.received_core_read_data += 1


