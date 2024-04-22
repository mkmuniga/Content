from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_llc_coherency_qry(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.uri_tid = (self.DB.all.TID == '@tid')
        self.uri_lid = (self.DB.all.LID == '@lid')
        self.uri_pid = (self.DB.all.PID == '@pid')

    def flow_by_tid(self):
        uri_e = self.uri_tid
        uri_flows = self.DB.flow(uri_e['+'])
        return self.DB.execute(uri_flows)

    class ccf_coherency_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass
