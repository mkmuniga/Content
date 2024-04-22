#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_analyzers.ccf_coherency_analyzer import ccf_coherency_analyzer
from agents.ccf_common_base.ccf_common_base import ccf_cbo_record_info, pipe_pass_info, ccf_addr_entry, ccf_reject
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_monitor_agent import monitor_event
from val_utdb_report import VAL_UTDB_ERROR
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils

import re
import copy

class ccf_cbo_analyzer(ccf_coherency_analyzer):
    """CBO analyzer description:
       This file contain ccf cbo analyzer to analyze any UTDB line for the coherency data base from cbo TRKs
    """
    def __init__(self):
        self.cbo_update_record_info = None
        self.cbo_record_info = None
        self.cbo_record_info = None
        self.configure()
        self.ref_monitor_array = None
        self.update_lookup = False

        self.ccf_cpipe_window_utils = ccf_cpipe_window_utils.get_pointer()

    def is_record_valid(self,record):
        return "CPIPE" in record.UNIT and record.MISC != "-" and record.MISC != "TOR deallocated"

    def get_field_from_msg(self, msg, field_name):
        if field_name in msg:
            split = msg.split(" ")
            field_value = [e for e in split if field_name in e][0].split(":")
            return field_value[1]
        else:
            return None


    def get_sad_results_from_misc(self,misc):
        if "SAD results" in misc:
            split_misc = misc.split("SAD results: ", 1)[1]
            sad_results = split_misc.split(",", 3)[0]
            return sad_results
        else:
            return None

    def get_deaddbp_results_from_misc(self,misc):
        if "SAD results" in misc:
            split_misc = misc.split("SAD results: ", 1)[1]
            deaddbp_results = split_misc.split(",", 3)[2]
            if "notDead" in deaddbp_results:
                return 0
            elif "Dead" in deaddbp_results:
                return 1
            else:
                return None
        else:
            return None

    def get_free_data_way_results_from_misc(self,misc):
        if "SAD results" in misc or "Conflict LookUp" in misc:
            if "notFoundFreeDataWay" in misc:
                return 0
            elif "FoundFreeDataWay" in misc:
                return 1
            else:
                return None

    def get_response_table_row(self,msg):
        if "ResponseTableRow" in msg:
            return msg.split(": ")[1]

    def is_txn_accepted(self,misc):
        return "ACCEPTED" in misc

    def is_send_go(self, msg):
        return "C2P_AK_GO" in msg

    def get_llc_initial_state(self, misc):
        if "HIT" in misc:
            return ("LLC_" + misc.split("LLC_")[1][0])
        elif "MISS" in misc:
            return "LLC_I"
        elif "LLC SPECIAL" in misc:
            return ("LLC_" + misc.split("LLC_")[1][0])
        elif "Flusher" in misc:
            return ("LLC_" + misc.split("LLC_")[1][0])
        else:
            return None

    def get_llc_initial_cv(self, misc):
        if "HIT" in misc or ("LLC SPECIAL" in misc and "LLC_I" not in misc):
            sub_str = misc.split(" CV=")[1]
            cv = sub_str.split(" ")[0]
            cv_f = cv.zfill(CCF_COH_DEFINES.num_physical_cv_bits)
            return cv_f
        else:
            return None

    def get_llc_initial_map(self, misc):
        if "HIT" in misc or ("LLC SPECIAL" in misc and "LLC_I" not in misc):
            if "->" in misc:   #-> sign say that map is changing on the first pass and we want to filter that out
                map_str = misc.split("->")[0]
            else:                   #use the input string from misc_data
                map_str = misc
            if "SF_ENTRY" in map_str:
                return "SF_ENTRY"
            elif "DWAY" in map_str:
                split_str = map_str.split(" ")
                split2 = [string for string in split_str if "DWAY_" in string]
                return "DWAY_" + split2[0].split("DWAY_")[1]
            else:
                return None
        elif ("MISS" in misc) or ("LLC SPECIAL: LLC_I" in misc):
            return "SF_ENTRY"
        else:
            return None

    def is_reject_reasons(self, misc):
       return ("RejectDue" in misc) or ("RejectLateDue" in misc) or ("RejectNo" in misc) \
              or ("RejectRspDataMNC" in misc) or ("ForceReject" in misc)

    def is_txn_rejected(self, misc):
        return "REJECTED" in misc

    def find_all_rejected_reasons(self,misc):
        return re.findall(r'\bReject\w+', misc)

    def is_prefetch_promotion(self, misc):
        if "Prefetch Promoting" in misc:
            return True
        else:
            return None

    def is_prefetch_elimination(self, misc):
        if "Prefetch Elimination" in misc:
            return True
        else:
            return None

    def get_victim_tag_way(self, misc):
        if "Victim:" in misc:
            vic_str = misc.split("Victim:")[1]
            return vic_str.split(" ")[1].split("=")[1]
        else:
            return None

    def get_victim_state(self, misc):
        if "Victim:" in misc:
            vic_str = misc.split("Victim:")[1]
            return ("LLC_"+vic_str.split("LLC_")[1][0])
        else:
            return None

    def get_victim_map(self, misc):
        if "Victim:" in misc:
            vic_misc = misc.split("Victim:")[1].split(" ")
            for vic_str in vic_misc:
                if "DWAY_" in vic_str:
                    return vic_str.split("MAP_")[1]
                elif "SF_ENTRY" in vic_str:
                    return "SF_ENTRY"

            return None
        else:
            return None

    def get_victim_clean_evict(self, misc):
        if "Victim:" in misc:
            if "VictimCleanEvict=1" in misc:
                return "1"
            elif "VictimCleanEvict=0" in misc:
                return "0"
        return None

    def get_allocated_way(self, misc, way_type):
        way = None
        if "Allocate:" in misc and way_type in misc:
            split_misc = misc.split(" ")
            for item in split_misc:
                if way_type in item:
                    way = item.split("=")[1]
                    break

            if way_type == "DataWay" and way != "SF_ENTRY":
                return way.split("MAP_")[1]
            else:
                return way

    def is_string_in_misc(self, misc, true_str, false_str):
        if true_str in misc:
            return True
        elif false_str in misc:
            return False
        else:
            return None

    def is_tor_occupency_above_th(self, misc):
        if "TorOccupBelowTH" in misc:
            return False
        elif "TorOccupAboveTH" in misc:
            return True
        else:
            return None

    def is_go_s_counter_above_th(self, misc):
        if "GoSCntrBelowTH" in misc:
            return False
        elif "GoSCntrAboveTH" in misc:
            return True
        else:
            return None

    def get_clos_en_from_misc(self, misc):
        if ("EnCLOS" in misc) or ("DisCLOS" in misc):
            return "EnCLOS" in misc
        else:
            return None

    def get_half_id(self, misc):
        if "Req InPipe" in misc:
            if "HA1" in misc:
                return "1"
            else:
                return "0"
        else:
            return None


    def is_last_pass(self, misc):
        return "LastPass" in misc

    def is_conflict_lookup_override(self, record):
        return (record.OPCODE == "FwdCnfltO") and "Conflict LookUp" in record.MISC

    def update_ccf_addr_promoted_entry(self, cbo_update_record_info):
        ccf_addr_entry_i = ccf_addr_entry()
        ccf_addr_entry_i.Allocated = 1
        ccf_addr_entry_i.uri_tid = cbo_update_record_info.rec_tid
        ccf_addr_entry_i.uri_lid = cbo_update_record_info.rec_lid
        ccf_addr_entry_i.uri_pid = cbo_update_record_info.rec_pid
        ccf_addr_entry_i.unit = cbo_update_record_info.rec_unit
        ccf_addr_entry_i.tor_id = cbo_update_record_info.qid
        ccf_addr_entry_i.time = cbo_update_record_info.rec_time
        ccf_addr_entry_i.record_type = "promoted"
        self.ccf_cpipe_window_utils.add_entry_in_address_flow(cbo_update_record_info.address, ccf_addr_entry_i)

    def get_record_info(self, record):
        #if self.cbo_record_info is None:
        self.cbo_record_info = ccf_cbo_record_info()

        if self.cbo_update_record_info is None:
            self.cbo_update_record_info = ccf_cbo_record_info()

        self.cbo_record_info.rec_time = record.TIME
        self.cbo_record_info.rec_unit = record.UNIT
        self.cbo_record_info.rec_lid = record.LID
        self.cbo_record_info.rec_tid = record.TID
        if "-" not in record.PID:
            self.cbo_record_info.rec_pid = record.PID
        self.cbo_record_info.rec_opcode = record.OPCODE

        self.cbo_update_record_info.address = record.ADDRESS
        self.cbo_update_record_info.rec_opcode = record.OPCODE
        self.cbo_update_record_info.rec_unit = record.UNIT
        self.cbo_update_record_info.rec_time = record.TIME

        if self.is_conflict_lookup_override(record):
            self.update_lookup = True

        #checking if our transaction was rejected
        self.cbo_record_info.entry_rejected = self.is_txn_rejected(record.MISC)

        #Checking if our transaction is accepted so we will start ccf_flow_update
        self.cbo_record_info.entry_accepted = self.is_txn_accepted(record.MISC)

        self.cbo_record_info.send_go = self.is_send_go(record.MSG)
        if self.cbo_update_record_info.send_go is None and self.cbo_record_info.send_go:
            self.cbo_update_record_info.send_go = self.cbo_record_info.send_go

        #URI
        if self.cbo_update_record_info.rec_lid is None:
            self.cbo_update_record_info.rec_lid = self.cbo_record_info.rec_lid
        if self.cbo_update_record_info.rec_tid is None:
            self.cbo_update_record_info.rec_tid = self.cbo_record_info.rec_tid
        if self.cbo_update_record_info.rec_pid is None and self.cbo_record_info.rec_pid is not None:
            self.cbo_update_record_info.rec_pid = self.cbo_record_info.rec_pid

        #Updateing the cbo_update_record_info object
        if self.cbo_update_record_info.cid is None:
            self.cbo_update_record_info.cid = self.get_field_from_msg(record.MSG, "cid")
        if self.cbo_update_record_info.sqid is None:
            self.cbo_update_record_info.sqid = self.get_field_from_msg(record.MSG, "sqid")
        if self.cbo_update_record_info.htid is None:
            self.cbo_update_record_info.htid = self.get_field_from_msg(record.MSG, "htid")
        if self.cbo_update_record_info.qid is None:
            self.cbo_update_record_info.qid = record.QID
        if self.cbo_update_record_info.selfsnp is None:
            self.cbo_update_record_info.selfsnp = self.get_field_from_misc(record.MISC, "SelfSnp")
        if self.cbo_update_record_info.half_id is None:
            self.cbo_update_record_info.half_id = self.get_half_id(record.MISC)
        if self.cbo_update_record_info.monitor_hit is None:
            self.cbo_update_record_info.monitor_hit = self.get_field_from_misc(record.MISC, "MonHit")

        if self.cbo_update_record_info.allocated_tag_way is None:
            self.cbo_update_record_info.allocated_tag_way = self.get_allocated_way(record.MISC, "TagWay")
        if self.cbo_update_record_info.allocated_data_way is None:
            self.cbo_update_record_info.allocated_data_way = self.get_allocated_way(record.MISC, "DataWay")

        if self.cbo_update_record_info.data_vic_avail is None:
            self.cbo_update_record_info.data_vic_avail = self.get_field_from_misc(record.MISC, "DataVicAvail")
        if self.cbo_update_record_info.go_s_opt is None:
            self.cbo_update_record_info.go_s_opt = self.get_field_from_misc(record.MISC, "GO_S_OPT")
        if self.cbo_update_record_info.go_s_counter_above_th is None:
            self.cbo_update_record_info.go_s_counter_above_th = self.is_go_s_counter_above_th(record.MISC)
        if self.cbo_update_record_info.data_vulnerable is None:
            self.cbo_update_record_info.data_vulnerable = self.get_field_from_misc(record.MISC, "DataVul")

        if self.cbo_update_record_info.TorOccupAboveTH is None:
            self.cbo_update_record_info.TorOccupAboveTH = self.is_string_in_misc(record.MISC, true_str="TorOccupAboveTH", false_str="TorOccupBelowTH")

        if self.cbo_update_record_info.EvctClnThrottle is None:
            self.cbo_update_record_info.EvctClnThrottle = self.get_field_from_misc(record.MISC, "EvctClnThrottle")

        if self.cbo_update_record_info.reqcv is None:
            self.cbo_update_record_info.reqcv = self.get_field_from_misc(record.MISC,"ReqCV")
        if self.cbo_update_record_info.edram is None:
            self.cbo_update_record_info.edram = self.get_field_from_misc(record.MISC, "Edram")
        if self.cbo_update_record_info.sad_results is None:
             self.cbo_update_record_info.sad_results = self.get_sad_results_from_misc(record.MISC)
        if self.cbo_update_record_info.clos_en is None:
            self.cbo_update_record_info.clos_en = self.get_clos_en_from_misc(record.MISC)
        if self.cbo_update_record_info.response_table_row is None:
            self.cbo_update_record_info.response_table_row = self.get_response_table_row(record.MSG)

        if self.cbo_update_record_info.llc_initial_state is None:
            self.cbo_update_record_info.llc_initial_state = self.get_llc_initial_state(record.MISC)
        if self.cbo_update_record_info.llc_initial_cv is None:
            self.cbo_update_record_info.llc_initial_cv = self.get_llc_initial_cv(record.MISC)

        if self.cbo_update_record_info.llc_cv_shared is None:
            self.cbo_update_record_info.llc_cv_shared = self.get_field_from_misc(record.MISC, "CV_Shared")

        if self.cbo_update_record_info.llc_initial_map is None:
            self.cbo_update_record_info.llc_initial_map = self.get_llc_initial_map(record.MISC)

        if self.cbo_update_record_info.prefetch_promotion is None:
            self.cbo_update_record_info.prefetch_promotion = self.is_prefetch_promotion(record.MISC)
        if self.cbo_update_record_info.prefetch_elimination_flow is None:
            self.cbo_update_record_info.prefetch_elimination_flow = self.is_prefetch_elimination(record.MISC)
        if self.cbo_update_record_info.victim_tag_way is None:
            self.cbo_update_record_info.victim_tag_way = self.get_victim_tag_way(record.MISC)
        if self.cbo_update_record_info.victim_state is None:
            self.cbo_update_record_info.victim_state = self.get_victim_state(record.MISC)
        if self.cbo_update_record_info.victim_map is None:
            self.cbo_update_record_info.victim_map = self.get_victim_map(record.MISC)
        if self.cbo_update_record_info.victim_clean_evict is None:
            self.cbo_update_record_info.victim_clean_evict = self.get_victim_clean_evict(record.MISC)
        if self.cbo_update_record_info.clean_evict is None:
            self.cbo_update_record_info.clean_evict = self.get_field_from_misc(record.MISC, "CleanEvict")
        if self.cbo_update_record_info.cache_near is None:
            self.cbo_update_record_info.cache_near = self.get_field_from_misc(record.MISC, "CacheNear")
        if self.cbo_update_record_info.dead_dbp is None:
            self.cbo_update_record_info.dead_dbp = self.get_deaddbp_results_from_misc(record.MISC)
        if self.cbo_update_record_info.found_free_data_way is None:
            self.cbo_update_record_info.found_free_data_way = self.get_free_data_way_results_from_misc(record.MISC)
        if self.is_reject_reasons(record.MISC):
            reject_reason = self.find_all_rejected_reasons(record.MISC)
            for reason in reject_reason:
                new_reject = ccf_reject()
                new_reject.new_recect(record.TIME,
                                      reason,
                                      self.cbo_update_record_info.llc_initial_state,
                                      self.cbo_update_record_info.rec_opcode)
                self.cbo_record_info.entry_rejected_reasons.append(new_reject)

    def create_flow_point(self, record):
        flow_point = copy.copy(self.cbo_update_record_info)
        return flow_point

    def get_physical_cbo_id(self, rec_unit):
        return int(rec_unit.split("_")[1])

    def update_monitor_array(self, ccf_flow, entry_rejected):
        if ((ccf_flow.opcode == "MONITOR" and self.cbo_update_record_info.sad_results == "HOM") or (ccf_flow.opcode == "CLRMONITOR")) and (ccf_flow.uri["TID"] == self.cbo_record_info.rec_tid):
            new_event = monitor_event(ccf_flow.requestor_physical_id,
                                      ccf_flow.lpid,
                                      self.cbo_update_record_info.address,
                                      ccf_flow.opcode,
                                      self.cbo_update_record_info.half_id,
                                      entry_rejected)
            self.ref_monitor_array.add_event(ccf_flow.cbo_id_log, self.cbo_record_info.rec_time, new_event)

    def update_ccf_flow(self, ccf_flow, ccf_flow_point):
        if (ccf_flow.received_pipe_first_pass_info == 0) and (self.cbo_record_info.entry_accepted or self.cbo_record_info.entry_rejected): #monitor is set also when cpipe pass is rejected
            if ccf_flow.opcode is not None and "MONITOR" in ccf_flow.opcode:
                self.update_monitor_array(ccf_flow, self.cbo_record_info.entry_rejected)

        #When we are rejected due to "RejectDuePartialHit" we are creating Victim
        #In a regular Victim the information about the victim will be in the parent transaction (PID) as can seeing below.
        if (len(self.cbo_update_record_info.entry_rejected_reasons) == 1) and (self.cbo_update_record_info.entry_rejected_reasons[0].reject_reason == "RejectDuePartialHit"):
            ccf_flow.victim_flow[self.cbo_record_info.rec_time] = {"STATE": self.cbo_update_record_info.victim_state,
                                                                   "MAP": self.cbo_update_record_info.victim_map,
                                                                   "TAG_WAY": self.cbo_update_record_info.victim_tag_way}

        if self.cbo_record_info.entry_accepted:
            super().update_ccf_flow(ccf_flow, ccf_flow_point)

            if ccf_flow.first_accept_time is not None and self.cbo_update_record_info.send_go is not None:
                if self.cbo_update_record_info.send_go:
                    ccf_flow.go_accept_time = self.cbo_record_info.rec_time

            if ccf_flow.cbo_id_phys is None:
                ccf_flow.cbo_id_phys = self.get_physical_cbo_id(self.cbo_record_info.rec_unit) # TODO need to add -> *CCF_COH_DEFINES.num_of_ccf_clusters + self.si.ccf_cluster_id

            if ccf_flow.cbo_id_log is None:
                ccf_flow.cbo_id_log = CCF_UTILS.get_logical_id_by_physical_id(ccf_flow.cbo_id_phys)*CCF_COH_DEFINES.num_of_ccf_clusters + self.si.ccf_cluster_id

            if "--" not in self.cbo_record_info.rec_opcode:  # add arbcommand to cpipe arbcommand list even if this isn't the first pass
                pipe_pass_info_obj = pipe_pass_info()
                pipe_pass_info_obj.arbcommand_opcode = self.cbo_record_info.rec_opcode
                pipe_pass_info_obj.arbcommand_time = self.cbo_record_info.rec_time
                pipe_pass_info_obj.clean_evict_value = self.cbo_update_record_info.clean_evict
                pipe_pass_info_obj.monitor_hit_value = self.cbo_update_record_info.monitor_hit
                pipe_pass_info_obj.evict_clean_throttle = self.cbo_update_record_info.EvctClnThrottle
                if self.cbo_update_record_info.send_go:
                    pipe_pass_info_obj.sent_go_in_pipe_pass = True
                ccf_flow.pipe_passes_information.append(pipe_pass_info_obj)

            if ccf_flow.address is None and self.cbo_update_record_info.address is not None:
                    ccf_flow.address = self.cbo_update_record_info.address

            if ccf_flow.allocated_tag_way is None and self.cbo_update_record_info.allocated_tag_way is not None:
                ccf_flow.allocated_tag_way = self.cbo_update_record_info.allocated_tag_way
            if ccf_flow.allocated_data_way is None and self.cbo_update_record_info.allocated_data_way is not None:
                ccf_flow.allocated_data_way = self.cbo_update_record_info.allocated_data_way

            if (ccf_flow.TorOccupAboveTH is None or ccf_flow.is_victim()) and self.cbo_update_record_info.TorOccupAboveTH is not None:
                ccf_flow.TorOccupAboveTH = self.cbo_update_record_info.TorOccupAboveTH

            #if ccf_flow.EvctClnThrottle is None and self.cbo_update_record_info.EvctClnThrottle is not None:
            #    ccf_flow.EvctClnThrottle = self.cbo_update_record_info.EvctClnThrottle

            if ccf_flow.prefetch_elimination_flow is None and self.cbo_update_record_info.prefetch_elimination_flow is not None:
                ccf_flow.prefetch_elimination_flow = self.cbo_update_record_info.prefetch_elimination_flow

            #If we have snoop conflict we will do second lookup at "FwdCnfltO" pipe stage
            #In this case we will update our State Map and CV according to the new lookup
            if self.update_lookup:
                self.update_lookup = False
                if self.cbo_update_record_info.llc_initial_state is not None:
                    ccf_flow.initial_cache_state = self.cbo_update_record_info.llc_initial_state
                if self.cbo_update_record_info.llc_initial_map is not None:
                    ccf_flow.initial_map = self.cbo_update_record_info.llc_initial_map
                #if self.cbo_update_record_info.llc_initial_cv is not None:
                #We always want to override the CV even if it is to None in case of LLC_I (in case it's not VIC flows in VIC flows we are getting it from another place)
                if not ("VIC" in self.cbo_update_record_info.rec_lid):
                    ccf_flow.initial_cv = self.cbo_update_record_info.llc_initial_cv
                    ccf_flow.initial_cv_shared = self.cbo_update_record_info.llc_cv_shared
                if self.cbo_update_record_info.found_free_data_way is not None:
                    ccf_flow.found_free_data_way = self.cbo_update_record_info.found_free_data_way
            if self.cbo_update_record_info.response_table_row is not None:
                ccf_flow.response_table_row.append(self.cbo_update_record_info.response_table_row)

            if ccf_flow.received_pipe_first_pass_info is 0:
                ccf_flow.received_pipe_first_pass_info = 1  #lock pipe for future first pipe passes which cannot be

                if ("VIC" in self.cbo_update_record_info.rec_lid) or (self.cbo_update_record_info.rec_pid is not None and "VIC" in self.cbo_update_record_info.rec_pid):
                    ccf_flow.opcode = "VICTIM"
                    ccf_flow.flow_origin = "CBo Victim Flow"
                    if ccf_flow.sad_results is None:
                        ccf_flow.sad_results = "HOM"
                if ("PMA" in self.cbo_update_record_info.rec_lid):
                    ccf_flow.flow_origin = "CBo FlushReadSet Flow"
                    if ("FlushReadSet" == self.cbo_record_info.rec_opcode):
                        ccf_flow.opcode = "FLUSHER"
                    if ("WbInvd"  == self.cbo_record_info.rec_opcode):
                        ccf_flow.opcode = "LLCWBINV"

                if ccf_flow.cbo_tor_qid is None and self.cbo_update_record_info.qid is not None:
                    ccf_flow.cbo_tor_qid = self.cbo_update_record_info.qid

                if ccf_flow.sad_results is None and self.cbo_update_record_info.sad_results is not None:
                    ccf_flow.sad_results = self.cbo_update_record_info.sad_results
                    if ccf_flow.is_flow_origin_uxi_snp():
                        ccf_flow.sad_results = "HOM"
                if ccf_flow.clos_en is None and self.cbo_update_record_info.clos_en is not None:
                    ccf_flow.clos_en = self.cbo_update_record_info.clos_en
                if ccf_flow.initial_cache_state is None and self.cbo_update_record_info.llc_initial_state is not None:
                    ccf_flow.initial_cache_state = self.cbo_update_record_info.llc_initial_state

                if ccf_flow.initial_map is None and self.cbo_update_record_info.llc_initial_map is not None:
                    ccf_flow.initial_map = self.cbo_update_record_info.llc_initial_map

                if ccf_flow.initial_cv is None and self.cbo_update_record_info.llc_initial_cv is not None:
                    ccf_flow.initial_cv = self.cbo_update_record_info.llc_initial_cv

                if ccf_flow.initial_cv_shared is None and self.cbo_update_record_info.llc_cv_shared:
                    ccf_flow.initial_cv_shared = self.cbo_update_record_info.llc_cv_shared


                #When Victim is part of the flow and not as a result of partial hit.
                if (self.cbo_update_record_info.victim_tag_way is not None) or (self.cbo_update_record_info.victim_state is not None) or (self.cbo_update_record_info.victim_map is not None):
                    ccf_flow.victim_flow[self.cbo_record_info.rec_time] = {"STATE": self.cbo_update_record_info.victim_state,
                                                                           "MAP": self.cbo_update_record_info.victim_map,
                                                                           "TAG_WAY": self.cbo_update_record_info.victim_tag_way}

                #if ccf_flow.victim_tag_way is None and self.cbo_update_record_info.victim_tag_way is not None:
                #    ccf_flow.victim_tag_way = self.cbo_update_record_info.victim_tag_way
                #if ccf_flow.victim_state is None and self.cbo_update_record_info.victim_state is not None:
                #    ccf_flow.victim_state = self.cbo_update_record_info.victim_state
                #if ccf_flow.victim_map is None and self.cbo_update_record_info.victim_map is not None:
                #    ccf_flow.victim_map = self.cbo_update_record_info.victim_map

                if ccf_flow.victim_clean_evict is None and self.cbo_update_record_info.victim_clean_evict is not None:
                    ccf_flow.victim_clean_evict = self.cbo_update_record_info.victim_clean_evict

                #allowing override of CN from 0 to 1 in CBO - based on YenMSR - In some cases the CBo will override the CacheNear field to 1
                if ccf_flow.cache_near is 0 and self.cbo_update_record_info.cache_near is 1:
                    ccf_flow.cache_near = 1
                if ccf_flow.data_ways_available is None and self.cbo_update_record_info.data_vic_avail is not None:
                    ccf_flow.data_ways_available = self.cbo_update_record_info.data_vic_avail
                if ccf_flow.go_s_opt is None and self.cbo_update_record_info.go_s_opt is not None:
                    ccf_flow.go_s_opt = self.cbo_update_record_info.go_s_opt
                if ccf_flow.go_s_counter_above_th is None and self.cbo_update_record_info.go_s_counter_above_th is not None:
                    ccf_flow.go_s_counter_above_th = self.cbo_update_record_info.go_s_counter_above_th
                if ccf_flow.data_vulnerable is None and self.cbo_update_record_info.data_vulnerable is not None:
                    ccf_flow.data_vulnerable = self.cbo_update_record_info.data_vulnerable

                if ccf_flow.dead_dbp is None and self.cbo_update_record_info.dead_dbp is not None:
                    ccf_flow.dead_dbp = self.cbo_update_record_info.dead_dbp
                if ccf_flow.found_free_data_way is None and self.cbo_update_record_info.found_free_data_way is not None:
                    ccf_flow.found_free_data_way = self.cbo_update_record_info.found_free_data_way

                if "PMA" in self.cbo_update_record_info.rec_lid or "VIC" in self.cbo_update_record_info.rec_lid or (self.cbo_update_record_info.rec_pid is not None and "VIC" in self.cbo_update_record_info.rec_pid):
                    if len(ccf_flow.pipe_passes_information) is 0:
                        if ccf_flow.opcode is None:
                            ccf_flow.opcode = self.cbo_update_record_info.rec_opcode
                        ccf_flow.flow_origin = "CBO REQ"

                    if ("VIC" in self.cbo_update_record_info.rec_lid or (self.cbo_update_record_info.rec_pid is not None and "VIC" in self.cbo_update_record_info.rec_pid)):
                        victim_info = self.ccf_flows[self.cbo_update_record_info.rec_pid].get_victim_flow_info(self.cbo_record_info.rec_time)
                        ccf_flow.initial_cache_state = victim_info["STATE"]
                        ccf_flow.initial_map = victim_info["MAP"]

                if ccf_flow.accept_time is None:
                    ccf_flow.accept_time = self.cbo_record_info.rec_time
                if ccf_flow.first_accept_time is None:
                    ccf_flow.first_accept_time = self.cbo_record_info.rec_time
                    ccf_flow.go_accept_time = self.cbo_record_info.rec_time
            self.cbo_update_record_info.reset()


        elif self.cbo_record_info.entry_rejected:
            ccf_flow.number_of_rejects += 1

            for reject_res in self.cbo_update_record_info.entry_rejected_reasons:
                if reject_res not in ccf_flow.rejected_reasons:
                    reject_res.is_ismq = (ccf_flow.received_pipe_first_pass_info == 1)
                    ccf_flow.rejected_reasons.append(reject_res)

            #Promotion is done with Reject on the pipe
            if ccf_flow.flow_promoted is None and self.cbo_update_record_info.prefetch_promotion is not None:
                ccf_flow.flow_promoted = self.cbo_update_record_info.prefetch_promotion
                ccf_flow.flow_promoted_time = self.ccf_cpipe_window_utils.get_promotion_time_for_address_and_uri(self.cbo_update_record_info.address, self.cbo_update_record_info.rec_tid)
                ccf_flow.first_accept_time = self.cbo_record_info.rec_time #When we are doing promotion the actual accepted time in the pipe is at the time of the promotion.
                if self.cbo_update_record_info.prefetch_promotion:
                    ccf_flow.TorOccupAboveTH = self.cbo_update_record_info.TorOccupAboveTH

                if ccf_flow.flow_promoted_time is None:
                    err_msg = "Val_Assert: The follow was marked as promoted but we couldn't found any promotion event in ccf_cpipe_window. URI: {}".format(ccf_flow.uri['TID'])
                    VAL_UTDB_ERROR(time=ccf_flow.initial_time_stamp, msg=err_msg)

                #Add the promotion pass to the flow
                pipe_pass_info_obj = pipe_pass_info()
                pipe_pass_info_obj.arbcommand_opcode = self.cbo_record_info.rec_opcode
                pipe_pass_info_obj.arbcommand_time = self.cbo_record_info.rec_time
                pipe_pass_info_obj.clean_evict_value = self.cbo_update_record_info.clean_evict
                pipe_pass_info_obj.monitor_hit_value = self.cbo_update_record_info.monitor_hit
                ccf_flow.pipe_passes_information.append(pipe_pass_info_obj)

            self.cbo_update_record_info.reset()

        else:
            if self.cbo_record_info.entry_rejected_reasons:
                for reject_res in self.cbo_record_info.entry_rejected_reasons:
                    if reject_res not in ccf_flow.rejected_reasons:
                        reject_res.is_ismq = (ccf_flow.received_pipe_first_pass_info == 1)
                        self.cbo_update_record_info.entry_rejected_reasons.append(reject_res)


    def is_allocate_record(self, record):
        return "ACCEPTED" in record.MISC and "FirstPass" in record.MISC
    def is_deallocate_record (self, record):
        return "TOR deallocated" in record.MISC




