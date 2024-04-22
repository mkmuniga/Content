from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_agent.ccf_llc_and_dump_chk_agent.ccf_llc_chk_cov import CCF_LLC_CHK_CG
from agents.ccf_common_base.ccf_common_base import ccf_llc_record_info, llc_refmodel_entry
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG

import copy


class ccf_llc_chk(ccf_coherency_base_chk):
    def __init__(self):
        self.checker_name = "ccf_llc_chk"
        self.ccf_llc_chk_cg = CCF_LLC_CHK_CG.get_pointer()
        self.ccf_llc_db_agent_i = ccf_llc_db_agent.get_pointer()
        self.cv_updates_ops = ["Wdsc", "Wdc", "Wc", "Wdsct", "Wsct", "Wsc"]
        self.state_update_ops = ["Ws", "Wdsc", "Wds", "Wsc", "Wsct", "Wdsct", "RdctWs", "RctWs"]
        self.preload_time = 0

    def sort_llc_rtl_db(self):
        self.llc_rtl_db.sort(key=ccf_llc_record_info.get_time)

    def add_special_entry(self, new):
        bin_format_vector = bin(int(new.rec_state_wr_way, 16))[2:].zfill(CCF_COH_DEFINES.max_num_of_tag_ways)
        s = new.get_slice_num()
        h = new.get_half()
        for i in range(len(bin_format_vector)):
            if bin_format_vector[i] == "1":
                accessed_way = CCF_COH_DEFINES.max_num_of_tag_ways - i - 1
                for t in self.llc_ref_db[s][h][new.rec_set].keys():
                    if (self.llc_ref_db[s][h][new.rec_set][t][-1].state != "I") and (t != new.rec_tag_ecc)\
                            and (accessed_way == int(self.llc_ref_db[s][h][new.rec_set][t][-1].way)):
                            special_entry = llc_refmodel_entry()
                            special_entry.tag_ecc = t
                            special_entry.slice = s
                            special_entry.set = new.rec_set
                            special_entry.half = h
                            special_entry.way = str(accessed_way)
                            special_entry.time = new.rec_time
                            if self.is_field_valid(new.rec_state_vl_way) and (bin(int(new.rec_state_vl_way, 16))[2:].zfill(CCF_COH_DEFINES.max_num_of_tag_ways)[i] == "1"):
                                if self.llc_ref_db[s][h][new.rec_set][t][-1].state != "E":
                                    VAL_UTDB_ERROR(time=new.rec_time, msg="llc_chk_failure: Vulnerable line state for eviction is not in E state. URI = " + new.rec_tid)

                                if self.llc_ref_db[s][h][new.rec_set][t][-1].map == str(CCF_COH_DEFINES.SNOOP_FILTER):
                                    VAL_UTDB_ERROR(time=new.rec_time, msg="llc_chk_failure: Vulnerable line for eviction is already in SF. URI = " + new.rec_tid)

                                if (new.rec_state_in_way != "-") and bin(int(new.rec_state_in_way, 16))[2:].zfill(CCF_COH_DEFINES.max_num_of_tag_ways)[i] == "1":
                                    VAL_UTDB_ERROR(time=new.rec_time, msg="llc_chk_failure: Invalidating line can't be in the same time with Vulnerable line eviction. URI = " + new.rec_tid)

                                special_entry.state = "I"
                                special_entry.cv = self.llc_ref_db[s][h][new.rec_set][t][-1].cv
                                special_entry.address = self.llc_ref_db[s][h][new.rec_set][t][-1].address
                                self.append_line_to_ref_db(special_entry, 1)

                            if self.is_field_valid(new.rec_state_in_way) and (bin(int(new.rec_state_in_way, 16))[2:].zfill(CCF_COH_DEFINES.max_num_of_tag_ways)[i] == "1"):
                                if accessed_way != new.rec_way:
                                    special_entry.state = "I"
                                    special_entry.address = self.llc_ref_db[s][h][new.rec_set][t][-1].address
                                    self.append_line_to_ref_db(special_entry, 1)
                                    if self.si.ccf_cov_en:
                                        self.ccf_llc_chk_cg.sample(silent_evict_accepted_cp=1)

    def run(self):
        self.preload_time = COH_GLOBAL.global_vars["PRELOAD_TIME"]
        self.c6_exit_times = COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"]
        if len(self.llc_rtl_db) != 0:
            self.sort_llc_rtl_db()

        for item in self.llc_rtl_db:
            self.check_lines(item)
        self.collect_coverage()
        self.dump_llc_ref()
        print("checking_llc ---> done")

    def dump_llc_ref(self):
        self.dump_llc_ref_db = {}
        for slice in self.llc_ref_db.keys():
            for half in self.llc_ref_db[slice].keys():
                for set in self.llc_ref_db[slice][half]:
                    for tag in self.llc_ref_db[slice][half][set]:
                        ref = self.llc_ref_db[slice][half][set][tag][-1]
                        if not self.is_field_valid(ref.time):
                            VAL_UTDB_ERROR(time=0, msg="llc_chk_failure: time is no valid")
                        if not self.is_field_valid(ref.address):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: address is no valid")
                        if not self.is_field_valid(ref.state):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: state is no valid")
                        if (ref.state != "I") and not self.is_field_valid(ref.map):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: map is no valid")
                        if (ref.state != "I") and (not self.is_field_valid(ref.cv)):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: cv is no valid")
                        if not self.is_field_valid(ref.tag_ecc):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: tag_ecc is no valid")
                        if not self.is_field_valid(ref.set):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: set is no valid")
                        if not self.is_field_valid(ref.half):
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: half is no valid")
                        if ((ref.state != "I") and not self.is_field_valid(ref.data)) and self.is_field_valid(ref.map) and int(ref.map) != CCF_COH_DEFINES.SNOOP_FILTER:
                            VAL_UTDB_ERROR(time=ref.time, msg="llc_chk_failure: data is no valid")
                        if (ref.address not in self.dump_llc_ref_db.keys()):
                            self.dump_llc_ref_db[ref.address] = ref
                        else:
                            VAL_UTDB_ERROR(time=0, msg="llc_chk_failure: dump_llc_ref already has a record in it")
        print("dumping_llc_ref ---> done")

    def update_llc_refmodel(self, new):
        should_update_something = 0
        ref = llc_refmodel_entry()
        s = new.get_slice_num()
        h = new.get_half()
        first_access_to_this_line = 1
        if s in self.llc_ref_db.keys():
            if h in self.llc_ref_db[s].keys():
                if new.rec_set in self.llc_ref_db[s][h]:
                    if new.rec_tag_ecc in self.llc_ref_db[s][h][new.rec_set]:
                        first_access_to_this_line = 0
                        ref = copy.copy(self.llc_ref_db[s][h][new.rec_set][new.rec_tag_ecc][-1])

        ref.time = new.rec_time
        ref.slice = s
        ref.half = h
        ref.set = new.rec_set
        ref.tag_ecc = new.rec_tag_ecc
        ref.address = new.rec_address

        if self.is_field_valid(new.rec_new_state):
            ref.state = new.rec_new_state
            ref.map = new.rec_new_map
            ref.way = new.rec_way
            should_update_something = 1
        elif self.is_field_valid(new.rec_state) and (new.rec_opcode in self.state_update_ops):
            ref.state = new.rec_state
            ref.map = new.rec_map
            ref.way = new.rec_way
            should_update_something = 1
        elif "LR" in new.rec_opcode:
            if new.rec_hitmiss == "Hit":
                ref.state = new.rec_state
                ref.map = new.rec_map
                ref.way = new.rec_way
                if self.si.ccf_cov_en:
                    self.ccf_llc_chk_cg.sample(hitmiss_cp=1)
            elif new.rec_hitmiss == "Miss":
                ref.state = "I"
                ref.map = None
                if self.si.ccf_cov_en:
                    self.ccf_llc_chk_cg.sample(hitmiss_cp=0)

        if self.is_field_valid(new.rec_cv_wr):
            ref.cv = new.rec_cv_wr
            should_update_something = 1
        elif first_access_to_this_line == 1:
            ref.cv = "0".zfill(CCF_COH_DEFINES.num_physical_cv_bits)
        #if we're in 1st transaction ever to this line and there is no CV write_en, it must be 0 because of llc_init
        elif self.is_field_valid(new.rec_cv_rd):
            if new.rec_opcode in self.cv_updates_ops and ref.cv != new.rec_cv_rd:
                VAL_UTDB_ERROR(time=new.rec_time, msg="llc_chk_cv_mismatch on LLC " + str(s) + ", half " + str(h) + " : on URI = " + new.rec_tid + " cv_read = " + new.rec_cv_rd + " cv_ref = " + ref.cv)
            else:
                ref.cv = new.rec_cv_rd


        if ((new.rec_state != "I" and new.rec_map != str(CCF_COH_DEFINES.SNOOP_FILTER)) or (new.rec_new_state != "I" and new.rec_new_map != str(CCF_COH_DEFINES.SNOOP_FILTER))) and ("Wd" in new.rec_opcode):
            ref.data = new.rec_data
            ref.data_ecc = new.rec_data_ecc
            should_update_something = 1

        if should_update_something == 1:
            self.append_line_to_ref_db(ref, 0)

        if self.is_field_valid(new.rec_state_wr_way):
            self.add_special_entry(new)

    def append_line_to_ref_db(self, ref, sort):
        if (ref.set not in self.llc_ref_db[ref.slice][ref.half].keys()):
            self.llc_ref_db[ref.slice][ref.half][ref.set] = {}
            self.llc_ref_db[ref.slice][ref.half][ref.set][ref.tag_ecc] = [ref]
        else:
            if (ref.tag_ecc not in self.llc_ref_db[ref.slice][ref.half][ref.set].keys()):
                self.llc_ref_db[ref.slice][ref.half][ref.set][ref.tag_ecc] = [ref]
            else:
                self.llc_ref_db[ref.slice][ref.half][ref.set][ref.tag_ecc].append(ref)

        if sort == 1:
           self.llc_ref_db[ref.slice][ref.half][ref.set][ref.tag_ecc].sort(key=llc_refmodel_entry.get_time)

    def is_rec_inside_llc_ref(self, l):
        return l.get_slice_num() in self.llc_ref_db.keys() and l.get_half() in self.llc_ref_db[l.get_slice_num()].keys()\
            and l.rec_set in self.llc_ref_db[l.get_slice_num()][l.get_half()] and\
            l.rec_tag_ecc in self.llc_ref_db[l.get_slice_num()][l.get_half()][l.rec_set]

    def clear_llc_ref_if_we_passed_c6(self, t):
        if t > self.c6_exit_times[0]:
            self.llc_ref_db = self.ccf_llc_db_agent_i.init_llc_db()
            print("C6 Exit time : " + str(self.c6_exit_times[0]) + " -> clearing llc_ref db")
            del self.c6_exit_times[0]


    def check_lines(self, line):
        if line.rec_time > self.preload_time:
            if self.si.ccf_cov_en:
                self.collect_common_coverage(line)
            if len(self.c6_exit_times) != 0:
                self.clear_llc_ref_if_we_passed_c6(line.rec_time)
            self.check_way_valid(line)
            self.check_map_valid(line)
            self.check_hitmiss(line)

            if self.is_rec_inside_llc_ref(line):
                self.check_same_tag_different_way(line)
                self.check_same_map_different_way(line)
                ref = self.llc_ref_db[line.get_slice_num()][line.get_half()][line.rec_set][line.rec_tag_ecc][-1]

                if ref.state != "I":
                    self.check_cv(line, ref)
                    if int(ref.map) != CCF_COH_DEFINES.SNOOP_FILTER:
                        self.check_data(line, ref)
                    self.check_state(line, ref)

            self.update_llc_refmodel(line)
        else:
            VAL_UTDB_MSG(time=line.rec_time,
                           msg="llc_chk_msg: LLC was accessed before preload time. URI = " + line.rec_tid + " . Won't be checked. Preload_time = " + str(self.preload_time))

    def collect_common_coverage(self, line : ccf_llc_record_info):
        if self.is_field_valid(line.rec_half):
            self.ccf_llc_chk_cg.sample(llc_half_cp=int(line.rec_half))
        if self.is_field_valid(line.rec_unit):
            self.ccf_llc_chk_cg.sample(llc_slice_cp=line.get_slice_num())
        if self.is_field_valid(line.rec_set):
            self.ccf_llc_chk_cg.sample(set_cp=int(line.rec_set, 16))
        if self.is_field_valid(line.rec_opcode):
            self.ccf_llc_chk_cg.sample(llc_uop_cp=line.rec_opcode)
        if self.is_field_valid(line.rejected):
            self.ccf_llc_chk_cg.sample(reject_cp=line.rejected)
        #if self.is_field_valid(line.rec_lru_rd):
        #    self.ccf_llc_chk_cg.sample(lru_cp=line.rec_lru_rd)
        if self.is_field_valid(line.rec_cv_rd):
            cv_rd = bint(int(line.rec_cv_rd, 2))
            for cv_index in range(CCF_COH_DEFINES.num_physical_cv_bits):
                if cv_rd[cv_index] == 1:
                    self.ccf_llc_chk_cg.sample(cv_cp=cv_index)
        if self.is_field_valid(line.rec_state_vl_way):
            self.ccf_llc_chk_cg.sample(vul_accepected_cp=1)


    def check_same_tag_different_way(self, r):
        for i in self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set].keys():
            if self.is_field_valid(self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][r.rec_tag_ecc][-1].state):
                current_state = self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][i][-1].state
                current_way = self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][i][-1].way

                if self.is_field_valid(r.rec_way) and (current_state != "I"):
                    if (int(r.rec_way) != int(current_way)) and ("I" not in current_state) and r.rec_tag_ecc == i:
                        VAL_UTDB_ERROR(time=r.rec_time, msg="llc_chk_failure: Same Tag = " + i + " but a different way. current access way = " + r.rec_way + ", other one = " + current_way \
                                                            + " slice = " + str(r.get_slice_num()) + " half = " + str(r.get_half()) + " TID = " + r.rec_tid)
    def check_same_map_different_way(self, r):
        for i in self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set].keys():
            if self.is_field_valid(self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][r.rec_tag_ecc][-1].state):
                current_state = self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][i][-1].state
                current_way = self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][i][-1].way

                if self.is_field_valid(r.rec_way) and (current_state != "I"):
                    if (int(r.rec_way) != int(current_way)) and ("I" not in current_state) and r.rec_map == self.llc_ref_db[r.get_slice_num()][r.get_half()][r.rec_set][i][-1].map and r.rec_map != str(CCF_COH_DEFINES.SNOOP_FILTER):
                        VAL_UTDB_ERROR(time=r.rec_time, msg="llc_chk_failure: Same map = " + r.rec_map + " but a different way. current access way = " + r.rec_way + ", other one = " + current_way \
                                                            + " slice = " + str(r.get_slice_num()) + " half = " + str(r.get_half()) + " TID = " + r.rec_tid)

    def check_hitmiss(self, rec):
        if self.is_field_valid(rec.rec_hitmiss_vector):
            tmp = bin(int(rec.rec_hitmiss_vector, 16))[2:].zfill(CCF_COH_DEFINES.max_num_of_tag_ways)
            count = 0
            for i in range(len(tmp)):
                count += int(tmp[i])
            if count > 1:
                VAL_UTDB_ERROR(time=rec.rec_time, msg="llc_chk_failure: Hitmiss Vector cannot be more than 1")

    def check_map_valid(self, rec):
        if self.is_field_valid(rec.rec_map):
            if int(rec.rec_map) != CCF_COH_DEFINES.SNOOP_FILTER and int(rec.rec_map) >= self.si.num_of_opened_data_ways:
                VAL_UTDB_ERROR(time=rec.rec_time, msg="llc_chk_failure: Map = " + rec.rec_map + " is not valid. Max num of data ways is " + str(self.si.num_of_opened_data_ways))
            elif self.si.ccf_cov_en:
                self.ccf_llc_chk_cg.sample(llc_data_way_cp=int(rec.rec_map))

        if self.is_field_valid(rec.rec_new_map):
            if int(rec.rec_new_map) != CCF_COH_DEFINES.SNOOP_FILTER and int(rec.rec_new_map) >= self.si.num_of_opened_data_ways:
                VAL_UTDB_ERROR(time=rec.rec_time, msg="llc_chk_failure: Late Map = " + rec.rec_new_map + " is not valid. Max num of data ways is " + str(self.si.num_of_opened_data_ways))
            elif self.si.ccf_cov_en:
                self.ccf_llc_chk_cg.sample(llc_data_way_cp=int(rec.rec_new_map))

    def check_way_valid(self, rec):
        if self.is_field_valid(rec.rec_way):
            if int(rec.rec_way) >= CCF_COH_DEFINES.max_num_of_tag_ways:
                VAL_UTDB_ERROR(time=rec.rec_time, msg="llc_chk_failure: Way = " + rec.rec_way + " is not valid. Max num of tag ways is " + str(CCF_COH_DEFINES.max_num_of_tag_ways))
            elif self.si.ccf_cov_en:
                self.ccf_llc_chk_cg.sample(llc_tag_way_cp=int(rec.rec_way))

    def check_cv(self, rtl, ref):
        if self.is_field_valid(rtl.rec_cv_rd):
            if (rtl.rec_state != "I") and (rtl.rec_opcode not in self.cv_updates_ops) and (rtl.rec_cv_rd != ref.cv):
                out_err_msg = "llc_chk_failure: CV mismatch on " + rtl.rec_unit + ", Set = " + rtl.rec_set + "\n REF = " + str(ref.time) + " : " + ref.cv + "\n RTL = " + str(rtl.rec_time) + " : " + rtl.rec_cv_rd
                VAL_UTDB_ERROR(time=rtl.rec_time, msg=out_err_msg)

    def check_state(self, rtl, ref):
        if self.is_field_valid(rtl.rec_state):
            if (rtl.rec_state != ref.state) and (rtl.rec_opcode not in self.state_update_ops):
                out_err_msg = "llc_chk_failure: State mismatch on " + rtl.rec_unit + ", Set = " + rtl.rec_set + ", Way = " + rtl.rec_way  + "\n" + "REF: " + str(ref.time) + " : " + ref.state + "\n" + "RTL: " + str(rtl.rec_time) + " : " + rtl.rec_state
                VAL_UTDB_ERROR(time=rtl.rec_time, msg=out_err_msg)

    def check_data(self, rtl, ref):
        data_error = 0
        data_ecc_error = 0
        if rtl.rec_state != "I" and self.is_field_valid(rtl.rec_data) and rtl.rec_map != str(CCF_COH_DEFINES.SNOOP_FILTER) and ("Wd" not in rtl.rec_opcode) and (rtl.rec_opcode != "LRsUcl"):
            if self.si.ccf_preload_data_correctable_errs == 0:
                data_error = (rtl.rec_data != ref.data)
                data_ecc_error = (rtl.rec_data_ecc != ref.data_ecc)
            else:
                dist_data = CCF_FLOW_UTILS.get_distance(rtl.rec_data, ref.data)
                dist_ecc  = CCF_FLOW_UTILS.get_distance(rtl.rec_data_ecc, ref.data_ecc)
                total_dist = dist_data + dist_ecc
                if total_dist > 1 :
                    data_error = (dist_data > 0)
                    data_ecc_error = (dist_ecc > 0)

        if data_error == 1:
            out_err_msg = "llc_chk_failure: Data mismatch on " + rtl.rec_unit + ", Set = " + rtl.rec_set + "\n" + "REF: " + str(
                ref.time) + " : " + ref.data + "\n" + "RTL: " + str(rtl.rec_time) + " : " + rtl.rec_data
            VAL_UTDB_ERROR(time=rtl.rec_time, msg=out_err_msg)

        if data_ecc_error == 1:
            out_err_msg = "llc_chk_failure: Data_ecc mismatch on " + rtl.rec_unit + ", Set = " + rtl.rec_set + "\n" + "REF: " + str(
                ref.time) + " : " + ref.data_ecc + "\n" + "RTL: " + str(rtl.rec_time) + " : " + rtl.rec_data_ecc
            VAL_UTDB_ERROR(time=rtl.rec_time, msg=out_err_msg)


    def is_field_valid(self, field):
        return (field != None and (field != "-") and (field != "--") and (field != ""))

