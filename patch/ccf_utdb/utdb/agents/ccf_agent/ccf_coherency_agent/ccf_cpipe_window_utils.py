#!/usr/bin/env python3.6.3
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base import ccf_addr_entry
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_report import VAL_UTDB_ERROR
from val_utdb_bint import bint
from agents.ccf_common_base.uxi_utils import UXI_UTILS

class ccf_cpipe_window_utils(ccf_base_component):
    def __init__(self):
        self.ccf_registers = ccf_registers.get_pointer()
        self.ccf_addressless_db = ccf_addressless_db.get_pointer()

        #internal vars
        self.prefetch_elimination_allocated = []
        self.prefetch_elimination_tor_ifa_allocated = []
        self.effective_allocated = 0
        self.allow_snoop =0
        self.allow_prefetct = 0
        self.allow_snp_counter = 0
        self.allow_prefetch_counter = 0
        self.err_msg = ""
        self.always_allocate = CCF_FLOW_UTILS.addressless_opcodes + CCF_FLOW_UTILS.idi_addressless_opcodes
        self.ignore_uri = []
        self.tor_id = None
        self.uri = None

    def sort_ccf_addr_flow_db(self):
        for addr in self.ccf_addr_flows.keys():
            self.sort_address_entry_per_time(addr)

    def swap_two_entries(self, addr, first_index, second_index):
        self.ccf_addr_flows[addr][first_index], self.ccf_addr_flows[addr][second_index] = self.ccf_addr_flows[addr][second_index], self.ccf_addr_flows[addr][first_index]
    def order_entries(self, addr, same_address_index_list):
        snoop_allocation_index = None
        close_allow_snoop_index = None
        promotion_index = None
        open_allow_promotion_index = None
        close_allow_promotion_index = None

        for index in same_address_index_list:
            #Rule1: deallocation always first
            if self.ccf_addr_flows[addr][index].record_type == "allocation" and self.ccf_addr_flows[addr][index].Allocated == 0 and index != same_address_index_list[0]:
                self.swap_two_entries(addr, same_address_index_list[0], index)

            #Rule2: snoop allocation before allowsnoop window close
            snoop_allocation = self.ccf_addr_flows[addr][index].record_type == "allocation" and self.ccf_addr_flows[addr][index].Allocated == 1 and self.ccf_addr_flows[addr][index].rec_opcode in UXI_UTILS.uxi_coh_snp_opcodes
            close_allow_snoop = (self.ccf_addr_flows[addr][index].record_type == "allowSnoop") and (self.ccf_addr_flows[addr][index].AllowSnoop == 0)


            if snoop_allocation:
                snoop_allocation_index = index
            if close_allow_snoop:
                close_allow_snoop_index = index

            if (snoop_allocation_index is not None) and (close_allow_snoop_index is not None) and \
                    (close_allow_snoop_index < snoop_allocation_index):
                self.swap_two_entries(addr, close_allow_snoop_index, snoop_allocation_index)
                snoop_allocation_index = None
                close_allow_snoop_index = None

            #Rule3: open promotion window before promoting
            promoted = self.ccf_addr_flows[addr][index].record_type == "promoted"
            open_allow_promotion = (self.ccf_addr_flows[addr][index].record_type == "allowPromotion") and (self.ccf_addr_flows[addr][index].PromotionWindow == 1)

            if promoted:
                promotion_index = index
            if open_allow_promotion:
                open_allow_promotion_index = index

            if (promotion_index is not None) and (open_allow_promotion_index is not None) and \
                    (open_allow_promotion_index > promotion_index):
                self.swap_two_entries(addr, promotion_index, open_allow_promotion_index)
                promotion_index = None
                open_allow_promotion_index = None

            #Rule4: close promotion window after promoting
            promoted = self.ccf_addr_flows[addr][index].record_type == "promoted"
            close_allow_promotion = (self.ccf_addr_flows[addr][index].record_type == "allowPromotion") and (self.ccf_addr_flows[addr][index].PromotionWindow == 0)

            if promoted:
                promotion_index = index
            if close_allow_promotion:
                close_allow_promotion_index = index

            if (promotion_index is not None) and (close_allow_promotion_index is not None) and \
                    (close_allow_promotion_index < promotion_index):
                self.swap_two_entries(addr, close_allow_promotion_index, promotion_index)
                promotion_index = None
                close_allow_promotion_index = None





    def return_index_if_same_time(self, addr, index, same_address_index_list):
        if (len(self.ccf_addr_flows[addr]) > index+1) and (self.ccf_addr_flows[addr][index].time == self.ccf_addr_flows[addr][index + 1].time):
            same_address_index_list.append(index + 1)
            return self.return_index_if_same_time(addr, index + 1, same_address_index_list)
        else:
            return same_address_index_list

    def sort_address_entry_per_time(self,addr):
        self.ccf_addr_flows[addr].sort(key=ccf_addr_entry.get_time)
        #Sometimes we have a situation that two event happen in the same time but was ordered in the wrong order in the list.
        #for example allocation and deallocation of two diffrent transactions.
        #if the order will be allocation and then deallocation and the deallocation is related to earlier URI we could find ourself failing on allocation before deallocation in the window checker.
        #therefore an order should be done for those cases as well.

        for index in range(len(self.ccf_addr_flows[addr]) - 1):
            same_address_index_list = []
            same_address_index_list.append(index)
            same_address_index_list = self.return_index_if_same_time(addr, index, same_address_index_list)
            if len(same_address_index_list) > 1:
                self.order_entries(addr, same_address_index_list)

    ## update_ccf_addr_flow
    # def update_ccf_addr_flow_for_addressless(self):
    #     keys_for_delete = []
    #     ccf_addr_flows_keys = list(self.ccf_addr_flows.keys())
    #     for addressless_addr_key in ccf_addr_flows_keys:
    #         should_delete_addr = 1
    #         for entry in list(self.ccf_addr_flows[addressless_addr_key]):
    #             if (entry.addressless is not None) and (addressless_addr_key == entry.addressless):
    #                 if entry.uri_tid in self.ccf_addressless_db.addressless_db.keys():
    #                     real_address = hex(int(self.ccf_addressless_db.get_real_address_by_uri(entry.uri_tid),16))
    #                     #The assumption here is that if we have addressless address we will always do lookup read to get TAG and line state.
    #                     #A reject due to PA match can be only after this lookup and therefore if we are in LLC_I the allocation open/close window is not relevant and the entry can be reduce from DB.
    #                     #Since anyway that address is fake address since it missing the TAG
    #                     if real_address != addressless_addr_key: #in case of cbo address is equal to real address
    #                        if self.ccf_addressless_db.get_addressless_state_by_uri(entry.uri_tid) != "LLC_I":
    #                             entry.real_address = real_address
    #                             if (real_address not in self.ccf_addr_flows.keys()):
    #                                 self.ccf_addr_flows[real_address] = [entry]
    #                             else:
    #                                 self.ccf_addr_flows[real_address].append(entry)
    #                             self.ccf_addr_flows[addressless_addr_key].remove(entry)
    #                     else:
    #                         should_delete_addr = 0
    #             else:
    #                 should_delete_addr = 0
    #         if should_delete_addr:
    #             keys_for_delete.append(addressless_addr_key)
    #     for key in keys_for_delete:
    #         for entry in list(self.ccf_addr_flows[key]):
    #             if (entry.addressless is not None) and (entry.real_address != key):
    #                 self.ccf_addr_flows[key].remove(entry)
    #         if len(self.ccf_addr_flows[key]) == 0:
    #             del self.ccf_addr_flows[key]

    # def clean_addressless_entries_after_relocated(self):
    #     ccf_addr_flows_keys = list(self.ccf_addr_flows.keys())
    #     for addressless_addr_key in ccf_addr_flows_keys:
    #         need_to_keep_cleaning = 1
    #         if (self.ccf_addr_flows[addressless_addr_key][-1].addressless is not None) and (addressless_addr_key == self.ccf_addr_flows[addressless_addr_key][-1].addressless):
    #             while need_to_keep_cleaning:
    #                 need_to_keep_cleaning = 0
    #                 for entry in self.ccf_addr_flows[addressless_addr_key]:
    #                     if (entry.addressless is not None) and (entry.real_address is not None) and (entry.addressless == addressless_addr_key) and (entry.addressless != entry.real_address):
    #                         need_to_keep_cleaning = 1
    #                         self.ccf_addr_flows[addressless_addr_key].remove(entry)

    def is_prefetch_opcode(self,opcode):
        return opcode in ["LlcPrefRFO", "LlcPrefData", "LlcPrefCode"]

    def add_uri_to_active_prefetch_elimination_list(self, uri_tid, type):
        if type == "TOR":
            self.prefetch_elimination_allocated.append(uri_tid)
        elif type == "IFA":
            self.prefetch_elimination_tor_ifa_allocated.append(uri_tid)
        else:
            VAL_UTDB_ERROR(time=0, msg="(is_prefetch_opcode):type-{} is not supposed to be used".format(type))

    def delete_uri_from_active_prefetch_elimination_list(self, uri_tid, type):
        if type == "TOR":
            if uri_tid in self.prefetch_elimination_allocated:
                self.prefetch_elimination_allocated.remove(uri_tid)
            else:
                err_msg = "Val_Assert (delete_uri_from_active_prefetch_elimination_list): User try to remove non-exist item- {} please check your code".format(uri_tid)
                VAL_UTDB_ERROR(time=0, msg=err_msg)
        elif type == "IFA":
            if uri_tid in self.prefetch_elimination_tor_ifa_allocated:
                self.prefetch_elimination_tor_ifa_allocated.remove(uri_tid)
            else:
                err_msg = "Val_Assert (delete_uri_from_active_prefetch_elimination_list): User try to remove non-exist item- {} please check your code".format(uri_tid)
                VAL_UTDB_ERROR(time=0, msg=err_msg)
        else:
            VAL_UTDB_ERROR(time=0, msg="(is_prefetch_opcode):type-{} is not supposed to be used".format(type))

    def is_uri_of_active_prefetch_elimination(self, uri_tid):
        return (uri_tid in self.prefetch_elimination_allocated) or (uri_tid in self.prefetch_elimination_tor_ifa_allocated)

    def is_uri_of_active_prefetch_elimination_in_tor_ifa(self, uri_tid):
        if (uri_tid in self.prefetch_elimination_tor_ifa_allocated):
            return  1
        else:
            return 0
    def is_prefetach_elimination_active_in_tor_or_IFA(self):
        if ((len(self.prefetch_elimination_allocated) > 0) or (len(self.prefetch_elimination_tor_ifa_allocated) > 0)):
            return 1
        else:
            return 0

    def is_prefetach_elimination_active_in_tor(self):
        if (len(self.prefetch_elimination_allocated) > 0):
            return 1
        else:
            return 0

    def update_db(self):
        #self.update_ccf_addr_flow_for_addressless()
        #self.clean_addressless_entries_after_relocated()
        self.sort_ccf_addr_flow_db()
        for addr in self.ccf_addr_flows.keys():
            self.effective_allocated = 0
            self.TorAllocate = 0
            self.TorIfaAllocate=0
            self.snoop_conflict_allocated = 0
            self.partial_hit_victim_during_snoop_conflict_allocated = 0
            self.prefetch_elimination_allocated = []
            self.allow_snoop =0
            self.allow_prefetch = 0
            self.ignore_uri = []
            self.uri = self.ccf_addr_flows[addr][0].uri_tid
            self.snoop_conflict_uri = None
            self.promoted_uri_dict = {}

            for entry in self.ccf_addr_flows[addr]:
                if (entry.time >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (entry.time < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    if entry.record_type == "allocation":
                        self.update_db_with_allocation(entry)
                    elif entry.record_type == "allowSnoop":
                        self.update_db_with_allow_snoop(entry)
                    elif entry.record_type == "allowPromotion":
                        self.update_db_with_allow_promotion(entry)
                    elif entry.record_type == "promoted":
                        self.update_db_with_promoted(addr, entry)
                    elif entry.record_type == "TorIfaAllocation":
                        self.update_db_with_ifa_allocation(entry)
                    #update prefetch_elimination_allocated item
                    entry.is_any_prefetch_elimination_allocated_in_tor = self.is_prefetach_elimination_active_in_tor()

    def update_db_with_allocation(self, entry: ccf_addr_entry):
        is_snoop_conflict = (entry.rec_opcode in UXI_UTILS.uxi_coh_snp_opcodes) and entry.TorAllocate == 1 and self.effective_allocated == 1 and self.allow_snoop == 1
        is_snoop_conflict_deallocation = (entry.rec_opcode in UXI_UTILS.uxi_coh_snp_opcodes) and self.snoop_conflict_allocated == 1 and entry.TorAllocate == 0

        #TODO: check the assumption that snoop from snoop conflict flow cannot be deallocated before Victim of partial hit of snoop during snoop conflcit is deallocated
        is_victim_due_to_partial_hit_while_conflict_allocation = (entry.rec_opcode == "Victim") and (entry.TorAllocate == 1) and (self.effective_allocated == 1) and (self.allow_snoop == 1) and (self.snoop_conflict_allocated == 1) and (self.snoop_conflict_uri == entry.uri_tid)
        is_victim_due_to_partial_hit_while_conflict_deallocation = (entry.rec_opcode == "Victim") and (self.partial_hit_victim_during_snoop_conflict_allocated == 1) and (entry.TorAllocate == 0)

        #Need to fix this condition and support the commented line.
        #is_prefetch_elimination = ((self.effective_allocated == 1) or ccf_dbs.ccf_flows[entry.uri_tid].flow_is_crababort())and

        is_prefetch_elimination = ccf_dbs.ccf_flows[entry.uri_tid].prefetch_elimination_flow and \
                                  (entry.record_type == "allocation" and entry.TorAllocate == 1) and \
                                  self.is_prefetch_opcode(entry.rec_opcode) and \
                                  (self.ccf_registers.prefetch_elimination_en[0] == 1)


        is_prefetch_elimination_deallocation = (self.is_uri_of_active_prefetch_elimination(entry.uri_tid)) and \
                                               (entry.record_type == "allocation" and entry.TorAllocate == 0) and \
                                                self.is_prefetch_opcode(entry.rec_opcode) and \
                                               (self.ccf_registers.prefetch_elimination_en[0] == 1)

        is_tor_deallocate_but_tor_ifa_still_allocate = ((entry.record_type == "allocation" and entry.TorAllocate == 0) and \
                                                        ((self.effective_allocated == 1) and (self.TorIfaAllocate == 1)))

        if entry.uri_tid == self.uri:
            entry.AllowSnoop = self.allow_snoop
            entry.PromotionWindow = self.allow_prefetch
        if (entry.rec_opcode in self.always_allocate):
            self.ignore_uri.append(entry.uri_tid)
        if entry.uri_tid not in self.ignore_uri:
            if is_snoop_conflict:
                entry.record_type = "snoop conflict allocation"
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorAllocate = self.TorAllocate
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.conflict_with_uri = self.uri
                entry.snoop_conflict_allocated = 1
                self.snoop_conflict_allocated  = 1
                self.snoop_conflict_uri = entry.uri_tid

            elif is_snoop_conflict_deallocation:
                entry.record_type = "snoop conflict allocation"
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorAllocate = self.TorAllocate
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.conflict_with_uri = self.uri
                entry.snoop_conflict_allocated = 0
                self.snoop_conflict_allocated = 0
                self.snoop_conflict_uri = None

            elif is_victim_due_to_partial_hit_while_conflict_allocation:
                entry.record_type = "victim due to partial hit while snoop conflict allocation"
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorAllocate = self.TorAllocate
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.conflict_with_uri = self.uri
                entry.snoop_conflict_allocated = self.snoop_conflict_allocated
                entry.victim_due_to_partial_hit_while_snoop_conflict_allocated = 1
                self.partial_hit_victim_during_snoop_conflict_allocated = 1

            elif is_victim_due_to_partial_hit_while_conflict_deallocation:
                entry.record_type = "victim due to partial hit while snoop conflict allocation"
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorAllocate = self.TorAllocate
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.conflict_with_uri = self.uri
                entry.snoop_conflict_allocated = self.snoop_conflict_allocated
                entry.victim_due_to_partial_hit_while_snoop_conflict_allocated = 0
                self.partial_hit_victim_during_snoop_conflict_allocated = 0

            elif is_prefetch_elimination:
                entry.record_type = "prefetch elimination"
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorAllocate = self.TorAllocate
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.current_prefetch_elimination_allocation_status = 1
                self.add_uri_to_active_prefetch_elimination_list(entry.uri_tid, "TOR")

            elif is_prefetch_elimination_deallocation:
                entry.record_type = "prefetch elimination"
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorAllocate = self.TorAllocate
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.current_prefetch_elimination_allocation_status = 0
                self.delete_uri_from_active_prefetch_elimination_list(entry.uri_tid, "TOR")

            elif is_tor_deallocate_but_tor_ifa_still_allocate:
                entry.AllowSnoop = self.allow_snoop
                entry.PromotionWindow = self.allow_prefetch
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.Allocated = self.effective_allocated
                self.TorAllocate = entry.TorAllocate

            elif (entry.Allocated != self.effective_allocated):
                self.effective_allocated = entry.Allocated
                self.TorAllocate = entry.TorAllocate
                if entry.Allocated:
                    self.uri = entry.uri_tid
        else:
            if not entry.Allocated:
                self.ignore_uri.remove(entry.uri_tid)

    def update_db_with_ifa_allocation(self, entry: ccf_addr_entry):
        #In victim we can see the TORIFA alocation before the allocation in the TOR.
        if "VIC" in entry.uri_lid and (entry.Allocated == 0) and (entry.TorIfaAllocate == 1):
            self.uri = entry.uri_tid
            self.effective_allocated = 1
            self.TorAllocate = 1 # this is wrong indication in case of Victim we should fix the TOR allocation to be on the right time in VICTIM flows.

        if entry.uri_tid == self.uri:
            entry.PromotionWindow = self.allow_prefetch
            entry.AllowSnoop = self.allow_snoop
            entry.TorAllocate = self.TorAllocate
            entry.Allocated = self.effective_allocated

            if (entry.TorIfaAllocate != self.TorIfaAllocate):
                self.TorIfaAllocate = entry.TorIfaAllocate

                if (entry.TorIfaAllocate == 1) and (self.effective_allocated == 1):
                    entry.Allocated = self.effective_allocated
                elif (entry.TorIfaAllocate == 0) and (entry.TorAllocate == 0) and (self.effective_allocated == 1):
                    self.effective_allocated = 0
                    entry.Allocated = 0
                elif (entry.TorIfaAllocate == 0) and (entry.TorAllocate == 1) and (self.effective_allocated == 1):
                    entry.Allocated = self.effective_allocated
                else:
                    err_msg = "Please check this case in debugger this shouldn't had happen."
                    VAL_UTDB_ERROR(time=entry.time, msg=err_msg)

                #In case allocated is not 1 we need to call for error
                if((entry.TorAllocate == 0) and (self.TorIfaAllocate == 1)):
                    err_msg = "TorIFAAllocation is 1 while TOR was already deallocated that was not expected."
                    VAL_UTDB_ERROR(time=entry.time, msg=err_msg)

        elif self.is_uri_of_active_prefetch_elimination(entry.uri_tid):
            #Take the previous value of the prefetch elimination ifa allocation
            entry.current_prefetch_elimination_ifa_allocation_status = self.is_uri_of_active_prefetch_elimination_in_tor_ifa(entry.uri_tid)

            #To cover cases where TOR is still allocated while TOR IFA is deallocated (can happen in coloc cases)
            if (entry.current_prefetch_elimination_ifa_allocation_status == 0) and (entry.TorIfaAllocate == 1):
                self.add_uri_to_active_prefetch_elimination_list(entry.uri_tid, "IFA")
            elif (entry.current_prefetch_elimination_ifa_allocation_status == 1) and (entry.TorIfaAllocate == 0):
                self.delete_uri_from_active_prefetch_elimination_list(entry.uri_tid, "IFA")
            else:
                err_msg = "Please check this case in debugger this shouldn't had happen."
                VAL_UTDB_ERROR(time=entry.time, msg=err_msg)

            # Take the new value of the prefetch elimination ifa allocation
            entry.current_prefetch_elimination_ifa_allocation_status = self.is_uri_of_active_prefetch_elimination_in_tor_ifa(entry.uri_tid)
            entry.AllowSnoop = self.allow_snoop
            entry.PromotionWindow = self.allow_prefetch
            entry.Allocated = self.effective_allocated
            entry.TorAllocate = self.TorAllocate
            entry.TorIfaAllocate = self.TorIfaAllocate
        else:
            VAL_UTDB_ERROR(time=entry.time, msg="We got to TorIfa allocation/deallocation with diffrent URI then expected.")

    def update_db_with_allow_snoop(self, entry: ccf_addr_entry):
        if entry.uri_tid == self.uri:
            entry.PromotionWindow = self.allow_prefetch
            entry.Allocated = self.effective_allocated
            entry.TorIfaAllocate = self.TorIfaAllocate
            entry.TorAllocate = self.TorAllocate
        else:
            #self.promoted_uri_dict[self.uri] - the DRd/CRd/RFO that cause the promotion,  entry.uri_tid - the prefetch URI
            #if we did promotion we may see some allow snoop window being close later and we can consider this is ok
            if ((self.uri not in self.promoted_uri_dict.keys()) or (self.promoted_uri_dict[self.uri] != entry.uri_tid)):
                self.uri = entry.uri_tid
            else:
                entry.PromotionWindow = self.allow_prefetch
                entry.Allocated = self.effective_allocated
                entry.TorIfaAllocate = self.TorIfaAllocate
                entry.TorAllocate = self.TorAllocate
        if (entry.AllowSnoop != self.allow_snoop):
            self.allow_snoop = entry.AllowSnoop

    def update_db_with_allow_promotion(self, entry: ccf_addr_entry):
        if entry.uri_tid == self.uri:
            entry.AllowSnoop = self.allow_snoop
            entry.Allocated = self.effective_allocated
            entry.TorIfaAllocate = self.TorIfaAllocate
            entry.TorAllocate = self.TorAllocate
        if (entry.PromotionWindow != self.allow_prefetch) and (self.effective_allocated == 1) and (self.uri == entry.uri_tid):
            self.allow_prefetch = entry.PromotionWindow

    def get_prefetch_uri_that_cause_the_promotion(self, addr, index):
        if self.ccf_addr_flows[addr][index-1].record_type == "allowPromotion":
            return self.ccf_addr_flows[addr][index-1].uri_tid
        if self.ccf_addr_flows[addr][index-1].record_type not in ["snoop conflict allocation", "allowSnoop", "prefetch elimination"]:
            err_msg = "Val_Assert (get_prefetch_uri_that_cause_the_promotion): We are not expecting any transaction to enter during another allocation unless it promotion or snoop conflict, check URI: {}".format(self.ccf_addr_flows[addr][index-1].uri_tid)
            VAL_UTDB_ERROR(time=self.ccf_addr_flows[addr][index-1].time, msg=err_msg)
        else:
            return self.get_prefetch_uri_that_cause_the_promotion(addr, index - 1)

    def get_current_prefetch_elimination_uri(self, addr, index):
        if self.ccf_addr_flows[addr][index].record_type == "prefetch elimination" and self.ccf_addr_flows[addr][index].current_prefetch_elimination_allocation_status == 1:
            return self.ccf_addr_flows[addr][index].uri_tid
        else:
            if index != 0:
                return self.get_current_prefetch_elimination_uri(addr, index - 1)
            else:
                return None

    def update_db_with_promoted(self, addr, entry: ccf_addr_entry):
        promoted_index = self.ccf_addr_flows[addr].index(entry)
        entry.prefetch_uri_tid = self.get_prefetch_uri_that_cause_the_promotion(addr, promoted_index)
        self.promoted_uri_dict[entry.uri_tid] = entry.prefetch_uri_tid
        #entry.PromotionWindow = self.allow_prefetch
        #When promoting we will close the promotion window once we choose transaction to promotion
        self.allow_prefetch = 0
        entry.PromotionWindow = self.allow_prefetch
        entry.AllowSnoop = self.allow_snoop
        if (entry.prefetch_uri_tid == self.uri):
            self.uri = entry.uri_tid
        else:
            VAL_UTDB_ERROR(time=entry.time, msg="uri {} got promoted on unexpected prefetch uri {}".format(entry.uri_tid,entry.prefetch_uri_tid))

    def check_windows(self):
        for addr in self.ccf_addr_flows.keys():
            self.ccf_addr_flows[addr].sort(key=ccf_addr_entry.get_time)

        for addr in self.ccf_addr_flows.keys():
            self.allow_snp_counter = 0
            self.allow_prefetch_counter = 0
            self.effective_allocated = 0
            self.TorIfaAllocate = 0
            self.half = None
            self.allow_snoop =0
            self.allow_prefetch = False
            self.was_promoted = False
            self.uri = None
            self.ignore_uri = []
            self.tor_id = None
            self.snoop_conflict_allocated=0
            self.partial_hit_victim_during_snoop_conflict_allocated = 0
            self.prefetch_elimination_allocated = []
            self.snoop_conflict_uri = None
            self.active_victim_due_to_paritial_hit = []

            for entry in self.ccf_addr_flows[addr]:
                if entry.record_type == "allocation":
                    self.check_windows_for_allocation(entry)

                elif entry.record_type == "snoop conflict allocation":
                    self.check_window_fo_snoop_conflict_allocation(entry)

                elif entry.record_type == "victim due to partial hit while snoop conflict allocation":
                    self.check_victim_due_to_partial_hit_while_snoop_conflict(entry)

                elif entry.record_type == "allowSnoop":
                    self.check_windows_for_allow_snoop(entry)

                elif (entry.record_type == "allowPromotion"):
                    self.check_windows_for_allow_promotion(entry)

                elif (entry.record_type == "promoted"):
                    self.check_windows_for_promoted(entry.full_address, entry)

                elif (entry.record_type == "prefetch elimination"):
                    self.check_windows_for_prefetch_elimination(entry)

                elif (entry.record_type == "TorIfaAllocation"):
                    self.check_windows_for_tor_ifa_allocation(entry)

                else:
                    self.err_msg = "we get non familiar record type URI TID " + entry.uri_tid
                    VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)


    def check_windows_for_allocation(self, entry: ccf_addr_entry):
        #Assumption:
        #When we are creating Victim flow for partial hit this victim will cause the transcation that created it to stop till the victim will be finish.
        #We can identify Victim that happen due to partial hit by see if we don't have any effective allocated (=0).
        #We will keep a list of those victims since at deallocation of them we will not be able to identify them.
        victim_flow_due_to_partial_hit = (("Victim" in entry.rec_opcode) and (self.effective_allocated == 0) and (entry.TorAllocate == 1)) or (entry.uri_lid in self.active_victim_due_to_paritial_hit)

        if victim_flow_due_to_partial_hit and entry.record_type == "allocation":
            if entry.TorAllocate == 1:
                self.active_victim_due_to_paritial_hit.append(entry.uri_lid)
            else:
                self.active_victim_due_to_paritial_hit.remove(entry.uri_lid)

        if entry.record_type == "allocation":
            if (entry.rec_opcode in self.always_allocate):
                self.ignore_uri.append(entry.uri_tid)
            elif (entry.uri_tid not in self.ignore_uri) and not (("Victim" in entry.rec_opcode) and not victim_flow_due_to_partial_hit):
                if (entry.Allocated != self.effective_allocated):
                    self.effective_allocated = entry.Allocated
                    if entry.Allocated:
                        self.uri = entry.uri_tid
                        self.tor_id = entry.tor_id
                    else:
                        if self.allow_prefetch_counter > 1:
                            VAL_UTDB_ERROR(time=entry.time, msg="uri " + entry.uri_tid + " has " + str(self.allow_prefetch_counter) +" windows of allow prefetch promotion")
                        if self.allow_snp_counter > 1:
                            VAL_UTDB_ERROR(time=entry.time, msg="uri " + entry.uri_tid + " has " + str(self.allow_snp_counter) +" windows of allow_snoop")
                        self.allow_snp_counter=0
                        self.allow_prefetch_counter=0
                        self.was_promoted = False #when deallocation we need to unflag this indication
                else:
                    if not (entry.TorIfaAllocate == 1): #TODO: need to check cases where TorIfa is before the TOR allocation
                        if entry.TorAllocate:
                            self.err_msg = "we are not expecting allocation of URI TID " + entry.uri_tid + " since it wasn't de-allocated"
                        else:
                            self.err_msg = "we are not expecting de-allocation of URI TID " + entry.uri_tid + " since it wasn't allocated"
                        VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)
            else:
                if (entry.Allocated == 0) and not (("Victim" in entry.rec_opcode) and not victim_flow_due_to_partial_hit):
                    self.ignore_uri.remove(entry.uri_tid)

    def check_windows_for_tor_ifa_allocation(self, entry: ccf_addr_entry):
        if((entry.TorIfaAllocate == 0) and (entry.TorAllocate == 0) and (entry.Allocated == 0)):
            self.effective_allocated =0
            if self.allow_prefetch_counter > 1:
                VAL_UTDB_ERROR(time=entry.time, msg="uri " + entry.uri_tid + " has " + str(self.allow_prefetch_counter) + " windows of allow prefetch promotion")
            if self.allow_snp_counter > 1:
                VAL_UTDB_ERROR(time=entry.time, msg="uri " + entry.uri_tid + " has " + str(self.allow_snp_counter) + " windows of allow_snoop")
            self.allow_snp_counter = 0
            self.allow_prefetch_counter = 0
            self.was_promoted = False  # when deallocation we need to unflag this indication


    # def check_ifa_windows_for_allocation(self, entry: ccf_addr_entry):
    #      if entry.record_type == "TorIfaAllocated":
    #          if (entry.Allocated != self.allocated):
    #                 self.allocated = entry.Allocated
    def check_window_fo_snoop_conflict_allocation(self, entry: ccf_addr_entry):
        if entry.snoop_conflict_allocated == 1:
            if self.snoop_conflict_allocated == 1:
                self.err_msg = "check_window_fo_snoop_conflict_allocation: we allready have snoop conflict allocated we cannot allocate new one"
                VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)
            elif entry.conflict_with_uri != self.uri:
                self.err_msg = "check_window_fo_snoop_conflict_allocation: we are allocating snoop while conflicting but the " \
                               "record say we are conflicting with {} while we think we should be in conflict with {}".format(entry.conflict_with_uri, self.uri)
                VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)
            else:
                self.snoop_conflict_allocated = 1
                self.snoop_conflict_uri = entry.uri_tid

        if entry.snoop_conflict_allocated == 0:
            if (entry.uri_tid != self.snoop_conflict_uri) or (self.snoop_conflict_allocated == 0):
                self.err_msg = "check_window_fo_snoop_conflict_allocation: We are deallocating snoop that was in snoop " \
                               "conflict but this snoop conflict was not allocated {}".format(entry.uri_tid)
                VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)
            else:
                self.snoop_conflict_uri = None
                self.snoop_conflict_allocated = 0

        if entry.snoop_conflict_allocated == 1 and ((entry.Allocated != 1) or (entry.AllowSnoop != 1)):
            self.err_msg = "check_window_fo_snoop_conflict_allocation: snoop cannot be allocate as snoop conflict allocation, URI- {}, Allocated= {}, AllowSnoop= {} ".format(entry.uri_tid, entry.Allocated, entry.AllowSnoop)
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)

        if (entry.conflict_with_uri is None):
            self.err_msg = "check_window_fo_snoop_conflict_allocation: We expected to have the URI of the trasnaction we had conflict with it"
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)

    def check_victim_due_to_partial_hit_while_snoop_conflict(self, entry: ccf_addr_entry):
        if entry.snoop_conflict_allocated != 1:
            self.err_msg = "check_victim_due_to_partial_hit_while_snoop_conflict: We are not expecting to have Victim that being caused by partial hit during snoop conflict while we don't have snoop conflict allocated."
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)

        if entry.uri_tid != self.snoop_conflict_uri:
            self.err_msg = "check_victim_due_to_partial_hit_while_snoop_conflict: Victim TID should be the same like the snoop transaction that caused it."
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)


    def check_windows_for_allow_snoop(self, entry: ccf_addr_entry):
        if (entry.AllowSnoop != self.allow_snoop):
            self.allow_snoop = entry.AllowSnoop
            if entry.AllowSnoop:
                self.allow_snp_counter+=1
        else:
            if entry.AllowSnoop:
                self.err_msg = "we are not expecting to open allow snoop window of URI TID " + entry.uri_tid + " since it was already open"
            else:
                self.err_msg = "we are not expecting to close allow snoop window of URI TID " + entry.uri_tid + " since it was already closed"
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)
        if entry.AllowSnoop == 0 and (self.effective_allocated == 0 or ((self.uri != entry.uri_tid) and (self.was_promoted is False))):
            self.err_msg = "we are not expecting to close allow snoop window of URI TID " + entry.uri_tid + " since it is not allocated"
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)

    def check_windows_for_allow_promotion(self, entry: ccf_addr_entry):
        if (entry.PromotionWindow != self.allow_prefetch) and (self.effective_allocated == 1) and (self.uri == entry.uri_tid):
            self.allow_prefetch = entry.PromotionWindow
            if entry.PromotionWindow:
                self.allow_prefetch_counter+=1
        else:
            if entry.PromotionWindow:
                self.err_msg = "we are not expecting to open allow prefetch promotion window of URI TID " + entry.uri_tid + " since it was already open"
            else:
                self.err_msg = "we are not expecting to close allow prefetch promotion window of URI TID " + entry.uri_tid + " since it was already closed"
            VAL_UTDB_ERROR(time=entry.time, msg=self.err_msg)

    def check_windows_for_promoted(self, addr, entry: ccf_addr_entry):
        if (entry.prefetch_uri_tid == self.uri):
            self.uri = entry.uri_tid
            self.was_promoted = True
        else:
            VAL_UTDB_ERROR(time=entry.time, msg="uri {} got promoted on unexpected prefetch uri {}".format(entry.uri_tid,entry.prefetch_uri_tid))

        status, last_uri = self.can_promote(addr_with_mktme=addr, time=entry.time)
        if not status:
            VAL_UTDB_ERROR(time=entry.time, msg="We didn't expect to have promotion in time: {} for TID: {}".format(entry.time, entry.uri_tid))

    def check_windows_for_prefetch_elimination(self, entry: ccf_addr_entry):
        if self.ccf_registers.prefetch_elimination_en[0] == 0:
            VAL_UTDB_ERROR(time=entry.time, msg="(check_windows_for_prefetch_elimination): Prefetch elimination is disable we didn't expect to see any prefetch elimination TID - {}".format(entry.uri_tid))

        if entry.current_prefetch_elimination_allocation_status == 1:
            if not self.is_uri_of_active_prefetch_elimination(entry.uri_tid):
                self.add_uri_to_active_prefetch_elimination_list(entry.uri_tid, "TOR")
            else:
                err_msg = "(check_windows_for_prefetch_elimination): It not make sense that we are trying to allocate the same prefetch elimination twice TID - {}".format(entry.uri_tid)
                VAL_UTDB_ERROR(time=entry.time, msg=err_msg)

        if entry.current_prefetch_elimination_allocation_status == 0:
            if self.is_uri_of_active_prefetch_elimination(entry.uri_tid):
                self.delete_uri_from_active_prefetch_elimination_list(entry.uri_tid, "TOR")
            else:
                err_msg = "(check_windows_for_prefetch_elimination): It not make sense that we are trying to deallocate prefetch elimination without it being allocated before TID - {}".format(entry.uri_tid)
                VAL_UTDB_ERROR(time=entry.time, msg=err_msg)


        #We need to enable this checking back that we are doing prefeatch elimination only when it's allowed.
        #If the flow is crab abourt flow we should do elimination even when we do not' have in fly transactions in the pipe.
        #if (self.effective_allocated == 0) and (entry.current_prefetch_elimination_allocation_status == 1) and not ccf_dbs.ccf_flows[entry.uri_tid].flow_is_crababort():
        #    VAL_UTDB_ERROR(time=entry.time, msg="(check_windows_for_prefetch_elimination): You cannot have prefetch elimination while no other transaction was allocated TID - {}".format(entry.uri_tid))

        if not self.is_prefetch_opcode(entry.rec_opcode):
            err_msg = "(check_windows_for_prefetch_elimination):entry opcode is -{} and it's not prefetch opcode so we cannot be in prefetch elimination process TID-{}".format(entry.rec_opcode, entry.uri_tid)
            VAL_UTDB_ERROR(time=entry.time, msg=err_msg)

    def get_transaction_allocation_entry(self, addr, uri_tid,uri_lid):
        addr_key = CCF_UTILS.get_address_align_and_without_mktme(addr)
        if addr_key in self.ccf_addr_flows.keys():
            for entry in self.ccf_addr_flows[addr_key]:
                if (entry.uri_tid == uri_tid) and (entry.uri_lid == uri_lid) and (entry.record_type == "allocation" or entry.record_type == "snoop conflict allocation") and (entry.Allocated == 1):
                    return entry
                elif (entry.uri_tid == uri_tid) and (entry.uri_lid == uri_lid) and (entry.record_type == "promoted"):
                    return entry
        return None

    def get_transaction_deallocation_entry(self, addr, uri_tid):
        addr_key = CCF_UTILS.get_address_align_and_without_mktme(addr)
        for entry in self.ccf_addr_flows[addr_key]:
            if (entry.uri_tid == uri_tid) and \
                    (((entry.record_type == "allocation" or entry.record_type == "snoop conflict allocation") and (entry.Allocated == 0))
                     or (entry.record_type == "prefetch elimination" and entry.current_prefetch_elimination_allocation_status == 0)):
                return entry
        return None

    def get_transaction_allocation_time(self, addr, uri_tid, uri_lid):
        return self.get_transaction_allocation_entry(addr, uri_tid, uri_lid).time

    def get_transaction_deallocation_time(self, addr, uri_tid):
        if self.get_transaction_deallocation_entry(addr, uri_tid) is not None:
            return self.get_transaction_deallocation_entry(addr, uri_tid).time
        else:
            return None

    def check_that_no_pa_match_reject_expected_for_uri(self, addr, flow_uri, time_for_error):
        addr_key = CCF_UTILS.get_address_align_and_without_mktme(addr)
        allocated_uri = None
        skip_uri_list = []

        if addr_key in self.ccf_addr_flows.keys():
            for entry in self.ccf_addr_flows[addr_key]:
                if (entry.time >= COH_GLOBAL.global_vars["START_OF_TEST"]) and (entry.time < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    if entry.rec_opcode in self.always_allocate:
                        skip_uri_list.append(entry.uri_tid)
                    if (entry.record_type == "allocation") and (entry.TorAllocate == 1) and entry.uri_tid not in skip_uri_list:
                        if allocated_uri is not None:
                            return allocated_uri
                        else:
                            allocated_uri = entry.uri_tid
                    elif (entry.record_type in ["allocation", "TorIfaAllocation"]) and (entry.Allocated == 0) \
                            and not (ccf_dbs.ccf_flows[entry.uri_tid].prefetch_elimination_flow):
                        if entry.uri_tid in skip_uri_list:
                            skip_uri_list.remove(entry.uri_tid)
                        else:
                            if entry.uri_tid != allocated_uri:
                                err_msg = "Val_Assert: we are deallocating entry that was not allocated before check what happen here. entry URI: {}, allocated URI: {}".format(entry.uri_tid,allocated_uri)
                                VAL_UTDB_ERROR(time=entry.time, msg=err_msg)
                            else:
                                allocated_uri = None
                    elif (entry.record_type == "promoted") and (entry.prefetch_uri_tid == allocated_uri):
                        allocated_uri = entry.uri_tid

                    if (flow_uri['TID'] == entry.uri_tid) and (flow_uri['LID'] == entry.uri_lid) and (entry.Allocated == 0):
                        return None
        else:
            VAL_UTDB_ERROR(time=time_for_error, msg="We didn't found the address:{} in ccf_addr_flows list please check it something went wrong.".format(addr_key))

        return None

    def get_address_allocation_window_at_specific_time(self, addr, time):
        addr_key = CCF_UTILS.get_address_align_and_without_mktme(addr)
        open_alloc_window = None
        close_alloc_window = None
        current_window_uri_tid = None
        for entry in self.ccf_addr_flows[addr_key]:
            if (open_alloc_window is None) and (entry.Allocated == 1):
                open_alloc_window = entry
                current_window_uri_tid = entry.uri_tid
            if entry.record_type == "promoted":
                current_window_uri_tid = entry.uri_tid
            if (open_alloc_window is not None) and (entry.Allocated == 0) and (entry.uri_tid == current_window_uri_tid):
                close_alloc_window = entry
                if time <= close_alloc_window.time and time >= open_alloc_window.time:
                    return open_alloc_window, close_alloc_window
                else:
                    #if we got here that mean the window was closed before our time and therefore not relevant
                    open_alloc_window = None
                    close_alloc_window = None

        if ((open_alloc_window is None) and (close_alloc_window is not None)) or \
            ((open_alloc_window is not None) and (close_alloc_window is None)):
                self.err_msg = "We got to not valid state where we have only open window or close window please check your code."
                VAL_UTDB_ERROR(time=time, msg=self.err_msg)

        return open_alloc_window, close_alloc_window

    def get_addr_state_at_specific_time(self, addr, time, flow=None):
        aligned_addr = CCF_UTILS.get_address_align_and_without_mktme(addr)
        to_return = ccf_addr_entry()
        to_return.record_type = "first entry"

        #if the User giving us the flow we can know better when to stop the search if we have several changes on the same time.
        if flow is None:
            for entry in self.ccf_addr_flows[aligned_addr]:
                #We will take entry time that equal to our time in case of promotion window open on the exact same time as our transaction.
                if (time > entry.time) or ((time == entry.time) and
                                           ((entry.record_type == "allowPromotion" and entry.PromotionWindow == 1) or
                                            (entry.record_type == "prefetch elimination" and entry.is_any_prefetch_elimination_allocated_in_tor == 0))):
                    to_return = entry
                if (entry.time > time):
                    return to_return
            return to_return
        else:
            for entry in self.ccf_addr_flows[aligned_addr]:
                if (entry.time > time) or (entry.time == time and (entry.uri_tid == flow.uri['TID'])):
                    return to_return
                elif time >= entry.time:
                    to_return = entry
            return to_return


    def get_promotion_time_for_address_and_uri(self, addr, uri_tid):
        addr_without_mktme = CCF_UTILS.get_address_align_and_without_mktme(addr)

        if addr_without_mktme in self.ccf_addr_flows.keys():
            for entry in self.ccf_addr_flows[addr_without_mktme]:
                if entry.record_type == "promoted" and entry.uri_tid == uri_tid:
                    return entry.time
        return None

    def can_promote(self, addr_with_mktme, time, monhit=None, flow=None):
        addr_without_mktme = CCF_UTILS.get_address_align_and_without_mktme(addr_with_mktme)

        if addr_without_mktme in self.ccf_addr_flows.keys():
            last_entry = self.get_addr_state_at_specific_time(addr_without_mktme, time, flow)

            #After finding the entry we need to check that our trasnaction entered when promotion window is 1 and both transaction have the same address with the same mktme(see promotion section in HAS)
            if (last_entry.PromotionWindow == 1) and (CCF_UTILS.are_addresses_equal_with_mktme(ccf_dbs.ccf_flows[last_entry.uri_tid].address, addr_with_mktme)):
                can_promote_status = True
                prefetch_uri = last_entry.uri_tid
                #When checking the monitor status we will use the time that apper in the CBO TRK since the monitor records are according to this time
                #(even if this time is not accurate it still give us good indication to the order of the transactions in the pipe)
                #Rule: if we have monitor hit we will not do promotion.
                if (flow is not None) and monhit:
                    can_promote_status = False

                #If we still have prefeatch elimination in the pipe and it's still not deallocate that mean we have two PA match in the pipe.
                # and in that case we are not doing promotion (RTL cannot know the right information to conclude to do prefetch)
                #In case we are not tracking the GO_I we will not assign entry in TOR to the prefetch that was eliminated. that can case a situation.
                #that we are not seeing this prefecth as PA match and we are doing the promotion anyway (that is ok since we will not have two PA match in the same time).
                #In some cases when the prefetch elimination is 2 cycles after we may see is and reject. therefore if we are in prefetch elimination that is not being written to the TOR
                #(The time of the dealocation is the same time the pass was ended) we will say that the RTL decision it probebly correct
                if last_entry.is_any_prefetch_elimination_allocated_in_tor == 1:
                    # TODO: please review again - Remove as not make sense in elimination always first accept_time and deallocation will be the same time.
                    #prefetch_elimination_uri = self.get_current_prefetch_elimination_uri(addr=addr_without_mktme, index=self.ccf_addr_flows[addr_without_mktme].index(last_entry))
                    #if (prefetch_elimination_uri is not None) and \
                    #        (ccf_dbs.ccf_flows[prefetch_elimination_uri].first_accept_time != self.get_transaction_deallocation_time(addr_without_mktme, prefetch_elimination_uri)):
                    can_promote_status = False

                #If we have active snoop (from snoop conflict) during the promotion time we will not do promotion.
                #The Rule is that if we have more then one PA match we will not do promotion.
                if last_entry.snoop_conflict_allocated == 1:
                    can_promote_status = False

                if last_entry.record_type != "allowPromotion":
                    prefetch_uri = self.get_prefetch_uri_that_cause_the_promotion(addr=addr_without_mktme, index=self.ccf_addr_flows[addr_without_mktme].index(last_entry))

                return can_promote_status, prefetch_uri
        return False, None

    def add_entry_in_address_flow(self, addr_with_mktme, entry: ccf_addr_entry):
        addr_without_mktme = CCF_UTILS.get_address_align_and_without_mktme(addr_with_mktme)
        if addr_without_mktme in self.ccf_addr_flows.keys():
            self.ccf_addr_flows[addr_without_mktme].append(entry)
            self.sort_address_entry_per_time(addr_without_mktme)
        else:
            self.ccf_addr_flows[addr_without_mktme] = [entry]

    def is_flow_had_reject_on_time(self, uri_tid,reject_name, time):
        if (uri_tid in self.ccf_reject_accurate_times.keys()) and (reject_name in self.ccf_reject_accurate_times[uri_tid].keys()):
            return any([True for item in self.ccf_reject_accurate_times[uri_tid][reject_name] if item['TIME'] == time])
        else:
            return False
