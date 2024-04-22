#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_analyzers.ccf_coherency_analyzer import ccf_coherency_analyzer
from agents.ccf_common_base.ccf_common_base import ccf_addr_entry
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils
from val_utdb_bint import bint

class ccf_cpipe_windows_analyzer(ccf_coherency_analyzer):
    def __init__(self):
        self.configure()
        self.ccf_cpipe_window_utils = ccf_cpipe_window_utils.get_pointer()
        self.rejects_list = ["RejectDuePaMatch", "RejectDueIRQSetMatchBlocked"]
        self.exclude_opcode_list = ["ClrMonitor", "Nop", "FlushReadSet", "Enqueue", "SpCyc"] #ClrMonitor is here since it's like Nop and no one will do reject for Nop and therefore no window is relevant for it.
        self.skip_uri_list = []

    def is_window_record_valid(self, record):
        status = True
        for event in self.rejects_list:
            if event in record.EVENT:
                status = False

        if record.REQ in self.exclude_opcode_list:
            self.skip_uri_list.append(record.URI_TID)

        return status and record.URI_TID not in self.skip_uri_list

    def is_reject_record_valid(self, record):
        events = record.EVENT.split(" ")
        return any([True for event in events if event in ["RejectDuePaMatch", "RejectDueIRQSetMatchBlocked"]])

    def update_ccf_addr_flow(self, record):
        addr_entry = ccf_addr_entry()
        addr_entry.time = record.TIME
        addr_entry.uri_lid = record.URI_LID
        addr_entry.uri_tid = record.URI_TID
        addr_entry.tor_id = record.TORID
        addr_entry.Occupancy = record.TOR_OCCUP
        if "-" not in record.URI_PID:
            addr_entry.uri_pid = record.URI_PID
        addr_entry.unit = record.UNIT
        addr_entry.full_address = record.ADDRESS
        int_addr = bint(int(str(record.ADDRESS),16))
        int_addr[5:0] = 0
        int_addr[51:41] = 0 #TODO: need to remove mktme bit according to the CCF_MKTME_WIDTH systeminit parameter and not hard coded to 11.
        aligned_addr = hex(int_addr)
        if "AllowSnoop=1" in record.MISC:
            addr_entry.AllowSnoop = 1
            addr_entry.record_type = "allowSnoop"
        if "AllowSnoop=0" in record.MISC:
            addr_entry.AllowSnoop = 0
            addr_entry.record_type = "allowSnoop"
        if "Promotion_window=1" in record.MISC:
            addr_entry.PromotionWindow = 1
            addr_entry.record_type = "allowPromotion"
        if "Promotion_window=0" in record.MISC:
            addr_entry.PromotionWindow = 0
            addr_entry.record_type = "allowPromotion"
        if "Promoting=1" in record.EVENT:
            addr_entry.Allocated = 1
            addr_entry.record_type = "promoted"
        if "TorIfaAllocate=1" in record.MISC:
            addr_entry.TorIfaAllocate= 1
            addr_entry.record_type = "TorIfaAllocation"
        if "TorIfaAllocate=0" in record.MISC:
            addr_entry.TorIfaAllocate= 0
            addr_entry.record_type = "TorIfaAllocation"
        if "Allocation=1" in record.MISC:
            addr_entry.Allocated = 1
            addr_entry.TorAllocate = 1
            addr_entry.record_type = "allocation"
            addr_entry.rec_opcode = record.REQ
            if (record.REQ in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes):
                addr_entry.addressless = aligned_addr
        if "Deallocation=1" in record.MISC:
            addr_entry.Allocated = 0
            addr_entry.TorAllocate = 0
            addr_entry.record_type = "allocation"
            addr_entry.rec_opcode = record.REQ
            if (record.REQ in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes):
                addr_entry.addressless = aligned_addr
        if aligned_addr not in self.ccf_cpipe_window_utils.ccf_addr_flows.keys():
            self.ccf_cpipe_window_utils.ccf_addr_flows[aligned_addr] = [addr_entry]
        else:
            self.ccf_cpipe_window_utils.ccf_addr_flows[aligned_addr].append(addr_entry)

    def add_reject_event_to_db(self, reject_name, record):
        if reject_name in record.EVENT:
            if record.URI_TID not in self.ccf_cpipe_window_utils.ccf_reject_accurate_times.keys():
                self.ccf_cpipe_window_utils.ccf_reject_accurate_times[record.URI_TID] = dict()
                self.ccf_cpipe_window_utils.ccf_reject_accurate_times[record.URI_TID][reject_name] = [{"TIME": record.TIME, "MonHit": record.MONHIT}]
            elif reject_name not in self.ccf_cpipe_window_utils.ccf_reject_accurate_times[record.URI_TID].keys():
                self.ccf_cpipe_window_utils.ccf_reject_accurate_times[record.URI_TID][reject_name] = [{"TIME": record.TIME, "MonHit": record.MONHIT}]
            else:
                self.ccf_cpipe_window_utils.ccf_reject_accurate_times[record.URI_TID][reject_name].append({"TIME": record.TIME, "MonHit": record.MONHIT})

    def update_reject_accurate_time_db(self, record):
        for reject in record.EVENT.split(" "):
            self.add_reject_event_to_db(reject, record)

    def analyze_record(self, record):
        if self.is_window_record_valid(record):
            self.update_ccf_addr_flow(record)
        elif self.is_reject_record_valid(record):
            self.update_reject_accurate_time_db(record)






