#!/usr/bin/env python3.6.3

from val_utdb_components import val_utdb_qry

class CcfUtdbSrPmcQry(val_utdb_qry):
    def __init__(self):
        self.Cstate = None

    def queries(self):
        # define utdb queires here
        self.pwr_up_ctrl_fsm = self.DB.all.CCFPWRUPCONTROLFSM == '@CcfPwrUpControlFsm'
        #self.c6_completed    = self.DB.all.CCFPWRUPCONTROLFSM.contains('CCF_C6_EXIT')

    def get_all_pwr_up_ctrl_fsm_recs(self):
        pwr_up_fsm    = self.DB.flow(self.pwr_up_ctrl_fsm)
        return self.DB.execute(pwr_up_fsm)

    # def get_num_of_c6_occured(self):
    #     c6_occured = self.DB.flow(self.c6_completed)
    #     return self.DB.execute(self.DB.flow(c6_occured))

    class Rec(val_utdb_qry.val_utdb_rec):
        pass