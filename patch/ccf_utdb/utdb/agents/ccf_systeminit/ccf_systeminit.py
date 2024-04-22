#!/usr/bin/env python3.6.3
from val_utdb.val_utdb_systeminit import val_utdb_systeminit
from val_utdb_bint import bint


class ccf_systeminit(val_utdb_systeminit):
    
    systeminit_ip_prefix = 'ccf'

    def si_knobs_declaration(self):
        # Get systeminit values using one of systeminit API functions
        # Ex: self.ccf_IS_CTE = self.get_si_val_by_name('ccf_is_cte')
        #     ccf_is_cte is taken from systeminit.dut_cfg file
        #self.lfc_chk_en = self.get_si_val_by_name('CCF_LFC_CHK')
        self.ccf_die = self.get_si_val_by_name('CCF_DIE')
        #BDADON remove and make sure coherency checkers are not ties to this knob self.ccf_cluster_id = self.get_si_val_by_name('CCF_CLUSTER_ID')
        self.atom_mask = self.get_si_val_by_name('CCF_ATOM_MASK')
        self.num_of_cbo = self.get_si_val_by_name('NUM_OF_CBO')*4#BDADON
        self.cbo_disable_mask = self.get_si_val_by_name('CBO_DISABLE_MASK')
        self.module_disable_mask = self.get_si_val_by_name('MODULE_DISABLE_MASK')
        self.ccf_mktme_mask = self.get_si_val_by_name('CCF_MKTME_MASK')
        self.enable_cr_randomization = self.get_si_val_by_name('ENABLE_CR_RANDOMIZATION')
        self.num_of_opened_data_ways = self.get_si_val_by_name('LLC_NUM_OPENED_DATA_WAYS')
        #self.pciexbar_en = self.get_si_val_by_name('CCF_PCIEXBAR_EN', topo="mem_map")
        self.dbp_en = self.get_si_val_by_name('DBP_EN')
        #self.ccf_isa_hole_en = self.get_si_val_by_name('CCF_ISA_HOLE_EN', topo="mem_map")
        self.is_nem_test = self.get_si_val_by_name('IS_NEM_TEST')
        self.dfd_en = self.get_si_val_by_name('CCF_DFD_EN')

        self.cdtf_en = self.get_si_val_by_name('CCF_CDTF_EN')

        self.ccf_fusa_rtl_en = self.get_si_val_by_name('CCF_FUSA_RTL_EN')




        #PMONS
        self.ccf_cbo_pmon_event = self.get_si_val_by_name('PMON_CBO_EVENT_NAME')
        self.ccf_cbo_pmon_mask = self.get_si_val_by_name('PMON_CBO_EVENT_MASK')
        self.ccf_pmon_cbo_id = self.get_si_val_by_name('CLR_PMON_SLICE_ID')
        self.ccf_pmon_cbo_counter = self.get_si_val_by_name('CLR_PMON_COUNTER_ID')
        self.pmon_sbo_en = self.get_si_val_by_name('PMON_SBO_EN')
        self.ccf_santa_ncu_pmon_event = self.get_si_val_by_name('PMON_SANTA_NCU_EVENT_NAME')
        self.ccf_santa_ncu_pmon_mask = self.get_si_val_by_name('PMON_SANTA_NCU_EVENT_MASK')
        self.ccf_pmon_santa_id = self.get_si_val_by_name('SANTA_NCU_PMON_SLICE_ID')
        self.ccf_pmon_santa_counter = self.get_si_val_by_name('SANTA_NCU_PMON_COUNTER_ID')
        self.pmon_overflow = self.get_si_val_by_name('PMON_OVERFLOW')
        self.pmon_lpid_en = self.get_si_val_by_name('PMON_LPID_EN')
        self.pmon_lpid = self.get_si_val_by_name('PMON_LPID')
        self.pmon_moduleid = self.get_si_val_by_name('PMON_MODULE_ID')
        self.dpt_dis = self.get_si_val_by_name('DPT_DIS')

        #checker enable
        self.ccf_lfc_chk_en = self.get_si_val_by_name('CCF_PP_LFC_CHK_EN')
        self.ccf_flow_chk_en = self.get_si_val_by_name('CCF_PP_FLOW_CHK_EN')
        self.ccf_go_chk_en = self.get_si_val_by_name('CCF_PP_GO_CHK_EN')
        self.ccf_llc_chk_en = self.get_si_val_by_name('CCF_PP_LLC_CHK_EN')
        self.ccf_snoop_chk_en = self.get_si_val_by_name('CCF_PP_SNOOP_CHK_EN')
        self.mem_hash_chk_en = self.get_si_val_by_name('CCF_PP_MEM_HASH_CHK_EN')
        self.ccf_data_chk_en = self.get_si_val_by_name('CCF_PP_DATA_CHK_EN')
        self.ccf_dump_chk_en = self.get_si_val_by_name('CCF_PP_DUMP_CHK_EN')
        self.ccf_transition_chk_en = self.get_si_val_by_name('CCF_PP_CCF_TRANSITION_CHK_EN')
        self.ccf_only_single_conflict_chk_en = 1 #self.get_si_val_by_name('CCF_PP_ONLY_SINGLE_CONFLICT_CHK_EN')
        self.ccf_vulnerable_chk_en = 1 #self.get_si_val_by_name('CCF_PP_VULNERABLE_CHK_EN')
        self.ccf_reqfwdcnflt_chk_en = 1 #self.get_si_val_by_name('CCF_PP_REQFWDCNFLT_CHK_EN')
        self.ccf_sad_mca_chk_en = self.get_si_val_by_name('CCF_PP_MCA_SAD_CHK_EN')
        self.ccf_sad_chk_en = 1
        self.ccf_general_flow_chk_en = self.get_si_val_by_name('CCF_PP_GENERAL_FLOW_CHK_EN')
        self.ccf_clos_chk_en    = self.get_si_val_by_name('CCF_PP_CLOS_CHK_EN')
        #self.ccf_preload_data_correctable_errs = self.get_si_val_by_name('CCF_PRELOAD_DATA_CORRECTABLE_ERRS')
        #self.ccf_preload_tag_correctable_errs = self.get_si_val_by_name('CCF_PRELOAD_TAG_CORRECTABLE_ERRS')
        self.ccf_preload_data_correctable_errs = 0
        self.ccf_preload_tag_correctable_errs = 0
        self.ccf_window_chk_en = self.get_si_val_by_name('CCF_PP_CCF_WINDOW_CHK_EN')
        self.ccf_pp_flow_to_df_en = self.get_si_val_by_name('CCF_PP_FLOW_TO_DF_EN')
        self.ccf_pp_bw_counter_chk_en = self.get_si_val_by_name('CCF_PP_BW_COUNTER_CHK_EN')
        self.ccf_pmon_chk_en = self.get_si_val_by_name('CCF_PMON_CHK_EN')
        self.conflict_chk_en = self.get_si_val_by_name('CCF_PP_CONFLICT_CHK_EN')
        self.corrupted_llc_preload_en = self.get_si_val_by_name('CCF_PP_CORRUPTED_LLC_PRELOAD_EN')

        #SoC
        self.ccf_soc_mode = self.get_si_val_by_name('CCF_PP_SOC_MODE_EN')

        #for mem hash
        self.mem_hash_mask = self.get_si_val_by_name('CCF_HASH_BIT0_MASK')

        #coverage
        self.ccf_cov_en = self.get_si_val_by_name('CCF_COV')

        #CLKs for coverage
        if not self.ccf_soc_mode:
            self.ring_min_pll_ratio = self.get_si_val_by_name('RING_MIN_PLL_RATIO')
            self.ring_max_pll_ratio = self.get_si_val_by_name('RING_MAX_PLL_RATIO')
            self.ccf_ring_pll_ratio = self.get_si_val_by_name('CCF_RING_PLL_RATIO')


