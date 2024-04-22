from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import  DBP_TO_MSCACHE_CG
from agents.ccf_common_base.ccf_registers import ccf_registers

from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from val_utdb_bint import bint

from agents.ccf_common_base.coh_global import COH_GLOBAL


class ccf_dbp_chk_and_update(ccf_coherency_base_chk):
    def __init__(self):
        super().__init__()
        self.checker_name = "ccf_dbp_chk_and_update"
        self.ccf_registers = ccf_registers.get_pointer()
        self.bin0_evictions = [0 for i in range(self.si.num_of_cbo)]
        self.bin1_evictions = [0 for i in range(self.si.num_of_cbo)]
        self.hit_in_bin0 = [0 for i in range(self.si.num_of_cbo)]
        self.hit_in_bin1 = [0 for i in range(self.si.num_of_cbo)]
        self.dbp_bx_to_core = dict()
        self.prev_trans_time = 0
        self.bad_params_for_core_observers = 0
        self.good_params_for_core_observers = 0
        self.core_bad_params_uri_list = []
        self.bad_dbpinfo_for_mscache_observers = 0
        self.good_dbpinfo_for_mscache_observers = 0
        self.bad_dbpinfo_for_mscache_uri_list = []
        self.c6_times = COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"].copy()


    def is_force_snoop_all_cb_en(self, flow: ccf_flow):
        if flow.cbo_id_phys is not None:
            return (self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("ingress_" + str(flow.cbo_id_phys),"flow_cntrl", "force_snoop_all",flow.first_accept_time) == 1)
        else:
            return False

    def config_dbp_initial_hits(self):
        self.c6_times = COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"].copy()
        self.reset_bin_counters()
        self.dbp_bx_to_core = dict()

    def reset_bin_counters(self):
        self.bin0_evictions = [0 for i in range(self.si.num_of_cbo)]
        self.bin1_evictions = [0 for i in range(self.si.num_of_cbo)]
        self.hit_in_bin0 = [0 for i in range(self.si.num_of_cbo)]
        self.hit_in_bin1 = [0 for i in range(self.si.num_of_cbo)]

    def is_b0_greater_than_threshold(self, cbo_id):
        if self.bin0_evictions[cbo_id] == 0:
            return True
        if (self.hit_in_bin0[cbo_id] / self.bin0_evictions[cbo_id]) >= self.ccf_registers.b0_threshold[cbo_id] * 0.025:#The threshold we use has a granularity of 1/40 = 2.5%
            return True
        else:
            return False


    def is_b0_distinct(self, cbo_id):
        if (abs(self.hit_in_bin0[cbo_id] - self.bin0_evictions[cbo_id]) < 3):
            return False
        if self.bin0_evictions[cbo_id] == 0:
            return True
        if ((self.hit_in_bin0[cbo_id] - 1) / self.bin0_evictions[cbo_id])>= ((self.ccf_registers.b0_threshold[cbo_id] + 1) * 0.025): #The threshold we use has a granularity of 1/40 = 2.5%
            return True
        if ((self.hit_in_bin0[cbo_id] + 1) / self.bin0_evictions[cbo_id]) < ((self.ccf_registers.b0_threshold[cbo_id] - 1) * 0.025): #The threshold we use has a granularity of 1/40 = 2.5%
            return True
        return False


    def is_b1_greater_than_threshold(self, cbo_id):
        if self.bin1_evictions[cbo_id] == 0:
            return True
        if (self.hit_in_bin1[cbo_id] / self.bin1_evictions[cbo_id]) >= self.ccf_registers.b1_threshold[cbo_id]* 0.025: #The threshold we use has a granularity of 1/40 = 2.5%
            return True
        else:
            return False


    def is_b1_distinct(self, cbo_id):
        if (abs(self.hit_in_bin1[cbo_id] - self.bin1_evictions[cbo_id]) <= self.ccf_registers.b1_threshold[cbo_id]):
            return False
        if self.bin1_evictions[cbo_id] == 0:
            return True
        if self.hit_in_bin1[cbo_id] == 0: # if current hit is 0 -> b1_hr = 0, so it is not distinctable (any "hit" while victim is rejected will tip the scale)
            return False
        if (self.hit_in_bin1[cbo_id] - 1) / (self.bin1_evictions[cbo_id]) > (self.ccf_registers.b1_threshold[cbo_id] * 0.025):
            return True
        if (self.hit_in_bin1[cbo_id] + 1) / (self.bin1_evictions[cbo_id]) < (self.ccf_registers.b1_threshold[cbo_id] * 0.025):#The threshold we use has a granularity of 1/40 = 2.5%
            return True
        return False

    def update_hits(self, flow: ccf_flow):
        if flow.cbo_got_ufi_uxi_cmpo() or flow.cbo_got_upi_fwdcnflto():
            dbp_params = flow.get_dbp_params()
            bin_dbp_params = bint(int(dbp_params, 16))
            psaudo_llc_hit = bin_dbp_params[0]
            bin_value = bin_dbp_params[2]
            if flow.is_ms_chche_observer() and (psaudo_llc_hit == 1):
                if bin_value == 0:
                    self.hit_in_bin0[flow.cbo_id_phys] = self.hit_in_bin0[flow.cbo_id_phys] + 1
                else:
                    self.hit_in_bin1[flow.cbo_id_phys] = self.hit_in_bin1[flow.cbo_id_phys] + 1

    def chk_clean_evict(self, flow: ccf_flow):
        expected = None
        if self.si.is_nem_test:
            expected = '0'
        if flow.is_core_clean():
            if flow.is_ms_chche_observer() or (self.is_b0_distinct(flow.cbo_id_phys) and self.is_b0_greater_than_threshold(flow.cbo_id_phys)):
                if flow.initial_cv_with_selfsnoop_zero() and flow.req_core_initial_cv_bit_is_one() and ((not flow.is_tor_occup_above_threshold()) or (self.ccf_registers.dis_clean_evict_occupancy_throttle[flow.cbo_id_phys]==1)):
                    expected = '1'
                else:
                    expected = '0'
            elif not flow.is_ms_chche_observer() and (self.is_b0_distinct(flow.cbo_id_phys) and not self.is_b0_greater_than_threshold(flow.cbo_id_phys)):
                    expected = '0'

        if flow.is_llc_clean() or flow.is_llc_modified():
            if (flow.is_ms_chche_observer() or (self.is_b1_distinct(flow.cbo_id_phys) and self.is_b1_greater_than_threshold(flow.cbo_id_phys))):
                if (not flow.is_tor_occup_above_threshold()) or (self.ccf_registers.dis_clean_evict_occupancy_throttle[flow.cbo_id_phys]==1):
                    expected = '1'
                else:
                    expected = '0'
            elif not flow.is_ms_chche_observer() and (self.is_b1_distinct(flow.cbo_id_phys) and not self.is_b1_greater_than_threshold(flow.cbo_id_phys)):
                    expected = '0'

        if (expected is not None and flow.get_clean_evict_value("first") != expected):
            err_msg = ":{} {} clean evict indication is wrong. actual is {} while expected is {}".format(flow.uri["TID"], flow.opcode,
                                                                                         flow.get_clean_evict_value("first") , expected)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

 
    def sample_dbp_cov(self, msg):
        if self.si.ccf_cov_en:
            dbp_to_mscache_cg = DBP_TO_MSCACHE_CG.get_pointer()
            dbp_to_mscache_cg.sample(dbp_info_cp=msg)

    def should_check_flow(self, flow: ccf_flow):
        return self.si.dbp_en

    def check_flow(self, flow: ccf_flow):
        if len(self.c6_times) > 0:
            first_key = list(self.c6_times.keys())[0]
            if self.prev_trans_time < first_key and flow.initial_time_stamp > first_key:  # In C6 we reset the MS$ bins counters
                print("reset bin counters and dbp bx bin to core at "+ str(flow.initial_time_stamp) + " ps")
                self.reset_bin_counters()
                self.c6_times.pop(first_key)
                self.dbp_bx_to_core = dict()
        self.check_core_dbp(flow)
        self.check_mscach_dbp(flow)

    def check_mscach_dbp(self, flow: ccf_flow):
        expected_info = None
        check_dbp = 0

        self.update_hits(flow)
        if flow.is_core_clean() or flow.is_core_modified() or flow.is_llc_clean() or flow.is_llc_modified():
            check_dbp = 1

        if check_dbp:
            self.chk_clean_evict(flow)
            if flow.is_ms_chche_observer():
                if flow.is_core_clean() or flow.is_core_modified():
                    if flow.wrote_data_to_upi():
                        self.bin0_evictions[flow.cbo_id_phys] = self.bin0_evictions[flow.cbo_id_phys] + 1
                    if flow.wrote_data_to_upi() and (flow.is_dead_dbp() or not flow.is_available_data()):
                        self.sample_dbp_cov("obserever_dead_bx0")
                        expected_info = "1"  # bx = 0
                    else:
                        self.sample_dbp_cov("obserever_not_dead")
                        expected_info = None  # fill in llc (it will be interesting to see cases when we are not filling llc - not necessarily bug)
                elif flow.is_llc_clean() or flow.is_llc_modified():
                    if flow.wrote_data_to_upi():
                        self.bin1_evictions[flow.cbo_id_phys] = self.bin1_evictions[flow.cbo_id_phys] + 1
                        expected_info = "3"  # bx = 1
                        self.sample_dbp_cov("obserever_bx1")
            elif not flow.is_ms_chche_observer():
                if flow.is_core_clean() or flow.is_core_modified():
                    if flow.is_dead_dbp() or not flow.is_available_data():
                        if self.is_b0_distinct(flow.cbo_id_phys):
                            if self.is_b0_greater_than_threshold(flow.cbo_id_phys):
                                if flow.wrote_data_to_upi():
                                    self.sample_dbp_cov("follower_dead_bin0_downgrade0")
                                    expected_info = "0"  # downgrade = 0
                                else:
                                    check_dbp = 0 #conditions are checked in flow_chk, we are checking here the expected value, not the flow
                            elif not self.is_b0_greater_than_threshold(flow.cbo_id_phys) and flow.is_core_modified():
                                if flow.wrote_data_to_upi():
                                    expected_info = "2"  # downgrade = 1
                                    self.sample_dbp_cov("follower_dead_bin0_downgrade1")
                                else:
                                    check_dbp = 0 #conditions are checked in flow_chk, we are checking here the expected value, not the flow
                            elif not self.is_b0_greater_than_threshold(flow.cbo_id_phys) and flow.is_core_clean():
                                expected_info = None  # drop
                                self.sample_dbp_cov("follower_dead_bin0_dropped")
                        else:
                            check_dbp = 0
                    else:
                        expected_info = None  # fill in llc (it will be interesting to see cases when we are not filling llc - not necessarily bug)
                        self.sample_dbp_cov("follower_not_dead_bin0")
                elif flow.is_llc_clean() or flow.is_llc_modified():
                    if self.is_b1_distinct(flow.cbo_id_phys):
                        if self.is_b1_greater_than_threshold(flow.cbo_id_phys):
                            if flow.wrote_data_to_upi():
                                expected_info = "0"  # downgrade = 0
                                self.sample_dbp_cov("follower_bin1_downgrade0")
                            else:
                                expected_info = None #conditions are checked in flow_chk, we are checking here the expected value, not the flow
                        elif not self.is_b1_greater_than_threshold(flow.cbo_id_phys) and flow.is_llc_clean():
                            expected_info = None  # drop
                            self.sample_dbp_cov("follower_bin1_dropped")
                        elif not self.is_b1_greater_than_threshold(flow.cbo_id_phys) and flow.is_llc_modified():
                            expected_info = "2"  # downgrade = 1
                            self.sample_dbp_cov("follower_bin1_downgrade1")
                    else:
                        check_dbp = 0
        if check_dbp and (expected_info != flow.dbpinfo):
            self.bad_dbpinfo_for_mscache_observers = self.bad_dbpinfo_for_mscache_observers + 1
            self.bad_dbpinfo_for_mscache_uri_list.append(flow.uri["TID"])
            err_msg = ":mscach dbp: {} {} DBP info is wrong, expected is {} while actual is {}".format(flow.uri["TID"], flow.opcode,                                                                                          expected_info, flow.dbpinfo)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif check_dbp:
            self.good_dbpinfo_for_mscache_observers = self.good_dbpinfo_for_mscache_observers + 1
            self.collect_coverage()

        self.prev_trans_time = flow.initial_time_stamp

    def check_core_dbp(self, flow: ccf_flow):
        self.check_obs_read_core_dbp = True
        expected_param = bint(0)

        is_wb = flow.is_wbmtoe() or flow.is_wbmtoi() or flow.is_wbeftoe() or flow.is_wbeftoi()
        is_rd = flow.is_itom() or flow.is_specitom() or flow.is_drd() or flow.is_crd() or flow.is_monitor() or flow.is_rfo()

        #from DBP HAS: A pseudo-hit indication is provided with GO, to be used only by DBP.
        # Lines with an LLCPref indication always indicate miss.
        # Non-LLCPref lines which hit in the local LLC, or have CV other than self set, indicate hit.
        # explenation on rfo/itom exception are in HSD #1309806008
        force_snoop_all_exclude = self.is_force_snoop_all_cb_en(flow) and flow.snoop_sent()
        pseudo_llc_hit_zero_exclude = ((flow.is_rfo() or flow.is_itom() or flow.is_specitom()) and flow.is_monitor_hit()) or force_snoop_all_exclude
        pseudo_llc_miss = flow.initial_state_llc_i() or (flow.initial_state_llc_s() and (flow.is_itom() or flow.is_specitom() or flow.is_rfo()))
        pseudo_llc_hit_brought_by_prefetch = flow.flow_is_hom() and flow.is_brought_by_prefetch() and not (pseudo_llc_hit_zero_exclude)
        pseudo_llc_hit = (not pseudo_llc_miss) and (not pseudo_llc_hit_brought_by_prefetch)
        
        msg = "uri: " + flow.uri["TID"] + "pseudo_llc_hit " + str(pseudo_llc_hit) + " pseudo_llc_hit_brought_by_prefetch " + str(pseudo_llc_hit_brought_by_prefetch)
        VAL_UTDB_MSG(time=flow.initial_time_stamp, msg=msg)
        if flow.is_idi_flow_origin() and (self.get_cl_align_address(flow.address) in self.dbp_bx_to_core.keys()) and (not is_wb) and (not (flow.is_llcpref() and flow.hit_in_cache())) and \
            (flow.initial_state_llc_i() or flow.initial_map_sf() or (flow.snoop_rsp_with_data() and not flow.is_itom()) or flow.is_data_written_to_cache()): #and flow.is_data_written_to_cache()
                del self.dbp_bx_to_core[self.get_cl_align_address(flow.address)]

        #HSD 13011014664- don't check for buggy case
        if is_rd and flow.initial_map_sf() and flow.is_allocating_map_data(): # buggy scenario
            self.check_obs_read_core_dbp = False

        if is_wb and flow.is_core_observer():
            self.update_bx_dict(flow)

        if is_rd:
            actual_param = int(flow.idi_dbp_params, 16)
            actual_observer = 0 if (actual_param < 2) else bint(actual_param)[1]
            is_observer = 0 if (not flow.is_core_observer()) else actual_observer  # flow.is_core_observer() and flow.final_map_dway() and not flow.initial_state_llc_i() # from TGL, HSD 2201518029


            expected_param[0] = pseudo_llc_hit
            expected_param[1] = 1 if is_observer else 0
            if is_observer:
                expected_param[4] = flow.initial_state_llc_m()
                if self.get_cl_align_address(flow.address) in self.dbp_bx_to_core.keys():
                    expected_param[3:2] = self.dbp_bx_to_core[self.get_cl_align_address(flow.address)]
                else:
                    expected_param[3:2] = bint(3)
            else:
                expected_param[4:2] = bint(0)

            if is_observer and self.check_obs_read_core_dbp:
                if (expected_param[4:2] != bint(actual_param)[4:2]):
                    self.bad_params_for_core_observers = self.bad_params_for_core_observers + 1
                    self.core_bad_params_uri_list.append(flow.uri["TID"])
                    #err_msg = "core dbp: {} {} DBP info is wrong, expected is {} while actual is {}".format(flow.uri["TID"], flow.opcode,                                                                         hex(expected_param),hex(actual_param))
                    #VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                else:
                    self.good_params_for_core_observers = self.good_params_for_core_observers + 1
            else:
                if expected_param[1:0] != bint(actual_param)[1:0]:
                    err_msg = ":core dbp: {} {} DBP info is wrong, expected is {} while actual is {}".format(flow.uri["TID"], flow.opcode,
                                                                                                  hex(expected_param[1:0]),hex(bint(actual_param)[1:0]) )
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def update_bx_dict(self, flow: ccf_flow):
        addr = self.get_cl_align_address(flow.address)
        self.dbp_bx_to_core[addr] = bint(flow.idi_dbpinfo)[1:0]

    def get_cl_align_address(self,addr):
        int_addr = bint(int(addr, 16))
        int_addr[5:0] = 0
        return str(hex(int_addr))

    def eot_check(self):
        if self.good_params_for_core_observers == 0:
            if self.bad_params_for_core_observers > 1:
                self.print_eot_core_dbp_error()
        else:
            if (((self.bad_params_for_core_observers * 100)/ self.good_params_for_core_observers) > 20) and (self.bad_params_for_core_observers > 1):
                self.print_eot_core_dbp_error()
            else:
                print("core dbp: there are bad dbp info messages in less than 20% of the observer messages: {}".format(self.core_bad_params_uri_list))

        if self.good_dbpinfo_for_mscache_observers == 0:
            if self.bad_dbpinfo_for_mscache_observers > 0:
                 self.print_eot_mscache_dbp_error()
        else:
            if ((self.bad_dbpinfo_for_mscache_observers * 100)/ self.good_dbpinfo_for_mscache_observers) > 2:
                self.print_eot_mscache_dbp_error()
            else:
                print("mscache dbp: there are bad dbpinfo messages in less than 2% of the mscache observer messages: {}".format(self.bad_dbpinfo_for_mscache_uri_list))




    def print_eot_core_dbp_error(self):
        err_msg = ":core dbp: there are bad core dbp info messages in more than 20% of the observer messages: {}, while test had {} good obserever".format(self.core_bad_params_uri_list, self.good_params_for_core_observers)
        VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)

    def print_eot_mscache_dbp_error(self):
        err_msg = ":mscache dbp: there are bad dbpinfo messages in more than 2% of the mscache observer messages: {}".format(self.bad_dbpinfo_for_mscache_uri_list)
        VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
