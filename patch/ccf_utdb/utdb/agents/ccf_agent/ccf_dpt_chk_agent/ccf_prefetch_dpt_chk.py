from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import ccf_flow_cov
from agents.ccf_agent.ccf_dpt_chk_agent.ccf_dpt_chk_cov import collect_dpt_coverage
from agents.ccf_data_bases.ccf_santa_db import ccf_santa_db
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_common_base.coh_global import COH_GLOBAL
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from agents.ccf_queries.ccf_hw_col_qry import ccf_hw_col_qry


class ccf_prefetch_dpt_chk(ccf_coherency_base_chk):
    def __init__(self):
        self.checker_name = "ccf_prefetch_dpt_chk"
        self.ccf_santa_db = ccf_santa_db.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.collect_dpt_cov_ptr = collect_dpt_coverage.get_pointer()
        self.santa_counter = 0
        self.min_expected_dpts = 0
        self.max_expected_dpts = 0
        self.actual_inc_dpt = 0
        self.actual_dec_dpt = 0

    def reset(self):
        self.santa_counter = 0
        self.min_expected_dpts = 0
        self.max_expected_dpts = 0
        self.actual_inc_dpt = 0
        self.actual_dec_dpt = 0

    def is_rec_during_test_time(self, r):
        return r.TIME > COH_GLOBAL.global_vars["START_OF_TEST"] and r.TIME < COH_GLOBAL.global_vars["END_OF_TEST"]

    def count_expected_dpt(self):
        hw_col = ccf_hw_col_qry.get_pointer()
        self.all_records = hw_col.get_all_DPT_records()
        for rec in self.all_records:
            for rec_entry in rec.EVENTS:
                event = hw_col.rec(rec_entry)
                if "x" not in event.r.DATA_STR and self.is_rec_during_test_time(event.r):
                    if int(event.r.DATA_STR, 16) > self.santa_counter:
                        self.santa_counter = self.santa_counter + 1
                        self.add_expected()
                    elif int(event.r.DATA_STR, 16) < self.santa_counter:
                        self.santa_counter = self.santa_counter - 1
                        self.add_expected()

    def add_expected(self):
        if self.santa_counter == self.ccf_registers.dpt_rwm[3]:
            self.min_expected_dpts = 1
        if (self.santa_counter in self.ccf_registers.dpt_rwm):
            self.max_expected_dpts = self.max_expected_dpts + 1

    def count_actual_dpt(self):
        current_status_in_core = 0
        for flow in self.ccf_flows:
            if self.ccf_flows[flow].is_u2c_dpt_req():
                if self.ccf_flows[flow].data == 'Intdata=0003':
                    self.actual_inc_dpt = self.actual_inc_dpt + 1
                    current_status_in_core = current_status_in_core + 1
                elif self.ccf_flows[flow].data == 'Intdata=0001':
                    self.actual_dec_dpt = self.actual_dec_dpt + 1
                    current_status_in_core = current_status_in_core - 1
                elif (self.ccf_flows[flow].data == 'Intdata=0007') or (self.ccf_flows[flow].data == 'Intdata=0005'):
                    VAL_UTDB_MSG(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="we get wcil dpt msg")
                else:
                    err_msg = "unexpected U2C REQ data{}".format(self.ccf_flows[flow].data)
                    VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
                if (current_status_in_core > 3) or (current_status_in_core < -1): # status in core can't be -1, but we allow short glitches since sbo can cause races
                    err_msg = "current dpt state in core is {} which is more then maximum or less the min".format(current_status_in_core)
                    VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)

    def check_register_configuration_fit_requirement(self):
        if self.si.dpt_dis == 0:
            for idx, dpt_rwm in enumerate(self.ccf_registers.dpt_rwm, start=1):
                if (idx != len(self.ccf_registers.dpt_rwm)) and (self.ccf_registers.dpt_rwm[idx - 1] > self.ccf_registers.dpt_rwm[idx]):
                    err_msg = "(DPT configuration): DPT RWM configuration looks wrong - dpt_rwm[{}]={} is bigger then dpt_rwm[{}]={}".format(str(idx-1), self.ccf_registers.dpt_rwm[idx - 1], str(idx), self.ccf_registers.dpt_rwm[idx])
                    VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)

    def check(self):
        dpt_dis = self.si.dpt_dis == 1 and self.si.enable_cr_randomization == 1
        self.check_register_configuration_fit_requirement()
        if dpt_dis and (self.actual_inc_dpt > 0 or self.actual_dec_dpt > 0):
            err_msg = "we are not expecting any dpt since DPT is disabled. actual inc dpt: {} actual dec dpt: {}".format(self.actual_inc_dpt,self.actual_dec_dpt )
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
        if self.actual_inc_dpt < self.min_expected_dpts and not dpt_dis:
            err_msg = "num of dpt transaction is {} while expected is more then {}".format(self.actual_inc_dpt, self.min_expected_dpts)
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
        if self.actual_inc_dpt > self.max_expected_dpts:
            err_msg = "num of dpt transaction is {} while expected is less then {}".format(self.actual_dec_dpt, self.max_expected_dpts)
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
        if self.actual_inc_dpt != self.actual_dec_dpt:
            err_msg = "the num of increases DPT events is different than the num of decreases. actual inc dpt: {} actual dec dpt: {}".format(self.actual_inc_dpt,self.actual_dec_dpt)
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)


    def run(self):
        self.count_expected_dpt()
        self.count_actual_dpt()
        self.check()
        if self.si.ccf_cov_en:
            self.collect_dpt_cov_ptr.collect_prefetch_dpt_coverage(self.actual_inc_dpt, self.min_expected_dpts, self.max_expected_dpts)
            self.collect_coverage()
