#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_analyzer.py
#
# Owner:              asaffeld
# Creation Date:      12.2020
#
# ###############################################
#
# Description:
#   This file contain ccf base anaylzer to analayze any utdb line for the coherency data base
#################################################################################################
import os,sys,inspect
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_common_base.ccf_common_base import ccf_flow_point
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_common_base_class import ccf_base_analyzer
from agents.ccf_common_base.coh_global import COH_GLOBAL


class ccf_coherency_analyzer(ccf_base_analyzer):

    def update_ccf_flow(self,ccf_flow, flow_point):
        super().update_ccf_flow(ccf_flow, flow_point)
        if flow_point is not None:
            ccf_flow.add_flow_point_to_flow_progress(flow_point)
        else:
            pass

    def create_flow_point(self, record):
        flow_point = ccf_flow_point()
        flow_point.unit = record.UNIT
        flow_point.time = record.TIME
        flow_point.interface = record.UNIT
        return flow_point

    def get_ccf_flow(self,record):
        super().get_ccf_flow(record)
        if "VIC" in record.LID:
            if not record.LID in self.ccf_flows:
                self.ccf_flows[record.LID] = ccf_flow()
                self.ccf_flows[record.LID].uri["TID"] = record.TID
                self.ccf_flows[record.LID].uri["PID"] = record.PID
                self.ccf_flows[record.LID].uri["LID"] = record.LID
                self.ccf_flows[record.LID].flow_key = record.LID
                self.ccf_flows[record.LID].initial_time_stamp = record.TIME

            return self.ccf_flows[record.LID]
        elif "VIC" in record.PID:
            if not record.PID in self.ccf_flows:
                self.ccf_flows[record.PID] = ccf_flow()
                self.ccf_flows[record.PID].uri["TID"] = record.TID
                self.ccf_flows[record.PID].uri["PID"] = record.PID
                self.ccf_flows[record.PID].uri["LID"] = record.LID
                self.ccf_flows[record.PID].flow_key = record.PID
                self.ccf_flows[record.PID].initial_time_stamp = record.TIME

            return self.ccf_flows[record.PID]
        # For SoC when HBO send snoop for CCF on the same flow CCF is the initiator of the flow.
        #In this case we will want to consider this HBO snoop as any other snoop flow separated from the original flow
        elif "HBO_SNP" in record.LID:
            if not record.LID in self.ccf_flows:
                self.ccf_flows[record.LID] = ccf_flow()
                self.ccf_flows[record.LID].uri["TID"] = record.TID
                self.ccf_flows[record.LID].uri["PID"] = record.PID
                self.ccf_flows[record.LID].uri["LID"] = record.LID
                self.ccf_flows[record.LID].flow_key = record.LID
                self.ccf_flows[record.LID].initial_time_stamp = record.TIME

            return self.ccf_flows[record.LID]
        elif "HBO_SNP" in record.PID:
            #If we got HBO_SNP on PID we are for sure saw this transaction in CFI first
            if record.PID in self.ccf_flows:
                return self.ccf_flows[record.PID]
            else:
                VAL_UTDB_ERROR(time=0, msg="Undefined case for PID URI: {}".format(record.PID))
        elif "SNP" in record.LID and "VIC" in record.PID:
            if not record.PID in self.ccf_flows:
                self.ccf_flows[record.PID] = ccf_flow()
                self.ccf_flows[record.PID].uri["TID"] = record.TID
                self.ccf_flows[record.PID].uri["PID"] = record.PID
                self.ccf_flows[record.PID].uri["LID"] = record.LID
                self.ccf_flows[record.PID].flow_key = record.PID
                self.ccf_flows[record.PID].initial_time_stamp = record.TIME

            return self.ccf_flows[record.PID]

        elif not record.TID in self.ccf_flows:
            self.ccf_flows[record.TID] = ccf_flow()
            self.ccf_flows[record.TID].uri["TID"] = record.TID
            self.ccf_flows[record.TID].uri["LID"] = record.LID
            self.ccf_flows[record.TID].uri["PID"] = record.PID
            self.ccf_flows[record.TID].flow_key = record.TID
            self.ccf_flows[record.TID].initial_time_stamp = record.TIME

        return self.ccf_flows[record.TID]

    def analyze_record(self,record):
        if self.is_record_valid(record):
            if record.TIME >= COH_GLOBAL.global_vars["START_OF_TEST"] and record.TIME < COH_GLOBAL.global_vars["END_OF_TEST"]:
                self.get_record_info(record)
                flow_point = self.create_flow_point(record)
                ccf_flow = self.get_ccf_flow(record)
                self.update_ccf_flow(ccf_flow, flow_point)

    #This function assumes that if a string is in a tracker/logdb it has an "=" sign and value following it for example SelfSnp=1 or CacheNear=0 etc.
    #checks for binary values only
    def get_misc_info_bin(self,misc_data,info):
        if info in misc_data:
            if (info+"=1") in misc_data:
                return "1"
            else:
                return "0"
        else:
            return None

    def get_field_from_misc(self, misc, field_name):
        if field_name in misc:
            field_name.strip()
            split = misc.split(" ")
            field_value = [e for e in split if field_name in e][0].split("=")
            return field_value[1]
        else:
            return None
