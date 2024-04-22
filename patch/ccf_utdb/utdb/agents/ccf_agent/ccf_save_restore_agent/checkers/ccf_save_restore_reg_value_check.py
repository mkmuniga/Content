from py_ral_db import PyRalXValueError
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_params import exclude_list, \
    regs_that_count_up, report_error_when_register_value_is_missing_from_cr_tracker_file, \
    report_error_when_register_is_x, report_error_when_rom_group_does_not_exist_in_rom
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_sr_pmc_qry import CcfUtdbSrPmcQry

class SaveRestoreRegisterValueCheck:

    def create_reset_done_time_db(self):
        self.pwr_up_fsm_db = dict()
        self.ccf_utdb_sr_pmc_qry : CcfUtdbSrPmcQry = CcfUtdbSrPmcQry.get_pointer()
        self.rst_done_db = dict()
        pwr_up_ctrl_iter = self.ccf_utdb_sr_pmc_qry.get_all_pwr_up_ctrl_fsm_recs()
        for itr in pwr_up_ctrl_iter:
            for ev in itr.EVENTS:
                if ( (ev.CCFPWRUPCONTROLFSM != '-') & (ev.CCFPWRUPCONTROLFSM != '') ):
                    self.pwr_up_fsm_db[ev.TIME] = ev.CCFPWRUPCONTROLFSM

    def set_data(self, rom, save_restore_pair):
        self.create_reset_done_time_db()
        self.rom = rom
        self.group = save_restore_pair.group
        self.regs_in_group = self.rom.get_regs_from_group(self.group)
        self.sr_command_save = save_restore_pair.sr_command_save
        self.sr_command_restore = save_restore_pair.sr_command_restore
        self.sr_restore_done = save_restore_pair.restore_done

        if len(self.regs_in_group) == 0:
            return

        self.set_save_value_for_registers_to_be_saved()
        self.set_restore_value_for_registers_to_be_restored()

    def check(self):
        self.check_rom_group_exists_in_rom()

        for reg in self.regs_in_group:
            if not self.should_check_register(reg.reg_full_name):
                continue

            self.check_register_data_exits(reg)
            self.check_register_is_not_x(reg)
            self.check_register_save_value_matches_restore_value(reg)

            reg.reset_fields()


    def check_rom_group_exists_in_rom(self):
        if not self.rom.does_group_exist(self.group) and report_error_when_rom_group_does_not_exist_in_rom:
            VAL_UTDB_ERROR(
                time=self.sr_command_save.time , 
                msg=
                f'Save Restore Checker: PMA Saved and Restored ROM group that doesn\'t exist\n'
                f'\texpected ROM Groups : {self.rom.get_rom_groups()}\n'
                f'\trequested ROM Group : {self.group}\n'
                f'ROM                 {self.rom.rom_name}\n'
                f'sr_save_command     {self.sr_command_save}\n'
                f'sr_restore_command  {self.sr_command_restore}\n'
            )


    def check_register_data_exits(self, reg):
        if reg.save_value is None and report_error_when_register_value_is_missing_from_cr_tracker_file:
            VAL_UTDB_ERROR(
                time=self.sr_command_restore.time,
                msg=
                f'Save Restore Checker: Register data is missing from PyRal\n'
                f'The following register is not being monitored: {reg.reg_full_name}'
            )

        if reg.save_value == None:
            print(f"Register {reg.reg_full_name} could not be found in PyRal.")

    def check_register_is_not_x(self, reg):
        if (reg.is_save_value_x() or reg.is_restore_value_x()) and report_error_when_register_is_x:
            VAL_UTDB_ERROR(
                time=self.sr_command_save.time,
                msg=
                f'Save Restore Checker: register save or restore value is x \n'
                f'From ROM: {self.rom.rom_name} Group {self.group} Register: {reg.reg_full_name} '
                f'save or restore value is x\n'
                f'\t Save Value    = {reg.save_value}\n'
                f'\t Restore Value = {reg.restore_value}\n'
            )

    def check_register_save_value_matches_restore_value(self, reg):
        if reg.save_value != reg.restore_value:
            if self.register_counts_upwards(reg.reg_full_name) and reg.restore_value >= reg.save_value:
                pass
            else:
                VAL_UTDB_ERROR(
                    time=self.sr_restore_done.time,
                    msg=
                    f'Save Restore Checker: save value does not match restore value\n'
                    f'From ROM: {self.rom.rom_name} Group {self.group} Register: {reg.reg_full_name} '
                    f'save does not match restore\n'
                    f'\t Save Value    = {hex(reg.save_value)}\n'
                    f'\t Restore Value = {hex(reg.restore_value)}\n'
                    f'sr_command_save    {self.sr_command_save}\n'
                    f'sr_command_restore {self.sr_command_restore}\n'
                    f'restore_done       {self.sr_restore_done}\n'
                )

    def set_save_value_for_registers_to_be_saved(self):
        for reg in self.regs_in_group:
            reg.set_save_value(self.get_value_of_register_at_time(reg.reg_full_name, self.sr_command_save.time  ))

    def set_restore_times(self):
        first_match  = False
        self.restore_time = []
        pwr_up_fsm_list = list(self.pwr_up_fsm_db.items())
        list_time_column  = 0
        list_value_column = 1
        for i in range(len(pwr_up_fsm_list)):
            if pwr_up_fsm_list[i][list_value_column] == 'CCF_VCCR_RESTORE':
                first_match = True
            elif first_match and pwr_up_fsm_list[i][list_value_column] == 'CCF_RESET_IN_PROG_DONE':
                first_match = False
                self.restore_time.append(pwr_up_fsm_list[i][list_time_column])
            else:
                first_match = False

        for i in range(len(self.restore_time)):
            if (self.sr_restore_done.time > self.restore_time[0]):
                self.restore_time.pop(0)
        return self.restore_time

    def set_restore_value_for_registers_to_be_restored(self):
        restore_time_check = self.set_restore_times()
        for reg in self.regs_in_group:
            reg.set_restore_value(self.get_value_of_register_at_time(reg.reg_full_name, restore_time_check[0]))

    def get_value_of_register_at_time(self, reg_name, time):
        ral_agent = ccf_ral_agent.get_pointer()
        reg = ral_agent.top.get_reg_by_name(reg_name)
        if reg is None:
            return None
        try:
            return reg.read(time)
        except PyRalXValueError as e:
            return e.value_str

    def should_check_register(self, register_full_name):
        return register_full_name not in exclude_list

    def register_counts_upwards(self, register_full_name):
        return register_full_name in regs_that_count_up
