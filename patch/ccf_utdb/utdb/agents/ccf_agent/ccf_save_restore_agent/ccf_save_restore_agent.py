#!/usr/bin/env python3.6.3

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker import CcfSaveRestoreChecker
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_srfsm_sb_qry import CcfSrfsmSbQry
from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_sr_pmc_qry import CcfUtdbSrPmcQry

class SaveRestoreAgent(ccf_base_agent):
    def build(self):
        super().build()
        self.ccf_srfsm_sb_qry                        = CcfSrfsmSbQry.create()
        self.ccf_sr_checker                          = CcfSaveRestoreChecker.create()
        self.ccf_utdb_sr_pmc_qry : CcfUtdbSrPmcQry = CcfUtdbSrPmcQry.create()

    def connect(self):
        super().connect()
        self.ccf_srfsm_sb_qry.connect_to_db('merged_sb_logdb')
        self.ccf_utdb_sr_pmc_qry.connect_to_db('pmc_logdb')

    def run(self):
        self.ccf_sr_checker.run()


if __name__ == "__main__":
    SaveRestoreAgent.initial()
