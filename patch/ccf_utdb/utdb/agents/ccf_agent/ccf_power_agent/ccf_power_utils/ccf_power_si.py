from val_utdb.val_utdb_systeminit import val_utdb_systeminit

class POWER_SI(val_utdb_systeminit):
    systeminit_ip_prefix = "ccf"

    def si_knobs_declaration(self):
        self.ccf_soc_mode = self.get_si_val_by_name("CCF_PP_SOC_MODE_EN") == 1
        self.num_of_cbo = self.get_si_val_by_name('NUM_OF_CBO')
