from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_santa_db(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.santa0 = (self.DB.all.UNIT == 'CCF_VC_SANTA0')
        self.santa1 = (self.DB.all.UNIT == 'CCF_VC_SANTA1')



    def get_santa_records(self):
        entry = self.santa0
        santa_entry = self.DB.flow(entry)
        return self.DB.execute(self.DB.flow(santa_entry))

    class ccf_coherency_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass

