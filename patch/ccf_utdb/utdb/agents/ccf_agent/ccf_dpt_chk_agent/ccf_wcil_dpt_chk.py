from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_dpt_chk_agent.ccf_dpt_chk_cov import collect_dpt_coverage
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_cbos_db import ccf_cbos_db
from agents.ccf_data_bases.ccf_prefetch_wcil_dpt_at_same_time_db import ccf_prefetch_wcil_dpt_at_same_time_db
from val_utdb_report import VAL_UTDB_ERROR


class AllocType:
    TorAlloc = 0
    TorDealloc = 1
    CohWcilAlloc = 2
    CohWcilDealloc = 3
    NcWcilAlloc = 4
    NcWcilDealloc = 5


class AllocRec:
    def __init__(self, time, uri, cbo_num, alloc_type):
        self.time = time
        self.uri = uri
        self.cbo_num = cbo_num
        self.alloc_type = alloc_type


def get_next_exp_dpt_type(cur_dpt_type):
    if cur_dpt_type == "increment":
        return "decrement"
    if cur_dpt_type == "decrement":
        return "increment"


class ccf_wcil_dpt_chk(ccf_coherency_base_chk):
    def __init__(self):
        self.checker_name = "ccf_wcil_dpt_chk"
        self.regs: ccf_registers = ccf_registers.get_pointer()
        self.collect_dpt_cov_ptr: collect_dpt_coverage = collect_dpt_coverage.get_pointer()
        self.distress_times = list()
        self.act_wcil_dpt_trans = dict()

    def is_rec_during_test_time(self, r):
        return r.TIME > COH_GLOBAL.global_vars["START_OF_TEST"] and r.TIME < COH_GLOBAL.global_vars["END_OF_TEST"]

    def get_cpipe_alloc_recs(self):
        recs_lists = list()
        # TODO mlugassi - should be removed after adding deallocation time to ccf_flow recoreds
        dealloc_times = ccf_cbos_db.get_pointer().get_dealloc_times()

        for uri in self.ccf_flows:
            if uri in dealloc_times.keys():
                recs_lists += self.flow_info_to_recs(self.ccf_flows[uri], dealloc_times[uri])

        return sorted(recs_lists, key=lambda r: r.time)

    def flow_info_to_recs(self, flow_info: ccf_flow, dealloc_time):
        tor_alloc_time = flow_info.accept_time if not flow_info.is_victim() else self.ccf_flows[flow_info.uri['TID']].accept_time
        recs = [AllocRec(time=tor_alloc_time, uri=flow_info.flow_key,
                         cbo_num=flow_info.cbo_id_phys, alloc_type=AllocType.TorAlloc),
                AllocRec(time=dealloc_time, uri=flow_info.flow_key,
                         cbo_num=flow_info.cbo_id_phys, alloc_type=AllocType.TorDealloc)]
        if "WCIL" in flow_info.opcode.upper():
            if flow_info.sad_results != "HOM":
                recs += [
                    AllocRec(time=flow_info.accept_time, uri=flow_info.flow_key,
                             cbo_num=flow_info.cbo_id_phys, alloc_type=AllocType.NcWcilAlloc),
                    AllocRec(time=flow_info.pipe_passes_information[-1].arbcommand_time, uri=flow_info.flow_key,
                             cbo_num=flow_info.cbo_id_phys, alloc_type=AllocType.NcWcilDealloc)]
            else:
                recs += [
                    AllocRec(time=flow_info.accept_time, uri=flow_info.flow_key,
                             cbo_num=flow_info.cbo_id_phys, alloc_type=AllocType.CohWcilAlloc),
                    AllocRec(time=flow_info.pipe_passes_information[-1].arbcommand_time, uri=flow_info.flow_key,
                             cbo_num=flow_info.cbo_id_phys, alloc_type=AllocType.CohWcilDealloc)]
        return recs

    def get_cur_distress_mode(self, cbo_distress_modes, tor_counter, coh_wcil_counter, nc_wcil_counter):
        for cbo_num in self.regs.cbo_phy_id_list:
            if self.regs.wcil_throttling_enable[cbo_num] == 1:
                if tor_counter[cbo_num] > self.regs.wcil_throttle_tor_entries_high_threshold[cbo_num] and \
                        (coh_wcil_counter[cbo_num] > self.regs.wcil_throttle_coherent_wcil_high_threshold[cbo_num] or
                         nc_wcil_counter[cbo_num] > self.regs.wcil_throttle_non_coherent_wcil_high_threshold[cbo_num]):
                    cbo_distress_modes[cbo_num] = True
                elif tor_counter[cbo_num] < self.regs.wcil_throttle_tor_entries_low_threshold[cbo_num] and \
                        coh_wcil_counter[cbo_num] < self.regs.wcil_throttle_coherent_wcil_low_threshold[cbo_num] and \
                        nc_wcil_counter[cbo_num] < self.regs.wcil_throttle_non_coherent_wcil_low_threshold[cbo_num]:
                    cbo_distress_modes[cbo_num] = False
                if self.si.ccf_cov_en == 1:
                    self.collect_dpt_cov_ptr.sample_distress(cbo_num=cbo_num, in_distress=cbo_distress_modes[cbo_num])
                    self.collect_dpt_cov_ptr.sample_cbo_tor_counter_passed_high(cbo_num=cbo_num,
                                                                                passed=tor_counter[cbo_num] >
                                                                                       self.regs.wcil_throttle_tor_entries_high_threshold[
                                                                                           cbo_num])
                    self.collect_dpt_cov_ptr.sample_cbo_coh_wcil_counter_passed_high(cbo_num=cbo_num,
                                                                                     passed=coh_wcil_counter[cbo_num] >
                                                                                            self.regs.wcil_throttle_tor_entries_high_threshold[
                                                                                                cbo_num])
                    self.collect_dpt_cov_ptr.sample_cbo_nc_wcil_counter_passed_high(cbo_num=cbo_num,
                                                                                    passed=nc_wcil_counter[cbo_num] >
                                                                                           self.regs.wcil_throttle_tor_entries_high_threshold[
                                                                                               cbo_num])

        return any(cbo_distress_modes)

    def get_num_of_close_distresses(self):
        num_of_close_distresses = 0
        if len(self.distress_times) > 1:
            cur_distress = self.distress_times[0]
        for nxt_distress in self.distress_times[1:]:
            if cur_distress[1] + 70000 > nxt_distress[0]:
                num_of_close_distresses += 1
            cur_distress = nxt_distress
        return num_of_close_distresses

    def get_num_of_prefetch_wcil_dpt_at_same_time(self):
        prefetch_wcil_dpt_at_same_time_times = ccf_prefetch_wcil_dpt_at_same_time_db.get_pointer().get_prefetch_wcil_dpt_at_same_time_times()
        num_of_prefetch_wcil_dpt_at_same_time = 0

        for dt in self.distress_times:
            for time in prefetch_wcil_dpt_at_same_time_times:
                if dt[0] <= time <= dt[1]:
                    num_of_prefetch_wcil_dpt_at_same_time += 1
                    break
        return num_of_prefetch_wcil_dpt_at_same_time



    def get_num_of_exp_dpt(self):
        num_of_close_distresses = self.get_num_of_close_distresses()
        num_of_prefetch_wcil_dpt_at_same_time = self.get_num_of_prefetch_wcil_dpt_at_same_time()

        max_exp_inc_dpt = len(self.distress_times) * 3
        max_exp_dec_dpt = len(self.distress_times) * 3
        min_exp_inc_dpt = max_exp_inc_dpt - ((num_of_close_distresses + num_of_prefetch_wcil_dpt_at_same_time) * 3)
        min_exp_dec_dpt = max_exp_dec_dpt - ((num_of_close_distresses + num_of_prefetch_wcil_dpt_at_same_time) * 3)

        if self.si.ccf_cov_en == 1:
            self.collect_dpt_cov_ptr.sample_prefetch_wcil_dpt_at_same_time(num_of_prefetch_wcil_dpt_at_same_time)

        return min_exp_inc_dpt, max_exp_inc_dpt, min_exp_dec_dpt, max_exp_dec_dpt

    def get_num_of_act_dpt(self):
        act_inc_dpt = 0
        act_dec_dpt = 0
        act_periodic_dpt = 0
        num_of_periodic_dpts = 0
        last_periodic_dpt_trans = 0
        for group_key, trans in self.act_wcil_dpt_trans.items():
            if group_key[1] == "increment":
                if len(trans) > 3:
                    act_inc_dpt += 3
                    last_periodic_dpt_trans = len(trans) - 3
                    act_periodic_dpt += last_periodic_dpt_trans
                    num_of_periodic_dpts += 1
                elif self.regs.sbo_disable_dpt_credit == 1 and len(trans) < 3 and \
                        ((len(trans) + last_periodic_dpt_trans) >= 3):
                    if (len(trans) + last_periodic_dpt_trans) == 3:
                        num_of_periodic_dpts -= 1
                        act_periodic_dpt -= last_periodic_dpt_trans
                    else:
                        act_periodic_dpt -= last_periodic_dpt_trans - (3 - len(trans))
                else:
                    act_inc_dpt += len(trans)
            elif group_key[1] == "decrement":
                act_dec_dpt += len(trans)

        if self.si.ccf_cov_en == 1:
            self.collect_dpt_cov_ptr.sample_num_of_periodic_dpt(num_of_periodic_dpts=num_of_periodic_dpts)
        return act_inc_dpt, act_dec_dpt, act_periodic_dpt

    def check_num_of_dpt(self):
        act_inc_dpt, act_dec_dpt, act_periodic_dpt = self.get_num_of_act_dpt()
        min_exp_inc_dpt, max_exp_inc_dpt, min_exp_dec_dpt, max_exp_dec_dpt = self.get_num_of_exp_dpt()

        if act_periodic_dpt > 0 and self.regs.santa_periodic_wcil_throttling_enable == 0:
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"],
                           msg="Got " + str(act_periodic_dpt) + " periodic DPT, while periodic DPT is disabled")
        if min_exp_dec_dpt > act_dec_dpt or act_dec_dpt > max_exp_dec_dpt:
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"],
                           msg="Expected " + str(min_exp_dec_dpt) + " to " + str(max_exp_dec_dpt) +
                               " decrements DPTs but got " + str(act_dec_dpt))
        if self.regs.sbo_disable_dpt_credit == 1 and self.regs.santa_periodic_wcil_throttling_enable == 1:
            if min_exp_inc_dpt > act_inc_dpt:
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"],
                               msg="Expected " + str(min_exp_inc_dpt) + " to " + str(max_exp_inc_dpt) +
                                   " increments DPTs but got " + str(act_inc_dpt))
        else:
            if min_exp_inc_dpt > act_inc_dpt or act_inc_dpt > max_exp_inc_dpt:
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"],
                               msg="Expected " + str(min_exp_inc_dpt) + " to " + str(max_exp_inc_dpt) +
                                   " increments DPTs but got " + str(act_inc_dpt))

    def check_dpts_ordering(self):
        if self.regs.sbo_disable_dpt_credit == 0:

            exp_dpt_type = "increment"

            for key, val in self.act_wcil_dpt_trans.items():
                if key[1] != exp_dpt_type:
                    VAL_UTDB_ERROR(time=key[0],
                                   msg="**** DPT event didn't report increments and decrements alternately ****\n"
                                       "\nExpected to get " + exp_dpt_type + " DPTs but got " +
                                       get_next_exp_dpt_type(exp_dpt_type) + "\n" +
                                       "\nURIs:\n" + "\n".join(t['uri'] for t in val))

                if key[1] == "decrement" and len(val) != 3:
                    VAL_UTDB_ERROR(time=key[0],
                                   msg="**** DPT event didn't report increments and decrements alternately ****\n"
                                       "\nExpected to get 3 decrements DPTs but got " + str(len(val)) + "\n" +
                                       "\nURIs:\n" + "\n".join(t['uri'] for t in val))

                if key[1] == "increment" and len(val) != 3 and self.regs.santa_periodic_wcil_throttling_enable == 0:
                    VAL_UTDB_ERROR(time=key[0],
                                   msg="**** DPT event didn't report increments and decrements alternately ****\n"
                                       "\nExpected to get 3 increments DPTs but got " + str(len(val)) + "\n" +
                                       "\nURIs:\n" + "\n".join(t['uri'] for t in val))

                if key[1] == "increment" and len(val) < 3 and self.regs.santa_periodic_wcil_throttling_enable == 1:
                    VAL_UTDB_ERROR(time=key[0],
                                   msg="**** DPT event didn't report increments and decrements alternately ****\n"
                                       "\nExpected to at least 3 increments DPTs but got " + str(len(val)) + "\n" +
                                       "\nURIs:\n" + "\n".join(t['uri'] for t in val))

                exp_dpt_type = get_next_exp_dpt_type(exp_dpt_type)

    def get_act_wcil_dpt_trans(self):
        act_dpt_trans = list()

        for uri in self.ccf_flows:
            if self.ccf_flows[uri].is_u2c_dpt_req() and self.ccf_flows[uri].data in ['Intdata=0007',
                                                                                     'Intdata=0005']:
                act_dpt_trans.append({
                    "time": self.ccf_flows[uri].flow_progress[-1].rec_time,
                    "uri": uri,
                    "type": "increment" if self.ccf_flows[uri].data == 'Intdata=0007' else "decrement"
                })
                if self.si.ccf_cov_en == 1:
                    self.collect_dpt_cov_ptr.sample_dpt_type(inc_dpt=act_dpt_trans[-1]["type"] == "increment",
                                                             dec_dpt=act_dpt_trans[-1]["type"] == "decrement")

        return sorted(act_dpt_trans, key=lambda t: t["time"])

    def get_act_wcil_dpt_group_by_type(self):
        grouped_dpts = dict()
        temp = dict()
        last_tran = None

        for tran in self.get_act_wcil_dpt_trans():
            if len(grouped_dpts) == 0 or last_tran["type"] != tran["type"]:
                grouped_dpts[(tran["time"], tran["type"])] = list()
                last_tran = tran
            grouped_dpts[(last_tran["time"], last_tran["type"])].append(tran)

        return grouped_dpts

    def calc_distress_times(self):
        distress_times = list()
        tor_counter = list()
        coh_wcil_counter = list()
        nc_wcil_counter = list()
        cbo_distress_modes = list()
        for cbo_num in self.regs.cbo_phy_id_list:
            tor_counter.append(0)
            coh_wcil_counter.append(0)
            nc_wcil_counter.append(0)
            cbo_distress_modes.append(False)

        last_distress_mode = False
        cur_distress_mode = False
        last_start_distress_time = 0

        if self.regs.santa_wcil_throttling_enable == 1:
            for rec in self.get_cpipe_alloc_recs():
                if rec.alloc_type == AllocType.TorAlloc:
                    tor_counter[rec.cbo_num] += 1
                elif rec.alloc_type == AllocType.TorDealloc:
                    tor_counter[rec.cbo_num] -= 1
                elif rec.alloc_type == AllocType.NcWcilAlloc:
                    nc_wcil_counter[rec.cbo_num] += 1
                elif rec.alloc_type == AllocType.NcWcilDealloc:
                    nc_wcil_counter[rec.cbo_num] -= 1
                elif rec.alloc_type == AllocType.CohWcilAlloc:
                    coh_wcil_counter[rec.cbo_num] += 1
                elif rec.alloc_type == AllocType.CohWcilDealloc:
                    coh_wcil_counter[rec.cbo_num] -= 1

                last_distress_mode = cur_distress_mode
                cur_distress_mode = self.get_cur_distress_mode(cbo_distress_modes, tor_counter,
                                                               coh_wcil_counter, nc_wcil_counter)

                if cur_distress_mode is True and last_distress_mode is False:
                    last_start_distress_time = rec.time
                elif cur_distress_mode is False and last_distress_mode is True:
                    distress_times.append((last_start_distress_time, rec.time))

        if self.si.ccf_cov_en == 1:
            self.collect_dpt_cov_ptr.sample_more_than_5_distresses(len(distress_times))

        return distress_times

    def check_default_values(self, reg_name, act_val, exp_val):
        if act_val != exp_val:
            VAL_UTDB_ERROR(time=0,
                           msg="{0} is default value {1}, while we expected {2}".format(reg_name, act_val, exp_val))

    def check_register_values(self):
        santa_wcil_throttling_en_def_val = True
        cbos_wcil_throttling_en_def_val = False
        periodic_wcil_throttling_en_def_val = True
        dpt_credit_dis = True

        tor_threshold_high_def_val = 40
        tor_threshold_low_def_val = 40
        coh_wcil_threshold_high_def_val = 40
        coh_wcil_threshold_low_def_val = 40
        nc_wcil_threshold_high_def_val = 40
        nc_wcil_threshold_low_def_val = 40

        periodic_threshold_def_val = 32

        if self.si.enable_cr_randomization == 0:
            self.check_default_values("santa_wcil_throttling_enable", self.regs.santa_wcil_throttling_enable,
                                      santa_wcil_throttling_en_def_val)
            self.check_default_values("santa_periodic_wcil_throttling_enable",
                                      self.regs.santa_periodic_wcil_throttling_enable,
                                      periodic_wcil_throttling_en_def_val)
            self.check_default_values("santa_periodic_wcil_threshold", self.regs.santa_periodic_wcil_threshold,
                                      periodic_threshold_def_val)
            self.check_default_values("sbo_disable_dpt_credit", self.regs.sbo_disable_dpt_credit, dpt_credit_dis)

            for cbo_num in range(self.si.num_of_cbo):
                self.check_default_values("cbo" + str(cbo_num) + "_wcil_throttling_enable",
                                          self.regs.wcil_throttling_enable[cbo_num], cbos_wcil_throttling_en_def_val)

                self.check_default_values("cbo" + str(cbo_num) + "_wcil_throttle_tor_entries_high_threshold",
                                          self.regs.wcil_throttle_tor_entries_high_threshold[cbo_num],
                                          tor_threshold_high_def_val)

                self.check_default_values("cbo" + str(cbo_num) + "_wcil_throttle_tor_entries_low_threshold",
                                          self.regs.wcil_throttle_tor_entries_low_threshold[cbo_num],
                                          tor_threshold_low_def_val)

                self.check_default_values("cbo" + str(cbo_num) + "_wcil_throttle_coherent_wcil_high_threshold",
                                          self.regs.wcil_throttle_coherent_wcil_high_threshold[cbo_num],
                                          coh_wcil_threshold_high_def_val)

                self.check_default_values("cbo" + str(cbo_num) + "wcil_throttle_coherent_wcil_low_threshold",
                                          self.regs.wcil_throttle_coherent_wcil_low_threshold[cbo_num],
                                          coh_wcil_threshold_low_def_val)

                self.check_default_values("cbo" + str(cbo_num) + "_wcil_throttle_non_coherent_wcil_high_threshold",
                                          self.regs.wcil_throttle_non_coherent_wcil_high_threshold[cbo_num],
                                          nc_wcil_threshold_high_def_val)

                self.check_default_values("cbo" + str(cbo_num) + "_wcil_throttle_non_coherent_wcil_low_threshold",
                                          self.regs.wcil_throttle_non_coherent_wcil_low_threshold[cbo_num],
                                          nc_wcil_threshold_low_def_val)

            if self.si.ccf_cov_en == 1:
                tor_threshold_high_def_vals = list()
                tor_threshold_low_def_vals = list()
                coh_wcil_threshold_high_def_vals = list()
                coh_wcil_threshold_low_def_vals = list()
                nc_wcil_threshold_high_def_vals = list()
                nc_wcil_threshold_low_def_vals = list()
                for i in range(self.si.num_of_cbo):
                    tor_threshold_high_def_vals.append(
                        self.regs.wcil_throttle_tor_entries_high_threshold[i] == tor_threshold_high_def_val)
                    tor_threshold_low_def_vals.append(
                        self.regs.wcil_throttle_tor_entries_low_threshold[i] == tor_threshold_low_def_val)
                    coh_wcil_threshold_high_def_vals.append(
                        self.regs.wcil_throttle_coherent_wcil_high_threshold[i] == coh_wcil_threshold_high_def_val)
                    coh_wcil_threshold_low_def_vals.append(
                        self.regs.wcil_throttle_coherent_wcil_low_threshold[i] == coh_wcil_threshold_low_def_val)
                    nc_wcil_threshold_high_def_vals.append(
                        self.regs.wcil_throttle_non_coherent_wcil_high_threshold[i] == nc_wcil_threshold_high_def_val)
                    nc_wcil_threshold_low_def_vals.append(
                        self.regs.wcil_throttle_non_coherent_wcil_low_threshold[i] == nc_wcil_threshold_low_def_val)

                self.collect_dpt_cov_ptr.sample_register_values(
                    dpt_credit_en=(not self.regs.sbo_disable_dpt_credit),
                    periodic_wcil_throttling_en=self.regs.santa_periodic_wcil_throttling_enable,
                    santa_wcil_throttling_en=self.regs.santa_wcil_throttling_enable,
                    cbos_wcil_throttling_en=[self.regs.wcil_throttling_enable[i] == 1 for i in
                                             range(self.si.num_of_cbo)],
                    periodic_threshold_def_val=self.regs.santa_periodic_wcil_threshold == periodic_threshold_def_val,
                    tor_threshold_high_def_vals=tor_threshold_high_def_vals,
                    tor_threshold_low_def_vals=tor_threshold_low_def_vals,
                    coh_wcil_threshold_high_def_vals=coh_wcil_threshold_high_def_vals,
                    coh_wcil_threshold_low_def_vals=coh_wcil_threshold_low_def_vals,
                    nc_wcil_threshold_high_def_vals=nc_wcil_threshold_high_def_vals,
                    nc_wcil_threshold_low_def_vals=nc_wcil_threshold_low_def_vals)

    def run(self):
        self.check_register_values()
        self.distress_times = self.calc_distress_times()
        self.act_wcil_dpt_trans = self.get_act_wcil_dpt_group_by_type()
        self.check_num_of_dpt()
        self.check_dpts_ordering()
