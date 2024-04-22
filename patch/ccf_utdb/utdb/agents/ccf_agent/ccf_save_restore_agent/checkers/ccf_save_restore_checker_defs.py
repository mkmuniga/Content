import re

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_params import *

#params for checker
NUM_OF_SAVE_RESTORE_ENGINES = 4
ROM_GROUP_15  = 15
SR_COMMAND_ADDR = '0x0000'
VIRTUAL_WIRE = '70'
HANGTIME = 9000000000
CMD_BIT_RESTORE = 16
CMD_BIT_SAVE = 17

class SaveRestoreTxn():
    def __init__(self, save, restore, restore_done, group):
        self.sr_command_save = save
        self.sr_command_restore = restore
        self.restore_done = restore_done
        self.group = group

    def __repr__(self):
        return f'SR group: {self.group}, sr_command_save : {self.sr_command_save} sr_command_restore : {self.sr_command_restore}'
