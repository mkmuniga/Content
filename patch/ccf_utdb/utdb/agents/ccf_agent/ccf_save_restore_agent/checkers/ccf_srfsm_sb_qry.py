import re
from dbWrapper import pred_t

from val_utdb_components import val_utdb_qry

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_params import *
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_defs import *

class CcfSrfsmSbQry(val_utdb_qry):
    def __init__(self):
        self.recs = []

    def queries(self):
        self.pmc_gpsb_trk_qry = (self.DB.all.TRACKER == PMC_GPSB_SB_LOG)
        self.recs = [self.SRFSM_SB_REC(t) for o in self.DB.execute(self.DB.alls[self.pmc_gpsb_trk_qry]) for t in o.EVENTS]

    def get_all_save_sr_command(self, srfsm_pid):
        return [r for r in self.recs if r.is_sr_command() and r.is_sr_command_save() and r.ldpid_matches_srfsm_pid(srfsm_pid)]

    def get_all_restore_sr_command(self, srfsm_pid):
        return [r for r in self.recs if r.is_sr_command() and r.is_sr_command_restore() and r.ldpid_matches_srfsm_pid(srfsm_pid)]

    def get_all_save_restore_done_command(self, srfsm_pid):
        return [r for r in self.recs if r.is_save_restore_done_command() and r.lspid_matches_srfsm_pid(srfsm_pid)]

    def get_time_ordered_sr_commands(self, srfsm_pid):
        all_sr_command_save = self.get_all_save_sr_command(srfsm_pid)
        all_sr_command_restore = self.get_all_restore_sr_command(srfsm_pid)
        all_save_and_restore_commands = all_sr_command_restore + all_sr_command_save
        all_save_and_restore_commands.sort(key=lambda x: x.time)
        return all_save_and_restore_commands

    def get_restore_done_command(self, time_of_restore, srfsm_pid):
        all_restore_done_commands = self.get_all_save_restore_done_command(srfsm_pid)
        list_of_all_restore_done_after_restore_start = [r for r in all_restore_done_commands if r.time > time_of_restore]
        return list_of_all_restore_done_after_restore_start[0]

    def has_save_restore_flow_occured(self, srfsm_pid):
        all_sr_command_save = self.get_all_save_sr_command(srfsm_pid)
        all_sr_command_restore = self.get_all_restore_sr_command(srfsm_pid)
        return not ((len(all_sr_command_save) == 0) and (len(all_sr_command_restore) == 0))


    class SRFSM_SB_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)
            self.time = self.r.TIME

        def get_tran(self):
            return self.r
        
        def __repr__(self):
            return(f"TIME:{self.time} DIR:{self.r.DIR} TYPE:{self.r.TYPE} LSPID:{self.r.LSPID} "
                   f"LDPID:{self.r.LDPID} OPC:{self.get_opcode()} Address:{self.r.ADDRESS} SAI:{self.r.SAI} DATA:{hex(self.get_sb_data())} "
                   f"TRACKER:{self.r.TRACKER}")

        def get_sb_data(self):
            if self.r.DATA == '-':
                return 0
            return int(self.r.DATA, 16)

        def is_sr_command_save(self):
            save_command = self.get_sb_data() >> CMD_BIT_SAVE & 0x1
            return save_command == 1

        def is_sr_command_restore(self):
            restore_command = self.get_sb_data() >> CMD_BIT_RESTORE & 0x1
            return restore_command == 1

        def is_sr_command(self):
            return (self.r.ADDRESS == SR_COMMAND_ADDR) and (self.r.LDPID in srfsm_pid_rom_name_dict.keys())

        def is_save_restore_done_command(self):
            return (self.get_opcode() == VIRTUAL_WIRE)  and (self.r.LSPID in srfsm_pid_rom_name_dict.keys())

        def ldpid_matches_srfsm_pid(self, srfsm_pid):
            return self.r.LDPID == srfsm_pid

        def lspid_matches_srfsm_pid(self, srfsm_pid):
            return self.r.LSPID == srfsm_pid

        def get_groups_from_sr_command(self):
            number_of_sr_fsms = NUM_OF_SAVE_RESTORE_ENGINES
            groups_from_command = []
            for i in range(number_of_sr_fsms):
                groups_from_command.append(self.get_sb_data() >> (i * NUM_OF_SAVE_RESTORE_ENGINES) & 0xf)
            # ROM groups go from 0-14, if agent (PMC) writes group 15 this is a dummy
            # group and the SR FSM will not do a save/restore
            while ROM_GROUP_15 in groups_from_command:
                groups_from_command.remove(ROM_GROUP_15)
            return groups_from_command

        def get_opcode(self):
            return self.r.OPC.split(' ')[0]
