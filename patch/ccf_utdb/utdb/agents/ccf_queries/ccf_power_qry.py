#!/usr/bin/env python3.6.3

from val_utdb_components import val_utdb_qry

class ccf_power_qry(val_utdb_qry):
    def __init__(self):
        self.Cstate = None

    def queries(self):
        # define utdb queires here
        self.Cstate = (self.DB.all.CSTATE == '@Cstate')
        self.monitor_copy_fsm = (self.DB.all.MONITORCPFSM == '@MonitorCpFsm')
        self.valid_Cstate = ~(self.DB.all.CSTATE == '-')
        self.valid_MCFsm = ~(self.DB.all.MONITORCPFSM == '-')

    def get_power_records(self):
        cstate = self.DB.flow(self.valid_Cstate)
        monitor_copy_fsm = self.DB.flow(self.valid_MCFsm)
        return self.DB.execute(monitor_copy_fsm|cstate)

    class power_rec(val_utdb_qry.val_utdb_rec):
        def __init__(self, rec):
            super().__init__(rec)
            self.time = rec.TIME
            self.cstate = rec.CSTATE
            self.copy_monitor_fsm = rec.MONITORCPFSM

