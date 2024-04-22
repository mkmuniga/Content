#!/usr/bin/env python3.6.3
from val_utdb_bint import bint
from val_utdb_components import val_utdb_component

from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent

class ccf_registers(val_utdb_component):

    def __init__(self):
        self.ccf_ral_agent_ptr = ccf_ral_agent.get_pointer()
        self.cbo_phy_id_list = self.initialize_cbo_phy_id_list()
        self.muli_instance_cbo_reg_initial_value = self.initial_none_value_for_cbo_registers()

        #registers:
        self.ymm_mask = None
        self.mktme_mask = None
        self.dis_wb2mmio_fix = None
        self.convert_clwb_to_clflushopt = None
        self.allow_only_single_snoop_conflict = None
        self.pam_normal_dram_operation = None
        self.b0_threshold = None
        self.b1_threshold = None
        self.dbp_ms_cache_mask = None
        self.prefetch_elimination_en = None
        self.force_critical_chunk_zero = None
        self.ia_cos_ways = None
        self.clos_to_tc_mlc_pref_is_demand = None
        self.allowitom_to_mmio = None
        self.dpt_rwm = [None]*4
        self.force_selfsnoop_all = None
        self.force_selfsnoop_snoopfilter_only = None
        self.force_selfsnoop_drd = None
        self.force_selfsnoop_drd_prefetch = None
        self.force_selfsnoop_crd = None
        self.force_selfsnoop_crd_prefetch = None
        self.force_selfsnoop_rfo = None
        self.force_selfsnoop_rfo_prefetch = None
        self.drd_always_cachenear = None
        self.crd_always_cachenear = None
        self.rfo_always_cachenear = None
        self.sad_always_to_hom = None
        self.lt_memlockcpu = None
        self.isa_hole_en = None
        self.cv_err_legacy_mode = None

    def initialize_cbo_phy_id_list(self):
        cbo_phy_id_l = []
        for i in range(self.si.num_of_cbo):
            cbo_phy_id_l.append(CCF_UTILS.get_physical_id_by_logical_id(i))
        return cbo_phy_id_l

    def initial_none_value_for_cbo_registers(self):
        return [None for i in range(self.si.num_of_cbo)]

    def get_multi_instance_register_value_from_all_cbos(self, register_read_function):
        register_value_list = self.muli_instance_cbo_reg_initial_value.copy()
        for cbo_phy_id in self.cbo_phy_id_list:
            register_value_list[cbo_phy_id] = register_read_function(int(cbo_phy_id/4))#BDADON
        return register_value_list

    def get_multi_instance_array_register_value_from_all_cbos(self, register_read_function, reg_array_size):
        register_value_list = self.muli_instance_cbo_reg_initial_value.copy()
        for cbo_phy_id in self.cbo_phy_id_list:
            temp_list = list()
            for index in range(reg_array_size):
                temp_list.insert(index, register_read_function(int(cbo_phy_id/4), index))#BDADON
            register_value_list[cbo_phy_id] = temp_list.copy()
        return register_value_list


    #Registers read functions

    def get_eot_prefetch_elimination_en(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_"+ str(cbo_id_phys), "flow_cntrl", "enable_prefetch_elimination")

    def get_eot_force_critical_chunk_zero(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_"+ str(cbo_id_phys), "flow_cntrl", "force_critical_chunk_zero")

    def get_eot_enable_prefetch_promotion(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_"+ str(cbo_id_phys), "flow_cntrl", "enable_prefetch_promotion")

    def get_eot_mktme_mask(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all"+str(cbo_id_phys), "mktme_keyid_mask", "MASK")

    def get_eot_ymm_mask(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_"+ str(cbo_id_phys), "l3_protected_ways", "ymm_mask")

    def get_eot_allow_only_single_snoop_conflict(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "cbregs_spare", "allow_only_single_snoop_conflict")

    def get_eot_convert_clwb_to_clflushopt(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "cbregs_spare", "convert_clwb_to_clflushopt")

    def get_eot_dis_wb2mmio_fix(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "cbregs_spare", "dis_wb2mmio_fix")

    def get_eot_mmio_clflush_defeature(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "cbregs_spare", "mmio_clflush_defeature")

    def get_eot_clos_to_tc_mlc_pref_is_demand_val(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "cbregs_spare", "clos_to_tc_mlc_pref_is_demand")

    #def get_eot_pam_normal_dram_operation(self, cbo_id_phys):
    #    pam_normal_dram_operation = [None for j in range(0, 7)]
    #    for j in range(0, 7):
    #        pam_normal_dram_operation[j] = [None, None]
    #         if j != 0:
    #             pam_normal_dram_operation[j][0] = self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "pam" + str(j) + "_0_0_0_pci", "loenable")
    #         pam_normal_dram_operation[j][1] = self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "pam" + str(j) + "_0_0_0_pci", "hienable")
    #    return pam_normal_dram_operation

    def get_eot_b0_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "general_config2","ms_cache_bin0_th")

    def get_eot_b1_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys),"general_config2", "ms_cache_bin1_th")

    def get_eot_dis_clean_evict_occupancy_throttle(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys),"general_config2", "dis_clean_evict_occupancy_throttle")

    def get_eot_dbp_ms_cache_mask(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "dbp_arac_cntrl", "isobserverind")

    def get_eot_enable_force_noavaildataway_in_any_reject(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "general_config1", "enable_force_noavaildataway_in_any_reject")


    def get_eot_override_core_clos(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "general_config1", "overridecoreclos")

    def get_eot_ia_override_clos_val(self,cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "general_config2", "iaoverrideclosval")

    #get all changes time during simulation
    def get_eot_clostagways(self, cbo_id_phys, index):
        return bint(self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "ia_cos_ways[{}]".format(index), "clostagways"))

    def get_eot_closways(self, cbo_id_phys, index):
        return bint(self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "ia_cos_ways[{}]".format(index), "closways"))

    def get_eot_uncore_demand_req_memory_priority_0(self, cbo_id_phys, index):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "uncore_demand_req_memory_priority_0", "clos{}_demand_priority".format(index))

    def get_eot_uncore_prefetch_req_memory_priority_0(self, cbo_id_phys, index):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "uncore_prefetch_req_memory_priority_0", "clos{}_pref_priority".format(index))

    def get_eot_allowitom_to_mmio(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "CBO_COH_CONFIG_CLIENT", "AllowItoM_to_MMIO")

    def get_eot_ltctrlsts_private(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "ltctrlsts", "private")
    def get_eot_ltctrlsts_acm(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "ltctrlsts", "inacm")
    def get_eot_ltctrlsts_loc3guarddis(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "ltctrlsts", "loc3guarddis")
    def get_eot_ltctrlsts_memlockcpu(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "ltctrlsts", "memlockcpu")
    def get_eot_dpt_rwm(self):
        for i in range(0, 4):
            self.dpt_rwm[i] = self.ccf_ral_agent_ptr.read_reg_field_at_eot("santa_regs", "DPT_RWM", "RWM"+str(i))
    #def get_eot_isa_hole_en(self,cbo_id_phys):
    #    return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "lac_0_0_0_pci", "hen")

    
    def get_eot_tor_occupency_th(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "general_config2", "llc_prefetch_occupancy_threshold")

    def get_eot_sbo_disable_dpt_credit(self):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("sbo_misc_regs", "sbo_misc_ctl", "disable_dpt_credit")

    def get_eot_santa_wcil_throttling_enable(self):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("santa_regs", "Santa_WCiL_Throttle_Control", "WCil_throttling_enable")

    def get_eot_santa_periodic_wcil_throttling_enable(self):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("santa_regs", "Santa_WCiL_Throttle_Control", "Periodic_WCiL_throttling_enable")

    def get_eot_santa_periodic_wcil_threshold(self):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("santa_regs", "Santa_WCiL_Throttle_Control", "Periodic_WCiL_threshold")

    def get_eot_wcil_throttle_coherent_wcil_high_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttle_coherent_wcil_high_threshold")

    def get_eot_wcil_throttle_coherent_wcil_low_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttle_coherent_wcil_low_threshold")

    def get_eot_wcil_throttle_non_coherent_wcil_high_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttle_non_coherent_wcil_high_threshold")

    def get_eot_wcil_throttle_non_coherent_wcil_low_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttle_non_coherent_wcil_low_threshold")

    def get_eot_wcil_throttle_tor_entries_high_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttle_tor_entries_high_threshold")

    def get_eot_wcil_throttle_tor_entries_low_threshold(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttle_tor_entries_low_threshold")

    def get_eot_wcil_throttling_enable(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "wcil_throttling_enable")


    def get_eot_sad_always_to_hom(self, cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("cbregs_all" + str(cbo_id_phys), "cbregs_spare", "sadalwaystohom")

    def get_cv_err_legacy_mode(self,cbo_id_phys):
        return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_" + str(cbo_id_phys), "cbo_misc_cfg", "en_mca_on_cv_parity_error")
    ##get value at certain time:
    def get_ni_control(self, cbo_id_phys, reg_field="", time=None):
        cbo_id_phys = int(cbo_id_phys/4)#BDADON
        if time is None:
            return self.ccf_ral_agent_ptr.read_reg_field_at_eot("ingress_"+ str(cbo_id_phys), "ni_control", reg_field)
        else:
            return self.ccf_ral_agent_ptr.read_reg_field("ingress_"+ str(cbo_id_phys), "ni_control", reg_field, time)

    def get_force_selfsnoop_all_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_all", time=time)
    def get_force_selfsnoop_snoopfilter_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_snoopfilter_only", time=time)
    def get_force_selfsnoop_drd_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_drd", time=time)
    def get_force_selfsnoop_drd_prefetch_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_drd_prefetch", time=time)
    def get_force_selfsnoop_crd_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_crd", time=time)
    def get_force_selfsnoop_crd_prefetch_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_crd_prefetch", time=time)
    def get_force_selfsnoop_rfo_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_rfo", time=time)
    def get_force_selfsnoop_rfo_prefetch_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="force_selfsnoop_rfo_prefetch", time=time)
    def get_drd_always_cachenear_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="drd_always_cachenear", time=time)
    def get_crd_always_cachenear_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="crd_always_cachenear", time=time)
    def get_rfo_always_cachenear_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="rfo_always_cachenear", time=time)
    def get_disable_data_vulnerable_field(self, cbo_id_phys, time=None):
        return self.get_ni_control(cbo_id_phys=cbo_id_phys, reg_field="disable_data_vulnerable", time=time)
    
    def get_fast_ipi_at_specific_time(self, time):
        return self.ccf_ral_agent_ptr.read_reg_field("ncdecs", "NCRADECS_OVRD", "FastIpi", time)


    #populate registers value
    def get_registers_value(self):
        self.prefetch_elimination_en = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_prefetch_elimination_en).copy()
        self.force_critical_chunk_zero = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_force_critical_chunk_zero).copy()
        self.enable_prefetch_promotion = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_enable_prefetch_promotion).copy()
        self.ymm_mask = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_ymm_mask).copy()
        self.mktme_mask = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_mktme_mask).copy()
        self.dis_wb2mmio_fix = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_dis_wb2mmio_fix).copy()
        self.convert_clwb_to_clflushopt = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_convert_clwb_to_clflushopt).copy()
        self.allow_only_single_snoop_conflict = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_allow_only_single_snoop_conflict).copy()
        #self.pam_normal_dram_operation = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_pam_normal_dram_operation).copy()
        self.b0_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_b0_threshold).copy()
        self.b1_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_b1_threshold).copy()
        self.dbp_ms_cache_mask = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_dbp_ms_cache_mask).copy()
        self.ia_cos_ways__clostagways = self.get_multi_instance_array_register_value_from_all_cbos(self.get_eot_clostagways, 16).copy()
        self.ia_cos_ways__closways = self.get_multi_instance_array_register_value_from_all_cbos(self.get_eot_closways, 16).copy()
        self.uncore_demand_req_memory_priority_0 = self.get_multi_instance_array_register_value_from_all_cbos(self.get_eot_uncore_demand_req_memory_priority_0, 16).copy()
        self.uncore_prefetch_req_memory_priority_0 = self.get_multi_instance_array_register_value_from_all_cbos(self.get_eot_uncore_prefetch_req_memory_priority_0, 16).copy()
        self.override_core_clos = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_override_core_clos).copy()
        self.iaoverrideclosval = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_ia_override_clos_val).copy()
        self.enable_force_noavaildataway_in_any_reject = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_enable_force_noavaildataway_in_any_reject).copy()
        self.mmio_clflush_defeature = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_mmio_clflush_defeature).copy()
        self.clos_to_tc_mlc_pref_is_demand = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_clos_to_tc_mlc_pref_is_demand_val).copy()
        self.get_eot_dpt_rwm()
        self.dis_clean_evict_occupancy_throttle = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_dis_clean_evict_occupancy_throttle).copy()
        self.allowitom_to_mmio = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_allowitom_to_mmio).copy()
        self.ltctrlsts_private = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_ltctrlsts_private).copy()
        self.ltctrlsts_acm = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_ltctrlsts_acm).copy()
        self.ltctrlsts_DisLocGuard = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_ltctrlsts_loc3guarddis).copy()
        self.lt_memlockcpu = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_ltctrlsts_memlockcpu).copy()
        self.force_selfsnoop_all = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_all_field).copy()
        self.force_selfsnoop_snoopfilter_only = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_snoopfilter_field).copy()
        self.force_selfsnoop_drd = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_drd_field).copy()
        self.force_selfsnoop_drd_prefetch = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_drd_prefetch_field).copy()
        self.force_selfsnoop_crd = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_crd_field).copy()
        self.force_selfsnoop_crd_prefetch = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_crd_prefetch_field).copy()
        self.force_selfsnoop_rfo = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_rfo_field).copy()
        self.force_selfsnoop_rfo_prefetch = self.get_multi_instance_register_value_from_all_cbos(self.get_force_selfsnoop_rfo_prefetch_field).copy()
        self.drd_always_cachenear = self.get_multi_instance_register_value_from_all_cbos(self.get_drd_always_cachenear_field).copy()
        self.crd_always_cachenear = self.get_multi_instance_register_value_from_all_cbos(self.get_crd_always_cachenear_field).copy()
        self.rfo_always_cachenear = self.get_multi_instance_register_value_from_all_cbos(self.get_rfo_always_cachenear_field).copy()
        self.disable_data_vulnerable = self.get_multi_instance_register_value_from_all_cbos(self.get_disable_data_vulnerable_field).copy()
        self.tor_occupency_th = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_tor_occupency_th).copy()
        self.sad_always_to_hom = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_sad_always_to_hom).copy()
        #self.isa_hole_en = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_isa_hole_en).copy()
        self.cv_err_legacy_mode = self.get_multi_instance_register_value_from_all_cbos(self.get_cv_err_legacy_mode).copy()
        self.wcil_throttle_coherent_wcil_high_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttle_coherent_wcil_high_threshold).copy()
        self.wcil_throttle_coherent_wcil_low_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttle_coherent_wcil_low_threshold).copy()
        self.wcil_throttle_non_coherent_wcil_high_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttle_non_coherent_wcil_high_threshold).copy()
        self.wcil_throttle_non_coherent_wcil_low_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttle_non_coherent_wcil_low_threshold).copy()
        self.wcil_throttle_tor_entries_high_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttle_tor_entries_high_threshold).copy()
        self.wcil_throttle_tor_entries_low_threshold = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttle_tor_entries_low_threshold).copy()
        self.wcil_throttling_enable = self.get_multi_instance_register_value_from_all_cbos(self.get_eot_wcil_throttling_enable).copy()
        self.santa_wcil_throttling_enable = self.get_eot_santa_wcil_throttling_enable()
        self.santa_periodic_wcil_throttling_enable = self.get_eot_santa_periodic_wcil_throttling_enable()
        self.santa_periodic_wcil_threshold = self.get_eot_santa_periodic_wcil_threshold()
        self.sbo_disable_dpt_credit = self.get_eot_sbo_disable_dpt_credit()
