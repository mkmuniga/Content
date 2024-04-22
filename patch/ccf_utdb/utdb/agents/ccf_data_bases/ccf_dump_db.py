#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_dump_db(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.address = (self.DB.all.ADDRESS == '@address')

    def address_sorting(self):
        entry = self.address
        address_entry = self.DB.flow(entry)
        return self.DB.execute(self.DB.flow(address_entry['+']))

    class ccf_dump_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass
