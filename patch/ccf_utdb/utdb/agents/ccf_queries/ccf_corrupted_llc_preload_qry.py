from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry

class ccf_corrupted_llc_preload_qry(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.only_tag_single = (self.DB.all.TAG_ER == 'SINGLE')

    def get_tag_ecc_errors(self):
        only_tag_single_e = self.only_tag_single
        address_tag_ecc_error = self.DB.flow(only_tag_single_e)
        return self.DB.execute(address_tag_ecc_error)

    class ccf_corrupted_llc_preload_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass
