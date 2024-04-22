from val_utdb_report import VAL_UTDB_MSG
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_common_base.ccf_common_cov import ccf_base_cov, ccf_cg, ccf_cp
from agents.ccf_common_base.ccf_registers import ccf_registers


def CBO(cbo_num):
    return "CBO" + str(cbo_num)


def EN(cbo_num):
    return CBO(cbo_num) + "_EN"


def DIS(cbo_num):
    return CBO(cbo_num) + "_DIS"


def DEFAULT(cbo_num):
    return CBO(cbo_num) + "_DEFAULT"


def NON_DEFAULT(cbo_num):
    return CBO(cbo_num) + "_NON_DEFAULT"


class CCF_DPT_CG(ccf_cg):
    def __init__(self):
        super().__init__()

    def coverpoints(self):
        self.num_of_inc_dpt_ev = ccf_cp(["min", "low", "high", "max"])
        self.highest_water_mark_value = ccf_cp(["0+", "10+", "20+", "30+", "40+", "50+", "60+"])
        self.CROSS_water_mark_and_events = self.cross(self.num_of_inc_dpt_ev, self.highest_water_mark_value)
        # WCIL DPT CPs
        self.wcil_dpt_type = ccf_cp(["increment", "decrement"])
        self.cbos_distress = ccf_cp([CBO(i) for i in range(self.si.num_of_cbo)])
        self.more_than_5_distresses = ccf_cp([True, False])
        self.num_of_periodic_dpt = ccf_cp(["zero", "one", "more_than_one"])
        self.prefetch_wcil_dpt_at_same_time = ccf_cp([True, False])
        self.dpt_credit_en = ccf_cp([True, False])
        self.periodic_wcil_throttling_en = ccf_cp([True, False])
        self.santa_wcil_throttling_en = ccf_cp([True, False])
        self.cbos_wcil_throttling_en = ccf_cp(
            [EN(i) for i in range(self.si.num_of_cbo)] + [DIS(i) for i in range(self.si.num_of_cbo)])
        self.tor_counter_passed_high_threshold = ccf_cp([CBO(i) for i in range(self.si.num_of_cbo)])
        self.coh_wcil_counter_passed_high_threshold = ccf_cp([CBO(i) for i in range(self.si.num_of_cbo)])
        self.nc_wcil_counter_passed_high_threshold = ccf_cp([CBO(i) for i in range(self.si.num_of_cbo)])
        self.periodic_threshold_def_val = ccf_cp([True, False])
        self.tor_threshold_high_def_vals = ccf_cp(
            [DEFAULT(i) for i in range(self.si.num_of_cbo)] + [NON_DEFAULT(i) for i in range(self.si.num_of_cbo)])
        self.tor_threshold_low_def_vals = ccf_cp(
            [DEFAULT(i) for i in range(self.si.num_of_cbo)] + [NON_DEFAULT(i) for i in range(self.si.num_of_cbo)])
        self.coh_wcil_threshold_high_def_vals = ccf_cp(
            [DEFAULT(i) for i in range(self.si.num_of_cbo)] + [NON_DEFAULT(i) for i in range(self.si.num_of_cbo)])
        self.coh_wcil_threshold_low_def_vals = ccf_cp(
            [DEFAULT(i) for i in range(self.si.num_of_cbo)] + [NON_DEFAULT(i) for i in range(self.si.num_of_cbo)])
        self.nc_wcil_threshold_high_def_vals = ccf_cp(
            [DEFAULT(i) for i in range(self.si.num_of_cbo)] + [NON_DEFAULT(i) for i in range(self.si.num_of_cbo)])
        self.nc_wcil_threshold_low_def_vals = ccf_cp(
            [DEFAULT(i) for i in range(self.si.num_of_cbo)] + [NON_DEFAULT(i) for i in range(self.si.num_of_cbo)])


class collect_dpt_coverage(ccf_base_component):
    def __init__(self):
        self.ccf_registers = ccf_registers.get_pointer()

    def collect_prefetch_dpt_coverage(self, amount_of_ev, min, max):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        self.amount_of_events = 0
        water_mark = self.ccf_registers.dpt_rwm[3]
        water_mark_str = str((water_mark // 10) * 10) + "+"
        if amount_of_ev != 0:
            if amount_of_ev == min:
                self.amount_of_events = "min"
            elif amount_of_ev == max:
                self.amount_of_events = "max"
            else:
                avarage = (min + max) // 2
                if amount_of_ev >= avarage:
                    self.amount_of_events = "high"
                else:
                    self.amount_of_events = "low"
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="num_of_inc_dpt_ev", bin_name=self.amount_of_events,
                                            print_msg_if_not_found=True) and \
                    ccf_dpt_cg.is_bin_in_cp_span(cp_name="highest_water_mark_value", bin_name=water_mark_str,
                                                 print_msg_if_not_found=True):
                ccf_dpt_cg.sample(num_of_inc_dpt_ev=self.amount_of_events, highest_water_mark_value=water_mark_str)

    def sample_dpt_type(self, inc_dpt=False, dec_dpt=False):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        dpt_type = "increment" if inc_dpt and not dec_dpt else ("decrement" if dec_dpt and not inc_dpt else None)
        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="wcil_dpt_type", bin_name=dpt_type,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(wcil_dpt_type=dpt_type)

    def sample_distress(self, cbo_num, in_distress):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        if in_distress:
            cbo_distress_bin = "CBO" + str(cbo_num)
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="cbos_distress", bin_name=cbo_distress_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(cbos_distress=cbo_distress_bin)

    def sample_more_than_5_distresses(self, num_of_distresses):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        more_than_5_distresses = (num_of_distresses > 5)

        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="more_than_5_distresses", bin_name=more_than_5_distresses,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(more_than_5_distresses=more_than_5_distresses)

    def sample_num_of_periodic_dpt(self, num_of_periodic_dpts):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        num_of_periodic_dpt = "zero" if num_of_periodic_dpts == 0 else ("more_than_one" if num_of_periodic_dpts > 1 else "one")
        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="num_of_periodic_dpt", bin_name=num_of_periodic_dpt,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(num_of_periodic_dpt=num_of_periodic_dpt)

    def sample_prefetch_wcil_dpt_at_same_time(self, num_of_prefetch_wcil_dpt_at_same_time):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        prefetch_wcil_dpt_at_same_time = num_of_prefetch_wcil_dpt_at_same_time > 0
        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="prefetch_wcil_dpt_at_same_time", bin_name=prefetch_wcil_dpt_at_same_time,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(prefetch_wcil_dpt_at_same_time=prefetch_wcil_dpt_at_same_time)

    def sample_cbo_tor_counter_passed_high(self, cbo_num, passed):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        if passed:
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="tor_counter_passed_high_threshold", bin_name=CBO(cbo_num),
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(tor_counter_passed_high_threshold=CBO(cbo_num))

    def sample_cbo_coh_wcil_counter_passed_high(self, cbo_num, passed):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        if passed:
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="coh_wcil_counter_passed_high_threshold", bin_name=CBO(cbo_num),
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(coh_wcil_counter_passed_high_threshold=CBO(cbo_num))

    def sample_cbo_nc_wcil_counter_passed_high(self, cbo_num, passed):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()
        if passed:
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="nc_wcil_counter_passed_high_threshold", bin_name=CBO(cbo_num),
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(nc_wcil_counter_passed_high_threshold=CBO(cbo_num))

    def sample_register_values(self, dpt_credit_en, periodic_wcil_throttling_en, santa_wcil_throttling_en,
                               cbos_wcil_throttling_en, periodic_threshold_def_val, tor_threshold_high_def_vals,
                               tor_threshold_low_def_vals, coh_wcil_threshold_high_def_vals,
                               coh_wcil_threshold_low_def_vals, nc_wcil_threshold_high_def_vals,
                               nc_wcil_threshold_low_def_vals):
        ccf_dpt_cg = CCF_DPT_CG.get_pointer()

        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="dpt_credit_en", bin_name=dpt_credit_en,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(dpt_credit_en=dpt_credit_en)
        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="periodic_wcil_throttling_en", bin_name=periodic_wcil_throttling_en,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(periodic_wcil_throttling_en=periodic_wcil_throttling_en)
        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="santa_wcil_throttling_en", bin_name=santa_wcil_throttling_en,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(santa_wcil_throttling_en=santa_wcil_throttling_en)
        if ccf_dpt_cg.is_bin_in_cp_span(cp_name="periodic_threshold_def_val", bin_name=periodic_threshold_def_val,
                                        print_msg_if_not_found=True):
            ccf_dpt_cg.sample(periodic_threshold_def_val=periodic_threshold_def_val)

        for cbo_num in range(self.si.num_of_cbo):
            cbo_en_dis_bin = EN(cbo_num) if cbos_wcil_throttling_en[cbo_num] else DIS(cbo_num)
            tor_threshold_high_def_val_bin = DEFAULT(cbo_num) if tor_threshold_high_def_vals[cbo_num] else NON_DEFAULT(cbo_num)
            tor_threshold_low_def_val_bin = DEFAULT(cbo_num) if tor_threshold_low_def_vals[cbo_num] else NON_DEFAULT(cbo_num)
            coh_wcil_threshold_high_def_val_bin = DEFAULT(cbo_num) if coh_wcil_threshold_high_def_vals[cbo_num] else NON_DEFAULT(cbo_num)
            coh_wcil_threshold_low_def_val_bin = DEFAULT(cbo_num) if coh_wcil_threshold_low_def_vals[cbo_num] else NON_DEFAULT(cbo_num)
            nc_wcil_threshold_high_def_val_bin = DEFAULT(cbo_num) if nc_wcil_threshold_high_def_vals[cbo_num] else NON_DEFAULT(cbo_num)
            nc_wcil_threshold_low_def_val_bin = DEFAULT(cbo_num) if nc_wcil_threshold_low_def_vals[cbo_num] else NON_DEFAULT(cbo_num)
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="cbos_wcil_throttling_en", bin_name=cbo_en_dis_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(cbos_wcil_throttling_en=cbo_en_dis_bin)
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="tor_threshold_high_def_vals",
                                            bin_name=tor_threshold_high_def_val_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(tor_threshold_high_def_vals=tor_threshold_high_def_val_bin)

            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="tor_threshold_low_def_vals", bin_name=tor_threshold_low_def_val_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(tor_threshold_low_def_vals=tor_threshold_low_def_val_bin)
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="coh_wcil_threshold_high_def_vals",
                                            bin_name=coh_wcil_threshold_high_def_val_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(coh_wcil_threshold_high_def_vals=coh_wcil_threshold_high_def_val_bin)

            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="coh_wcil_threshold_low_def_vals",
                                            bin_name=coh_wcil_threshold_low_def_val_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(coh_wcil_threshold_low_def_vals=coh_wcil_threshold_low_def_val_bin)
            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="nc_wcil_threshold_high_def_vals",
                                            bin_name=nc_wcil_threshold_high_def_val_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(nc_wcil_threshold_high_def_vals=nc_wcil_threshold_high_def_val_bin)

            if ccf_dpt_cg.is_bin_in_cp_span(cp_name="nc_wcil_threshold_low_def_vals",
                                            bin_name=nc_wcil_threshold_low_def_val_bin,
                                            print_msg_if_not_found=True):
                ccf_dpt_cg.sample(nc_wcil_threshold_low_def_vals=nc_wcil_threshold_low_def_val_bin)


class ccf_dpt_chk_cov(ccf_base_cov):
    def __init__(self):
        super().__init__()
        self.ccf_dpt_cg: CCF_DPT_CG = CCF_DPT_CG.get_pointer()

    def create_cg(self):
        # define covergroups here
        pass

    def run(self):
        # coverage run phase start here
        VAL_UTDB_MSG(time=0, msg="End of dpt chk coverage Run..")
