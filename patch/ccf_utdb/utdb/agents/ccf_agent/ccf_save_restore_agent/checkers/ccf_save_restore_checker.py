
from val_utdb_components import val_utdb_chk
from val_utdb_report import val_utdb_reporter

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_helpper_functions import \
    get_save_restore_sr_command_pairs
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_command_ordering_check import \
    SaveRestoreCommandOrderingCheck
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_reg_value_check import \
    SaveRestoreRegisterValueCheck
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_rom_info import ROMStructure
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_params import *
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_srfsm_sb_qry import CcfSrfsmSbQry
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_sr_pmc_qry import CcfUtdbSrPmcQry


class CcfSaveRestoreChecker(val_utdb_chk):

    def run(self):
        self.ccf_srfsm_sb_qry = CcfSrfsmSbQry.get_pointer()
        self.error_reporter = val_utdb_reporter.get_pointer()
        self.roms = ROMStructure.get_roms()

        for srfsm_pid in srfsm_pid_rom_name_dict:
            self.set_sr_checker_txn_lists(srfsm_pid)
            if (self.ccf_srfsm_sb_qry.has_save_restore_flow_occured(srfsm_pid)):
                self.check_sr_command_ordering()
                if (len(self.error_reporter.error_q) == 0):  # Do not check the values of the registers if commands aren't ordered correctly
                    self.check_save_restore_reg_value(srfsm_pid_rom_name_dict[srfsm_pid])

    def check_sr_command_ordering(self):
        sr_command_ordering_check = SaveRestoreCommandOrderingCheck()
        sr_command_ordering_check.set_data(self.time_ordered_sr_commands)
        sr_command_ordering_check.check()

    def set_sr_checker_txn_lists(self, srfsm_ldst_pid):
        self.time_ordered_sr_commands = self.ccf_srfsm_sb_qry.get_time_ordered_sr_commands(srfsm_ldst_pid)
        self.all_save_restore_done_command = self.ccf_srfsm_sb_qry.get_all_save_restore_done_command(srfsm_ldst_pid)

    def check_save_restore_reg_value(self, rom_name):
        self.ccf_utdb_sr_pmc_qry : CcfUtdbSrPmcQry = CcfUtdbSrPmcQry.get_pointer()
        # c6_count = 0
        # c6_iter = self.ccf_utdb_sr_pmc_qry.get_num_of_c6_occured()
        # for itr in c6_iter:
        #     for ev in itr.EVENTS:
        #         c6_count += 1

        for save_restore_command_pair in get_save_restore_sr_command_pairs(self.time_ordered_sr_commands, self.all_save_restore_done_command):
            sr_reg_value_check = SaveRestoreRegisterValueCheck()
            sr_reg_value_check.set_data(self.roms[rom_name], save_restore_command_pair)
            sr_reg_value_check.check()
