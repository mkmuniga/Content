#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_qry.py 
#
# Owner:              asaffeld
# Creation Date:      11.2020
#
# ###############################################
#
# Description:
#   This file contain all ccf_coherency queries and flow definitions
#################################################################################################
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_mlc_db(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.address = (self.DB.all.ADDRESS == '@address')

    def address_sorting(self):
        entry = self.address
        address_entry = self.DB.flow(entry)
        return self.DB.execute(self.DB.flow(address_entry['+']))

    class ccf_coherency_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass





