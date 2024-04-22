from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG

from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_cov import SAD_CHANGE_CG
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from agents.ccf_agent.ccf_sad_chk_agent.ccf_sad_chk_cov import ccf_sad_cov_collect
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_common_base.ccf_registers import ccf_registers


class ccf_sad_chk(ccf_coherency_base_chk):
    def __init__(self):
        super().__init__()
        self.ccf_sm_db = SM_DB.get_pointer()
        self.ccf_ral_agent_ptr = ccf_ral_agent.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.ccf_sad_cov_collect_ptr = ccf_sad_cov_collect.get_pointer()
        self.sample_cov = self.si.ccf_cov_en

    def should_check_flow(self, flow: ccf_flow):
        return super().should_check_flow(flow) and self.si.ccf_sad_chk_en == 1 \
               and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_flusher() and not flow.is_u2c_dpt_req()

    def reset(self):
        pass

    def is_wcilf(self, flow: ccf_flow):
        return flow.is_wcilf() or flow.is_wilf()

    def is_itom(self, flow: ccf_flow):
        return flow.is_itom() or flow.is_specitom()


    def is_wbmto(self, flow: ccf_flow):
        return flow.is_wbmtoi() or flow.is_wbmtoe() or flow.is_itomwr() or flow.is_itomwr_wt() or flow.is_mempushwr()

    def is_clflush(self, flow: ccf_flow):
        return flow.is_clflush() or flow.is_clflush_opt() or flow.is_cldemote() or flow.is_clwb()

    def lock_sad_change(self, flow: ccf_flow):
        region = ""
        sad_change_cg = SAD_CHANGE_CG.get_pointer()

        if "LOCK" == flow.opcode:
            if flow.get_address(msb=11, lsb=6) in ["10", "4"]:
                region = "NA"
            else:
                region = "CRABABORT"

        if "UNLOCK" == flow.opcode:
            if flow.get_address(msb=11, lsb=6) == "3":
                region = "NA"
            else:
                region = "CRABABORT"

        if "SPLITLOCK" == flow.opcode:
            if flow.get_address(msb=11, lsb=6) == "5":
                region = "NA"
            else:
                region = "CRABABORT"
        if flow.is_spcyc():
            if flow.is_spcyc_addr_zero():
                region = "NA"
            else:
                region = "CRABABORT"

        if self.sample_cov == 1:
            sad_change_cg.sample(lock_opcodes_cp=flow.opcode,
                                 lock_sad_results=region)

        return region

    def simple_mmio_sad(self, flow: ccf_flow):
        if flow.is_prd():
            return "MMIOPTL"
        elif flow.is_wil() or flow.is_wcil() or self.is_wcilf(flow) or flow.is_crd() or flow.is_ucrdf_or_crd_uc() or flow.is_drd() or flow.is_rfo():
            return "MMIO"
        elif flow.is_wbeftoi() or flow.is_wbeftoe():  ##  NC flows with crababort flow
            return "MMIO"
        elif flow.is_wbstoi():
            return "MMIO"
        elif self.is_itom(flow):
            if self.ccf_registers.allowitom_to_mmio[flow.cbo_id_phys] == 1:
                return "MMIO"
            else:
                return "CRABABORT"
        elif flow.is_llcpref() or self.is_wbmto(flow) or flow.is_monitor():
            return "CRABABORT"
        elif self.is_clflush(flow):
            if flow.is_cldemote() or self.ccf_registers.mmio_clflush_defeature[flow.cbo_id_phys] == 1 or \
                    self.ccf_registers.mmio_clflush_defeature[flow.cbo_id_phys] == 3:
                return "CRABABORT"
            else:
                return "MMIO"
        else:
            err_msg = "there is no sad result option for flow " + flow.uri["TID"] + " " + flow.opcode + " " + flow.sad_results + " " + sub_region
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def mmio_sad_change(self, flow: ccf_flow, region, sub_region):
        sad_change_cg = SAD_CHANGE_CG.get_pointer()

        if region == "CRAB_ABORT":
            region = "CRABABORT"

        elif "PCIE_MMCFG" in region:
            if self.si.pciexbar_en:
                if flow.is_prd() or flow.is_wil():
                    region = "CFG"
                else:
                    region = "CRABABORT"
            else:
                region = self.simple_mmio_sad(flow)

            if self.sample_cov == 1:
                sad_change_cg.sample(origin_region="PCIE_MMCFG",
                                     final_region=region,
                                     flow_opcode=flow.opcode)

        elif (sub_region is not None and "LT" in region):
            bin_addr = bint(int(flow.address, 16))
            addr_without_mktme = str(hex(bin_addr[CCF_COH_DEFINES.mktme_lsb - 1:0]))
            fed2_split_addr = addr_without_mktme.split("fed2")
            fed43_split_addr = addr_without_mktme.split("fed43")
            private = self.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(flow.cbo_id_phys), "ltctrlsts",
                                                                 "private", flow.initial_time_stamp)
            ACM = self.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(flow.cbo_id_phys), "ltctrlsts", "inacm",
                                                             flow.initial_time_stamp)
            DisLocGuard = self.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(flow.cbo_id_phys), "ltctrlsts",
                                                                     "loc3guarddis", flow.initial_time_stamp)

            if flow.opcode in ["WBEFTOI", "WBEFTOE"]:
                # According to Leon HAS this should be HOM region.
                # legacy behavior is not like this and it seems that this was the behavior since CNL.
                # Leon said that the more correct behavior is that we will return MMIO in CCF.
                region = "MMIO"
            elif (fed2_split_addr[0] == "0x") and len(fed2_split_addr[1]) == 4 and (private == 0):
                region = "CRABABORT"
            elif (fed43_split_addr[0] == "0x") and len(fed43_split_addr[1]) == 3 and (ACM == 0) and (DisLocGuard == 0):
                region = "CRABABORT"
            elif flow.is_prd():
                region = "MMIOPTL"
            elif flow.is_wil() or flow.is_wcil() or self.is_wcilf(flow) or flow.is_crd() or flow.is_ucrdf_or_crd_uc() or flow.is_drd() or flow.is_rfo():
                region = "MMIO"
            elif self.is_itom(flow):
                if self.ccf_registers.allowitom_to_mmio[flow.cbo_id_phys]:
                    region = "MMIO"
                else:
                    region = "CRABABORT"
            elif flow.is_llcpref() or flow.is_monitor():
                region = "CRABABORT"
            elif self.is_wbmto(flow):
                region = "CRABABORT"
            elif flow.is_wbstoi():
                region = "MMIO"
            elif self.is_clflush(flow):
                if flow.is_cldemote() or self.ccf_registers.mmio_clflush_defeature[flow.cbo_id_phys] == 1 or \
                        self.ccf_registers.mmio_clflush_defeature[flow.cbo_id_phys] == 3:
                    region = "CRABABORT"
                else:
                    region = "MMIO"
            else:
                self.sample_cov = 0
                err_msg = "there is no sad result option for flow " + flow.uri["TID"] + " " + flow.opcode + " " + flow.sad_results + " " + sub_region
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            if self.sample_cov == 1:
                sad_change_cg.sample(origin_region="LT",
                                     final_region=region,
                                     flow_opcode=flow.opcode)
        else:
            region = self.simple_mmio_sad(flow)
        if "DRAM" in region:
            return "DRAM"
        if "MMIO" in region and not "MMIOPTL" in region:
            return "MMIO"
        return region

    def dram_sad_change(self, flow: ccf_flow, region, sub_region):
        sad_change_cg = SAD_CHANGE_CG.get_pointer()
        if (sub_region is not None and "PAM" in sub_region):

            pam_num = sub_region.split("PAM")[1]
            pam_num = int(pam_num.split("_")[0])

            # PAM HI/LOW
            pam_field_str = "loenable"
            if "HI" in sub_region or pam_num == 0:
                pam_field_str = "hienable"

            pam_normal_dram_operation = self.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(flow.cbo_id_phys),
                                                                                   "pam" + str(pam_num) + "_0_0_0_pci",
                                                                                   pam_field_str,
                                                                                   flow.initial_time_stamp)

            if pam_normal_dram_operation == 3:
                region = "DRAM"
            else:
                if flow.is_prd():
                    region = "MMIOPTL"
                elif flow.is_wil() or flow.is_wcil() or self.is_wcilf(flow) or flow.is_crd() or flow.is_ucrdf_or_crd_uc() or flow.is_drd() or flow.is_rfo() or\
                        flow.is_wbeftoi() or flow.is_wbeftoe() or flow.is_wbstoi():
                    region = "MMIO"
                elif self.is_itom(flow):
                    if self.ccf_registers.allowitom_to_mmio[flow.cbo_id_phys] == 1:
                        region = "MMIO"
                    else:
                        region = "CRABABORT"
                elif flow.is_llcpref() or self.is_wbmto(flow) or flow.is_monitor():
                    region = "CRABABORT"
                elif self.is_clflush(flow):
                    region = "DRAM"
                else:
                    self.sample_cov = 0
                    err_msg = "there is no sad result option for flow " + flow.uri[
                        "TID"] + " " + flow.opcode + " " + flow.sad_results + " " + sub_region
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            if self.sample_cov == 1:
                sad_change_cg.sample(origin_region="PAM",
                                     final_region=region,
                                     flow_opcode=flow.opcode)

        elif (sub_region is not None and "ISA" in region):
            if self.ccf_registers.isa_hole_en[flow.cbo_id_phys] == 0:
                return "DRAM"
            if flow.is_prd():
                region = "MMIOPTL"
            elif flow.is_wil() or flow.is_wcil() or self.is_wcilf(
                    flow) or flow.is_crd() or flow.is_ucrdf_or_crd_uc() or flow.is_drd() or flow.is_rfo():
                region = "MMIO"
            elif self.is_itom(flow):
                if self.ccf_registers.allowitom_to_mmio[flow.cbo_id_phys]:
                    region = "MMIO"
                else:
                    region = "CRABABORT"
            elif flow.is_wbeftoi() or flow.is_wbeftoe() or flow.is_wbstoi():
                region = "MMIO"
            elif flow.is_llcpref() or flow.is_monitor() or self.is_clflush(flow) or self.is_wbmto(
                    flow):
                region = "CRABABORT"
            else:
                self.sample_cov = 0
                err_msg = "there is no sad result option for flow " + flow.uri[
                    "TID"] + " " + flow.opcode + " " + flow.sad_results + " " + sub_region
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            if self.sample_cov == 1:
                sad_change_cg.sample(origin_region="ISA",
                                     final_region=region,
                                     flow_opcode=flow.opcode)


        elif (sub_region is not None and (("SMM" in sub_region) or ("VGAGSA" == region))):
            if flow.is_prd():
                region = "MMIOPTL"
            elif flow.is_wil() or self.is_wcilf(
                    flow) or flow.is_wcil() or flow.is_ucrdf_or_crd_uc() or flow.is_wbeftoi() or flow.is_wbeftoe():
                region = "MMIO"
            else:
                region = "CRABABORT"

            if self.sample_cov == 1:
                if sub_region is not None and ("SMM" in sub_region):
                    sad_change_cg.sample(origin_region="SMM",
                                         final_region=region,
                                         flow_opcode=flow.opcode)
                else:
                    sad_change_cg.sample(origin_region="VGAGSA",
                                         final_region=region,
                                         flow_opcode=flow.opcode)

        if region == "GSM":
            if flow.is_idi_flow_origin():
                region = "CRABABORT"
            else:
                region = "DRAM"

        if region in ["DOS", "DPR", "TSEG", "-"]:
            region = "DRAM"
        if region in ["IMR0", "IMR1"]:
            region = "CRABABORT"
        if "DRAM" in region:
            return "DRAM"
        if "MMIO" in region:
            return "MMIO"
        return region

    def get_region(self, flow: ccf_flow):
        if flow.is_lock_or_unlock() or flow.is_spcyc():
            return self.lock_sad_change(flow)

        bin_addr = bint(int(flow.address, 16))
        addr_without_mktme = str(hex(bin_addr[CCF_COH_DEFINES.mktme_lsb - 1:0]))
        addr = int(addr_without_mktme, 16)

        if self.si.is_nem_test == 1:
            if flow.is_wbmtoe() or flow.is_wbmtoi():
                region = "DRAM"
                memory_space = "DRAM"
                sub_region = "DRAM"
            else:
                region = "MMIO"
                memory_space = "MMIO"
                sub_region = "MMIO"
        else:
            region = self.ccf_sm_db.get_region(addr)
            memory_space = self.ccf_sm_db.get_memory_space(addr)
            sub_region = self.ccf_sm_db.get_sub_region(addr)

        if region == "CRAB_ABORT":
           return "CRABABORT"
        if flow.is_snoop_opcode():
            return "DRAM"
        if "MMIO" in memory_space:
            return self.mmio_sad_change(flow, region, sub_region)
        else:
            return self.dram_sad_change(flow, region, sub_region)


    def override_region_result(self,flow: ccf_flow, region_result, is_pam, is_mem, is_pcie_cfg):
    #in some cases the resulted region we calculated can be overrided by chicken bits etc
        #Override region based on sadisalwayshom
        sad_always_hom = self.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(flow.cbo_id_phys), "cbregs_spare", "sadalwaystohom",flow.first_accept_time) == 1
        # Bug in CLFLUSH and CLFLUSH_OPT, WIL CLDEMOTE and maybe other flows  dont work with this CB HSD: 13010093760
        # The bug is even when RTL calculates CRAB or NA it does not override - should be fixed in PTL
        mmio_crab = is_mem and (self.is_itom(flow) or flow.is_llcpref() or self.is_wbmto(flow) or flow.is_monitor() or
                                ((self.si.pciexbar_en == 0) and is_pcie_cfg and (flow.is_clflush() or flow.is_clflush_opt() or flow.is_clwb())))
        if (sad_always_hom and ((region_result not in ["CRABABORT","NA"]) or is_pam or mmio_crab)):
            return "DRAM"
        else:
            return region_result

    def is_0x8(self, flow: ccf_flow):
        address_bint = bint(int(flow.address, 16))
        return hex(address_bint[31:28]) == "0x8"

    def is_LT(self, flow: ccf_flow):
        address_bint = bint(int(flow.address, 16))
        is_fed = (hex(address_bint[31:20]) == CCF_COH_DEFINES.LT_region_prefix)
        offset = hex(address_bint[19:0])
        return is_fed and (int(CCF_COH_DEFINES.LT_LOW_OFFSET, 16) <= int(offset, 16) <= int(CCF_COH_DEFINES.LT_HIGH_OFFSET, 16))


    def sad_chk(self, flow: ccf_flow):
        if flow.is_llc_special_opcode():
            if flow.sad_results != "HOM":  # We will only check here that the SAD result of the first cycle is HOM as expected.
                err_msg = "flow {} URI {} expect to be HOM on it's first cycle".format(flow.opcode, flow.uri["TID"])
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return

        if flow.is_addressless_opcode() and not flow.is_lock_or_unlock() and not flow.is_spcyc():
            if flow.is_portin() or flow.is_portout(): #crab_abourt IO is also MMIO
                if self.is_0x8(flow):
                    if not flow.is_cfg():
                        err_msg = "flow {} URI {}  is expected to be CFG and not {}".format(flow.opcode, flow.uri["TID"], flow.sad_results)
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                elif self.is_LT(flow):
                    if not flow.is_sad_lt(): #can be CRABABORT
                        err_msg = "flow {} URI {}  is expected to be LT and not {}".format(flow.opcode, flow.uri["TID"], flow.sad_results)
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                elif not flow.is_sad_io():
                    err_msg = "flow {} URI {}  is expected to be IO and not {}".format(flow.opcode, flow.uri["TID"], flow.sad_results)
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            if flow.flow_is_hom() or flow.flow_is_crababort():
                err_msg = "flow {} URI {}  is not expected to be {}".format(flow.opcode, flow.uri["TID"], flow.sad_results)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return
        if flow.is_spcyc():
            if flow.get_address(msb=11, lsb=6) != 0:
                if not flow.flow_is_crababort():
                    err_msg = "flow {} URI {}  is not expected to be {}".format(flow.opcode, flow.uri["TID"],
                                                                                flow.sad_results)
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return




        bin_mask = bint(self.si.ccf_mktme_mask)
        bin_addr = bint(int(flow.address, 16))
        mktme_bits = bin_addr[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.mktme_lsb]
        mktme_crab = ((bin_mask & mktme_bits) != 0)
        addr = int(bin_addr[CCF_COH_DEFINES.mktme_lsb - 1:0])
        sub_region = self.ccf_sm_db.get_sub_region(addr)
        memory_space = self.ccf_sm_db.get_memory_space(addr)
        region = self.ccf_sm_db.get_region(addr)

        is_pam = (sub_region is not None) and ("PAM" in sub_region)
        is_mem = (memory_space is not None) and ("MMIO" in memory_space) and (self.ccf_sm_db.get_region(bin_addr) != "CRAB_ABORT")

        is_pcie_cfg = (region is not None) and "PCIE" in region
        if flow.is_victim():
            if is_mem:
                msg = "flow {} URI {} is MMIO but Victim is sent".format(
                    flow.opcode, flow.uri["TID"])
                VAL_UTDB_MSG(time=flow.initial_time_stamp, msg=msg) # this is nor an error. victim is always hom. and we can preload MMIO data to llc
            return

        region_result = self.get_region(flow)  # calculate
        region = self.override_region_result(flow,region_result, is_pam, is_mem, is_pcie_cfg)

        # memlockcpu is not POR in LNl
        # if (self.ccf_registers.lt_memlockcpu[flow.cbo_id_phys] == 1) and flow.is_idi_flow_origin() and (("DRAM" in region) or (sub_region is not None and "PAM" in sub_region)): #HSD - https://hsdes.intel.com/appstore/article/#/1309920771
        #     region = "CRABABORT"

        if (not flow.is_addressless_opcode()) and mktme_crab and not flow.flow_is_crababort():
            err_msg = "flow {} URI {} expect CRABABORT: mktme mask is {} while flow mktme bits are {}, sad should be CRABABORT and not {}".format(
                flow.opcode, flow.uri["TID"], str(self.si.ccf_mktme_mask), str(mktme_bits), flow.sad_results)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

        if flow.flow_is_hom():
            if "DRAM" not in region:
                err_msg = "sad_chk rtl actual DRAM: flow {} URI {} address expected region is {}".format(flow.opcode,
                                                                                                         flow.uri["TID"],
                                                                                                         region)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif flow.is_sad_crababort():
            if (flow.is_llc_special_opcode() or flow.is_addressless_opcode()) and not flow.is_spcyc():
                err_msg = "flow {}: mktme mask is {} while flow mktme bits are {}, since this is addressless or special opcode flow we are not expecting CRABABORT".format(
                    flow.opcode, str(self.si.ccf_mktme_mask), str(mktme_bits))
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif ("CRABABORT" != region) and not mktme_crab:
                err_msg = "sad_chk rtl actual CRABABORT: flow {} URI {} address expected region is {} and mktme bits are ()".format(
                    flow.opcode, flow.uri["TID"], region, mktme_bits)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif flow.is_sad_na():
            if (region is None or "NA" != region):
                err_msg = "sad_chk rtl actual NA: flow {} URI {} address expected region is {}".format(flow.opcode, flow.uri["TID"], region)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif flow.is_mmio():
            if (region is None or "MMIO" not in region):
                err_msg = "sad_chk rtl actual MMIO:flow {} URI {} address expected region is {}".format(flow.opcode, flow.uri["TID"], region)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif flow.is_cfg():
            if (region is None or "CFG" not in region):
                err_msg = "sad_chk rtl actual CFG: flow {} URI {} address expected region is {}".format(flow.opcode, flow.uri["TID"], region)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        elif flow.is_sad_io():
            if (region is None or "IO" != region):
                err_msg = "sad_chk rtl actual IO: flow {} URI {} address expected region is {}".format(flow.opcode, flow.uri["TID"], region)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        else:
            err_msg = "sad_chk unexpected: flow {} URI {} we expect {} but address expected region is {}".format(flow.opcode, flow.uri["TID"], flow.sad_results, region)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

        if self.sample_cov:
            self.ccf_sad_cov_collect_ptr.collect_mktme_crababort_coverage(mktme_crab, region)
            if flow.is_monitor():
                self.ccf_sad_cov_collect_ptr.collect_set_monitor_coverage(region)

    def check_flow(self, flow):
        if not flow.is_flow_origin_uxi_snp():
            self.sample_cov = self.si.ccf_cov_en #each time we are entering the checker we should reset the sample_cov
            self.sad_chk(flow)
