#!/usr/bin/env python3.6.3a

#################################################################################################
# ccf_coherency_qry.py 
#
# Owner:              ranzohar & mlugassi
# Creation Date:      6.2021
#
# ###############################################
#
# Description:
#   This file contain all ccf NC queries and flow definitions
#################################################################################################

from val_utdb_components import val_utdb_qry, pred_t


class CCF_NC_MCAST_QRY(val_utdb_qry):
    nc_dbs: pred_t
    uri_stitch: pred_t

    def queries(self):
        self.all_trans = (self.DB.all.TIME > 0)

    def __execute_all_trans_qry(self):
        all_trans_groups = self.DB.flow(self.all_trans['+'])
        return self.DB.execute(all_trans_groups)

    def get_all_trans(self):
        trans = list()

        for trans_groups in self.__execute_all_trans_qry():
            for event in trans_groups.EVENTS:
                print(event)
                if (event.SELECTOR == "cfi" and event.PROTOCOL_ID == "UPI.NC") or \
                        event.SELECTOR == "racu_sb" or \
                        (event.SELECTOR == "aligned_sb" and "EVENTS" in event.PORT):
                    trans.append(CCF_NC_MCAST_QRY.TRAN_REC(event))

        return trans

    class TRAN_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)
