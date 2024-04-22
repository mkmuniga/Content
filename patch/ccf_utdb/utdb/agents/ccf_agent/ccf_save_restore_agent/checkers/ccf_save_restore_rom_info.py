import time

import subprocess

import re

import os
import sys


from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_params import MODELROOT_PATH_TO_ROMS, \
    ROMS

sys.path.append('/p/hdk/rtl/proj_tools/validation_scripts/xhdk74/17.04.609') # FIXME: PTL - NICE TO HAVE -> hard-coded path
from helpful_utilities.model_utils import get_model_root

class InformationUtils:
    rom_file_path = None

    @classmethod
    def get_raw_lines_from_debug_file(cls, rom_name):
        rom_debug_file = rom_name + ".debug"
        with open(os.path.join(cls.rom_file_path, rom_debug_file), 'r') as f:
            lines = f.readlines()
            f.close()
            return lines

    @classmethod
    def get_full_name(cls, line):
        match = re.search(r"'CRIF_locator':\s+'(?P<reg_name>\S+)',", line)
        full_name = match.group('reg_name').split('/')
        full_name[-1] = full_name[-1].split('.')[-1]
        return '.'.join(full_name)

    @classmethod
    def get_reg_full_name_dict(cls):
        reg_full_name_dict = {}
        with open(os.path.join(cls.rom_file_path, 'ccf_regs.py'), 'r') as f:
            for line in f.readlines():
                match = re.search(r"'(?P<reg_name>\S+)':", line)
                if match:
                    name = match.group('reg_name')
                    full_name = cls.get_full_name(line)
                    reg_full_name_dict[name] = full_name
        return reg_full_name_dict


    @classmethod
    def set_rom_file_path(cls):
        cls.rom_file_path = os.path.join(cls.get_model_root(), MODELROOT_PATH_TO_ROMS)

    @staticmethod
    def get_model_root():
        if os.environ.get('WORKAREA'):
            return os.environ.get('WORKAREA')
        return get_model_root()

    @staticmethod
    def grepFile(file_name, search_for, arguments=""):
        return InformationUtils.runCmdLine(f'/bin/grep {arguments} "{search_for.replace("[", ".").replace("]", ".").replace("/", ".")}" {file_name}')

    @staticmethod
    def runCmdLine(cmdLine, printCmdLine=False):
        if printCmdLine:
            print(cmdLine)
        popenObj = subprocess.Popen(cmdLine, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return popenObj.communicate()[0].decode().split("\n")

class Register:
    def __init__(self, reg_full_name):
        self.list_of_all_values = []
        self.reg_full_name = reg_full_name
        self.reg_name = ""
        self.reset_value = ""
        self.save_value = ""
        self.restore_value = ""
        self.cr_save_txn = ""
        self.cr_restore_txn = ""
        self.sr_command_save = ""
        self.sr_command_restore = ""
        self.restore_done = ""

    def __repr__(self):
        return f'regname: {self.reg_full_name} save_value :  {self.save_value} restore_value :  {self.restore_value} '

    def set_save_command_info(self, save_command_txn):
        self.sr_command_save = save_command_txn

    def set_restore_command_info(self, restore_command_txn, restore_done_txn):
        self.sr_command_restore = restore_command_txn
        self.restore_done = restore_done_txn

    def set_save_value(self, value):
        self.save_value = value

    def set_restore_value(self, value):
        self.restore_value = value

    def is_save_value_x(self):
        return 'x' in str(self.save_value)

    def is_restore_value_x(self):
        return 'x' in str(self.restore_value)

    def reset_fields(self):
        self.save_value = ""
        self.restore_value = ""
        self.sr_command_save = ""
        self.sr_command_restore = ""
        self.restore_done = ""

class ROM:
    def __init__(self, rom_name):
        self.rom_name = rom_name
        self.rom_groups = {}

    def __repr__(self):
        return f'ROM Groups : {self.rom_groups}'

    def add_rom_group(self, group):
        self.rom_groups[group] = []

    def add_reg_to_rom_group(self, group, reg_full_name):
        if group not in self.rom_groups:
            self.rom_groups[group] = []
        if not any(reg.reg_full_name == reg_full_name for reg in self.rom_groups[group]):
            self.rom_groups[group].append(Register(reg_full_name))

    def get_regs_from_group(self, group):
        if type(group) == str:
            return self.rom_groups[group]

        for i, rom_group in enumerate(self.rom_groups):
            if i == group:
                return self.rom_groups[rom_group]
        return []

    def does_group_exist(self, group):
        if type(group) == str:
            return group in self.rom_groups
        else:
            return group in range(0, len(self.rom_groups))

    def get_rom_groups(self):
        groups = ''
        for i, rom_group in enumerate(self.rom_groups):
            groups += f'{i}:{rom_group}, '
        return groups

class ROMStructure:
    roms = {}

    @classmethod
    def reset_roms(cls):
        cls.roms = {}

    @classmethod
    def get_roms(cls):
        # cls.reset_roms()
        if cls.roms == {} :
            InformationUtils.set_rom_file_path()
            cls.create_rom_structure()
        return cls.roms

    @classmethod
    def create_rom_structure(cls):
        start_time = time.time()
        cls.create_roms()
        cls.populate_rom_data()

    @classmethod
    def create_roms(cls):
        for rom in ROMS:
            cls.roms[rom] = ROM(rom)

    @classmethod
    def populate_rom_data(cls):
        reg_full_name_dict = InformationUtils.get_reg_full_name_dict()
        for rom in cls.roms:
            lines = InformationUtils.get_raw_lines_from_debug_file(rom)
            for line in lines:
                match = re.search(r"rom-group: (?P<rom_group>\S+)\s+name: (?P<reg_name>\S+)", line)
                if match:
                    full_name = reg_full_name_dict[match.group('reg_name')]
                    rom_group = match.group('rom_group')
                    cls.roms[rom].add_reg_to_rom_group(rom_group, full_name)
