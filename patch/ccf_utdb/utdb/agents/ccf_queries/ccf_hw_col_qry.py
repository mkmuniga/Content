#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_hw_col_qry(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.is_DPT = self.DB.all.SIGNAL_NAME.contains('RtidCntrInU202H')
        self.is_peer_clk_req = self.DB.all.SIGNAL_NAME.contains('USidePeerClkReq')
        self.rec_type_is_valid = self.DB.all.REC_TYPE == 'valid'

    def get_all_DPT_records(self):
        name = self.is_DPT
        e = self.DB.flow(name)
        return self.DB.execute(self.DB.flow(e))

    def get_peer_clk_sig(self):
        peer_clk_sig = self.DB.flow(self.DB.flow(self.is_peer_clk_req & self.rec_type_is_valid))
        return self.DB.execute(self.DB.flow(peer_clk_sig))

    class ccf_coherency_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass

