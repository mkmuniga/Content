from agents.ccf_agent.ccf_data_chk_agent.ccf_data_chk_cov import CCF_DATA_CHK_CG
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base import memory_data_entry, ccf_cbo_record_info, ccf_ufi_record_info, \
    ccf_idi_record_info
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from collections import OrderedDict
from val_utdb_report import VAL_UTDB_ERROR, EOT

class ccf_data_chk(ccf_coherency_base_chk):
    def __init__(self):
        self.checker_name = "ccf_data_chk"
        self.u2c_data_chunk_count = {}
        self.c2s_data_chunk_count = {}
        self.temp_fragmented_data_write = {}
        self.ccf_data_chk_cg = CCF_DATA_CHK_CG.get_pointer()

    def sort_dbs(self):
        ccf_dbs.sort_ccf_flows()
        self.sort_mem_db()

    def sort_mem_db(self):
        for addr in self.mem_db.keys():
            self.mem_db[addr].sort(key=memory_data_entry.get_time)
        ccf_dbs.sort_mem_db()

    def check_core_got_crababort_data(self, flow: ccf_flow):
        for tran in flow.flow_progress:
            if (type(tran) is ccf_idi_record_info) and (tran.is_u2c_data_if()):
                if any([True for char in tran.data.replace(" ", "") if ((char != "f") and (char != "-"))]):
                    err_msg = "(check_core_got_crababort_data): {} - SAD is CRABABORT but data is not all ones. Actual data is: {}".format(flow.uri['TID'], tran.data)
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def check_flow(self, flow):
        if flow.sad_results == "CRABABORT":
            self.check_core_got_crababort_data(flow)
        else:
            for idx in range(len(flow.flow_progress)):
                self.check_flow_progress(flow, idx)

    def should_check_flow(self, flow):
        if super().should_check_flow(flow) and self.should_check_sad(flow) and (flow.opcode not in CCF_FLOW_UTILS.idi_addressless_opcodes) \
                and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
                and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
                and not flow.is_u2c_dpt_req():
            return 1

    def should_check_sad(self, flow):
        return (flow.sad_results not in ["CFG"])
    #CFG is a region that might have changes in address when txn gets to CFI. will be checked by Ran

    def check_flow_progress(self, flow, idx):
        if self.is_u2c_read(flow, idx):
            self.check_u2c_data(flow, idx)
        elif self.is_llc_write(flow, idx):
            self.check_llc_data_write(flow, idx)
        elif self.is_cfi_write(flow, idx):
            self.check_cfi_data_write(flow, idx)

        self.collect_coverage()

    def check_cfi_data_write(self, flow, idx):
        if flow.uri["LID"] in self.c2s_data_chunk_count:
            if self.c2s_data_chunk_count[flow.uri["LID"]] == 1:
                if flow.sad_results != "HOM":
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[0].address)
                else:
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[idx].address)
                actual = self.get_actual_rec(flow, idx, address, "WRITE_TO_MEM")
                expected = self.get_expected_cfi_data(flow, actual, address)
                if expected != None and self.mem_db[address][expected] != None:
                    if flow.flow_progress[idx].rec_opcode not in ["NcWrPtl", "WcWrPtl"]:
                        if self.check(address, self.mem_db[address][expected], self.mem_db[address][actual]) == 1:
                            if self.si.ccf_cov_en:
                                self.ccf_data_chk_cg.sample(cfi_write_chks=1, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)
                    else:
                        frag_num = int(bin(int(flow.flow_progress[idx].rtid, 16))[2:].zfill(8)[:3], 2)
                        if flow.uri["LID"] not in self.temp_fragmented_data_write:
                            self.temp_fragmented_data_write[flow.uri["LID"]] = {}

                        self.temp_fragmented_data_write[flow.uri["LID"]][frag_num] = memory_data_entry()
                        self.temp_fragmented_data_write[flow.uri["LID"]][frag_num].cache_type = self.mem_db[address][actual].cache_type
                        self.temp_fragmented_data_write[flow.uri["LID"]][frag_num].time = self.mem_db[address][actual].time
                        self.temp_fragmented_data_write[flow.uri["LID"]][frag_num].data = self.mem_db[address][actual].data
                        how_many = self.calculate_how_many_fragments_should_be_sent(address, expected)
                        if len(self.temp_fragmented_data_write[flow.uri["LID"]]) == how_many:
                            actual_entry = memory_data_entry()
                            actual_entry.data = self.fix_fragmented_data(address, expected, flow)
                            actual_entry.time = self.temp_fragmented_data_write[flow.uri["LID"]][how_many-1].time
                            actual_entry.cache_type = self.temp_fragmented_data_write[flow.uri["LID"]][how_many-1].cache_type

                            if self.check(address, self.mem_db[address][expected], actual_entry) == 1:
                                self.temp_fragmented_data_write.pop(flow.uri["LID"])
                                if self.si.ccf_cov_en:
                                    self.ccf_data_chk_cg.sample(cfi_write_chks=1, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)

                    self.c2s_data_chunk_count.pop(flow.uri["LID"])
                else:
                    if self.si.ccf_cov_en:
                        self.ccf_data_chk_cg.sample(cfi_write_chks=0, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)
            else:
                self.c2s_data_chunk_count[flow.uri["LID"]] +=1
        else:
            self.c2s_data_chunk_count[flow.uri["LID"]] = 1

    # This function aims to calcaulate a correct data fragment number.
    # it depends if the full_byte_en for the relevant quadrant is "00".
    # if it is 00, the counting skips on this quadrant.
    # example:
    # for full byte_en = ffff_ffff_ffff_ffff we will get 8 CFI writes
    # if full_byte_en = ff00_ffff_ffff_ffff, we will get 7 chunks.

    def calculate_how_many_fragments_should_be_sent(self, address, expected):
        counter = 0
        for part in range(8):
            if not self.is_byteen_zero(address, expected, part):
                counter+=1
        return counter

    def fix_fragmented_data(self, address, expected, flow):
        assembled_data = ""
        skipped_part = 0
        for part in range(8):
            if self.is_byteen_zero(address, expected, part):
                assembled_data = '----------------' + assembled_data
            else:
                assembled_data = self.temp_fragmented_data_write[flow.uri["LID"]][skipped_part].data[((7-part)*16):((8-part)*16)] + assembled_data
                skipped_part+=1
        return assembled_data

    def is_byteen_zero(self, address, expected, part_num):
        return self.mem_db[address][expected].byteen[(7-part_num)*2:(8-part_num)*2] == "00"

    def check_u2c_data(self, flow, idx):
        if flow.uri["LID"] in self.u2c_data_chunk_count:
            if self.u2c_data_chunk_count[flow.uri["LID"]] == 1:
                if flow.opcode in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes_on_idi:
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(self.special_address_db.get_real_address_by_uri(flow.uri["TID"]))
                else:
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[idx].address)
                actual = self.get_actual_rec(flow, idx, address, "U2C_DATA")
                expected = self.get_expected_u2c_data(flow, actual, address)
                if expected != None and self.mem_db[address][expected] != None and flow.sad_results == "HOM":
                    if self.is_core_still_own_the_line(self.mem_db[address], self.mem_db[address][actual]) and self.should_check_expected(self.mem_db[address][expected]):
                        partial_expected = memory_data_entry()
                        partial_expected.data = self.extract_partial_data_if_needed(self.mem_db[address][expected].data, flow.flow_progress[0])
                        partial_expected.cache_type = self.mem_db[address][expected].cache_type
                        partial_expected.access_type = self.mem_db[address][expected].access_type
                        partial_expected.time = self.mem_db[address][expected].time
                        if self.check(address, partial_expected, self.mem_db[address][actual]) == 1:
                            if self.si.ccf_cov_en:
                                self.ccf_data_chk_cg.sample(core_write_chks=1, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)
                    else:
                        if self.si.ccf_cov_en:
                            self.ccf_data_chk_cg.sample(core_write_chks=0, opcodes=flow.opcode.upper(),
                                                        sad_result=flow.sad_results)
                    self.u2c_data_chunk_count.pop(flow.uri["LID"])
                else:
                    if self.si.ccf_cov_en:
                        self.ccf_data_chk_cg.sample(core_write_chks=0, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)
            else:
                self.u2c_data_chunk_count[flow.uri["LID"]] += 1
        else:
            self.u2c_data_chunk_count[flow.uri["LID"]] = 1

    def should_check_expected(self, expected):
        return (not ("MLC" in expected.cache_type and expected.state == "M"))

    def is_core_still_own_the_line(self, rec_list, actual):
        response_i_found = 0
        for i in range(-1, -1 * (len(rec_list)) - 1, -1):
            rec = rec_list[i]
            if rec.time < actual.time and "MLC" in actual.cache_type and actual.cache_type == rec.cache_type:
                if rec.access_type == "STATE_RSP_UPDATE" and "->I" in rec.state:
                    response_i_found = 1
                elif rec.access_type == "GO_STATE_UPDATE" and rec.tid == actual.tid and rec.state != "I":
                    if response_i_found == 1:
                        return False
                    else:
                        return True
        return True

    def check_llc_data_write(self, flow, idx):
        address = flow.flow_progress[idx].get_llc_aligned_address()
        actual = self.get_actual_rec(flow, idx, address, "WRITE_TO_LLC")
        expected = self.get_expected_llc_data(flow, actual, address)
        #TO: need to review the sad_results in case of noUn HOM sad that going to upi_nc
        #The other condition is when data_chk consider the wrong expected because it was preloaded and the actual was received by SB VC
        #which is not connected to address_db
        if expected != None and self.mem_db[address][expected] != None and flow.sad_results == "HOM":
            if self.check(address, self.mem_db[address][expected], self.mem_db[address][actual]) == 1:
                if self.si.ccf_cov_en:
                    self.ccf_data_chk_cg.sample(llc_write_chks=1, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)
        else:
            if self.si.ccf_cov_en:
                self.ccf_data_chk_cg.sample(llc_write_chks=0, opcodes=flow.opcode.upper(), sad_result=flow.sad_results)

    def check(self, address, entry1, entry2):
        if entry2.tid != None:
            uri_str = ", URI = " + entry2.tid
        else:
            uri_str = ""
        dist_data = CCF_FLOW_UTILS.get_distance(entry1.data, entry2.data)
        if dist_data > 1:
            out_err_msg = "data_chk_failure: data mismatch for address = " + address + uri_str  + "\n" + "EXP: " + \
                          entry1.cache_type.split("_")[0] + " = " + entry1.data + "\n" +\
                          "ACT: " + entry2.cache_type.split("_")[0] + " = " + entry2.data
            VAL_UTDB_ERROR(time=entry2.time, msg=out_err_msg)
        else:
            return 1

    def get_actual_rec(self, flow, idx, address, cond):
        saved = None
        for rec in self.mem_db[address]:
            if (rec.time <= flow.flow_progress[idx].rec_time):
                qualifier = (rec.tid != None and rec.tid == flow.uri["TID"]) or rec.tid == None
                if rec.data != None and cond in rec.access_type and qualifier:
                    saved = rec
            else:
                return self.mem_db[address].index(saved)
        if saved != None:
            return self.mem_db[address].index(saved)
        else:
            err_str = "data_chk_failure: No Actual " + cond + " was found in address_db for LID: " + flow.uri["LID"] + " " + "address: " + address + " for time: " + str(flow.flow_progress[idx].rec_time)
            self.dump_fatal_error(err_str)


    # write to memory of full_lines CFI Writes
    #  (WILF/WCILF/WbMtoE/WbMtoI with no bogus etc) -> data from core
    #  else  - get most updated data - LLCM  or FwdM
    #   WbMtoIPtl - Partial writes to mem -> data from core

    # Write to LLC
    # WbMtoI/E with no bogus
    # Read from CFI
    # FwdM

    # Read to Core U2C / Write to MLC
    # Read from CFI
    # Read From LLC
    # Fwd*

    def create_mlc_array(self):
        array = {}
        for i in range(self.si.num_of_cbo):
            array.update({"MLC_" + str(i): 0})
        return array


    def get_expected_cfi_data(self, flow ,actual, address):
        if address in self.mem_db.keys():
            mlc_was_invalidated = self.create_mlc_array()
            for i in range((actual-1), -1, -1):
                rec = self.mem_db[address][i]
                if "UPI_" in flow.uri["TID"]:
                    if rec.access_type == "C2U_DATA_RSP":
                        if not self.is_first_accept_time_in_cbo_ok(flow, rec):
                            return self.mem_db[address].index(rec)
                    elif "LLC" in rec.cache_type:
                        if not self.is_first_accept_time_in_cbo_ok(flow, rec):
                            return self.mem_db[address].index(rec)
                    elif rec.access_type == "C2U_DATA":
                        if not self.is_first_accept_time_in_cbo_ok(flow, rec):
                            return self.mem_db[address].index(rec)
                else:
                    if rec.is_m():
                        if "MLC" in rec.cache_type and mlc_was_invalidated[rec.cache_type] == 0:
                            return self.get_core_data_entry(flow, self.mem_db[address][0:i])
                        elif "LLC" in rec.cache_type:
                            return self.mem_db[address].index(rec)

                    elif "C2U_DATA" in rec.access_type:
                        return self.mem_db[address].index(rec)
                    elif "LLC" in rec.cache_type and rec.state != "I":
                        return self.mem_db[address].index(rec)
                    elif rec.access_type == "GO_STATE_UPDATE" and rec.state == "I":
                        mlc_was_invalidated[rec.cache_type] = 1

            err_str = "data_chk_failure: No expected CFI was found for LID: " + flow.uri["LID"] + " " + "address: " + address
            self.dump_fatal_error(err_str)
        else:

            err_str = "data_chk_failure: No address = " + address + " was found in address_db for time =  " + self.mem_db[address][actual].time
            self.dump_fatal_error(err_str)


    def is_first_accept_time_in_cbo_ok(self, flow: ccf_flow, rec):
        if rec.tid != None and (self.ccf_flows[rec.tid].is_c2u_data_write_flow_opcode() or self.ccf_flows[rec.tid].snoop_rsp_m()):
            if not flow.had_conflict:
                return self.ccf_flows[rec.tid].first_accept_time > flow.first_accept_time
            elif flow.had_conflict and (self.ccf_flows[rec.tid].read_data_from_mem() or self.ccf_flows[rec.tid].is_one_of_uxi_opcodes_exist_in_flow(["InvItoE", "InvItoM"]), ccf_ufi_record_info):
                for i in self.ccf_flows[rec.tid].flow_progress:
                    if (type(i) == ccf_cbo_record_info) and ("CmpO" in i.rec_opcode):
                        cmpo_time = i.rec_time
                return cmpo_time > flow.first_accept_time
        else:
            return False

    def is_pipe_accept_time_ok(self, actual_flow: ccf_flow, expected_rec):
        if expected_rec.tid != None:#means not preload
            return (self.ccf_flows[expected_rec.tid].first_accept_time < actual_flow.first_accept_time)

    def get_expected_u2c_data(self, flow ,actual, address):
        if address in self.mem_db:
            for i in range((actual - 1), -1, -1):
                rec = self.mem_db[address][i]
                #check from LLC or MEM
                if rec.cache_type == "MEM":
                    if rec.tid == self.mem_db[address][actual].tid:
                        return self.mem_db[address].index(rec)
                    elif flow.is_flow_promoted() and flow.promotion_flow_orig_pref_uri != None and rec.tid == flow.promotion_flow_orig_pref_uri:
                        return self.mem_db[address].index(rec)

                # in case that MLC already in M and received a new U2C_DATA from LLC, it should drop it
                elif "LLC" in rec.cache_type:
                    if self.is_pipe_accept_time_ok(flow, rec) and rec.is_m():
                        return self.mem_db[address].index(rec)
                    elif rec.tid == self.mem_db[address][actual].tid:
                        return self.mem_db[address].index(rec)
                    elif rec.state in ["E", "S"]:
                        if self.is_pipe_accept_time_ok(flow, rec) or "PRELOAD" in rec.access_type:
                            #in case of race, another flow can accepeted in the pipe before this flow and update the LLC states
                            return self.mem_db[address].index(rec)
                    elif rec.state == "M" and "PRELOAD" in rec.access_type:
                        return self.mem_db[address].index(rec)


                elif "C2U_DATA" in rec.access_type and flow.uri["TID"] == rec.tid:
                    return self.mem_db[address].index(rec)
            if flow.sad_results == "HOM":
                err_str = "data_chk_failure: No expected U2C was found for LID: " + flow.uri["LID"] + " " + "address: " + address
                self.dump_fatal_error(err_str)
        else:

            err_str = "data_chk_failure: No address = " + address + " was found in address_db for time =  " + self.mem_db[address][actual].time
            self.dump_fatal_error(err_str)


    def get_expected_llc_data(self, flow ,actual, address):
        if address in self.mem_db:
            buried_m = flow.is_idi_flow_origin() and flow.req_core_initial_cv_bit_is_one() and flow.initial_cv_one() and not flow.is_selfsnoop() \
                       and flow.initial_map_sf() and flow.initial_state_llc_m_or_e() and (flow.is_drd() or flow.is_crd() or flow.is_rfo())
            llc_or_mlc_is_m = flow.initial_state_llc_m() or (flow.initial_state_llc_e() and (flow.snoop_rsp_m() or flow.is_wbmtoi() or flow.is_wbmtoe()))
            dont_check_mem = llc_or_mlc_is_m and not buried_m
            for i in range((actual - 1), -1, -1):
                rec = self.mem_db[address][i]
                if (not dont_check_mem) and rec.cache_type == "MEM":
                    if (rec.tid != self.mem_db[address][actual].tid): #in case of a race in the pipe
                        if self.is_pipe_accept_time_ok(flow, rec): # and (self.mem_db[address][actual].state != "M"):
                            return self.mem_db[address].index(rec)
                    else:
                        return self.mem_db[address].index(rec)
                elif "MLC" in rec.cache_type and "C2U_DATA" in rec.access_type:
                        return self.mem_db[address].index(rec)
                elif rec.is_m():
                    return self.get_write_source_for_llc(flow, self.mem_db[address][0:i])
                elif flow.is_possible_evict_in_read_flow():
                    if "C2U_DATA" in rec.access_type:
                        return self.mem_db[address].index(rec)
                    elif "MLC" in rec.cache_type and rec.is_m():
                        return self.get_core_data_entry(flow, self.mem_db[address][0:i])

            if flow.sad_results == "HOM":
                err_str = "data_chk_failure: No expected llc was found for LID: " + flow.uri["LID"] + "address: " + address
                self.dump_fatal_error(err_str)
        else:
            err_str = "data_chk_failure: No address = " + address + " was found in address_db for time =  " + self.mem_db[address][actual].time
            self.dump_fatal_error(err_str)

    #In case we are in LLC_M and Map=Dway and snoop response is RspI We may write to the LLC the same data we read in the lookup
    #That mean that in this case we don't want to force ourself to search the data in the same flow and we allow to
    #search the data in other flow prior to our flow according to the order.
    def write_source_for_llc_extra_condition(self, flow: ccf_flow, rec):
        if flow.initial_state_llc_m() and flow.snoop_rsp_i() and flow.initial_map_dway():
            return True
        else:
            return (rec.tid == flow.uri["TID"])

    def get_write_source_for_llc(self, flow, dict):
        for i in range(-1, -1 * len(dict) - 1, -1):
            rec = dict[i]
            if rec.data != None and self.write_source_for_llc_extra_condition(flow, rec) and ("MLC" in rec.cache_type or rec.cache_type == "MEM"):
                return dict.index(rec)
            elif rec.cache_type == "MEM" and flow.is_flow_promoted() and flow.promotion_flow_orig_pref_uri != None and rec.tid == flow.promotion_flow_orig_pref_uri:
                return dict.index(rec)
        if flow.sad_results == "HOM":
            err_str = "data_chk_failure: No expected LLC Write data was found in address_db for LID: " + flow.uri["LID"]
            self.dump_fatal_error(err_str)

    def get_core_data_entry(self, flow, dict):
        for i in range(-1, -1 * len(dict) - 1, -1):
            rec = dict[i]
            if rec.data != None and rec.tid == flow.uri["TID"] and "MLC" in rec.cache_type:
                return dict.index(rec)

        if flow.sad_results == "HOM":
            err_str = "data_chk_failure: No expected data was found in address_db for LID: " + flow.uri["LID"]
            self.dump_fatal_error(err_str)

    def extract_partial_data_if_needed(self, data, req):
        offset = CCF_FLOW_UTILS.get_address_offset(req.address)
        if req.rec_len != None and req.rec_len != '00':
            length = int(req.rec_len, 16)
            pad = ''
            raw_partial_data = data[(128 - 2 * offset - 2 * length):(128 - 2 * offset)]
            for i in range(128 - 2 * offset - 2 * length):
                pad = pad + '-'
            pad = pad + raw_partial_data
            for i in range(2 * offset):
                pad = pad + '-'
        else:
            pad = data
        return pad

    def is_u2c_read(self, flow, idx):
        return flow.flow_progress[idx].is_record_belong_to_interface("IDI") and flow.flow_progress[idx].rec_idi_interface == "U2C DATA"

    def is_c2u_data(self, flow, idx):
        return flow.flow_progress[idx].is_record_belong_to_interface("IDI") and flow.flow_progress[idx].rec_idi_interface == "C2U DATA"

    def is_cfi_write(self, flow, idx):
        return flow.flow_progress[idx].is_record_belong_to_interface("CFI") and flow.flow_progress[idx].is_cfi_write_data()

    def is_llc_write(self, flow, idx):
        return flow.flow_progress[idx].is_record_belong_to_interface("LLC") and flow.flow_progress[idx].is_wr_data_uop()

    def dump_fatal_error(self, err_str):
        VAL_UTDB_ERROR(time=EOT, msg=err_str)


        #Old
        #core writebacks (*toI/E) - are the most updated data
        #if bogus data (it can come only from core)  ->  it is not updated -> won't be written to CFI
        #snoop responses - "fwd" are the most updated .
        #partial writes
        #if modified data - there  will be 2 writes:
        # 1 full line with M data
        # 2 -partial write with data from core
        #Evict cases: only if state = M it is relevent (same os #1)
        #else - LLC
        # if flows initiated by HBO (snoop) -> if state != M /FwdM from core, no snp_response will be sent
        #special case - data came

