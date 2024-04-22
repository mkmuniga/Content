#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_common_base.py
#
# Owner:              kmoses1
# Creation Date:      07.2021
#
# ###############################################
#
# Description:
#   This file includes all monitor array classes that define monitor array reference model
#
#################################################################################################
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from val_utdb_components import val_utdb_object
from val_utdb_report import VAL_UTDB_ERROR
from val_utdb_bint import bint
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
import copy

from agents.ccf_common_base.ccf_common_base_class import ccf_base_component


class ref_monitor_array(ccf_base_component):

    def config(self, num_of_cbo):
        for i in range(num_of_cbo):
            self.ref_monitor_per_cbo_db[i] = dict()

    def add_event(self, cbo_id, time, object):
        self.ref_monitor_per_cbo_db[cbo_id][time] = object

    def sort_dict(self, dct):
        kys = dct.keys()
        kys = sorted(kys)
        from collections import OrderedDict
        d = OrderedDict()
        for x in kys:
            for k, v in dct.items():
                if (k == x):
                    d[x] = v
        return d

    def get_current_monitor_array(self, time, cbo_id):
        relevant_snapshot_time = 0
        for array_time in self.ref_monitor_per_cbo_db[cbo_id].keys():
            if array_time < time:
                relevant_snapshot_time = array_time
        if relevant_snapshot_time == 0:
            return None
        return self.ref_monitor_per_cbo_db[cbo_id][relevant_snapshot_time]

    def sort_db(self):
        for i in self.ref_monitor_per_cbo_db:
            self.ref_monitor_per_cbo_db[i] = self.sort_dict(self.ref_monitor_per_cbo_db[i])

    def arrange_db(self):
        for cbo in self.ref_monitor_per_cbo_db:
            last_monitor_time = 0
            for time in self.ref_monitor_per_cbo_db[cbo].keys():
                if (last_monitor_time == 0):
                    new_snapshot = monitor_array_snapshot()
                    new_snapshot.create()
                else:
                    new_snapshot = self.ref_monitor_per_cbo_db[cbo][last_monitor_time].clone()

                new_snapshot.time = time

                if ("MONITOR" == self.ref_monitor_per_cbo_db[cbo][time].opcode):
                    new_snapshot.update_monitor_array_snapshot(self.ref_monitor_per_cbo_db[cbo][time].core, self.ref_monitor_per_cbo_db[cbo][time].lpid, self.ref_monitor_per_cbo_db[cbo][time].address, self.ref_monitor_per_cbo_db[cbo][time].set_monitor_during_reject)
                elif ("CLRMONITOR" == self.ref_monitor_per_cbo_db[cbo][time].opcode):
                    new_snapshot.clear_monitor(self.ref_monitor_per_cbo_db[cbo][time].core, self.ref_monitor_per_cbo_db[cbo][time].lpid)
                self.ref_monitor_per_cbo_db[cbo][time] = new_snapshot
                last_monitor_time = time

class monitor_entry(val_utdb_object):
    def __init__(self):
        self.core = None
        self.lpid = None
        self.set_monitor_during_reject = None


    def create(self, core, lpid, set_monitor_during_reject):
        self.core = core
        self.lpid = lpid
        self.set_monitor_during_reject = set_monitor_during_reject



class monitor_event(val_utdb_object):
    def __init__(self, core=None, lpid=None, addr=None, opcode=None, half=None, set_monitor_during_reject=False):
        self.core = core
        self.lpid = lpid
        self.address = addr
        self.opcode = opcode
        self.half = half
        self.set_monitor_during_reject = set_monitor_during_reject

class monitor_array_snapshot(val_utdb_object):
    def __init__(self):
        self.time = None
        self.entries = dict() # dictionary of {address: monitor_entry}
        self.overflow_array = []

    def create(self):
        pass

    def clone(self):
        new_monitor_entries = monitor_array_snapshot()
        for addr in self.entries.keys():
            new_monitor_entries.entries[addr] = copy.deepcopy(self.entries[addr])
        for i in range(len(self.overflow_array)):
            new_monitor_entries.overflow_array.append(self.overflow_array[i])
        return new_monitor_entries


    def update_monitor_array_snapshot(self, core, lpid, address, set_monitor_during_reject):
        monitor_was_updated = 0
        self.clear_monitor(core, lpid)
        cl_align_address = CCF_UTILS.get_cl_align_address(address)
        # replace exist monitor in the same cbo_id,core, lpid
        for addr in self.entries.keys():
            if (addr == cl_align_address):
                new_entry = monitor_entry()
                new_entry.create(core, lpid, set_monitor_during_reject)
                self.entries[addr].append(new_entry)
                monitor_was_updated = 1
        if not monitor_was_updated:
            if len(self.entries) < CCF_COH_DEFINES.num_of_monitor_entries:
                new_entry = monitor_entry()
                new_entry.create(core, lpid, set_monitor_during_reject)
                self.entries[cl_align_address] = [new_entry]
            else:
                new_entry = monitor_entry()
                new_entry.create(core, lpid, set_monitor_during_reject)
                self.overflow_array.append(new_entry)
                print("kmoses1: add monitor to cbo " + str(core)+ " thread " + str(lpid) +" with address " + address)

    def clear_monitor(self, core, lpid):
        monitor_was_clear = 0
        addr_to_remove = None
        for addr, cores in self.entries.items():
            for i in range(len(cores)):
                if (cores[i].core == core) and (cores[i].lpid == lpid):
                    cores.pop(i)
                    monitor_was_clear += 1
                    break
            if len(cores) == 0:
                addr_to_remove = addr
        if addr_to_remove is not None:
            self.entries.pop(addr_to_remove)
        for i in range(len(self.overflow_array)):
            if self.overflow_array[i].core is not None:
                if self.overflow_array[i].lpid == lpid and self.overflow_array[i].core == core:
                    self.overflow_array.pop(i)
                    monitor_was_clear += 1
                    break
        if monitor_was_clear > 1:
            VAL_UTDB_ERROR(time=self.time, msg=str(monitor_was_clear) + "monitors with sabe core and lpid were exist in ref model")

    def get_monitor_vector(self, address):
        cv = []
        for addr, cores in self.entries.items():
            transaction_addr = CCF_UTILS.get_cl_align_address(address)
            #According to HAS we should trigger the monitor even in case the address is the same but MKTME is different
            #if (bint(int(addr, 16))[(CCF_COH_DEFINES.mktme_lsb-1):0]) == (bint(int(transaction_addr, 16))[(CCF_COH_DEFINES.mktme_lsb-1):0]):
            if CCF_UTILS.are_addresses_equal_without_mktme(addr, transaction_addr):
                for entry in self.entries[addr]:
                    cv.append(entry.core)
        for element in self.overflow_array:
            cv.append(element.core)
        return cv

    def get_num_of_entries(self):
        return len(self.entries)

    def does_array_contain_partial_monitor_hit(self, flow_addr, tag_way, half_id):
        bint_flow_addr = bint(int(flow_addr, 16))
        for addr, cores in self.entries.items():
            bint_entry_addr = bint(int(addr, 16))

            same_set = (bint_entry_addr[CCF_COH_DEFINES.set_msb:CCF_COH_DEFINES.set_lsb] == bint_flow_addr[CCF_COH_DEFINES.set_msb:CCF_COH_DEFINES.set_lsb])
            same_half_id = (CCF_UTILS.address_half_calculation(bint_entry_addr) == int(half_id))

            #According to the restructure if TAG LSB bit is 0 we will use ways 0-(CCF_COH_DEFINES.max_num_of_tag_ways/2)
            if int(tag_way) >= (CCF_COH_DEFINES.max_num_of_tag_ways/2):
                same_tag_lsb = (bint_entry_addr[CCF_COH_DEFINES.tag_lsb] == 1)
            else:
                same_tag_lsb = (bint_entry_addr[CCF_COH_DEFINES.tag_lsb] == 0)

            if (same_set and same_tag_lsb and same_half_id):
                return True

        return False

    def entry_is_monitor_hit_match(self, entry_address, cl_trans_address, tag_way=None, half_id=None, check_for_partial_mon_hit=False):
        if check_for_partial_mon_hit:
            return self.does_array_contain_partial_monitor_hit(cl_trans_address, tag_way, half_id)
        else:
            #In CBB HAS we shouldn't consider MKTME bits and we have monitor hit even if MKTME bits are different.
            return CCF_UTILS.are_addresses_equal_without_mktme(entry_address, cl_trans_address)

    def is_monitor_hit_correct(self, time, mon_hit, address, tag_way=None, half_id=None, check_for_partial_mon_hit=False):
        snapshot_has_mon = "0"
        set_monitor_during_reject = False
        cl_addr = CCF_UTILS.get_cl_align_address(address)
        for addr, cores in self.entries.items():
            if self.entry_is_monitor_hit_match(addr, cl_addr, tag_way, half_id, check_for_partial_mon_hit):
                snapshot_has_mon = "1"
                set_monitor_during_reject = any([True if item.set_monitor_during_reject is True else False for item in self.entries[addr]])
                break

        if len(self.overflow_array) > 0:
            snapshot_has_mon = "1"

        #Checker exception:
        #If we are doing SET_MONITOR during reject of the set_monitor we can get to a corner case when another
        #transaction is entering the pipe and accepted and it's b2b with our SET_MONIOR it will take to the SET_MONITOR ~4 cycles to really set the monitor
        #While our b2b transaction will get MonHit=0 even that the SET_MONITOR entered before.
        #Since this can happen only when checker think we have monitor and RTL don't think that and the set monitor happen during reject we can add this exception.
        #since the core don't count on this set monitor till it will get it's GO message and that didn't happened yet.
        checker_exception = (snapshot_has_mon == '1') and (mon_hit == '0') and set_monitor_during_reject

        if (snapshot_has_mon != mon_hit) and not checker_exception:
            VAL_UTDB_ERROR(time=time, msg="monitor hit indication from rtl is not expected for address {} rtl indication is {} while validation is {}".format(address, mon_hit, snapshot_has_mon))
