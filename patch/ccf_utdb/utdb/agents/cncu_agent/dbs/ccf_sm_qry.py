from val_utdb_components import val_utdb_qry


class CCF_SM_QRY(val_utdb_qry):

    def __init__(self):
        self.all_sm_recs = None

    def queries(self):
        # define utdb queries here
        self.all_sm_recs = (self.DB.all.LOW_ADDRESS != '0X0')

    def get_sm_records(self):
        sm_flow = (self.DB.flow(self.all_sm_recs['+']))
        return self.DB.execute(sm_flow)

    class SM_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)
            self.low_addr = int(rec.LOW_ADDRESS, 16)
            self.high_addr = int(rec.HIGH_ADDRESS,16)
            self.mem_space = rec.MEM_NAME
            self.region = rec.REGION_NAME
            self.sub_region = rec.SUB_NAME
            self.size = rec.SIZE

        def get_sm_rec_str(self):
            sm_rec_str = "low_addr: {}, high_addr: {}, mem_space: {}, region: {}, sub_region: {}, size: {}".format(
                self.low_addr, self.high_addr, self.mem_space, self.region, self.sub_region, self.size)
            return sm_rec_str
