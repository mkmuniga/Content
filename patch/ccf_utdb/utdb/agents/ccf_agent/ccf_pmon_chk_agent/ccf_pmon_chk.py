from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_pmon_chk_agent.ccf_pmon_chk_cov import CCF_PMON_CG
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import ccf_flow_cov
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.coh_global import COH_GLOBAL
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from agents.ccf_data_bases.ccf_power_sb_db import CCF_POWER_SB_DB
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_bint import bint
from agents.cncu_agent.dbs.cncu_flow_qry import CNCU_FLOW_QRY
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.common.cncu_defines import SB
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_queries.ccf_common_qry import CCF_COMMON_QRY, ccf_common_custom_qry
from agents.ccf_common_base.ccf_common_base import ccf_idi_record_info, ccf_cfi_record_info
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils
from collections.__init__ import OrderedDict

class ccf_pmon_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.checker_name = "ccf_pmon_chk"
        self.ccf_flow_cov_ptr = ccf_flow_cov.get_pointer()
        self.llc_db_agent = ccf_llc_db_agent.get_pointer()
        self.ccf_coherency_qry_i = ccf_coherency_qry.get_pointer()
        self.ccf_common_custom_qry = ccf_common_custom_qry.get_pointer()
        self.check_per_pmon = {"MLC_EVICTION_0": clean_evict_hit.get_pointer(),
                               "MLC_EVICTION_1": clean_evict_drop.get_pointer(),
                               "MLC_EVICTION_2": mlc_eviction_dirty_evict_to_memory.get_pointer(),
                               "DCS_EVICTION_0": eviction_by_flush.get_pointer(),
                               "MLC_WB_DBP_0": WbMtoIDead.get_pointer(),
                               "MLC_WB_DBP_1": WbMtoIAlive.get_pointer(),
                               "MLC_WB_DBP_2": WbMtoIBypass2MUFASA.get_pointer(),
                               "MLC_WB_DBP_3": WbMtoIBypass2Mem.get_pointer(),
                               "MLC_WB_DBP_4": WbEtoIDead.get_pointer(),
                               "MLC_WB_DBP_5": WbEtoIAlive.get_pointer(),
                               "MLC_WB_DBP_6": WbEtoIDrop.get_pointer(),
                               "MLC_WB_DBP_7": WbEtoIBypass2MUFASA.get_pointer(),
                               "LLC_EVICTION_DBP_0": Modified_live_eviction.get_pointer(),
                               "LLC_EVICTION_DBP_1": Modified_dead_eviction.get_pointer(),
                               "LLC_EVICTION_DBP_2": Clean_silent_drop.get_pointer(),
                               "LLC_EVICTION_DBP_3": clean_evicted_to_MUFASA.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA0_0": santa0_NoSharedRdCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA0_1": santa0_NoSharedDataCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA0_2": santa0_NoDRSCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA0_3": santa0_NoNCCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA1_0": santa1_NoSharedRdCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA1_1": santa1_NoSharedDataCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA1_2": santa1_NoDRSCredit.get_pointer(),
                               #"CBO_No_CREDITS_FOR_SANTA1_3": santa1_NoNCCredit.get_pointer(),
                               "CBO_CACHE_LOOKUP_FREE": lookup_all.get_pointer(),
                               "LLCPrefThrottling_0": LLCPrefThrottling.get_pointer(),
                               "CBO_PMON_MONITOR_ARRAY_ALLOCATION_0": OverFlow_alloc.get_pointer(),
                               "CBO_PMON_MONITOR_ARRAY_ALLOCATION_1": Multiple_entry_alloc_to_same_entry.get_pointer(),
                               "CBO_XSNP_RESPONSE_FREE": XSNP_RESPONSE_all.get_pointer(),
                               "CBO_C2P_SNP_REQ_0_4" :SNP_NUM_1_ALL.get_pointer(),
                               "CBO_C2P_SNP_REQ_1_4" :SNP_NUM_2_ALL.get_pointer(),
                               "CBO_C2P_SNP_REQ_2_4" :SNP_NUM_4_ALL.get_pointer(),
                               "CBO_C2P_SNP_REQ_3_4" :SNP_NUM_8_ALL.get_pointer(),
                               "CBO_C2P_SNP_REQ_0_5" :SNP_NUM_1_EXTERNAL.get_pointer(),
                               "CBO_C2P_SNP_REQ_1_5" :SNP_NUM_2_EXTERNAL.get_pointer(),
                               "CBO_C2P_SNP_REQ_2_5" :SNP_NUM_4_EXTERNAL.get_pointer(),
                               "CBO_C2P_SNP_REQ_3_5" :SNP_NUM_8_EXTERNAL.get_pointer(),
                               "CBO_C2P_SNP_REQ_0_6" :SNP_NUM_1_XCORE.get_pointer(),
                               "CBO_C2P_SNP_REQ_1_6" :SNP_NUM_2_XCORE.get_pointer(),
                               "CBO_C2P_SNP_REQ_2_6" :SNP_NUM_4_XCORE.get_pointer(),
                               "CBO_C2P_SNP_REQ_3_6" :SNP_NUM_8_XCORE.get_pointer(),
                               "CBO_C2P_SNP_REQ_0_7" :SNP_NUM_1_EVICTION.get_pointer(),
                               "CBO_C2P_SNP_REQ_1_7" :SNP_NUM_2_EVICTION.get_pointer(),
                               "CBO_C2P_SNP_REQ_2_7" :SNP_NUM_4_EVICTION.get_pointer(),
                               "CBO_C2P_SNP_REQ_3_7" :SNP_NUM_8_EVICTION.get_pointer(),
                               "CBO_IRQ_SANTA_CREDITS_REJECTS_0" :IRQ_NoSharedRdCredit.get_pointer(),
                               "CBO_IRQ_SANTA_CREDITS_REJECTS_1" :IRQ_NoSharedDataCredit.get_pointer(),
                               "CBO_IRQ_SANTA_CREDITS_REJECTS_2" :IRQ_NoAnyDataCredit.get_pointer(),
                               "CBO_IRQ_SANTA_CREDITS_REJECTS_3" :IRQ_NoNCCredit.get_pointer(),
                               "CBO_IRQ_REJECTS_0": IRQ_Any.get_pointer(),
                               "CBO_IRQ_REJECTS_1": IRQ_Egress_full.get_pointer(),
                               "CBO_IRQ_REJECTS_2": IRQ_Address_conflict.get_pointer(),
                               "CBO_IRQ_REJECTS_4": IRQ_Prefetch_promotion.get_pointer(),
                               "CBO_IRQ_REJECTS_5": IRQ_No_Victim_TOR.get_pointer(),
                               "CBO_IRQ_REJECTS_6": IRQ_No_NonHOM_TOR.get_pointer(),
                               "CBO_IRQ_REJECTS_7": IRQ_All_data_ways_are_reserved.get_pointer(),
                               "CBO_IPQ_REJECTS_0": IPQ_Any.get_pointer(),
                               "CBO_IPQ_REJECTS_1": IPQ_Egress_full.get_pointer(),
                               "CBO_IPQ_REJECTS_2": IPQ_Address_conflict.get_pointer(),
                               "CBO_IPQ_REJECTS_5": IPQ_NoSharedDataCredit.get_pointer(),
                               "CBO_IPQ_REJECTS_6": IPQ_NoAnyDataCredit.get_pointer(),
                               "CBO_ISMQ_REJECTS_0": ISMQ_Any.get_pointer(),
                               "CBO_ISMQ_REJECTS_1": ISMQ_Egress_full.get_pointer(),
                               "CBO_ISMQ_REJECTS_4": ISMQ_NoSharedRdCredit.get_pointer(),
                               "CBO_ISMQ_REJECTS_5": ISMQ_NoSharedDataCredit.get_pointer(),
                               "CBO_ISMQ_REJECTS_6": ISMQ_NoAnyDataCredit.get_pointer(),
                               "CBO_ISMQ_REJECTS_7": ISMQ_NoNCCredit.get_pointer(),
                               "CBO_LINES_VICTIMIZED_0" : LINES_VICTIMIZED_M.get_pointer(),
                               "CBO_LINES_VICTIMIZED_1" : LINES_VICTIMIZED_E.get_pointer(),
                               "CBO_LINES_VICTIMIZED_2" : LINES_VICTIMIZED_S.get_pointer(),
                               "CBO_LINES_VICTIMIZED_3" : LINES_VICTIMIZED_I.get_pointer(),

                               "CBO_LINES_VICTIMIZED_4" : LINES_VICTIMIZED_NO_DATA_ALLOC.get_pointer(),
                               "CBO_LINES_VICTIMIZED_5" : LINES_VICTIMIZED_NO_DATA_ALLOC_AND_DATA_VICTIM.get_pointer(),
                               "CBO_TOR_ALLOCATION_0" : ALLOCATION_DRD.get_pointer(),
                               "CBO_TOR_ALLOCATION_1" : ALLOCATION_IMPHREQ.get_pointer(),
                               "CBO_TOR_ALLOCATION_2" : ALLOCATION_EVICTIONS.get_pointer(),
                               "CBO_TOR_ALLOCATION_3" : ALLOCATION_ALL.get_pointer(),
                               "CBO_TOR_ALLOCATION_4" : ALLOCATION_WB.get_pointer(),
                               "CBO_TOR_ALLOCATION_5" : ALLOCATION_WCIL.get_pointer(),
                               "CBO_TOR_ALLOCATION_6" : ALLOCATION_snoop_reserved_slot.get_pointer(),
                               "CBO_TOR_ALLOCATION_7" : ALLOCATION_victim_reserved_slot.get_pointer(),
                               # was removed from excel"CBO_MISC_0" :RspIwasFSE.get_pointer(),
                               "CBO_MISC_1":WC_aliasing.get_pointer(),
                               "CBO_CACHE_HITS_0_4" : IA_Hits_SF.get_pointer(),
                               "CBO_CACHE_HITS_0_5" : IA_Hits_DATA.get_pointer(),
                               "CBO_CACHE_HITS_3_4" : IO_Hits_SF.get_pointer(),
                               "CBO_CACHE_HITS_3_5" : IO_Hits_DATA.get_pointer(),

                               "MUFASA_DBP_Rsp_0" : Bin0_Rd_hit.get_pointer(),
                               "MUFASA_DBP_Rsp_1" : Bin1_Rd_hit.get_pointer(),
         
                               "SANTA_TXQ_ALLOCATION_0": TXQ_ALLOCATION_RDQ.get_pointer(),
                               "SANTA_TXQ_ALLOCATION_1": TXQ_ALLOCATION_WRQ_DRS.get_pointer(),
                               "SANTA_TXQ_ALLOCATION_2": TXQ_ALLOCATION_NCQ.get_pointer(),
                               "SANTA_TXQ_ALLOCATION_3": TXQ_ALLOCATION_RSPQ.get_pointer(),
                               "SANTA_TXQ_ALLOCATION_4": TXQ_ALLOCATION_RDIFA.get_pointer(),
                               "SANTA_TXQ_ALLOCATION_5": TXQ_ALLOCATION_WRQ_WB.get_pointer(),
                               "SANTA_TXQ_ALLOCATION_6":TXQ_ALLOCATION_RDIFA_without_invalidation.get_pointer(),
                               "SANTA_RXQ_ALLOCATION_0":RXQ_ALLOCATION_DataQ.get_pointer(),
                               "SANTA_RXQ_ALLOCATION_1":RXQ_ALLOCATION_LockQ.get_pointer(),
                               "SANTA_RXQ_ALLOCATION_2":RXQ_ALLOCATION_RspQ.get_pointer(),
                               "SANTA_RXQ_ALLOCATION_3":RXQ_ALLOCATION_ReqQ.get_pointer(),
                               "SANTA_REQ_3": number_of_dirty_evictions.get_pointer(),
                               "SANTA_REQ_4": number_of_clear_evictions.get_pointer(),
                               "SANTA_CFI_TX_Transactions_0": SANTA_CFI_TX_Transactions_all.get_pointer(),
                               "SANTA_CFI_TX_Transactions_1": SANTA_CFI_TX_Transactions_reads.get_pointer(),
                               "SANTA_CFI_TX_Transactions_2": SANTA_CFI_TX_Transactions_writes.get_pointer(),
                               "SANTA_CFI_TX_Transactions_3": SANTA_CFI_TX_Transactions_ReqFwdCnflt.get_pointer(),
                               "SANTA_CFI_TX_Transactions_4": SANTA_CFI_TX_Transactions_wbeftoi.get_pointer(),
           
                               "SANTA_SNP_RESPONSE_0" : SANTA_SNP_RESPONSE_RspI.get_pointer(),
                               "SANTA_SNP_RESPONSE_1" : SANTA_SNP_RESPONSE_RspS.get_pointer(),
                               "SANTA_SNP_RESPONSE_3" : SANTA_SNP_RESPONSE_RspIWb.get_pointer(),
                               "SANTA_SNP_RESPONSE_4" : SANTA_SNP_RESPONSE_RspSWb.get_pointer(),
                               "SANTA_SNP_RESPONSE_5" : SANTA_SNP_RESPONSE_RspE.get_pointer(),
                               "SANTA_SNP_RESPONSE_6" : SANTA_SNP_RESPONSE_RspCurData.get_pointer(),
                               "NCU_MSG_RECEIVED_0" : VLW.get_pointer(),
                               "NCU_MSG_RECEIVED_1" :IntPhy_IntLog.get_pointer(),
                               "NCU_MSG_RECEIVED_2" :IntPhy_IntLog_FastIpi.get_pointer(),
                               "NCU_MSG_RECEIVED_3" :DoorBell.get_pointer()

                               #removed from excel "RING_SCALE_EVENTS_0" :ring_scale_events.get_pointer()
                                }
        self.check_per_occ_pmon = {"CBO_TOR_OCCUPANCY_5": TOR_OCC_WCIL.get_pointer(),
                               "CBO_TOR_OCCUPANCY_0" : TOR_OCC_DRD.get_pointer(),
                               "CBO_TOR_OCCUPANCY_1" : TOR_OCC_IMPHREQ.get_pointer(),
                               "CBO_TOR_OCCUPANCY_2" : TOR_OCC_EVICTIONS.get_pointer(),
                               "CBO_TOR_OCCUPANCY_3" : TOR_OCC_ALL.get_pointer(),
                               "CBO_TOR_OCCUPANCY_4" : TOR_OCC_DFV.get_pointer(),
                               "CBO_TOR_OCCUPANCY_0_6" : TOR_OCC_DRD_IA.get_pointer(),
                               "CBO_TOR_OCCUPANCY_1_6" : TOR_OCC_IMPHREQ_IA.get_pointer(),
                               "CBO_TOR_OCCUPANCY_2_6" : TOR_OCC_EVICTIONS_IA.get_pointer(),
                               "CBO_TOR_OCCUPANCY_3_6" : TOR_OCC_ALL_IA.get_pointer(),
                               "CBO_TOR_OCCUPANCY_4_6" : TOR_OCC_DFV_IA.get_pointer(),
                               "CBO_TOR_OCCUPANCY_5_6" : TOR_OCC_WCIL_IA.get_pointer(),
                               "CBO_INGRESS_ARBITER_0" : INGRESS_ARBITER_BLOCK_IRQ_HA0.get_pointer(),
                               "CBO_INGRESS_ARBITER_1" : INGRESS_ARBITER_BLOCK_IPQ_HA0.get_pointer(),
                               "CBO_INGRESS_ARBITER_2" : INGRESS_ARBITER_BLOCK_IRQ_IPQ_HA0.get_pointer(),
                               "CBO_INGRESS_ARBITER_3" : INGRESS_ARBITER_BID_HA0.get_pointer(),
                               "CBO_INGRESS_ARBITER_4" : INGRESS_ARBITER_BLOCK_IRQ_HA1.get_pointer(),
                               "CBO_INGRESS_ARBITER_5" : INGRESS_ARBITER_BLOCK_IPQ_HA1.get_pointer(),
                               "CBO_INGRESS_ARBITER_6" : INGRESS_ARBITER_BLOCK_IRQ_IPQ_HA1.get_pointer(),
                               "CBO_INGRESS_ARBITER_7" : INGRESS_ARBITER_BID_HA1.get_pointer(),
                               "CBO_AD_RING_IN_USE_0"  : AD_RING_IN_USE_UP_EVEN.get_pointer(),
                               "CBO_AD_RING_IN_USE_1"  : AD_RING_IN_USE_UP_ODD.get_pointer(),
                               "CBO_AD_RING_IN_USE_2"  : AD_RING_IN_USE_DN_EVEN.get_pointer(),
                               "CBO_AD_RING_IN_USE_3"  : AD_RING_IN_USE_DN_ODD.get_pointer(),
                               "CBO_BL_RING_IN_USE_0"  : BL_RING_IN_USE_UP_EVEN.get_pointer(),
                               "CBO_BL_RING_IN_USE_1"  : BL_RING_IN_USE_UP_ODD.get_pointer(),
                               "CBO_BL_RING_IN_USE_2"  : BL_RING_IN_USE_DN_EVEN.get_pointer(),
                               "CBO_BL_RING_IN_USE_3"  : BL_RING_IN_USE_DN_ODD.get_pointer(),
                               "CBO_AK_RING_IN_USE_0"  : AK_RING_IN_USE_UP_EVEN.get_pointer(),
                               "CBO_AK_RING_IN_USE_1"  : AK_RING_IN_USE_UP_ODD.get_pointer(),
                               "CBO_AK_RING_IN_USE_2"  : AK_RING_IN_USE_DN_EVEN.get_pointer(),
                               "CBO_AK_RING_IN_USE_3"  : AK_RING_IN_USE_DN_ODD.get_pointer(),
                               "CBO_IV_RING_IN_USE_0"  : IV_RING_IN_USE_UP_EVEN.get_pointer(),
                               "CBO_IV_RING_IN_USE_1"  : IV_RING_IN_USE_UP_ODD.get_pointer(),
                               "CBO_IV_RING_IN_USE_2"  : IV_RING_IN_USE_DN_EVEN.get_pointer(),
                               "CBO_IV_RING_IN_USE_3"  : IV_RING_IN_USE_DN_ODD.get_pointer(),
                               "SANTA_TXQ_OCCUPANCY_0" : TXQ_RDQ_OCCUPANCY.get_pointer(),
                               "SANTA_TXQ_OCCUPANCY_1" : TXQ_WRQ_OCCUPANCY.get_pointer(),
                               "SANTA_TXQ_OCCUPANCY_2" : TXQ_NCQ_OCCUPANCY.get_pointer(),
                               "SANTA_TXQ_OCCUPANCY_3" : TXQ_RSP_OCCUPANCY.get_pointer(),
                               "SANTA_TXQ_OCCUPANCY_4" : TXQ_RDIFA_OCCUPANCY.get_pointer()
                                }


    def reset(self):
        pass


    def check_pmon(self,clk_period):
        self.check_clr_pmon()
        self.check_santa_ncu_pmon()
        self.collect_coverage()
        cov_pmons = CCF_PMON_CG.get_pointer().pmons
        for pmon in self.check_per_pmon.keys():
            if pmon not in cov_pmons:
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="val assertion: CCF_PMON_CG doesn't have {} pmon event".format(pmon))
        for pmon in self.check_per_occ_pmon.keys():
            if pmon not in cov_pmons:
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="val assertion: CCF_PMON_CG doesn't have {} pmon event".format(pmon))

    def get_cbo_time_of_reset_pmon_count(self):
        reset_times = {0:0}
        block = "cbregs_all" + str(self.si.ccf_pmon_cbo_id)
        reg = "ltctrlsts"
        field  = "ltpmoncntclr"
        times = ccf_ral_agent.get_pointer().get_field_change_times(block, reg, field)
        for time in times:
            if time >= COH_GLOBAL.global_vars["START_OF_TEST"] and time <= COH_GLOBAL.global_vars["END_OF_TEST"]:
                if ccf_ral_agent.get_pointer().read_reg_field(block, reg, field, time) == 1:
                    reset_times[time] = 0
        return reset_times

    def get_santa_time_of_reset_pmon_count(self):
        reset_times = {0:0}
        block = "ncevents"
        reg = "LTCtrlSts"
        field = "LTPmonCntClr"
        times = ccf_ral_agent.get_pointer().get_field_change_times(block, reg, field)
        for time in times:
            if time >= COH_GLOBAL.global_vars["START_OF_TEST"] and time <= COH_GLOBAL.global_vars["END_OF_TEST"]:
                if ccf_ral_agent.get_pointer().read_reg_field(block, reg, field, time) == 1:
                    reset_times[time] = 0
        return reset_times

    def get_cbo_time_of_stop_pmon_count(self):
        if (self.si.pmon_sbo_en == 1):
            block = "sbo_misc_regs"
            reg = "ltctrlsts_sbo"
            field  = "ltpmonctrclr"
        else:
            block = "cbregs_all" + str(self.si.ccf_pmon_cbo_id)
            reg = "ltctrlsts"
            field  = "ltpmonctrclr"
        times = ccf_ral_agent.get_pointer().get_field_change_times(block, reg, field)
        for time in times:
            if time >= COH_GLOBAL.global_vars["START_OF_TEST"] and time <= COH_GLOBAL.global_vars["END_OF_TEST"]:
                if ccf_ral_agent.get_pointer().read_reg_field(block, reg, field, time) == 1:
                    return time
        return COH_GLOBAL.global_vars["END_OF_TEST"]

    def get_santa_time_of_stop_pmon_count(self):
        block = "ncevents"
        reg = "LTCtrlSts"
        field = "LTPmonCtrClr"
        times = ccf_ral_agent.get_pointer().get_field_change_times(block, reg, field)
        for time in times:
            if time >= COH_GLOBAL.global_vars["START_OF_TEST"] and time <= COH_GLOBAL.global_vars["END_OF_TEST"]:
                if ccf_ral_agent.get_pointer().read_reg_field(block, reg, field, time) == 1:
                    return time
        return COH_GLOBAL.global_vars["END_OF_TEST"]

    def get_time_of_setting_pmon_event(self, IP = "CBO"):
        if (IP == "CBO"):
            self.block = "egress_sbo"
            if self.si.pmon_sbo_en == 0:
                self.block = "egress_" + str(self.si.ccf_pmon_cbo_id)
            self.reg = "cbopmonctrctrl"+ str(self.si.ccf_pmon_cbo_counter)
        elif (IP == "SANTA"):
            self.block = "santa" + str(self.si.ccf_pmon_santa_id)+ "_regs"
            self.reg = "pmon_ctrl_"+ str(self.si.ccf_pmon_santa_counter)
        times = ccf_ral_agent.get_pointer().get_register_change_times(self.block, self.reg)
        register_set = dict()
        register_off = []
        for time in times:
            if time >= COH_GLOBAL.global_vars["START_OF_TEST"] and time <= COH_GLOBAL.global_vars["END_OF_TEST"]:
                if ccf_ral_agent.get_pointer().read_reg_field(self.block, self.reg, "evslct", time) > 0:
                    register_set[time] = COH_GLOBAL.global_vars["END_OF_TEST"]
                elif ccf_ral_agent.get_pointer().read_reg_field(self.block, self.reg, "evslct", time) == 0:
                    register_off.append(time)
        if len(register_set) == 0:
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="val assertion: {} PMON event register was not set during test that start in {}".format(IP, COH_GLOBAL.global_vars["START_OF_TEST"]))
        for zero_time in register_off:
            for key in register_set.keys():
                if (key < zero_time) and (register_set[key] > zero_time):
                    register_set[key] = zero_time
        return register_set

 #   def is_occ_module_lpid_match(self, tid, event_tested):    
 #       if (self.si.pmon_lpid_en == 0) or ((self.check_per_occ_pmon[event_tested].get_module_id(tid)==self.si.pmon_moduleid) and (self.check_per_occ_pmon[event_tested].get_lpid(tid) == self.si.pmon_lpid)):
 #           VAL_UTDB_MSG(time=0, msg=self.check_per_occ_pmon[event_tested].get_module_id(tid))
 #           return 1
 #       else: 
 #           return 0

 #   def get_tor_occupancy_time_rec(self, event_tested):
 #       start_time = []
 #       end_time = []
 #       allocate_cntr=0
 #       allocate_tid=dict()
 #       cpipe_name="CPIPE_" + str(self.si.ccf_pmon_cbo_id)
 #       VAL_UTDB_MSG(time=0, msg=cpipe_name)
 #       for t in self.ccf_coherency_qry_i.DB.execute(self.ccf_coherency_qry_i.DB.flow(self.ccf_coherency_qry_i.only_cbo_trk)):
 #           for txn in t.EVENTS:
 #               if ((txn.OPCODE=='DRd')or(txn.OPCODE=='DRd_NS')or(txn.OPCODE=='DRd_Pref')or(txn.OPCODE=='DRd_Opt_Pref'))and(txn.UNIT==cpipe_name):
 #                   if (txn.MISC =='TOR allocated')and(self.is_occ_module_lpid_match(txn.TID, event_tested)):
 #                       if (allocate_cntr==0):
 #                           VAL_UTDB_MSG(time=0, msg=txn)
 #                           start_time.append(txn.TIME)
 #                           VAL_UTDB_MSG(time=0, msg="START TIME")
 #                       allocate_cntr=allocate_cntr+1       
 #                       allocate_tid[txn.TID]=1
 #                       VAL_UTDB_MSG(time=0, msg=allocate_cntr)
 #               if ((txn.MISC=='TOR deallocated')and (txn.TID in allocate_tid))and(txn.UNIT==cpipe_name):
 #                   VAL_UTDB_MSG(time=0, msg="Deallocating")
 #                   VAL_UTDB_MSG(time=0, msg=txn)
 #                   allocate_cntr=allocate_cntr-1       
 #                   if (allocate_cntr==0):
 #                       VAL_UTDB_MSG(time=0, msg=txn)
 #                       end_time.append(txn.TIME)
 #                       VAL_UTDB_MSG(time=0, msg="END TIME")
##  Calculting the time till when the tor is occupied by drd. Both queue size should be same  
 #       #return self.tmp
 #       time1=0
 #       time2=0
 #       for i in start_time:
 #           time1=time1+i
 #           VAL_UTDB_MSG(time=0, msg=time1)
 #       for j in end_time:
 #           time2=time2+j
 #           VAL_UTDB_MSG(time=0, msg=time2)
 #       occ_time=time2-time1
 #       VAL_UTDB_MSG(time=0, msg=occ_time)
 #       return occ_time

 #   def get_occupancy_cycles(self, clk_timeperiod, event_tested):    
 #       total_time=self.check_per_occ_pmon[event_tested].get_tor_occupancy_time_rec(self.ccf_coherency_qry_i) 
 #       VAL_UTDB_MSG(time=0, msg=clk_timeperiod)
 #       VAL_UTDB_MSG(time=0, msg=total_time)
 #       expected_pmon_cnt=total_time // clk_timeperiod
 #       return expected_pmon_cnt

    def check_clr_occupancy_pmon(self, event, mask, stop_count_time, reset_times, actual_value, is_cbo, valid_times):
        #actual_value = ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cbopmonct"+ str(self.si.ccf_pmon_cbo_counter),"pmonctrdata")
        event_tested = event+mask.split("MASK")[-1]
        expected_value = self.check_per_occ_pmon[event_tested].num_of_pmon_occ_cycles(self.ccf_flows, self.ccf_coherency_qry_i, valid_times, reset_times)
        reset_pmon_happened = len(reset_times) > 1 or (stop_count_time < COH_GLOBAL.global_vars["END_OF_TEST"])
        diff = abs(expected_value - actual_value)
        diff_is_ok_to_avoid_cycle_accurate_cases_due_to_pmon_resets = reset_pmon_happened and (diff <= 2)
        if(event=="CBO_TOR_OCCUPANCY")and (expected_value <=10):
            final_exp_diff=expected_value*0.2 ###allow 20% for CBO_TOR_OCC as it difficult to predict exact cycles 
        elif(event=="CBO_TOR_OCCUPANCY")and (expected_value <=100):
            final_exp_diff=expected_value*0.1  ###for less number ratio become higer
        else:
            final_exp_diff=expected_value*0.05 #allow 5% of mistakes for all other events and if CBO_TOR_OCC is more than 100
        if ((diff > (final_exp_diff)) and not diff_is_ok_to_avoid_cycle_accurate_cases_due_to_pmon_resets): ##check final_exp_diff only here ..and print expected_value only to get the real number 
            if(is_cbo):
                err_msg = "PMON event {}: MASK {} in cbo {} counter {} {} is wrong.\n" \
                          "actual is {} while expected is {}" \
                          .format(event, mask,str(self.si.ccf_pmon_cbo_id), str(self.si.ccf_pmon_cbo_counter),
                          "module_id " + str(self.si.pmon_moduleid) + " lpid " + str(self.si.pmon_lpid) if self.si.pmon_lpid_en == 1 else "",
                          actual_value, expected_value)
            else:
                err_msg = "PMON event {}: with MASK {} in santa {} counter {} is wrong.\n" \
                          "actual is {} while expected is {}" \
                          .format(event, mask,str(self.si.ccf_pmon_santa_id), str(self.si.ccf_pmon_santa_counter),actual_value, expected_value)
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
        else:
            if expected_value > 0:
                self.ccf_flow_cov_ptr.collect_pmon_hit(event_tested)
            if(is_cbo):
                msg = "CLR PMON CHECK PASS" + " event_tested: " + event + " mask: " + mask + " event tested " + event_tested + " actual value " + str(actual_value) + " expected value " + str(expected_value)
            else:    
                msg = "SANTA PMON CHECK PASS" + " event_tested: " + event + " mask: " + mask + " event tested " + event_tested + " actual value " + str(actual_value) + " expected value " + str(expected_value)
            VAL_UTDB_MSG(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=msg)
            print(msg)

    def check_cbo_pmon_event_is_clear_at_eot(self):
        clr_block_name = "egress_sbo" if (self.si.pmon_sbo_en == 1) else "egress_" + str(self.si.ccf_pmon_cbo_id)
        clr_event = ccf_ral_agent.get_pointer().read_reg_field_at_eot(clr_block_name, "cbopmonctrctrl" + str(self.si.ccf_pmon_cbo_counter),"evslct")
        if clr_event != 0:
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="PMON clr event was not clear")

    def check_santa_pmon_event_is_clear_at_eot(self):
        ncu_block_name = "santa" + str(self.si.ccf_pmon_santa_id) + "_regs"
        ncu_event =ccf_ral_agent.get_pointer().read_reg_field_at_eot(ncu_block_name, "pmon_ctrl_"+ str(self.si.ccf_pmon_santa_counter),"evslct")
        if ncu_event != 0:
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="PMON ncu event was not clear")


    def check_clr_pmon(self):
        event = self.si.ccf_cbo_pmon_event
        mask = self.si.ccf_cbo_pmon_mask
        valid_times = self.get_time_of_setting_pmon_event("CBO")
        stop_count_time = self.get_cbo_time_of_stop_pmon_count()
        reset_times = self.get_cbo_time_of_reset_pmon_count()
        block_name = "egress_sbo" if (self.si.pmon_sbo_en == 1) else "egress_" + str(self.si.ccf_pmon_cbo_id)
        actual_value = ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cbopmonct"+ str(self.si.ccf_pmon_cbo_counter),"pmonctrdata")
        event_tested = event+mask.split("MASK")[-1]
        if stop_count_time < COH_GLOBAL.global_vars["END_OF_TEST"]:
            self.check_cbo_pmon_event_is_clear_at_eot()
        if event_tested in self.check_per_pmon:
            self.check_per_pmon[event_tested].llc_db_agent = self.llc_db_agent
            expected_value = self.check_per_pmon[event_tested].count_pmon_hits(self.ccf_flows, self.si.ccf_pmon_cbo_id, True, valid_times, stop_count_time, reset_times)
            reset_pmon_happened = len(reset_times) > 1 or (stop_count_time < COH_GLOBAL.global_vars["END_OF_TEST"])
            diff = abs(expected_value - actual_value)
            diff_is_ok_to_avoid_cycle_accurate_cases_due_to_pmon_resets = reset_pmon_happened and (diff <= 2)
            if ((diff > (expected_value*0.05)) and not diff_is_ok_to_avoid_cycle_accurate_cases_due_to_pmon_resets): #allow 5% of mistakes
                err_msg = "PMON event {}: MASK {} in cbo {} counter {} {} is wrong.\n" \
                          "actual is {} while expected is {}" \
                          .format(event, mask,str(self.si.ccf_pmon_cbo_id), str(self.si.ccf_pmon_cbo_counter),
                                  "module_id " + str(self.si.pmon_moduleid) + " lpid " + str(self.si.pmon_lpid) if self.si.pmon_lpid_en == 1 else "",
                                  actual_value, expected_value)
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
            else:
                if expected_value > 0:
                    self.ccf_flow_cov_ptr.collect_pmon_hit(event_tested)
                msg = "CLR PMON CHECK PASS" + " event_tested: " + event + " mask: " + mask + " event tested " + event_tested + " actual value " + str(actual_value) + " expected value " + str(expected_value)
                VAL_UTDB_MSG(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=msg)
                print(msg)
        elif event_tested in self.check_per_occ_pmon:
             self.check_clr_occupancy_pmon(event, mask, stop_count_time, reset_times, actual_value, 1, valid_times)
        else:
            if actual_value > 0:
                self.ccf_flow_cov_ptr.collect_pmon_counter_for_not_checked_pmons(event_tested)
            print("event_tested: " + event + " mask: " + mask + " event tested :" + event_tested + " is not part of PMON CHK yet")

    def check_santa_ncu_pmon(self):
        event = self.si.ccf_santa_ncu_pmon_event
        mask = self.si.ccf_santa_ncu_pmon_mask
        valid_times = self.get_time_of_setting_pmon_event("SANTA")
        stop_count_time = self.get_santa_time_of_stop_pmon_count()
        reset_times = self.get_santa_time_of_reset_pmon_count()
        if stop_count_time < COH_GLOBAL.global_vars["END_OF_TEST"]:
            self.check_santa_pmon_event_is_clear_at_eot()
        actual_value = ccf_ral_agent.get_pointer().read_reg_field_at_eot("santa" + str(self.si.ccf_pmon_santa_id)+ "_regs", "pmon_ctr_"+ str(self.si.ccf_pmon_santa_counter),"pmonctrdata")
        event_tested = event+mask.split("MASK")[-1]
        if event_tested in self.check_per_pmon:
            expected_value = self.check_per_pmon[event_tested].count_pmon_hits(self.ccf_flows, self.si.ccf_pmon_santa_id, False, valid_times,stop_count_time, reset_times)
            diff = abs(expected_value - actual_value)
            if (diff > (expected_value*0.1)): #allow 10% of mistakes
                err_msg = "PMON event {}: with MASK {} in santa {} counter {} is wrong.\n" \
                          "actual is {} while expected is {}" \
                          .format(event, mask,str(self.si.ccf_pmon_santa_id), str(self.si.ccf_pmon_santa_counter),actual_value, expected_value)
                VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg=err_msg)
            else:
                if expected_value > 0:
                    self.ccf_flow_cov_ptr.collect_pmon_hit(event_tested)
                print("SANTA NCU PMON CHECK PASS" + " event_tested: " + event + " mask: " + mask + " event tested " + event_tested + " actual value " + str(actual_value) + " expected value " + str(expected_value))
        elif event_tested in self.check_per_occ_pmon:
             self.check_clr_occupancy_pmon(event, mask, stop_count_time, reset_times, actual_value, 0, valid_times)
        else:
            if actual_value > 0:
                self.ccf_flow_cov_ptr.collect_pmon_counter_for_not_checked_pmons(event_tested)
            print("event_tested: " + event + " mask: " + mask + " event tested :" + event_tested + " is not part of PMON CHK yet")




class pmon_base_chk(ccf_coherency_base_chk):
    def __init__(self):
        self.count = 0
        self.cbo_santa_id = 0
        self.is_per_flow = 1
        self.freeze_count = 0
        self.ccf_pmsb_db = CCF_POWER_SB_DB.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.llc_db_agent = ccf_llc_db_agent.get_pointer()
        self.nc_racu_sb_transactions = []
        self.sb_db = CCF_NC_SB_DB.get_pointer()
        self.ccf_common_cus_qry=ccf_common_custom_qry.get_pointer()
        self.ccf_cpipe_window_utils = ccf_cpipe_window_utils.get_pointer()
        self.ccf_common_qry=CCF_COMMON_QRY.get_pointer()
        self.opcode_to_bin = {"CLFlush": bin(24),
                               "WbOtoE": bin(85),
                               "DRd": bin(2),
                               "ItoM": bin(72),
                               "LLCInv": bin(40),
                               "LlcPrefCode": bin(89),
                               "LLCWBInv":	bin(41),
                               "Lock":	bin(127),
                               "PortIn":	bin(124),
                               "SpecItoM":	bin(74)
                             }


    def is_relevant_lpid(self, flow :ccf_flow):
        return True if (self.si.pmon_lpid_en == 0) or ((self.is_relevant_moduleid(flow) and (flow.lpid == self.si.pmon_lpid)) or self.is_relevant_victim_lpid(flow)) else False

    def is_relevant_victim_lpid(self, flow: ccf_flow):
        return True if (self.name in ["ALLOCATION_ALL", "ALLOCATION_EVICTIONS"]) and (flow.is_victim() and (self.get_lpid(flow.uri["TID"]) == self.si.pmon_lpid) and (
                    self.get_module_id(flow.uri["TID"]) == self.si.pmon_moduleid)) else False


    def is_relevant_moduleid(self, flow :ccf_flow):
        return True if (self.si.pmon_lpid_en == 0) or (flow.requestor_logic_id == self.si.pmon_moduleid) else False


    def get_module_id(self, tid):
        if "COR_EMU" in tid:
            return int(tid[8])
        else:
            return -1

    def get_response_table_row(self,msg):
        if "ResponseTableRow" in msg:
            return msg.split(": ")[1]

    def get_lpid(self, tid):
        if "COR_EMU" in tid:
            return int(tid[10])
        else:
            return -1

    def get_nc_racu_sb_transactions(self):
        ccf_nc_flow_qry = CNCU_FLOW_QRY.get_pointer()
        for nc_flow in ccf_nc_flow_qry.get_nc_flows():
            for trans in nc_flow:
                if (type(trans) is SB_TRANSACTION):
                    self.nc_racu_sb_transactions.append(trans.uri)

    def check_freeze_on_overflow(self, check_time):
        self.should_freeze_at_eot = (ccf_ral_agent.get_pointer().read_reg_field("ncevents", "NcuPMONGlCtrl",
                                                                                    "FrzCountr", check_time) == 1) and \
                                 (ccf_ral_agent.get_pointer().read_reg_field("ncevents","NcuEvOveride",
                                                                                    "freeze_on_local_pmon_overflow",check_time ) == 1)
        self.pmon_counter_en_eot = (ccf_ral_agent.get_pointer().read_reg_field("ncevents","NcuPMONGlCtrl",
                                                                                         "PMONGEn", check_time) == 1)
        if(self.should_freeze_at_eot and self.pmon_counter_en_eot):
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="Freeze on overflow is enable but pmongen is not deasserting till EOT ")

    def count_pmon_hits(self, flows, cbo_santa_id, is_cbo, valid_times, stop_count_time, reset_times):
        if self.si.pmon_overflow == 1:
            self.count = CCF_COH_DEFINES.MAX_PMON_COUNTER
        else:
            self.count = 0
        self.cbo_santa_id = cbo_santa_id
        self.get_nc_racu_sb_transactions()
        if (self.is_per_flow == 1):
            for t in flows:
                if flows[t].first_accept_time is None:
                    flows[t].first_accept_time = flows[t].initial_time_stamp
            flows=OrderedDict(sorted(flows.items(), key=lambda item: item[1].first_accept_time))
            for flow in flows:
                if (flows[flow].first_accept_time is not None) or (flows[flow].initial_time_stamp is not None):
                   # if flows[flow].first_accept_time is None:
                   #      flows[flow].first_accept_time = flows[flow].initial_time_stamp
                    for time in reset_times.keys():
                        if (time != 0) and flows[flow].first_accept_time > time and reset_times[time] == 0:
                            reset_times[time] = 1
                            self.count = 0
                            pmon_msg = "URI {} reset {} {} pmon counter".format(flows[flow].uri["TID"], "CBO" if is_cbo else "SANTA", str(cbo_santa_id))
                            VAL_UTDB_MSG(time=flows[flow].first_accept_time, msg=pmon_msg)
                    if flows[flow].first_accept_time < stop_count_time:
                        self.is_valid_time = False
                        for key in valid_times.keys():
                            if (flows[flow].first_accept_time > key) and (flows[flow].first_accept_time < valid_times[key]):
                                self.is_valid_time = True
                        pmon_global_en = (ccf_ral_agent.get_pointer().read_reg_field("ncevents", "NcuPMONGlCtrl","PMONGEn",time=flows[flow].initial_time_stamp) == 1)
                        if pmon_global_en and self.is_valid_time:
                            if (is_cbo and flows[flow].cbo_id_phys == cbo_santa_id and (self.is_relevant_lpid(flows[flow]))) or (not is_cbo and ((flows[flow].santa_id is not None) or (self.name == "TXQ_ALLOCATION_NCQ"))):
                                num_of_pmon_hits = self.num_of_pmon_hits(flows[flow])
                                if num_of_pmon_hits > 0:
                                    if self.count == CCF_COH_DEFINES.MAX_PMON_COUNTER:
                                        self.check_overflow_triggered(flows[flow].flow_progress[-1].get_time(), is_cbo)
                                        self.check_freeze_on_overflow(flows[flow].flow_progress[-1].get_time() + 100000)
                                        self.count = self.count - 1 #the first pmon hit will increase counter to 0. so i reeduce the counterso it won't cont it
                                        

                                    self.count = (self.count+num_of_pmon_hits) % CCF_COH_DEFINES.MAX_PMON_COUNTER
                                    pmon_msg = "URI {} add {} to {} {} pmon counter".format(flows[flow].uri["TID"], str(num_of_pmon_hits) , "CBO" if is_cbo else "SANTA", str(cbo_santa_id))
                                    VAL_UTDB_MSG(time=flows[flow].first_accept_time, msg=pmon_msg)
        else:
            self.count = self.num_of_pmon_hits_in_test()
        return self.count

    def check_overflow_triggered(self, time, is_cbo):
        if (is_cbo):
            self.block = "egress_sbo"
            if self.si.pmon_sbo_en == 0:
                self.block = "egress_" + str(self.si.ccf_pmon_cbo_id)
            self.reg = "cbopmonctrstatus"
        else:
            self.block = "santa" + str(self.si.ccf_pmon_santa_id)+ "_regs"
            self.reg = "pmon_ctr_status"

        counter_id = self.si.ccf_pmon_cbo_counter if is_cbo else self.si.ccf_pmon_santa_counter
        overflow_reg = ccf_ral_agent.get_pointer().read_reg_field(self.block, self.reg, "counter"+str(counter_id)+"ovf", time+2000)
        VAL_UTDB_MSG(time=time, msg="overflow should be triggered from " + ("CBO" if is_cbo else "SANTA") + " at " + str(time))
        print("kmoses1: overflow_was trigger from " + ("CBO" if is_cbo else "SANTA") + " at " + str(time))
        if overflow_reg != 1:
            pmon_msg = "pmon overflow: register was not written for {}".format("CBO" if is_cbo else "SANTA")
            VAL_UTDB_ERROR(time=time, msg=pmon_msg)

        en_pmi_on_overflow = ccf_ral_agent.get_pointer().read_reg_field("ncevents", "NcuPMONGlCtrl", "PMIOvfEnUBP", time) == 1
        if (self.sb_pmi_msg() == 0):
            pmon_msg = "pmon overflow: pmi msg was not triggered from {}".format("CBO" if is_cbo else "SANTA")
            VAL_UTDB_ERROR(time=time, msg=pmon_msg)
            

    def sb_pmi_msg(self):
        actual_sb_msg_count = 0
        msgs = self.sb_db.get_trans_at_time(SB.OPCODES.mclk_event, COH_GLOBAL.global_vars["START_OF_TEST"],COH_GLOBAL.global_vars["END_OF_TEST"])
        for msg in msgs:
            is_to_sncu = (msg.dest_pid == SB.EPS.sncu)
            is_pmi_event = (bint(msg.data[3])[0] == 1) # bit[24] = 1
            is_from_ncu = (msg.src_pid == SB.EPS.ncevents)
            if is_from_ncu and is_to_sncu and is_pmi_event:
                actual_sb_msg_count += 1
        return actual_sb_msg_count
        

    def num_of_pmon_hits(self, flow: ccf_flow):
        return 0
    def num_of_pmon_hits_in_test(self):
        return 0

    def get_num_of_rejects(self, flow: ccf_flow, reject_reason):
        rej_count = 0
        for reason in flow.rejected_reasons:
            if reason == reject_reason:
                rej_count = rej_count + 1
        return rej_count

    def get_num_of_ismq_rejects(self, flow: ccf_flow, reject_reason):
        rej_count = 0
        reject_time = 0
        for reason in flow.rejected_reasons:
            if reject_time != reason.time: #we don't want to count every reject in the same cycle
                if (reject_reason in reason.reject_reason) and (reason.is_ismq or flow.is_victim()):
                    rej_count = rej_count + 1
                    reject_time = reason.time
        return rej_count

    def get_num_of_irq_rejects(self, flow: ccf_flow, reject_reason, exclude_reason = "ABCD"):
        rej_count = 0
        reject_time = 0
        if flow.is_idi_flow_origin() or flow.is_flusher_origin():
            for reason in flow.rejected_reasons:
                if reject_time != reason.time: #we don't want to count every reject in the same cycle
                    if (reject_reason in reason.reject_reason) and not (exclude_reason in reason.reject_reason) and not reason.is_ismq:
                        rej_count = rej_count + 1
                        reject_time = reason.time
        return rej_count


    def get_num_of_ipq_rejects(self, flow: ccf_flow, reject_reason):
        rej_count = 0
        reject_time = 0
        if flow.is_flow_origin_uxi_snp():
            for reason in flow.rejected_reasons:
                if reject_time != reason.time: #we don't want to count every reject in the same cycle
                    if (reject_reason in reason.reject_reason) and not reason.is_ismq:
                        rej_count = rej_count + 1
                        reject_time = reason.time
        return rej_count

    def get_num_of_snp_rsp(self, flow: ccf_flow, rsp_opcode):
        rsp_count = 0
        for rsp in flow.snoop_responses:
            if rsp.snoop_rsp_opcode == rsp_opcode:
                rsp_count = rsp_count + 1
        return rsp_count

    def is_bin0_hit(self, flow: ccf_flow):
        if (flow.cbo_got_ufi_uxi_cmpo() or flow.cbo_got_upi_fwdcnflto()) and not flow.is_flow_promoted():
            dbp_params = flow.get_dbp_params()
            bin_dbp_params = bint(int(dbp_params, 16))
            psaudo_llc_hit = bin_dbp_params[0]
            bin_value = bin_dbp_params[2]
            if flow.is_ms_chche_observer() and (psaudo_llc_hit == 1):
                if bin_value == 0:
                    return True
        return False

    def is_bin1_hit(self, flow: ccf_flow):
        if (flow.cbo_got_ufi_uxi_cmpo() or flow.cbo_got_upi_fwdcnflto()) and not flow.is_flow_promoted():
            dbp_params = flow.get_dbp_params()
            bin_dbp_params = bint(int(dbp_params, 16))
            psaudo_llc_hit = bin_dbp_params[0]
            bin_value = bin_dbp_params[2]
            if flow.is_ms_chche_observer() and (psaudo_llc_hit == 1):
                if bin_value == 1:
                    return True
        return False

    def is_occ_module_lpid_match(self, tid):    
        if (self.si.pmon_lpid_en == 0) or ((self.get_module_id(tid)==self.si.pmon_moduleid) and (self.get_lpid(tid) == self.si.pmon_lpid)):
         #   VAL_UTDB_MSG(time=0, msg=self.get_module_id(tid))
            return 1
        else: 
            return 0

    def is_hom_tor_half(self, flows, tid, cr_ha_id, opcodes):
        for flow in flows:
            if((flows[flow].uri["TID"]==tid) and (flows[flow].cbo_id_phys==self.si.ccf_pmon_cbo_id)):
                if(self.is_valid_flow(flows[flow], opcodes))and (flows[flow].cbo_tor_qid is not None):
                    if(((cr_ha_id==1) or (cr_ha_id==0))and (int(flows[flow].cbo_tor_qid) < (int(CCF_COH_DEFINES.num_of_tor_entries)/2))):
                        return 1
                    elif(((cr_ha_id==2) or (cr_ha_id==0))and (int(flows[flow].cbo_tor_qid)>(int(CCF_COH_DEFINES.num_of_tor_entries)/2))):
                        return 1
                    else:
                        return 0

    def should_freeze_cntr_on_overflow(self, txn_time, is_cbo, counter): ##call this function when counter is sure to get increment 
        freeze_done = (ccf_ral_agent.get_pointer().read_reg_field("ncevents",
                                                                       "NcuPMONGlCtrl",
                                                                       "FrzCountr",
                                                                       time=txn_time) == 1) and \
                           (ccf_ral_agent.get_pointer().read_reg_field("ncevents",
                                                                      "NcuEvOveride",
                                                                      "freeze_on_local_pmon_overflow",
                                                                      time=txn_time) == 1) and \
                           (not (ccf_ral_agent.get_pointer().read_reg_field("ncevents",
                                                                         "NcuPMONGlCtrl",
                                                                         "PMONGEn",
                                                                         time=txn_time) == 1))
        if (counter == CCF_COH_DEFINES.MAX_PMON_COUNTER):
            self.check_freeze_on_overflow(txn_time + 100000)
            self.check_overflow_triggered(txn_time, is_cbo)

        return freeze_done

    def get_start_time_for_IMPHREQ_from_cbo(self, addr_flows, tid, cr_ha_id, opcodes, cpipe):
        time=0
        for addr in self.ccf_cpipe_window_utils.ccf_addr_flows.keys():
            for entry in self.ccf_cpipe_window_utils.ccf_addr_flows[addr]:
                if (entry.AllowSnoop==1)and(entry.unit==cpipe)and (entry.uri_tid==tid):
                    VAL_UTDB_MSG(time=0, msg=entry.time)
                    VAL_UTDB_MSG(time=0, msg=entry.uri_tid)
                    time=entry.time
                    break

        return time

###is_valid_flow check for cutsom opcodes and what can be covered by ccf_flow only. custom opcodes are different from IDI/tracker txn opcodes. 
    def is_valid_flow(self, flow, opcodes):
        if("EVICTIONS" in opcodes):
            if flow.is_victim():
                return 1
            else:
                return 0
        elif("EVICTIONS_IA" in opcodes):
            for tk in flow.flow_progress: ## this is required bcz in case of victim one txn can have 2 ccf_flows. orig. one is orignated by idi and and second by CBO  
                if type(tk) is ccf_idi_record_info:
                    self.flow_origin_is_core = tk.is_core_unit()
            if flow.is_victim()and(self.flow_origin_is_core):
                return 1
            else:
                return 0
        elif("IMPHREQ" in opcodes):
            if (flow.is_conflict_flow() or (flow.cbo_got_ufi_uxi_cmpo() and not flow.is_flow_promoted())):
                return 1
            else:
                return 0
        elif("IMPHREQ_IA" in opcodes):
            if (flow.is_conflict_flow() or (flow.cbo_got_ufi_uxi_cmpo() and not flow.is_flow_promoted()))and (flow.is_idi_flow_origin()) :
                return 1
            else:
                return 0
        elif(("WCIL_IA" in opcodes)or("ALL_IA" in opcodes)or ("DFV_IA" in opcodes)):
            if (flow.is_idi_flow_origin()):
                return 1
            else:
                return 0
        elif("DRd" in opcodes):
            if flow.flow_is_hom():
                return 1
            else:
                return 0
        elif("DRD_IA" in opcodes):
            if (flow.flow_is_hom())and (flow.is_idi_flow_origin()):
                return 1
            else:
                return 0
        else:
            return 1 ## this function is to check condition for only when opcodes match(mainly custom opcodes). Don't check if no opcode match and return 1.  

    def is_cpipe_valid_optimized(self, time, tid, ccf_coherency_qry_i):
    ##CPIPE may have req in pipe with no valid or single cycle valid due to optimization. check cpipe.vs ReqMayFinishWo*
        go_track_rsp={"C2P_AK_FastGO_EXTCMP","C2P_AK_FAST_GO","C2P_AK_FAST_GO_PULL","C2P_AK_EXTCMP","C2P_AK_GO","C2P_AK_GO_PULL_DROP"}
        cpipe_name="CPIPE_" + str(self.si.ccf_pmon_cbo_id)
        cycles_to_add=0
        for t in ccf_coherency_qry_i.DB.execute(ccf_coherency_qry_i.DB.flow(ccf_coherency_qry_i.only_cbo_trk)):
            for txn in t.EVENTS:
                if(txn.TID==tid and txn.UNIT==cpipe_name and txn.TIME==time and (txn.MSG in go_track_rsp)):
                    VAL_UTDB_MSG(time=0, msg=txn.MSG)
                    cycles_to_add=1
        return cycles_to_add

    def get_occupancy_cycles(self, flows, ccf_coherency_qry_i, opcodes, is_custom_opcode, valid_times, reset_times):    
        total_cycles=self.get_tor_occupancy_time_rec(flows, ccf_coherency_qry_i, opcodes, is_custom_opcode, valid_times, reset_times) 
        expected_pmon_cnt=total_cycles % CCF_COH_DEFINES.MAX_PMON_COUNTER
        return expected_pmon_cnt

    def is_dfv_match(self, flows, txn, opcodes):
        cpipe_name="CPIPE_" + str(self.si.ccf_pmon_cbo_id)
        block_name = "ingress_" + str(self.si.ccf_pmon_cbo_id)
        dfv_rsp_table_en=ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","table_row_en")
        dfv_rsp_table=ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","table_row")
        dfv_idi_opcode_en=ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","idi_opcode_en")
        dfv_idi_opcode=ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","idi_opcode")
        dfv_llc_state_en=ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","llc_state_en")
        dfv_llc_state=ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","llc_state")
        txn_rsp_table_val=self.get_response_table_row(txn.MSG)
        opcode_bin=bin(dfv_idi_opcode)
        opcode_bin=opcode_bin[4:]
        if txn.OPCODE in self.opcode_to_bin:
            txn_opcode_bin=self.opcode_to_bin[txn.OPCODE]
            txn_opcode_bin=txn_opcode_bin[2:]
            VAL_UTDB_MSG(time=0, msg=txn_opcode_bin)
            VAL_UTDB_MSG(time=0, msg=opcode_bin)
        else:
            txn_opcode_bin=bin(0)
        if ("LLC_I" in txn.MISC) or (txn.OPCODE=="RspI"): ## opcode (prd,crd_uc,uccrdf) will not cache the line and change the state to I.
            cache_state=0
        elif "LLC_E" in txn.MISC:
            cache_state=2
        elif "LLC_S" in txn.MISC:
            cache_state=1
        elif "LLC_M" in txn.MISC:
            cache_state=3
        else:
            cache_state=55
        
        if txn_rsp_table_val is not None:
            rsp_tbl_val=int(txn_rsp_table_val)
        else:
            rsp_tbl_val=0
     #   VAL_UTDB_MSG(time=0, msg=cache_state)
      #  VAL_UTDB_MSG(time=0, msg=dfv_llc_state)
        if (dfv_rsp_table_en==0)and(dfv_idi_opcode_en==0)and(dfv_llc_state_en==0):
            VAL_UTDB_ERROR(time=COH_GLOBAL.global_vars["END_OF_TEST"], msg="Mask DFV is selected but non of DFV event is programmed")
        if (dfv_rsp_table_en==1)and(dfv_idi_opcode_en==0)and(dfv_llc_state_en==0):
            return 1 if (dfv_rsp_table==rsp_tbl_val) else 0
        if (dfv_rsp_table_en==0)and(dfv_idi_opcode_en==1)and(dfv_llc_state_en==0):
            return 1 if (int(txn_opcode_bin,2)==int(opcode_bin,2)) else 0
        if (dfv_rsp_table_en==0)and(dfv_idi_opcode_en==0)and(dfv_llc_state_en==1):
            return 1 if (cache_state==dfv_llc_state) else 0
        if (dfv_rsp_table_en==1)and(dfv_idi_opcode_en==0)and(dfv_llc_state_en==1):
            return 1 if ((cache_state==dfv_llc_state)and (dfv_rsp_table==rsp_tbl_val)) else 0
        if (dfv_rsp_table_en==1)and(dfv_idi_opcode_en==1)and(dfv_llc_state_en==0):
            return 1 if ((dfv_rsp_table==rsp_tbl_val)and(int(txn_opcode_bin,2)==int(opcode_bin,2))) else 0
        if (dfv_rsp_table_en==0)and(dfv_idi_opcode_en==1)and(dfv_llc_state_en==1):
            return 1 if ((dfv_rsp_table==rsp_tbl_val)and(int(txn_opcode_bin,2)==int(opcode_bin,2))) else 0
        if (dfv_rsp_table_en==1)and(dfv_idi_opcode_en==1)and(dfv_llc_state_en==1):
            return 1 if ((cache_state==dfv_llc_state)and(dfv_rsp_table==rsp_tbl_val)and(int(txn_opcode_bin,2)==int(opcode_bin,2))) else 0
        else:
            return 0


    def get_tor_occupancy_time_rec(self, flows, ccf_coherency_qry_i, opcodes, is_custom_opcode, valid_times, reset_times):
        start_time = dict()
        end_time = dict()
        clkperiod_at_alloc = dict()
        clkperiod_at_dealloc = dict()
        allocate_cntr=0
        is_valid_time=0
        allocate_opc_tid=dict()
        one_more_reset_after_events=0
        cpipe_name="CPIPE_" + str(self.si.ccf_pmon_cbo_id)
        VAL_UTDB_MSG(time=0, msg=cpipe_name)
        block_name = "ingress_" + str(self.si.ccf_pmon_cbo_id)
        dfv_cr_half_id = ccf_ral_agent.get_pointer().read_reg_field_at_eot(block_name, "cpipe_rsp_dfv","halfforoccupancy")
        for t in ccf_coherency_qry_i.DB.execute(ccf_coherency_qry_i.DB.flow(ccf_coherency_qry_i.only_cbo_trk)):
            for txn in t.EVENTS:
                is_valid_time = self.is_event_in_valid_times(txn.TIME, valid_times)
                if (((txn.OPCODE in opcodes)or(is_custom_opcode))and(txn.UNIT==cpipe_name)and is_valid_time):
                    if ("DFV" in opcodes) or ("DFV_IA" in opcodes):
                        if (self.is_dfv_match(flows, txn, opcodes))and(self.is_occ_module_lpid_match(txn.TID)and (self.is_hom_tor_half(flows, txn.TID, dfv_cr_half_id, opcodes))):
                            VAL_UTDB_MSG(time=0, msg=txn)
                            start_time[txn.TID]=txn.TIME
                            clkperiod_at_alloc[txn.TID]=self.get_uclk_time_period(txn.TIME)
                            allocate_cntr=allocate_cntr+1       
                            allocate_opc_tid[txn.TID]=txn.OPCODE
                            VAL_UTDB_MSG(time=0, msg="allocating")
                    else:
                        if (txn.MISC =='TOR allocated')and(self.is_occ_module_lpid_match(txn.TID)and (self.is_hom_tor_half(flows, txn.TID, dfv_cr_half_id, opcodes))):
        ##below if condition is for check the rejects. Mostly rejects will get retry and same tid entry will get overiwrite with latest one. But in case of DRD rejects due to LLCpref. DRD opcode gets merge and change in TOR so that should not be counted. hence checking opcode too.
                            if ((txn.TID in allocate_opc_tid)and(allocate_opc_tid[txn.TID]==txn.OPCODE))or (txn.TID not in allocate_opc_tid):
                                VAL_UTDB_MSG(time=0, msg=txn)
                                if ("IMPHREQ" in opcodes) or ("IMPHREQ_IA" in opcodes):
                                    start_time[txn.TID]=self.get_start_time_for_IMPHREQ_from_cbo(flows, txn.TID, dfv_cr_half_id, opcodes, cpipe_name)
                                else:
                                    start_time[txn.TID]=txn.TIME
                                clkperiod_at_alloc[txn.TID]=self.get_uclk_time_period(txn.TIME)
                                allocate_cntr=allocate_cntr+1       
                                allocate_opc_tid[txn.TID]=txn.OPCODE
                                VAL_UTDB_MSG(time=0, msg="allocating")
                            else:
                                VAL_UTDB_MSG(time=0, msg=txn.TID)
                                allocate_opc_tid.pop(txn.TID)    
                if ((txn.MISC=='TOR deallocated')and (txn.TID in allocate_opc_tid))and(txn.UNIT==cpipe_name):
                    VAL_UTDB_MSG(time=0, msg="Deallocating")
                    VAL_UTDB_MSG(time=0, msg=txn)
                    allocate_cntr=allocate_cntr-1       
                    if("EVICTIONS" in opcodes)or("EVICTIONS_IA" in opcodes): ## check deallocation for VICTIM entry 
                        if("CCF_VIC" in txn.LID):
                            end_time[txn.TID]=txn.TIME
                            allocate_opc_tid.pop(txn.TID) ## for victim flow, same TID will have 2 deall0cation.and pmon counter stops on victim torid de-allocation. so removing allocate_tid entry to avoid second de-allocation match for single allocation.
                    else:
                        end_time[txn.TID]=txn.TIME
                        allocate_opc_tid.pop(txn.TID)
                    clkperiod_at_dealloc[txn.TID]=self.get_uclk_time_period(txn.TIME)
#  Calculting the time till when the tor is occupied. Both queue size should be same  
        time1=0
        time2=0
        total_cycles=0
        for tid in start_time.keys():
            time1=start_time[tid]
            time2=end_time[tid]
            if(time2==time1):
                cycles_to_add=self.is_cpipe_valid_optimized(time1, tid, ccf_coherency_qry_i) 
            else:
                cycles_to_add=0
            if(clkperiod_at_dealloc[tid]==clkperiod_at_alloc[tid]):
                timeperiod=clkperiod_at_dealloc[tid]
            else:
                timeperiod=clkperiod_at_dealloc[tid]
            total_cycles=total_cycles + ((time2-time1)// timeperiod) + cycles_to_add
            for time in reset_times.keys():
                if (time != 0) and (time1 > time or time2 > time) and reset_times[time] == 0:
                    reset_times[time] = 1
                    total_cycles=0
                if (time !=0) and (time > time2) and reset_times[time]==0:
                    one_more_reset_after_events=1
                else:
                    one_more_reset_after_events=0
            VAL_UTDB_MSG(time=time2, msg=total_cycles)
        if (one_more_reset_after_events==1):
            total_cycles=0
        return total_cycles

    def get_uclk_time_period(self, time):    
        timeperiod=0
        records=self.ccf_common_qry.get_common_records()
        for p in records:
              for t in p.EVENTS:
                if((t.TIME < time)or(t.TIME==time)):
                    timeperiod=t.TIMEPERIOD
        VAL_UTDB_MSG(time=t.TIME, msg=int(timeperiod))
        return int(timeperiod)

##Check for INGRESS ARB OCC with module ID LPID, Valid times & Reset times. No overflow check for santa occupancy 
    def get_starve_cycles(self, cmp_val, half_id, is_ismq, valid_times, reset_times):    
        cbo_name="cbob" + str(self.si.ccf_pmon_cbo_id)
        start_time=0
        end_time=0
        starvation_start=0
        is_valid_time=0
        total_cycles=0
        clkperiod_during_start=0
        clkperiod_during_end=0
        one_more_reset_after_events=0
        if (half_id==0) and (not is_ismq):
            rec_data=self.ccf_common_cus_qry.get_cbo_ingress_arbiterstate_ha0()
        elif (half_id==1) and (not is_ismq): 
            rec_data=self.ccf_common_cus_qry.get_cbo_ingress_arbiterstate_ha1()
        elif (half_id==0) and (is_ismq): 
            VAL_UTDB_MSG(time=0, msg=cmp_val)
            rec_data=self.ccf_common_cus_qry.get_cbo_ingress_qbid_ha0()
        else:
            rec_data=self.ccf_common_cus_qry.get_cbo_ingress_qbid_ha1()
        for rec in rec_data:
            for rec_entry in rec.EVENTS:
                is_valid_time = self.is_event_in_valid_times(rec_entry.TIME, valid_times)
                if rec_entry.SIGNAL_NAME.find(cbo_name)!= -1:
                    VAL_UTDB_MSG(time=0, msg=rec_entry.DATA0)
                    if (is_ismq):
                        actual_data=(rec_entry.DATA0 & cmp_val) 
                    else: 
                        actual_data=rec_entry.DATA0
                    if (actual_data==cmp_val) and is_valid_time and (starvation_start==0): #B2B can occur for ex. ismq bid 3 to 1. So count from first and avoid override by second   
                        start_time=rec_entry.TIME
                        clkperiod_during_start=self.get_uclk_time_period(rec_entry.TIME)
                        starvation_start=1
                        VAL_UTDB_MSG(time=0, msg=rec_entry.TIME)
                    if (actual_data !=cmp_val) and (starvation_start==1):    
                        end_time=rec_entry.TIME
                        clkperiod_during_end=self.get_uclk_time_period(rec_entry.TIME)
                        starvation_start=0
                        # since counter events are sequential so we expect single event start_time will be followed by same event end_time. i.e. start time can't be overrite before updating end_time
                        if (clkperiod_during_end == clkperiod_during_start): 
                            timeperiod=clkperiod_during_end
                        else:
                            timeperiod=clkperiod_during_end
                        for time in reset_times.keys():
                            if (time != 0) and (start_time > time or end_time > time) and reset_times[time] == 0:
                                reset_times[time] = 1
                                total_cycles=0
                            if (time !=0) and (time > end_time) and reset_times[time]==0:
                                one_more_reset_after_events=1
                            else:
                                one_more_reset_after_events=0
                        total_cycles=total_cycles + ((end_time-start_time) // int(timeperiod)) 
                        VAL_UTDB_MSG(time=end_time, msg=total_cycles)
        expected_pmon_cnt=total_cycles % CCF_COH_DEFINES.MAX_PMON_COUNTER
        if (one_more_reset_after_events==1):
            expected_pmon_cnt=0
        VAL_UTDB_MSG(time=0, msg=expected_pmon_cnt)
        return expected_pmon_cnt

##Check for SANTA Q OCC with module ID LPID, Valid times & Reset times. No overflow check for santa occupancy 
    def get_santa_txq_occupancy_cycles(self, q_name, valid_times, reset_times):
        start_time = dict()
        end_time = dict()
        clkperiod_at_alloc = dict()
        clkperiod_at_dealloc = dict()
        time1=0
        time2=0
        total_cycles=0
        key_cntr=0
        mul_factor=0
        if(q_name=="TX_NCQ"):
            santa_name="SANTA_0"
        else:
            santa_name="SANTA_" + str(self.si.ccf_pmon_santa_id)
        if(q_name=="TX_RDIFA_Q"):
            records=self.ccf_common_cus_qry.get_santa_rdifaactiveentry_value(self.si.ccf_pmon_santa_id)
        else:
            records=self.ccf_common_qry.get_santa_q_records(santa_name)
        for t in records:
            for txn in t.EVENTS:
                is_valid_time = self.is_event_in_valid_times(txn.TIME, valid_times)
                if(q_name=="TX_RDIFA_Q"):
                    if(is_valid_time):
                        start_time[key_cntr]=txn.DATA0*txn.TIME
                        clkperiod_at_alloc[key_cntr]=self.get_uclk_time_period(txn.TIME)
                        VAL_UTDB_MSG(time=txn.TIME, msg=txn.DATA0)
                    if(key_cntr>0):
                        end_time[key_cntr-1]=mul_factor*txn.TIME
                        clkperiod_at_dealloc[key_cntr-1]=self.get_uclk_time_period(txn.TIME)
                        VAL_UTDB_MSG(time=txn.TIME, msg=mul_factor)
                    mul_factor=txn.DATA0 ## since end_time use prev multip. factor
                    key_cntr=key_cntr+1
                else:
                    if(txn.UNIT==santa_name):
                        key=txn.TID+"_"+txn.LID ## combine TID and LID to make uniue key.BCZ some flow can have 2 txns same TID at SANTA
                        if (q_name in txn.QUEUE) and ("INPUT_REQ" in txn.DIRECTION) and (is_valid_time): #and (self.is_occ_module_lpid_match(key)):
                            if(key not in start_time): ## allocate first chunk of data incase of tx_wr_q
                                start_time[key]=txn.TIME
                                clkperiod_at_alloc[key]=self.get_uclk_time_period(txn.TIME)
                                VAL_UTDB_MSG(time=txn.TIME, msg=key)
                        if ("OUTPUT_REQ" in txn.DIRECTION)and (q_name in txn.QUEUE)and(key in start_time):    
                            end_time[key]=txn.TIME
                            clkperiod_at_dealloc[key]=self.get_uclk_time_period(txn.TIME)
                            VAL_UTDB_MSG(time=txn.TIME, msg=key)
        for tid in start_time.keys():
            if(q_name=="TX_RDIFA_Q")and tid==(len(start_time)):
                end_time[tid]=start_time[tid] ## do this to avoid index error for last key as key is not allocated to end_time for last change 
                clkperiod_at_dealloc[tid]=clkperiod_at_alloc[tid]
            time1=start_time[tid]
            time2=end_time[tid]
            if(clkperiod_at_dealloc[tid]==clkperiod_at_alloc[tid]):
                timeperiod=clkperiod_at_dealloc[tid]
            else:
                timeperiod=clkperiod_at_dealloc[tid]
            total_cycles=total_cycles + (((time2-time1)// timeperiod)-(1*(q_name != "TX_RDIFA_Q"))) ## reduce one cycle bcz queue rden is one cycle earlier then pkt valid. FOR rdifa don't reduce 1
            for time in reset_times.keys():
                if (time != 0) and (time1 > time or time2 > time) and reset_times[time] == 0:
                    reset_times[time] = 1
                    total_cycles=0
            VAL_UTDB_MSG(time=time2, msg=total_cycles)
        expected_pmon_cnt=total_cycles % CCF_COH_DEFINES.MAX_PMON_COUNTER
        return expected_pmon_cnt

##Check for INGRESS ARB OCC with module ID LPID, Valid times, Reset times & Overflow. 
    def get_num_ring_valids(self, ccf_coherency_qry_i, ring_type, direction, polarity, valid_times, reset_times):
        cbo_id="CBO_" + str(self.si.ccf_pmon_cbo_id)
        ring_counter = CCF_COH_DEFINES.MAX_PMON_COUNTER * self.si.pmon_overflow
        for t in ccf_coherency_qry_i.DB.execute(ccf_coherency_qry_i.DB.flow(ccf_coherency_qry_i.only_ring_trk)):
            for txn in t.EVENTS:
                is_valid_time = self.is_event_in_valid_times(txn.TIME, valid_times)
                if (ring_type in txn.UNIT) and (txn.DIRECTION == direction) and (is_valid_time):
                    if ('entering ring' in txn.MISC) or ('passing through' in txn.MISC):
                        if (polarity==self.get_polarity_from_ring_trk(txn.MISC)) and (cbo_id==self.get_ringstop_from_ring_trk(txn.MISC)):
                            if(not self.should_freeze_cntr_on_overflow(txn.TIME, 1, ring_counter)):
                                VAL_UTDB_MSG(time=0, msg=txn.TID)
                                ring_counter=(ring_counter+1) % CCF_COH_DEFINES.MAX_PMON_COUNTER
                                for time in reset_times.keys():
                                    if (time != 0) and (txn.TIME > time) and reset_times[time] == 0:
                                        reset_times[time] = 1
                                        ring_counter=0
        
        ring_counter=ring_counter-self.si.pmon_overflow ## first pmon event will hit overflow and than start from 0. so deduct one from counter

        return ring_counter

    def is_event_in_valid_times(self, time, valid_times):
        valid_hit=0
        for key in valid_times.keys():
            if (time > key) and (time < valid_times[key]):
                valid_hit=1
        if (valid_hit):
            return True
        else: 
            return False

    def get_polarity_from_ring_trk(self,msg):
        if "polarity" in msg:
            tmp_msg=msg.split("=")[1]
            return tmp_msg.split(",")[0] 

    def get_ringstop_from_ring_trk(self,msg):
        if "Ringstop" in msg:
            return msg.split("=")[2] 
                    

class clean_evict_hit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.initial_map_dway() and flow.is_wbeftoi() and flow.flow_is_hom()) else 0

class clean_evict_drop(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbeftoi() and flow.flow_is_hom() and flow.cbo_sent_go_wr_pull_drop() and not flow.initial_map_dway()) else 0

class mlc_eviction_dirty_evict_to_memory(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((flow.is_wbmtoi() or flow.is_wbmtoe())and flow.wrote_data_to_mem()) else 0

class eviction_by_flush(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flusher_origin() and flow.wrote_data_to_mem()) else 0

class WbMtoIDead(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbmtoi() and (flow.is_dead_dbp_from_core() and not flow.is_core_observer())) else 0

class WbMtoIAlive(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbmtoi() and ((not flow.is_dead_dbp_from_core()) or flow.is_core_observer())) else 0

class WbMtoIBypass2MUFASA(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbmtoi() and (flow.is_bypass_llc_to_mufasa() or (flow.is_ms_chche_observer() and (not flow.is_data_written_to_cache()) and (not flow.core_sent_bogus_data())))) else 0

class WbMtoIBypass2Mem(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbmtoi() and flow.is_bypass_llc_to_dram()) else 0

class WbEtoIDead(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbeftoi() and (flow.is_dead_dbp_from_core() and not flow.is_core_observer())) else 0

class WbEtoIAlive(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_wbeftoi() and (not flow.is_dead_dbp_from_core() or flow.is_core_observer())) else 0

class WbEtoIDrop(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_core_clean() and flow.cbo_sent_go_wr_pull_drop()) else 0

class WbEtoIBypass2MUFASA(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_core_clean() and ((flow.is_ms_chche_observer() and flow.wrote_data_to_mem()) or flow.is_bypass_llc_to_mufasa())) else 0

class Modified_live_eviction(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_llc_modified() and (flow.is_ms_chche_observer() or flow.is_bypass_llc_to_mufasa())) else 0

class Modified_dead_eviction(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_llc_modified() and flow.is_bypass_llc_to_dram()) else 0

class Clean_silent_drop(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((flow.is_llc_clean() and not flow.wrote_data_to_mem()) or flow.is_flow_with_silent_evict()) else 0

class clean_evicted_to_MUFASA(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        num_of_wbetoi = len(flow.get_flow_progress(record_type=ccf_cfi_record_info, direction="C2S", channel="DATA", opcode="WbEtoI"))
        return 1 if (flow.is_llc_clean() and (num_of_wbetoi > 0) and (flow.is_ms_chche_observer() or flow.is_bypass_llc_to_mufasa())) else 0

class lookup_all(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        mask = bint(ccf_ral_agent.get_pointer().read_reg_field("egress_" + str(self.si.ccf_pmon_cbo_id), "cbopmonctrctrl"+ str(self.si.ccf_pmon_cbo_counter) , "unitmask", flow.first_accept_time))
        pmon_msg = "CACHE LOOKUP MASK is {}".format(str(mask))
        VAL_UTDB_MSG(time=flow.first_accept_time, msg=pmon_msg)
        count = False
        if mask[0] == 1:
            if mask[4] == 1:
                count = count or self.lookup_M_and_Read(flow)
            if mask[5] == 1:
                count = count or self.lookup_M_and_Write(flow)
            if mask[6] == 1:
                count = count or self.lookup_M_and_ExtSnp(flow)
            if mask[7] == 1:
                count = count or self.lookup_M_any(flow)
        if mask[1] == 1:
            if mask[4] == 1:
                count = count or self.lookup_E_and_Read(flow)
            if mask[5] == 1:
                count = count or self.lookup_E_and_Write(flow)
            if mask[6] == 1:
                count = count or self.lookup_E_and_ExtSnp(flow)
            if mask[7] == 1:
                count = count or self.lookup_E_any(flow)
        if mask[2] == 1:
            if mask[4] == 1:
                count = count or self.lookup_S_and_Read(flow)
            if mask[5] == 1:
                count = count or self.lookup_S_and_Write(flow)
            if mask[6] == 1:
                count = count or self.lookup_S_and_ExtSnp(flow)
            if mask[7] == 1:
                count = count or self.lookup_S_any(flow)
        if mask[3] == 1:
            if mask[4] == 1:
                count = count or self.lookup_I_and_Read(flow)
            if mask[5] == 1:
                count = count or self.lookup_I_and_Write(flow)
            if mask[6] == 1:
                count = count or self.lookup_I_and_ExtSnp(flow)
            if mask[7] == 1:
                count = count or self.lookup_I_any(flow)
        return 1 if count else 0

    def lookup_M_and_Read(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_m() and flow.is_drd()) else False

    def lookup_M_and_Write(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_m() and (flow.is_wbmtoe() or flow.is_wbmtoi())) else False

    def lookup_M_and_ExtSnp(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_m() and flow.is_snoop_opcode()) else False

    def lookup_M_any(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_m() and not flow.is_victim()) else False

    def lookup_E_and_Read(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_e() and flow.is_drd()) else False

    def lookup_E_and_Write(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_e() and (flow.is_wbmtoe() or flow.is_wbmtoi())) else False

    def lookup_E_and_ExtSnp(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_e() and flow.is_snoop_opcode()) else False

    def lookup_E_any(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_e() and not flow.is_victim()) else False

    def lookup_S_and_Read(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_s() and flow.is_drd()) else False

    def lookup_S_and_Write(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_s() and (flow.is_wbmtoe() or flow.is_wbmtoi())) else False

    def lookup_S_and_ExtSnp(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_s() and flow.is_snoop_opcode()) else False

    def lookup_S_any(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_s() and not flow.is_victim()) else False

    def lookup_I_and_Read(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_i() and (not flow.is_flow_promoted()) and flow.is_drd()) else False

    def lookup_I_and_Write(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_i() and (flow.is_wbmtoe() or flow.is_wbmtoi())) else False

    def lookup_I_and_ExtSnp(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_i() and flow.is_snoop_opcode()) else False

    def lookup_I_any(self, flow: ccf_flow):
        return True if (flow.initial_state_llc_i() and (not flow.is_flow_promoted())) else False

class number_of_non_prefeth_reads(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_non_prefetch_read() and flow.read_data_from_mem()) else 0

class number_of_non_req_fwd_cnflt(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_conflict_flow() and flow.read_data_from_mem()) else 0

class number_of_llc_pref(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_llcpref() and flow.read_data_from_mem()) else 0

class santa0_NoNCCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA0":
            count = self.get_num_of_rejects(flow,"RejectNoSantaCredit_C2SDataNonCoherent")
        return count

class santa0_NoDRSCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA0":
            count = self.get_num_of_rejects(flow, "NoSantaCredit_C2SDataCoherentNonDRS")
        return count

class santa0_NoSharedDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA0":
            count = self.get_num_of_rejects(flow,"NoSantaCredit_UPIC_C2SData")
        return count

class santa0_NoSharedRdCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA0":
            count = 0 # TODO FIXME CBB ygrotas is meirlevy. will have new pmon hence commented. self.get_num_of_rejects(flow,"NoSantaCredit_UPIC_C2SReq")
        return count

class santa1_NoNCCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA1":
            count = self.get_num_of_rejects(flow,"RejectNoSantaCredit_C2SDataNonCoherent")
        return count

class santa1_NoDRSCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA1":
            count = self.get_num_of_rejects(flow,"NoSantaCredit_C2SDataCoherentNonDRS")
        return count

class santa1_NoSharedDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA1":
            count = self.get_num_of_rejects(flow,"NoSantaCredit_UPIC_C2SData")
        return count

class santa1_NoSharedRdCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if flow.santa_id == "CCF_VC_SANTA1":
            count =  0 # TODO FIXME CBB ygrotas is meirlevy. will have new pmon hence commented. self.get_num_of_rejects(flow,"NoSantaCredit_UPIC_C2SReq")
        return count

class LLCPrefThrottling(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_llcpref() and flow.is_tor_occup_above_threshold()) else 0


class OverFlow_alloc(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 0


class Multiple_entry_alloc_to_same_entry(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if flow.is_monitor():
            int_addr = bint(int(flow.address, 16))
            int_addr[5:0] = 0
            hex_addr = hex(int_addr)
            if flow.current_monitor_array is not None and len(flow.current_monitor_array.entries.keys()) > 0:
                if hex_addr in flow.current_monitor_array.entries.keys():
                    for monitor in flow.current_monitor_array.entries[hex_addr]:
                        if monitor.core != flow.requestor_physical_id or monitor.lpid != flow.lpid:
                            return 1
        return 0



class XSNP_RESPONSE_all(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        mask = bint(ccf_ral_agent.get_pointer().read_reg_field("egress_" + str(self.si.ccf_pmon_cbo_id), "cbopmonctrctrl"+ str(self.si.ccf_pmon_cbo_counter) , "unitmask", flow.first_accept_time))
        pmon_msg = "XSNP RESPONSE MASK is {}".format(str(mask))
        VAL_UTDB_MSG(time=flow.first_accept_time, msg=pmon_msg)
        count = 0
        if mask[5] == 1:
            if mask[0] == 1:
                count = count + self.RSPIHITI_EXTERNAL(flow)
            if mask[1] == 1:
                count = count + self.RSPIHITFSE_EXTERNAL(flow)
            if mask[2] == 1:
                count = count + self.RSPSHITFSE_EXTERNAL(flow)
            if mask[3] == 1:
                count = count + self.RSPSFWDM_EXTERNAL(flow)
            if mask[4] == 1:
                count = count + self.RSPIFWDM_EXTERNAL(flow)
        if mask[6] == 1:
            if mask[0] == 1:
                count = count + self.RSPIHITI_XCORE(flow)
            if mask[1] == 1:
                count = count + self.RSPIHITFSE_XCORE(flow)
            if mask[2] == 1:
                count = count + self.RSPSHITFSE_XCORE(flow)
            if mask[3] == 1:
                count = count + self.RSPSFWDM_XCORE(flow)
            if mask[4] == 1:
                count = count + self.RSPIFWDM_XCORE(flow)
        if mask[7] == 1:
            if mask[0] == 1:
                count = count + self.RSPIHITI_EVICTION(flow)
            if mask[1] == 1:
                count = count + self.RSPIHITFSE_EVICTION(flow)
            if mask[2] == 1:
                count = count + self.RSPSHITFSE_EVICTION(flow)
            if mask[3] == 1:
                count = count + self.RSPSFWDM_EVICTION(flow)
            if mask[4] == 1:
                count = count + self.RSPIFWDM_EVICTION(flow)
        return count

    def RSPIHITI_EXTERNAL(self, flow: ccf_flow):
         count = 0
         if flow.is_flow_origin_uxi_snp() and not flow.is_interrupt():
             count = self.get_num_of_snp_rsp(flow, "RspIHitI")
         return count

    def RSPIHITFSE_EXTERNAL(self, flow: ccf_flow):
        count = 0
        if flow.is_flow_origin_uxi_snp():
            count = self.get_num_of_snp_rsp(flow, "RspIHitFSE")
        return count

    def RSPSHITFSE_EXTERNAL(self, flow: ccf_flow):
        count = 0
        if flow.is_flow_origin_uxi_snp():
            count = self.get_num_of_snp_rsp(flow, "RspSHitFSE")
        return count

    def RSPSFWDM_EXTERNAL(self, flow: ccf_flow):
        count = 0
        if flow.is_flow_origin_uxi_snp():
            count = self.get_num_of_snp_rsp(flow, "RspSFwdMO")
        return count

    def RSPIFWDM_EXTERNAL(self, flow: ccf_flow):
        count = 0
        if flow.is_flow_origin_uxi_snp():
            count = self.get_num_of_snp_rsp(flow, "RspIFwdMO")
        return count

    def RSPIHITI_XCORE(self, flow: ccf_flow):
        count = 0
        if flow.is_idi_flow_origin() and not flow.is_interrupt():
            count = self.get_num_of_snp_rsp(flow, "RspIHitI")
        return count

    def RSPIHITFSE_XCORE(self, flow: ccf_flow):
        count = 0
        if flow.is_idi_flow_origin():
            count = self.get_num_of_snp_rsp(flow, "RspIHitFSE")
        return count

    def RSPSHITFSE_XCORE(self, flow: ccf_flow):
        count = 0
        if flow.is_idi_flow_origin():
            count = self.get_num_of_snp_rsp(flow, "RspSHitFSE")
        return count

    def RSPSFWDM_XCORE(self, flow: ccf_flow):
        count = 0
        if flow.is_idi_flow_origin():
            count = self.get_num_of_snp_rsp(flow, "RspSFwdMO")
        return count

    def RSPIFWDM_XCORE(self, flow: ccf_flow):
        count = 0
        if flow.is_idi_flow_origin():
            count = self.get_num_of_snp_rsp(flow, "RspIFwdMO")
        return count

    def RSPIHITI_EVICTION(self, flow: ccf_flow):
        count = 0
        if flow.is_victim():
            count = self.get_num_of_snp_rsp(flow, "RspIHitI")
        return count

    def RSPIHITFSE_EVICTION(self, flow: ccf_flow):
        count = 0
        if flow.is_victim():
            count = self.get_num_of_snp_rsp(flow, "RspIHitFSE")
        return count

    def RSPSHITFSE_EVICTION(self, flow: ccf_flow):
        count = 0
        if flow.is_victim():
            count = self.get_num_of_snp_rsp(flow, "RspSHitFSE")
        return count

    def RSPSFWDM_EVICTION(self, flow: ccf_flow):
        count = 0
        if flow.is_victim():
            count = self.get_num_of_snp_rsp(flow, "RspSFwdMO")
        return count

    def RSPIFWDM_EVICTION(self, flow: ccf_flow):
        count = 0
        if flow.is_victim():
            count = self.get_num_of_snp_rsp(flow, "RspIFwdMO")
        return count

class SNP_NUM_1_ALL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 1 else 0

class SNP_NUM_2_ALL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 2 else 0

class SNP_NUM_4_ALL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 4 else 0

class SNP_NUM_8_ALL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 8 else 0

class SNP_NUM_1_EXTERNAL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flow_origin_uxi_snp() and len(flow.snoop_requests) >= 1) else 0

class SNP_NUM_2_EXTERNAL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flow_origin_uxi_snp() and len(flow.snoop_requests) >= 2) else 0

class SNP_NUM_4_EXTERNAL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flow_origin_uxi_snp() and len(flow.snoop_requests) >= 4) else 0

class SNP_NUM_8_EXTERNAL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flow_origin_uxi_snp() and len(flow.snoop_requests) >= 8) else 0

class SNP_NUM_1_XCORE(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((flow.is_idi_flow_origin() and (not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 1) else 0

class SNP_NUM_2_XCORE(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((flow.is_idi_flow_origin() and (not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 2) else 0

class SNP_NUM_4_XCORE(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((flow.is_idi_flow_origin() and (not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 4) else 0

class SNP_NUM_8_XCORE(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((flow.is_idi_flow_origin() and (not flow.is_ipi_interrupt()) and (not flow.is_lock_or_unlock())) and len(flow.snoop_requests) >= 8) else 0

class SNP_NUM_1_EVICTION(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_victim() and len(flow.snoop_requests) >= 1) else 0

class SNP_NUM_2_EVICTION(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_victim() and len(flow.snoop_requests) >= 2) else 0

class SNP_NUM_4_EVICTION(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_victim() and len(flow.snoop_requests) >= 4) else 0

class SNP_NUM_8_EVICTION(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_victim() and len(flow.snoop_requests) >= 8) else 0

class LINES_VICTIMIZED_M(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_llc_modified()) else 0

class LINES_VICTIMIZED_E(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if flow.is_victim() and flow.initial_state_llc_e() and not flow.snoop_rsp_m(): # and not (flow.is_clean_evict() and flow.is_rejected()):
            return 1
        if flow.is_flow_with_silent_evict():
            if self.llc_db_agent.get_llc_state(flow.cbo_id_phys, flow.cbo_half_id, flow._first_llc_trans.rec_set,flow.get_silent_evict_way(), flow.first_accept_time) == "E":
                return 1
        return 0

class LINES_VICTIMIZED_S(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        #TODO: this is not correct to look at flow and ask about it's victim since in CBB one flow can create many victims in case of multiple partial hits.
        if (flow.is_victim_line() and flow.victim_state == "LLC_S"):
            return 1
        if flow.is_flow_with_silent_evict():
            #if self.llc_db_agent.get_llc_state(flow.cbo_id_phys, flow.cbo_half_id,flow._first_llc_trans.rec_set,flow.get_silent_evict_way(),flow.first_accept_time) == "S":
            llc_name="LLC_"+str(flow.cbo_id_phys)
            for item in self.llc_rtl_db:
                if(item.rec_way!="-")and llc_name==item.rec_unit:
                    if (int(flow.cbo_half_id)==int(item.rec_half))and (int(flow._first_llc_trans.rec_set,16)==int(item.rec_set,16)) and (int(flow.get_silent_evict_way())==int(item.rec_way)):
                        if(item.rec_time <=flow._first_llc_trans.rec_time)and item.rec_state=="S":
                            return 1
        return 0

class LINES_VICTIMIZED_I(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((not flow.is_victim()) and (not flow.is_victim_line()) and (not flow.is_flow_with_silent_evict()) and (not flow.is_flow_promoted()) and flow.is_allocating_line()) else 0


class LINES_VICTIMIZED_NO_DATA_ALLOC(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
       return 1 if ((not flow.is_victim()) and flow.is_allocating_tag_way_only() and flow.is_victim_line()) else 0

class LINES_VICTIMIZED_NO_DATA_ALLOC_AND_DATA_VICTIM(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if ((not flow.is_victim()) and flow.is_allocating_tag_way_only() and flow.is_alloc_tag_and_victim_map_data()) else 0

class IRQ_NoSharedRdCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 0 # TODO FIXME CBB ygrotas is meirlevy. will have new pmon hence commented. self.get_num_of_irq_rejects(flow,"NoSantaCredit_UPIC_C2SReq")

class IRQ_NoSharedDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"NoSantaCredit_C2SDataCoherentNonDRS")

class IRQ_NoAnyDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"NoSantaCredit_C2SDataCoherentDRS")

class IRQ_NoNCCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"NoSantaCredit_C2SDataNonCoherent")

class IRQ_Any(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"")

class IRQ_Egress_full(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"RejectLateDueToEgrCredit")

class IRQ_Address_conflict(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow, "RejectDuePaMatch", "EntryWrCV")

class IRQ_Prefetch_promotion(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if flow.is_flow_promoted() else 0

class IRQ_No_Victim_TOR(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"RejectLateDueToVictimTor")

class IRQ_No_NonHOM_TOR(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_irq_rejects(flow,"RejectDueToLastNonHomRequest")

class IRQ_All_data_ways_are_reserved(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        rej_count = 0
        if flow.is_idi_flow_origin():
            for reason in flow.rejected_reasons:
                if ("RejectDueAllDataWaysAreReserved" in reason.reject_reason) and (self.ccf_registers.enable_force_noavaildataway_in_any_reject[flow.cbo_id_phys] or reason.llc_state == "LLC_I"):
                    rej_count = rej_count + 1
        return rej_count

class IPQ_Any(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ipq_rejects(flow,"")

class IPQ_Egress_full(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ipq_rejects(flow,"RejectLateDueToEgrCredit")

class IPQ_Address_conflict(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ipq_rejects(flow, "RejectDueNotAllowSnoop")

class IPQ_NoSharedDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ipq_rejects(flow,"RejectNoSantaCredit_C2SDataCoherentNonDRS")

class IPQ_NoAnyDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ipq_rejects(flow,"RejectNoSantaCredit_C2SDataCoherentDRS")

class ISMQ_Any(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ismq_rejects(flow,"")

class ISMQ_Egress_full(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ismq_rejects(flow,"RejectLateDueToEgrCredit")

class ISMQ_NoSharedRdCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 0 # TODO FIXME CBB ygrotas is meirlevy. will have new pmon hence commented.  self.get_num_of_ismq_rejects(flow,"NoSantaCredit_UPIC_C2SReq")

class ISMQ_NoSharedDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ismq_rejects(flow,"NoSantaCredit_C2SDataCoherentNonDRS")

class ISMQ_NoAnyDataCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ismq_rejects(flow,"NoSantaCredit_C2SDataCoherentDRS")

class ISMQ_NoNCCredit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return self.get_num_of_ismq_rejects(flow,"NoSantaCredit_C2SDataNonCoherent")

class ALLOCATION_DRD(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if (flow.is_drd() and flow.flow_is_hom() and not flow.is_flow_promoted()):
            return self.get_num_of_ipq_rejects(flow,"") + 1 #we caunt rejects+ allocation (or allocation with retries)
        return 0

class TOR_OCC_DRD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"DRd","DRd_NS","DRd_Pref","DRd_Opt_Pref","DRd_Opt"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 0, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_DRD_IA(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"DRd","DRd_NS","DRd_Pref","DRd_Opt_Pref","DRd_Opt","DRD_IA"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 0, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_ALL(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"ALL"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_DFV(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"DFV"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_EVICTIONS(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"EVICTIONS"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_IMPHREQ(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"IMPHREQ"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_IMPHREQ_IA(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"IMPHREQ_IA"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_EVICTIONS_IA(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"EVICTIONS_IA"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_WCIL(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"WCiL","WCiLF"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 0, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_WCIL_IA(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"WCiL","WCiLF","WCIL_IA"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 0, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_ALL_IA(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"ALL_IA"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class TOR_OCC_DFV_IA(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        opcodes={"DFV_IA"}
        expected_pmon_cnt=self.get_occupancy_cycles(flows, ccf_coherency_qry_i, opcodes, 1, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BLOCK_IPQ_HA0(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##for BLOCK_IPQ=2, BLOCK_IRQ=1 BLOCK_IRQ_IPQ=1. Normal state=0
        cmp_val=2 
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 0, 0, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BLOCK_IRQ_HA0(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##for BLOCK_IPQ=2, BLOCK_IRQ=1  BLOCK_IRQ_IPQ=1. Normal state=0
        cmp_val=1 
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 0, 0, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BLOCK_IRQ_IPQ_HA0(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##for BLOCK_IPQ=2, BLOCK_IRQ=1  BLOCK_IRQ_IPQ=1. Normal state=0
        cmp_val=3 
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 0, 0, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BID_HA0(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##qbid[0] 0th bit give ISMQ bid info. 
        cmp_val=1
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 0, 1, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BLOCK_IPQ_HA1(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##for BLOCK_IPQ=2, BLOCK_IRQ=1 BLOCK_IRQ_IPQ=1. Normal state=0
        cmp_val=2 
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 1, 0, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BLOCK_IRQ_HA1(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##for BLOCK_IPQ=2, BLOCK_IRQ=1  BLOCK_IRQ_IPQ=1. Normal state=0
        cmp_val=1 
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 1, 0, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BLOCK_IRQ_IPQ_HA1(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##for BLOCK_IPQ=2, BLOCK_IRQ=1  BLOCK_IRQ_IPQ=1. Normal state=0
        cmp_val=3 
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 1, 0, valid_times, reset_times)
        return expected_pmon_cnt

class INGRESS_ARBITER_BID_HA1(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        ##qbid[0] 0th bit give ISMQ bid info. 
        cmp_val=1
        expected_pmon_cnt=self.get_starve_cycles(cmp_val, 1, 1, valid_times, reset_times)
        return expected_pmon_cnt

class AD_RING_IN_USE_UP_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AD", "UP", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class AD_RING_IN_USE_UP_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AD", "UP", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class AD_RING_IN_USE_DN_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AD", "DOWN", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class AD_RING_IN_USE_DN_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AD", "DOWN", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class BL_RING_IN_USE_UP_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "BL", "UP", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class BL_RING_IN_USE_UP_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "BL", "UP", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class BL_RING_IN_USE_DN_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "BL", "DOWN", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class BL_RING_IN_USE_DN_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "BL", "DOWN", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class AK_RING_IN_USE_UP_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AK", "UP", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class AK_RING_IN_USE_UP_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AK", "UP", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class AK_RING_IN_USE_DN_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AK", "DOWN", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class AK_RING_IN_USE_DN_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "AK", "DOWN", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class IV_RING_IN_USE_UP_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "IV", "UP", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class IV_RING_IN_USE_UP_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "IV", "UP", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class IV_RING_IN_USE_DN_EVEN(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "IV", "DOWN", "EVEN", valid_times, reset_times)
        return expected_pmon_cnt

class IV_RING_IN_USE_DN_ODD(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        expected_pmon_cnt=self.get_num_ring_valids(ccf_coherency_qry_i, "IV", "DOWN", "ODD", valid_times, reset_times)
        return expected_pmon_cnt

class TXQ_RDQ_OCCUPANCY(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        q_name="TX_RD_Q"
        expected_pmon_cnt=self.get_santa_txq_occupancy_cycles(q_name, valid_times, reset_times)
        return expected_pmon_cnt

class TXQ_WRQ_OCCUPANCY(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        q_name="TX_WR_Q"
        expected_pmon_cnt=self.get_santa_txq_occupancy_cycles(q_name, valid_times, reset_times)
        return expected_pmon_cnt

class TXQ_NCQ_OCCUPANCY(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        q_name="TX_NCQ"
        expected_pmon_cnt=self.get_santa_txq_occupancy_cycles(q_name, valid_times, reset_times)
        return expected_pmon_cnt

class TXQ_RSP_OCCUPANCY(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        q_name="TX_RSP_Q"
        expected_pmon_cnt=self.get_santa_txq_occupancy_cycles(q_name, valid_times, reset_times)
        return expected_pmon_cnt

class TXQ_RDIFA_OCCUPANCY(pmon_base_chk):
    def num_of_pmon_occ_cycles(self, flows, ccf_coherency_qry_i, valid_times, reset_times):
        q_name="TX_RDIFA_Q"
        expected_pmon_cnt=self.get_santa_txq_occupancy_cycles(q_name, valid_times, reset_times)
        return expected_pmon_cnt
 #   def is_occ_module_lpid_match(self, tid):    
 #       if (self.si.pmon_lpid_en == 0) or ((self.get_module_id(tid)==self.si.pmon_moduleid) and (self.get_lpid(tid) == self.si.pmon_lpid)):
 #           VAL_UTDB_MSG(time=0, msg=self.get_module_id(tid))
 #           return 1
 #       else: 
 #           return 0

 #   def get_occupancy_cycles(self, clk_timeperiod, ccf_coherency_qry_i ):    
 #       total_time=self.get_tor_occupancy_time_rec(ccf_coherency_qry_i) 
 #       VAL_UTDB_MSG(time=0, msg=clk_timeperiod)
 #       VAL_UTDB_MSG(time=0, msg=total_time)
 #       expected_pmon_cnt=total_time // clk_timeperiod
 #       return expected_pmon_cnt

 #   def get_tor_occupancy_time_rec(self, ccf_coherency_qry_i):
 #       start_time = []
 #       end_time = []
 #       allocate_cntr=0
 #       allocate_tid=dict()
 #       cpipe_name="CPIPE_" + str(self.si.ccf_pmon_cbo_id)
 #       VAL_UTDB_MSG(time=0, msg=cpipe_name)
 #       for t in ccf_coherency_qry_i.DB.execute(ccf_coherency_qry_i.DB.flow(ccf_coherency_qry_i.only_cbo_trk)):
 #           for txn in t.EVENTS:
 #               if ((txn.OPCODE=='DRd')or(txn.OPCODE=='DRd_NS')or(txn.OPCODE=='DRd_Pref')or(txn.OPCODE=='DRd_Opt_Pref'))and(txn.UNIT==cpipe_name):
 #                   if (txn.MISC =='TOR allocated')and(self.is_occ_module_lpid_match(txn.TID)):
 #                       if (allocate_cntr==0):
 #                           VAL_UTDB_MSG(time=0, msg=txn)
 #                           start_time.append(txn.TIME)
 #                           VAL_UTDB_MSG(time=0, msg="START TIME")
 #                       allocate_cntr=allocate_cntr+1       
 #                       allocate_tid[txn.TID]=1
 #                       VAL_UTDB_MSG(time=0, msg=allocate_cntr)
 #               if ((txn.MISC=='TOR deallocated')and (txn.TID in allocate_tid))and(txn.UNIT==cpipe_name):
 #                   VAL_UTDB_MSG(time=0, msg="Deallocating")
 #                   VAL_UTDB_MSG(time=0, msg=txn)
 #                   allocate_cntr=allocate_cntr-1       
 #                   if (allocate_cntr==0):
 #                       VAL_UTDB_MSG(time=0, msg=txn)
 #                       end_time.append(txn.TIME)
 #                       VAL_UTDB_MSG(time=0, msg="END TIME")
##  Calculting the time till when the tor is occupied by drd. Both queue size should be same  
 #       #return self.tmp
 #       time1=0
 #       time2=0
 #       for i in start_time:
 #           time1=time1+i
 #           VAL_UTDB_MSG(time=0, msg=time1)
 #       for j in end_time:
 #           time2=time2+j
 #           VAL_UTDB_MSG(time=0, msg=time2)
 #       occ_time=time2-time1
 #       VAL_UTDB_MSG(time=0, msg=occ_time)
 #       return occ_time

class ALLOCATION_IMPHREQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.flow_is_hom() and (flow.is_conflict_flow() or (flow.cbo_got_ufi_uxi_cmpo() and not flow.is_flow_promoted()))) else 0

class ALLOCATION_EVICTIONS(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if flow.is_victim() else 0

class ALLOCATION_ALL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if not flow.is_flow_promoted() else 0

class ALLOCATION_WB(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if flow.is_wb_flow() and not flow.is_wbstoi():
            return self.get_num_of_ipq_rejects(flow,"") + 1 #we caunt rejects+ allocation (or allocation with retries)
        return 0

class ALLOCATION_WCIL(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if (flow.is_wcilf() or flow.is_wcil()):
            return self.get_num_of_ipq_rejects(flow,"") + 1 #we caunt rejects+ allocation (or allocation with retries)
        return 0

class ALLOCATION_snoop_reserved_slot(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        SNOOP_RESERVED_TORID = ['19', '51']
        if (flow.is_flow_origin_uxi_snp() and (flow.cbo_tor_qid in SNOOP_RESERVED_TORID)):
            return 1
        return 0

class ALLOCATION_victim_reserved_slot(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        VICTIM_RESERVED_TORID = ['18', '50']
        if (flow.is_victim() and (flow.cbo_tor_qid in VICTIM_RESERVED_TORID)):
            return self.get_num_of_ipq_rejects(flow,"") + 1 #we caunt rejects+ allocation (or allocation with retries)
        return 0

class RspIwasFSE(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.snoop_rsp_i() and flow.is_flow_origin_uxi_snp() and flow.initial_state_llc_e_or_s()) else 0
class WC_aliasing(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.flow_is_hom() and (flow.is_wcil() or flow.is_wcilf() or flow.is_mempushwr()) and flow.initial_state_llc_m()) else 0

class IA_Hits_SF(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_idi_flow_origin() and (not flow.is_llc_special_opcode()) and (not flow.initial_state_llc_i()) and flow.initial_map_sf()) else 0

class IO_Hits_SF(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flow_origin_uxi_snp() and (not flow.initial_state_llc_i()) and flow.initial_map_sf()) else 0

class IA_Hits_DATA(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_idi_flow_origin() and (not flow.is_llc_special_opcode()) and (not flow.initial_state_llc_i()) and flow.initial_map_dway()) else 0

class IO_Hits_DATA(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_flow_origin_uxi_snp() and (not flow.initial_state_llc_i()) and flow.initial_map_dway()) else 0

class Bin0_Rd_hit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if self.is_bin0_hit(flow) else 0

class Bin1_Rd_hit(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if self.is_bin1_hit(flow) else 0

class SANTA_CFI_TX_Transactions_all(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            if flow.wrote_data_to_mem() and flow.flow_is_hom():
                if ((flow.is_wcil() or flow.is_wil()) and (flow.initial_state_llc_m() or flow.snoop_rsp_m())):
                    count = count + 4
                else:
                    count = count + 2
            if flow.is_conflict_flow():
                count = count + 2
        return count

class SANTA_CFI_TX_Transactions_reads(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_rd_santa_id():
            if flow.cbo_got_ufi_uxi_cmpo() and flow.flow_is_hom():
                for trans in flow.flow_progress:
                    if isinstance(trans, ccf_cfi_record_info):
                        if trans.is_upi_c_read_opcode_besides_Inv():
                            return 1
        return 0

class SANTA_CFI_TX_Transactions_writes(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        add = 0
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            if flow.wrote_data_to_mem() and flow.flow_is_hom() and (not flow.is_flow_origin_upi_snp()):
                add = 4 if ((flow.is_wcil() or flow.is_wil()) and (flow.initial_state_llc_m() or flow.snoop_rsp_m())) else 2
        return add

class SANTA_CFI_TX_Transactions_ReqFwdCnflt(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if flow.is_conflict_flow() else 0
        return 0

class SANTA_CFI_TX_Transactions_wbeftoi(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 2 if ((flow.is_core_clean() or flow.is_llc_clean()) and flow.wrote_data_to_mem()) else 0
        return 0

class SANTA_SNP_RESPONSE_RspI(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if (flow.is_flow_origin_uxi_snp() and flow.santa_snoop_response == "RspI") else 0
        return 0

class SANTA_SNP_RESPONSE_RspIWb(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if flow.is_santa_RspIWb() else 0
        return 0

class SANTA_SNP_RESPONSE_RspS(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if (flow.is_flow_origin_uxi_snp() and flow.santa_snoop_response == "RspS") else 0
        return 0

class SANTA_SNP_RESPONSE_RspSWb(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if (flow.is_flow_origin_uxi_snp() and flow.santa_snoop_response == "RspSWb") else 0
        return 0

class SANTA_SNP_RESPONSE_RspE(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if (flow.is_flow_origin_uxi_snp() and flow.santa_snoop_response == "RspE") else 0
        return 0

class SANTA_SNP_RESPONSE_RspCurData(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if (flow.is_flow_origin_uxi_snp() and flow.santa_snoop_response == "RspCurData") else 0
        return 0

class TXQ_ALLOCATION_RDQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if self.is_relevant_moduleid(flow) and str(self.cbo_santa_id) in flow.get_rd_santa_id():
            return 1 if flow.cbo_got_ufi_uxi_cmpo() else 0
        return 0

class TXQ_ALLOCATION_RDIFA(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_rd_santa_id():
            if flow.cbo_got_ufi_uxi_cmpo() and flow.flow_is_hom():
                return 1
        return 0

class TXQ_ALLOCATION_RDIFA_without_invalidation(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_rd_santa_id():
            if flow.cbo_got_ufi_uxi_cmpo() and flow.flow_is_hom():
                for trans in flow.flow_progress:
                    if isinstance(trans, ccf_cfi_record_info):
                        if trans.is_upi_c_read_opcode_besides_Inv():
                            return 1
        return 0


class TXQ_ALLOCATION_WRQ_DRS(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if flow.wrote_data_to_mem() and flow.is_flow_origin_uxi_snp() else 0
        return 0

class TXQ_ALLOCATION_WRQ_WB(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        count = 0
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            if flow.flow_is_hom() and (flow.wrote_data_to_mem() and not flow.is_flow_origin_uxi_snp()) or flow.is_conflict_flow():
                if flow.is_conflict_flow():
                    count = count + 1
                else:
                    count = count + 2
                #if ((flow.is_wcil() or flow.is_wil() of flow.) and (flow.initial_state_llc_m() or flow.snoop_rsp_m())):
                #    count = count + 2
                #else:
                #    count = count + 1
        return count

class TXQ_ALLOCATION_NCQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if flow.is_lock_or_unlock():
            return 0
        if (str(self.cbo_santa_id) == "0") and (not flow.flow_is_hom()) and (not flow.is_sad_crababort()):
            for trans in flow.flow_progress:
                if (type(trans) is ccf_cfi_record_info):
                    if trans.is_upi_nc_c2u_data():
                        return 1
            if flow.uri["TID"] in self.nc_racu_sb_transactions:
                return 1
        return 0

#TODO: check the correctness of this class for CBB
class TXQ_ALLOCATION_RSPQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            if(flow.is_flow_origin_uxi_snp()):
                for trans in flow.flow_progress:
                    if (type(trans) is ccf_cfi_record_info):
                        if(trans.is_upi_c_snoop_rsp()) and (not trans.is_upi_c_c2u_data()):
                            return 1
        return 0


class RXQ_ALLOCATION_RspQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return flow.get_num_of_cmp_per_santa_id(self.cbo_santa_id)

class RXQ_ALLOCATION_ReqQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_rx_req_santa_id():
            return 1 if flow.is_flow_origin_uxi_snp() else 0
        return 0

class RXQ_ALLOCATION_DataQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id() and flow.flow_is_hom():
            return 2 if flow.read_data_from_mem() else 0
        return 0

class RXQ_ALLOCATION_LockQ(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if flow.is_lock_or_splitlock() else 0
        return 0

class number_of_dirty_evictions(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            if (flow.wrote_data_to_mem() and flow.is_santa_dirty_wb()):
                return 2 if ((flow.is_wcil() or flow.is_wil()) and (flow.initial_state_llc_m() or flow.snoop_rsp_m())) else 1
        return 0

class number_of_clear_evictions(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        if str(self.cbo_santa_id) in flow.get_wr_santa_id():
            return 1 if (flow.wrote_data_to_mem() and flow.is_santa_clean_wb()) else 0
        return 0


class VLW(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        return 1 if (flow.is_vlw()) else 0


class DoorBell(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        fastipi = self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp)
        return 1 if flow.is_u2c_upi_nc_ltdoorbell() else 0

class IntPhy_IntLog(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        fastipi = self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp) == 1
        return 1 if flow.is_u2c_upi_nc_ipi_interrupt() and (not flow.is_idi_flow_origin()) else 0

class IntPhy_IntLog_FastIpi(pmon_base_chk):
    def num_of_pmon_hits(self, flow: ccf_flow):
        fastipi = self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp) == 1
        return 1 if flow.is_ipi_interrupt() and fastipi and flow.is_idi_flow_origin() else 0


class ring_scale_events(pmon_base_chk):
    def __init__(self):
        super().__init__()
        self.is_per_flow = 0

    def num_of_pmon_hits_in_test(self):
        cr_writes = self.ccf_pmsb_db.power_sb_msgs_db['07 CRWRITE']

        count = 0
        for msg in cr_writes:
            is_in_time = (msg.time > COH_GLOBAL.global_vars["START_OF_TEST"]) and (msg.time < COH_GLOBAL.global_vars["END_OF_TEST"])
            is_from_pma = (msg.src_pid == int('b1',16))
            is_to_punit = (msg.dest_pid == int('1',16))
            is_ring_scalability_event = (msg.addr == int('1c8',16))
            if is_in_time and is_from_pma and is_to_punit and is_ring_scalability_event:
                count = count + 1
        return count
