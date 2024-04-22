from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_defs import *


class SaveRestoreCommandOrderingCheck():
    def __init__(self):
        self.error_list = []
        self.time_ordered_all_save_and_restore_commands = []

    def set_data(self, time_ordered_all_save_and_restore_commands):
        self.time_ordered_all_save_and_restore_commands = time_ordered_all_save_and_restore_commands
        self.printable_all_sr_cmds = "\n\t" + "\n\t".join([str(t) for t in time_ordered_all_save_and_restore_commands])
        self.all_sr_groups = set(group for sr_cmd in self.time_ordered_all_save_and_restore_commands for group in sr_cmd.get_groups_from_sr_command())
        self.prior_sr_cmd_to_this_group = {group: None for group in self.all_sr_groups}

    def check(self):

        for sr_command in self.time_ordered_all_save_and_restore_commands:
            for group in sr_command.get_groups_from_sr_command():
                    if sr_command.is_sr_command_save() \
                       and self.prior_sr_cmd_to_this_group[group] is not None \
                       and self.prior_sr_cmd_to_this_group[group].is_sr_command_save() \
                       and not ALLOW_ABORTED_SAVES_WITHOUT_RESTORES:
                        VAL_UTDB_ERROR(
                                time=sr_command.time,
                                msg=
                                    f'Save Restore Checker: Save Command issued for group that has already been saved\n'
                                    f'A save cmd has been issued for group {group} that was previously saved with '
                                    f'no intervening restores.\n'
                                    f'The prior save to this group was:\n'
                                    f'\t{self.prior_sr_cmd_to_this_group[group]}\n'
                                    f'This save happened afterward with no intervening restore:\n'
                                    f'\t{sr_command}\n'
                                    f'\t\t*****to decode sr_command: bit {CMD_BIT_RESTORE} is restore, bit {CMD_BIT_SAVE} is save****\n'
                                    f'List of All Sr_Commands {self.printable_all_sr_cmds}')

                    if sr_command.is_sr_command_restore():
                        if self.prior_sr_cmd_to_this_group[group] is None:
                            VAL_UTDB_ERROR(
                                time=sr_command.time,
                                msg=
                                    f'Save Restore Checker: Restore Command issued for group that has never been saved\n'
                                    f'A restore cmd has been issued for group {group} when there have been '
                                    f'no recent saves.\n'
                                    f'This restore happened with no prior save to that group:\n'
                                    f'\t{sr_command}\n'
                                    f'\t\t*****to decode sr_command: bit {CMD_BIT_RESTORE} is restore, bit {CMD_BIT_SAVE} is save****\n'
                                    f'List of All Sr_Commands {self.printable_all_sr_cmds}')

                        elif self.prior_sr_cmd_to_this_group[group].is_sr_command_restore() and group not in groups_that_can_restore_multiple_times_from_same_save:
                            VAL_UTDB_ERROR(
                                time=sr_command.time,
                                msg=
                                    f'Save Restore Checker: Restore Command issued for group that was already restored\n'
                                    f'A restore cmd has been issued for group {group} that was previously restored with '
                                    f'no intervening saves.\n'
                                    f'The prior restore to this group was:\n'
                                    f'\t{self.prior_sr_cmd_to_this_group[group]}\n'
                                    f'This restore happened afterward with no intervening save:\n'
                                    f'\t{sr_command}\n'
                                    f'\t\t*****to decode sr_command: bit {CMD_BIT_RESTORE} is restore, bit {CMD_BIT_SAVE} is save****\n'
                                    f'List of All Sr_Commands {self.printable_all_sr_cmds}')


                    self.prior_sr_cmd_to_this_group[group] = sr_command

        for group in self.prior_sr_cmd_to_this_group:
            sr_command = self.prior_sr_cmd_to_this_group[group]
            if sr_command.is_sr_command_save() and not ALLOW_ABORTED_SAVES_WITHOUT_RESTORES:
                VAL_UTDB_ERROR(
                        time=sr_command.time,
                        msg=
                            f'Save Restore Checker: Save Command issued that was never followed by a restore\n'
                            f'This save cmd was issued for group {group}, and never followed by a restore to that group.\n'
                            f'\t{sr_command}\n'
                            f'\t\t*****to decode sr_command: bit {CMD_BIT_RESTORE} is restore, bit {CMD_BIT_SAVE} is save****\n'
                            f'List of All Sr_Commands {self.printable_all_sr_cmds}')

