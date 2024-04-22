#!/usr/bin/env python3.6.3a
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_checker import CCF_NC_EVENTS_CHECKER
from agents.cncu_agent.common.cncu_base_agent import CNCU_BASE_AGENT
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.dbs.ccf_nc_sb_qry import CCF_NC_SB_QRY


class CNCU_EVENT_AGENT(CNCU_BASE_AGENT):

    def __init__(self):
        super().__init__()
        self.ccf_nc_sb_db: CCF_NC_SB_DB = None
        self.ccf_nc_sb_qry: CCF_NC_SB_QRY = None
        self.ccf_nc_events_checker = CCF_NC_EVENTS_CHECKER.create()

    def build(self):
        super().build()
        self.ccf_nc_sb_db = CCF_NC_SB_DB.create()
        self.ccf_nc_sb_qry = CCF_NC_SB_QRY.create()

    def connect(self):
        super().connect()
        self.ccf_nc_sb_qry.connect_to_db('aligned_sb_logdb')

    def run(self):
        super().run()
        self.ccf_nc_sb_db.run_db_builder()
        if self.si.events_chk_en: # TODO: ranzohar - move to default_jobs file
            self.ccf_nc_events_checker.run()


if __name__ == "__main__":
    CNCU_EVENT_AGENT.initial()
