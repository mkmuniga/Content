from agents.ccf_agent.ccf_power_agent.ccf_power_utils.ccf_power_hw_db import POWER_HW_DB
from val_utdb_components import val_utdb_chk
from val_utdb_bint import bint
from py_ral_db import PyRalReg
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_power_agent.ccf_power_utils.ccf_power_ral_utils import POWER_RAL_AGENT
from agents.ccf_data_bases.ccf_power_sb_db import CCF_POWER_SB_DB
from agents.ccf_agent.ccf_power_agent.common_power.ccf_power_sb_base_txn import DATA_CONVERSION_UTILS
from agents.ccf_agent.ccf_power_agent.common_power.ccf_virtual_signal_txn import VIRTUAL_SIGNAL, CCF_PMA_COMMAND


class ccf_power_virtual_signals_writes_to_punit_checker(val_utdb_chk):

    def __init__(self):
        super().__init__()
        self.ccf_ral_agent_i = POWER_RAL_AGENT.get_pointer()
        self.sb_db = CCF_POWER_SB_DB.get_pointer()
        self.ccf_power_hw_db = POWER_HW_DB.get_pointer()
        self.eom_time_list = self.ccf_power_hw_db.get_list_of_eom_times()
        self.asserted_put_time_list = self.ccf_power_hw_db.get_list_of_asserted_pcput_times()
        self.de_asserted_put_time_list = self.ccf_power_hw_db.get_list_of_de_asserted_pcput_times()
        self.pcput_time_dic = self.ccf_power_hw_db.get_dict_of_pcput_times()
        self.posted_put_time_dic = dict(zip(self.asserted_put_time_list, self.de_asserted_put_time_list))


    def compare_sb_msg_virtual_signal_wr_to_pmc_reg_data(self):
        virtual_signal_msgs = list()
        virtual_signal_msgs = self.get_virtual_signal_sb_msgs()
        # TODO: ranzohar - fix me
        # self.compare_virtual_signals_sb_wr_with_reg_data(virtual_signal_msgs)

    def is_pcput_cross_eom_time(self,eom_time):
        #temp = sorted(self.pcput_time_dic.keys())
        for asseted_put_time,deasserted_put_time in self.posted_put_time_dic.items():
            if ((eom_time >= asseted_put_time) and (eom_time < deasserted_put_time)):
              return True
        return False

    def get_eom_time(self, sb_txn_time):
        for time in self.eom_time_list:
            if (sb_txn_time < time) and (self.is_pcput_cross_eom_time(time)):
                return time
        VAL_UTDB_ERROR(time=sb_txn_time, msg="We didn't found any eom for sb_txn at time {} please check you checker".format(sb_txn_time))



    def compare_virtual_signals_sb_wr_with_reg_data(self, virtual_signal_msgs):
        for sb_txn in virtual_signal_msgs:
            eom_posted_time = self.get_eom_time(sb_txn.time)
            virtual_reg_changes = self.get_virtual_signal_reg_data(eom_posted_time)
            if sb_txn != virtual_reg_changes:
                err_msg = self.print_err_in_virtual_sigs_diff_for_log(sb_txn, eom_posted_time, virtual_reg_changes)
                VAL_UTDB_ERROR(time=sb_txn.time,
                               msg="sb virtual signals write txn to PUNIT don't match reg value in PMC: " + err_msg)
            # else:
            #     self.debug_print_comp(sb_txn, virtual_reg_changes, "values are equal:")
        return 1

    def debug_print_comp(self, sb_txn, virtual_reg_changes, str):
        print("")
        print("")
        print(str)
        self.print_virtual_sigs_comp(sb_txn, virtual_reg_changes)
        print("")
        print("")

    def get_virtual_signal_reg_data(self, sb_msg_txn_time):
        # assumption - sb_wr time happens before reg write time
        block_name = "ccf_pmc_regs"
        reg_name = "CCF_PMA_VIRTUAL_SIGNALS"
        reg_change_time = self.ccf_ral_agent_i.get_reg_change_time_for_later_event(
            block_name, reg_name, sb_msg_txn_time, max_time_delta=1)
        reg: PyRalReg = self.ccf_ral_agent_i.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        return self.get_field_values_from_reg(reg, reg_change_time)

    def get_virtual_signal_sb_msgs(self):
        virual_signals_reg_address = "0x1bc"
        virtual_signal_address_val = bint(int(virual_signals_reg_address, 16))
        virtual_signal_msgs = list()
        print(self.sb_db.power_sb_msgs_db)
        for tran in self.sb_db.power_sb_msgs_db["07 CRWRITE"]:
            if tran.addr == virtual_signal_address_val:
                current_virtual_signal_msg = self.get_virtual_signal_fields_from_sb_txn(tran)
                virtual_signal_msgs.append(current_virtual_signal_msg)
                # print(current_virtual_signal_msg.to_string())
        return virtual_signal_msgs

    def get_field_values_from_reg(self, reg, reg_change_time):
        field_values = VIRTUAL_SIGNAL()
        field_values.time = reg_change_time
        field_values.curr_llc_ways = reg.get_field_by_name("curr_llc_ways").read(reg_change_time)
        field_values.curr_llc_ceiling = reg.get_field_by_name("curr_llc_ceiling").read(reg_change_time)
        field_values.curr_llc_floor = reg.get_field_by_name("curr_llc_floor").read(reg_change_time)
        field_values.llc_command_ack = reg.get_field_by_name("llc_command_ack").read(reg_change_time)
        field_values.flush_ack = reg.get_field_by_name("flush_ack").read(reg_change_time)
        field_values.monitor_overflow = reg.get_field_by_name("monitor_overflow").read(reg_change_time)
        field_values.monitor_copied = reg.get_field_by_name("monitor_copied").read(reg_change_time)
        field_values.ccf_blocked = reg.get_field_by_name("ccf_blocked").read(reg_change_time)
        field_values.ccf_fsm_pwr_up_surv_halt = reg.get_field_by_name("ccf_fsm_pwr_up_surv_halt").read(reg_change_time)
        field_values.ccf_fsm_pwr_dn_surv_halt = reg.get_field_by_name("ccf_fsm_pwr_dn_surv_halt").read(reg_change_time)
        field_values.ccf_fsm_gv_ctl_surv_halt = reg.get_field_by_name("ccf_fsm_gv_ctl_surv_halt").read(reg_change_time)
        return field_values

    def print_err_in_virtual_sigs_diff_for_log(self, current_sb_txn, eom_posted_time, virtual_reg_changes):
        sb_msg = "SB message values: time= {} txn_eom time={} ".format(current_sb_txn.time, eom_posted_time)
        reg_msg = "ccf_pma_virtual_signals register values: time= %s " % virtual_reg_changes.time
        if current_sb_txn.curr_llc_ways != virtual_reg_changes.curr_llc_ways:
            sb_msg = sb_msg + "curr_llc_ways= %s " % current_sb_txn.curr_llc_ways
            reg_msg = reg_msg + "curr_llc_ways= %s " % virtual_reg_changes.curr_llc_ways
        if current_sb_txn.curr_llc_ceiling != virtual_reg_changes.curr_llc_ceiling:
            sb_msg = sb_msg + "curr_llc_ceiling= %s " % current_sb_txn.curr_llc_ceiling
            reg_msg = reg_msg + "curr_llc_ceiling= %s " % virtual_reg_changes.curr_llc_ceiling
        if current_sb_txn.curr_llc_floor != virtual_reg_changes.curr_llc_floor:
            sb_msg = sb_msg + "curr_llc_floor= %s " % current_sb_txn.curr_llc_floor
            reg_msg = reg_msg + "curr_llc_floor= %s " % virtual_reg_changes.curr_llc_floor
        if current_sb_txn.ccf_blocked != virtual_reg_changes.ccf_blocked:
            sb_msg = sb_msg + "ccf_blocked= %s " % current_sb_txn.ccf_blocked
            reg_msg = reg_msg + "ccf_blocked= %s " % virtual_reg_changes.ccf_blocked
        if current_sb_txn.ccf_fsm_pwr_up_surv_halt != virtual_reg_changes.ccf_fsm_pwr_up_surv_halt:
            sb_msg = sb_msg + "ccf_fsm_pwr_up_surv_halt= %s " % current_sb_txn.ccf_fsm_pwr_up_surv_halt
            reg_msg = reg_msg + "ccf_fsm_pwr_up_surv_halt= %s " % virtual_reg_changes.ccf_fsm_pwr_up_surv_halt
        if current_sb_txn.ccf_fsm_pwr_dn_surv_halt != virtual_reg_changes.ccf_fsm_pwr_dn_surv_halt:
            sb_msg = sb_msg + "ccf_fsm_pwr_dn_surv_halt= %s " % current_sb_txn.ccf_fsm_pwr_dn_surv_halt
            reg_msg = reg_msg + "ccf_fsm_pwr_dn_surv_halt= %s " % virtual_reg_changes.ccf_fsm_pwr_dn_surv_halt
        if current_sb_txn.ccf_fsm_gv_ctl_surv_halt != virtual_reg_changes.ccf_fsm_gv_ctl_surv_halt:
            sb_msg = sb_msg + "ccf_fsm_gv_ctl_surv_halt= %s " % current_sb_txn.ccf_fsm_gv_ctl_surv_halt
            reg_msg = reg_msg + "ccf_fsm_gv_ctl_surv_halt= %s " % virtual_reg_changes.ccf_fsm_gv_ctl_surv_halt
        if current_sb_txn.monitor_copied != virtual_reg_changes.monitor_copied:
            sb_msg = sb_msg + "monitor_copied= %s " % current_sb_txn.monitor_copied
            reg_msg = reg_msg + "monitor_copied= %s " % virtual_reg_changes.monitor_copied
        if current_sb_txn.monitor_overflow != virtual_reg_changes.monitor_overflow:
            sb_msg = sb_msg + "monitor_overflow= %s " % current_sb_txn.monitor_overflow
            reg_msg = reg_msg + "monitor_overflow= %s " % virtual_reg_changes.monitor_overflow
        return "differences in virtual_signals are " + sb_msg + "while " + reg_msg

    def print_virtual_sigs_comp(self, current_sb_txn, virtual_reg_changes):
        print("sb        |            reg")
        print("time", current_sb_txn.time, virtual_reg_changes.time)
        print("curr_llc_ways", current_sb_txn.curr_llc_ways, virtual_reg_changes.curr_llc_ways)
        print("curr_llc_ceiling", current_sb_txn.curr_llc_ceiling, virtual_reg_changes.curr_llc_ceiling)
        print("curr_llc_floor", current_sb_txn.curr_llc_floor, virtual_reg_changes.curr_llc_floor)
        print("llc_command_ack", current_sb_txn.llc_command_ack, virtual_reg_changes.llc_command_ack)
        print("flush_ack", current_sb_txn.flush_ack, virtual_reg_changes.flush_ack)
        print("monitor_overflow", current_sb_txn.monitor_overflow, virtual_reg_changes.monitor_overflow)
        print("monitor_copied", current_sb_txn.monitor_copied, virtual_reg_changes.monitor_copied)
        print("ccf_blocked", current_sb_txn.ccf_blocked, virtual_reg_changes.ccf_blocked)
        print("ccf_fsm_pwr_up_surv_halt", current_sb_txn.ccf_fsm_pwr_up_surv_halt, virtual_reg_changes.ccf_fsm_pwr_up_surv_halt)
        print("ccf_fsm_pwr_dn_surv_halt", current_sb_txn.ccf_fsm_pwr_dn_surv_halt, virtual_reg_changes.ccf_fsm_pwr_dn_surv_halt)
        print("ccf_fsm_gv_ctl_surv_halt", current_sb_txn.ccf_fsm_gv_ctl_surv_halt, virtual_reg_changes.ccf_fsm_gv_ctl_surv_halt)
        pass

    def get_virtual_signal_fields_from_sb_txn(self, tran):
        data_in_bits = DATA_CONVERSION_UTILS.get_data_in_bits(tran.data)
        virtual_sig = VIRTUAL_SIGNAL()
        virtual_sig.time = tran.time
        virtual_sig.curr_llc_ways = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 4, 0)
        virtual_sig.curr_llc_ceiling = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 9, 5)
        virtual_sig.curr_llc_floor = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 14, 10)
        virtual_sig.llc_command_ack = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 15, 15)
        virtual_sig.flush_ack = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 17, 17)
        virtual_sig.monitor_overflow = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 18, 18)
        virtual_sig.monitor_copied = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 19, 19)
        virtual_sig.ccf_blocked = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 16, 16)
        virtual_sig.ccf_fsm_pwr_up_surv_halt = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 21, 21)
        virtual_sig.ccf_fsm_pwr_dn_surv_halt = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 22, 22)
        virtual_sig.ccf_fsm_gv_ctl_surv_halt = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 23, 23)
        return virtual_sig

    def get_ccf_pma_command_fields(self, tran):
        data_in_bits = DATA_CONVERSION_UTILS.get_data_in_bits(tran.data)
        virtual_sig = CCF_PMA_COMMAND()
        virtual_sig.time = tran.time
        virtual_sig.block_req = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 0, 0)
        virtual_sig.unblock_req = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 1, 1)
        virtual_sig.monitor_copy = DATA_CONVERSION_UTILS.get_data_slice_from_bit(data_in_bits, 2, 2)

        return virtual_sig

    def get_ccf_pma_command_msgs(self):
        ccf_pma_command_addr = bint(int("0x1244", 16))
        ccf_pma_command_msgs = list()
        for tran in self.sb_db.power_sb_msgs_db["07 CRWRITE"]:
            if tran.addr == ccf_pma_command_addr:
                print(f"{tran.time} {tran.addr}")
                current_virtual_signal_msg = self.get_ccf_pma_command_fields(tran)
                ccf_pma_command_msgs.append(current_virtual_signal_msg)
        return ccf_pma_command_msgs

    def check_pmc_acks_vs_punit_cfgs(self):
        virtual_signal_msgs = list()
        virtual_signal_msgs = self.get_virtual_signal_sb_msgs()
        ccf_pma_command_msgs = list()
        ccf_pma_command_msgs = self.get_ccf_pma_command_msgs()
        united_list = list()
        united_list = virtual_signal_msgs + ccf_pma_command_msgs
        united_list.sort(key=CCF_PMA_COMMAND.get_time)
        should_expect_ack = 0

        for tran1 in united_list:#monitor_copy req/ack checker
            if hasattr(tran1, 'monitor_copy') and tran1.monitor_copy == 1:
                should_expect_ack = 1
            if hasattr(tran1, 'monitor_copied') and tran1.monitor_copied == 1:
                if should_expect_ack == 0:
                    VAL_UTDB_ERROR(time=tran1.time, msg="Punit get monitor_copy_ack from PMC but monitor_copy request wasn't send")
                else:
                    should_expect_ack = 0


    def run(self):
         self.compare_sb_msg_virtual_signal_wr_to_pmc_reg_data()
         self.check_pmc_acks_vs_punit_cfgs()
