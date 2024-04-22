#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_mini_features_qry(ccf_base_qry):

    def queries(self):
        self.is_peer_clk_req = self.DB.all.SIGNAL_NAME.contains('USidePeerClkReq')
        self.rec_type_is_valid = self.DB.all.REC_TYPE == 'valid'


    def get_peer_clk_sig(self):
        peer_clk_sig = self.DB.flow(self.DB.flow(self.is_peer_clk_req & self.rec_type_is_valid))

        for rec in self.DB.execute(self.DB.flow(peer_clk_sig)):
            for rec_entry in rec.EVENTS:
                print("rec_entry", rec_entry)

        return self.DB.execute(self.DB.flow(peer_clk_sig))


    class ccf_coherency_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass