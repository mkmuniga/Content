from agents.ccf_common_base.ccf_common_base import ccf_llc_record_info, llc_refmodel_entry
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES

class ccf_llc_db_agent(ccf_base_agent):

    def reset(self):
        self.configure()
        self.llc_ref_db = self.init_llc_db()
        ccf_dbs.reset_llc_rtl_db()
        COH_GLOBAL.global_vars["PRELOAD_TIME"] = 0


    def init_llc_db(self):
        db = {}
        for cbo_num in range(self.si.num_of_cbo):
            db[cbo_num] = {}
            for half in range(2):
                db[cbo_num][half] = {}
        return db

    def update_llc_ref_db(self, new):# in use only for preloader
        ref = llc_refmodel_entry()
        ref.time = new.rec_time
        ref.slice = new.get_slice_num()
        ref.half = new.get_half()
        ref.set = new.rec_set
        ref.way = new.rec_way
        ref.map = new.rec_map
        ref.state = new.rec_state
        ref.tag_ecc = new.rec_tag_ecc
        ref.cv = bin(int(new.rec_cv, 16))[2:].zfill(CCF_COH_DEFINES.num_physical_cv_bits)
        ref.data = new.rec_data
        if self.is_field_valid(new.rec_data_ecc):
            ref.data_ecc = new.rec_data_ecc.zfill(5)
        ref.address = new.get_llc_aligned_address()
        COH_GLOBAL.global_vars["PRELOAD_TIME"] = ref.time

        self.append_line_to_ref_db(ref, 0)


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

    def get_llc_state(self, slice, half, set, way, time):
        state= "-"
        most_updated_entry_time = 0
        ref = self.llc_ref_db[slice][int(half)][set]
        for tag in ref:
            for i in range(-1, -1 * len(ref[tag]) - 1, -1):
                if (ref[tag][i].time < time) and (ref[tag][i].time > most_updated_entry_time) and str(int(ref[tag][i].way)) == str(way):
                    state = ref[tag][i].state
                    most_updated_entry_time = ref[tag][i].time
        return state


    def update_llc_rtl_db(self, new):
        entry = ccf_llc_record_info()

        entry.rejected = new.REJECTED
        entry.rec_half = int(new.HALF)
        entry.rec_set =  new.SET
        entry.rec_unit = new.UNIT
        entry.rec_opcode = new.OPCODE
        entry.rec_time = new.TIME
        entry.rec_way = new.WAY
        entry.rec_hitmiss = new.HIT_MISS
        entry.rec_tag_ecc = new.TAG_ECC

        if self.is_field_valid(entry.rec_tag_ecc):
            #if it is a special address and state = I, there is no meaning for the line, so tag won't printed
            entry.rec_tag_ecc = self.check_and_correct_tag_using_llc_rec(entry)
            entry.rec_address = entry.get_llc_aligned_address()
            entry.rec_map = new.MAP
            entry.rec_new_map = new.NEW_MAP

            if self.is_field_valid(new.STATE):
                entry.rec_state = new.STATE.split("LLC_")[1][0]

            if self.is_field_valid(new.NEW_STATE):
                entry.rec_new_state = new.NEW_STATE.split("LLC_")[1][0]

            if self.is_field_valid(new.CV_RD):
                entry.rec_cv_rd = bin(int(new.CV_RD, 16))[2:].zfill(CCF_COH_DEFINES.num_physical_cv_bits)

            if self.is_field_valid(new.CV_WR):
                cv = new.CV_WR.split("(")[0] if "(E)" in new.CV_WR else new.CV_WR
                entry.rec_cv_wr = bin(int(cv, 16))[2:].zfill(CCF_COH_DEFINES.num_physical_cv_bits)

            if self.is_field_valid(new.LRU_RD):
                entry.rec_lru_rd = bin(int(new.LRU_RD, 16))[2:].zfill(64)

            if self.is_field_valid(new.LRU_WR):
                entry.rec_lru_wr = bin(int(new.LRU_WR, 16))[2:].zfill(64)

            entry.rec_data = new.DATA.replace(" ","")
            entry.rec_arbcmd = new.ARBCMD
            entry.rec_tid = new.TID
            if self.is_field_valid(new.ECC):
                entry.rec_data_ecc = new.ECC.zfill(5)
            entry.rec_hitmiss_vector = new.HITMISS_VECTOR

            entry.rec_state_wr_way = new.STATE_WR_WAY
            entry.rec_state_in_way = new.STATE_IN_WAY
            entry.rec_state_vl_way = new.STATE_VL_WAY

            if len(self.llc_rtl_db) == 0:
                self.llc_rtl_db = [entry]
            else:
                self.llc_rtl_db.append(entry)

            delattr(entry, "rec_pid")

    def is_field_valid(self, field):
        return (field != None and "-" not in field and field != "")


    #When MCA_ECC is enabled, refmodel db is filled with correct values since it is taken from ccf_preload_trk
    #but llc_trks might have wrong values in tag when reading (because the read value is l2c_tag/l2c_tag_ecc)
    #in Writes, the correct values should appear in llc_trk since it is c2l_tag (after RTL correction)
    # so here we'll fix it manually
    #this lead us to understanding that if line[i] is with a corrupted tag (but correctable one), is must have the corrected tag in the ref model
    # -> refmdoel_db can't be empty in the same line.

    def check_and_correct_tag_using_llc_rec(self, rec):
        return self.check_and_correct_tag(slice_num=rec.get_slice_num(),
                                          half=rec.get_half(),
                                          set=rec.rec_set,
                                          tag_ecc=rec.rec_tag_ecc,
                                          time_for_err_print=rec.rec_time)

    def get_binary_tag(self, r):
        tmp = r.replace("(", "")
        tmp = tmp.replace(")", "")
        return bin(int(tmp, 16))[2:].zfill(50)

    def check_and_correct_tag(self, slice_num, half, set, tag_ecc, time_for_err_print):
        if set not in self.llc_ref_db[slice_num][half]:
            return tag_ecc
        for i in self.llc_ref_db[slice_num][half][set].keys():
            if i == tag_ecc:
                return tag_ecc
            else:
                income_bin_tag_ecc = self.get_binary_tag(tag_ecc)
                current_bin_tag_ecc = self.get_binary_tag(i)
                distance = CCF_FLOW_UTILS.get_distance(income_bin_tag_ecc, current_bin_tag_ecc)
                if distance == 1:
                    return i
                elif distance == 2:
                    if self.si.ccf_llc_chk_en:
                        str_msg = "llc_db_chk_failure: Uncorrectable Tag error in slice = " + str(slice_num) + " , half = " + str(half) + " , set = " + str(set) + " , ref_tag = " + i + " , income_tag = " + tag_ecc
                        VAL_UTDB_ERROR(time=time_for_err_print, msg=str_msg)
        return tag_ecc





