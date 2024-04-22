#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_gcfi_qry(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.is_upi_nc = self.DB.all.PROTOCOL_ID.contains('UPI.NC')
        self.is_upi_c =self.DB.all.PROTOCOL_ID.contains('UPI.C')
        self.is_santa_0 = self.DB.all.SANTA_PORT_ID == 0
        self.is_santa_1 = self.DB.all.SANTA_PORT_ID == 1
        self.all = self.DB.all.SANTA_PORT_ID >= 0


    def get_all_upi_c_santa0_records(self):
        is_upi_c_santa_0 = (self.is_upi_c & self.is_santa_0)
        return self.DB.execute(self.DB.flow(is_upi_c_santa_0))
    def get_all_upi_c_santa1_records(self):
        is_upi_c_santa_1 = (self.is_upi_c & self.is_santa_1)
        return self.DB.execute(self.DB.flow(is_upi_c_santa_1))
    def get_all_upi_nc_records(self):
        return self.DB.execute(self.DB.flow(self.is_upi_nc))
    def get_all_upi_c_records(self):
        return self.DB.execute(self.DB.flow(self.is_upi_c))
    def get_all_records(self):
        gcfi_rec = (self.DB.flow(self.all['+']))
        return self.DB.execute(gcfi_rec)

    class ccf_gcfi_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass