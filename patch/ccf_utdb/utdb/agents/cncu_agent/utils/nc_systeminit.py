from val_utdb.val_utdb_systeminit import val_utdb_systeminit
from val_utdb_bint import bint


class NC_SI(val_utdb_systeminit):
    
    systeminit_ip_prefix = "ccf"

    def si_knobs_declaration(self):
        self.module_disable_mask = bint(self.get_si_val_by_name('MODULE_DISABLE_MASK'))
        self.cbo_disable_mask = bint(self.get_si_val_by_name('CBO_DISABLE_MASK'))
        #self.cluster_id = bint(self.get_si_val_by_name('CCF_CLUSTER_ID'))
        self.cluster_id = 0
        self.soc_mode = self.get_si_val_by_name("CCF_PP_SOC_MODE_EN") == 1
        self.num_of_cbo = self.get_si_val_by_name('NUM_OF_CBO')
        self.ccf_die = self.get_si_val_by_name('CCF_DIE')
        self.ccf_socket_id = bint(self.get_si_val_by_name('CCF_SOCKET_ID'))
        self.ccf_cbb_id = bint(self.get_si_val_by_name('CCF_CBB_ID'))
        #self.dev_en = bint(self.get_si_val_by_name('CCF_DEV_EN_MASK', topo="mem_map"))
        self.get_mem_knobs()
        #if not self.soc_mode:
        self.get_agent_knobs()

    def get_agent_knobs(self):
        self.funnyio_0x2_0x5_chk_en = True#self.get_si_val_by_name("NC_PP_FUNNYIO_0x2_0x5_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_0x3_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_0x3_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_0x4_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_0x4_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_0x6_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_0x6_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_0x8_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_0x8_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_lt_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_LT_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_legacy_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_LEGACY_CHK_EN", topo="nc_agt_sw") == 1
        self.funnyio_sub_decode_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_SUB_DECODE_CHK_EN", topo="nc_agt_sw") == 1
        self.semaphores_chk_en = self.get_si_val_by_name("NC_PP_SEMAPHORES_CHK_EN", topo="nc_agt_sw") == 1
        self.interrupts_chk_en = self.get_si_val_by_name("NC_PP_INTERRUPTS_CHK_EN", topo="nc_agt_sw") == 1
        self.cfg_chk_en = self.get_si_val_by_name("NC_PP_CFG_CHK_EN", topo="nc_agt_sw") == 1
        self.mmio_chk_en = self.get_si_val_by_name("NC_PP_MMIO_CHK_EN", topo="nc_agt_sw") == 1
        self.mmio_patching_chk_en = self.get_si_val_by_name("NC_PP_MMIO_PATCHING_CHK_EN", topo="nc_agt_sw") == 1
        self.vcrpla_patching_chk_en = self.get_si_val_by_name("NC_PP_FUNNYIO_0x4_VCRPLA_PATCHING_CHK_EN", topo="nc_agt_sw") == 1
        self.spcyc_chk_en = self.get_si_val_by_name("NC_PP_SPCYC_CHK_EN", topo="nc_agt_sw") == 1
        self.lock_chk_en = self.get_si_val_by_name("NC_PP_LOCK_CHK_EN", topo="nc_agt_sw") == 1
        self.events_chk_en = self.get_si_val_by_name("NC_PP_EVENTS_CHK_EN", topo="nc_agt_sw") == 1
        self.mcast_token_chk_en = self.get_si_val_by_name("NC_PP_MCAST_TOKEN_CCF_ALL_CHK_EN", topo="nc_agt_sw") == 1
 
    def get_mem_knobs(self):
        self.mmcfgbar_size = bint(self.get_si_val_by_name('CCF_MMCFGBAR_SIZE', topo="mem_map"))
        self.mmcfgbar_en = self.get_si_val_by_name('CCF_MMCFGBAR_EN', topo="mem_map") == 1
        self.mmcfgbar_value = self.get_si_val_by_name('CCF_MMCFGBAR_VALUE', topo="mem_map")
        self.mmio_h_base = self.get_si_val_by_name('CCF_MMIO_H_BASE', topo="mem_map")
        self.sad_always_hom_en = self.get_si_val_by_name("CCF_SAD_ALWAYS_HOM_EN", topo="mem_map") == 1
