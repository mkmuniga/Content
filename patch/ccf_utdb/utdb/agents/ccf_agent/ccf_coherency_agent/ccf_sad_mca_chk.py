
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB

from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_ral_chk import ccf_ral_chk
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_agent.ccf_coherency_agent.ccf_sad_mca_cov import SAD_MCA_CG


from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG

from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from agents.ccf_analyzers.ccf_cbo_analyzer import ccf_cbo_analyzer
from agents.ccf_common_base.coh_global import COH_GLOBAL

from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.common.cncu_defines import EVENTS_TYPES, SB

from val_utdb_bint import bint
import copy

class ccf_sad_mca_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.checker_name = "ccf_sad_mca_chk"
        self.last_uri = None
        self.opcode = ""
        self.mem_region = ""
        self.sad_mca_list = []
        self.actual_sb_msg_count = {}
        self.expected_sb_msg_count = {}
        self.my_sad_mca_dict = {}
        self.cbo_mca_dict = {}
        self.ccf_sm_db = SM_DB.get_pointer()
        self.ccf_ral_chk_i = ccf_ral_chk.create()
        self.ccf_ral_agent_i = ccf_ral_agent.create()
        self.ccf_sad_mca_cg = SAD_MCA_CG.get_pointer()
        self.sad_mca_count = 0
        self.register_change_count = 0
        self.register_change_dict = {}
        self.enable_sad_err_clflush_list = []
        self.disable_sad_err_wb2mmio_on_reject_list = []
        self.disable_iagtexc_imr_saderr_code_list = []
        self.sad_corruping_err_other_list = []      #relevant for sb messager only?
        self.sad_non_corruping_err_other_list = []  #relevant for sb messager only?
        self.sad_err_wb_to_mmio_list = []
        self.sad_err_ia_access_to_gsm_list =[]
        self.disable_sad_err_list = []
        self.new_sad_err_dis_list = []
        self.monitor_mmio_sad_err_dis_list = []
        self.dis_wb2mmio_fix_list = []
        self.old_error_dict = {}
        self.old_error_time = {}
        self.ccf_registers = ccf_registers.get_pointer()
        self.ccf_addressless_db = ccf_addressless_db.get_pointer()
        self.check_this_flow = False
        self.ccf_cbo_analyzer = ccf_cbo_analyzer.get_pointer()
        self.read_register_later = False
        self.mca_old_error_clear_times = {}
        self.c6_times = None
        self.sb_db = CCF_NC_SB_DB.get_pointer()
        self.sad_mca_case = ""
        self.check_mca = True

    def should_check_flow(self, flow : ccf_flow):
        return super().should_check_flow(flow) and \
               (not (flow.opcode == "PORT_IN" or flow.opcode == "PORT_OUT" or flow.opcode == "NcMsgS" or flow.opcode == "IntLogical"
                or flow.opcode == "EOI" or flow.opcode == "NcMsgB" or "Nc" in flow.opcode or "Int" in flow.opcode or "DPTEV" in flow.opcode) and
               (ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(flow.cbo_id_phys), "cbregs_spare", "sadalwaystohom", flow.first_accept_time) == 0))


    def reset(self):
        self.read_register_later = False
        self.enable_sad_err_clflush_list = []
        self.disable_sad_err_wb2mmio_on_reject_list = []
        self.disable_iagtexc_imr_saderr_code_list = []
        self.sad_corruping_err_other_list = []
        self.sad_non_corruping_err_other_list = []
        self.sad_err_wb_to_mmio_list = []
        self.sad_err_ia_access_to_gsm_list =[]
        self.disable_sad_err_list = []
        self.new_sad_err_dis_list = []
        self.monitor_mmio_sad_err_dis_list = []
        self.should_check_cb = True
        self.expected_sb_msg_count = {x:0 for x in range(self.si.num_of_cbo)}
        self.actual_sb_msg_count = {x:0 for x in range(self.si.num_of_cbo)}
        self.check_mca = True

    def cold_reset_only(self):
        self.cbo_mca_dict = {}
        self.register_change_dict = {}
        self.old_error_dict = {}
        self.old_error_time = {}
        self.my_sad_mca_dict = {}
        self.sad_mca_list = []
        self.sad_mca_count = 0
        self.register_change_count = 0
        self.c6_times = COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"].copy()
        self.get_mca_old_error_clear_times()

    def get_mca_old_error_clear_times(self):
        for cbo_id in range(self.si.num_of_cbo):
            self.mca_old_error_clear_times[cbo_id] = []
            times = ccf_ral_agent.get_field_change_times(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id), "mc_status", "val")
            for time in times:
                if ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id), "mc_status", "val", time) == 0:
                    if self.is_not_during_c6(time):
                        self.mca_old_error_clear_times[cbo_id].append(time)


    def is_not_during_c6(self, time):
        for entry_time in self.c6_times.keys():
            if time > entry_time and time < self.c6_times[entry_time]:
                return False
        return True

    def is_sad_mca_corr_other(self,flow,opcode,mem_region,region_name,lac0_hienable):
        if opcode == "MONITOR" and "PAM" in mem_region:
            print("Monitor to mmio uri: " + flow.uri["TID"])
            self.sad_mca_case = "SETMON_TO_MMIO"
            return True
        if opcode == "MONITOR" and (("ISA" in mem_region and lac0_hienable) or ("MMIO" in mem_region or "MMIO" in region_name and "PCIE_MMCFG" not in mem_region)):
            print("Monitor to mmio uri: " + flow.uri["TID"])
            self.sad_mca_case = "SETMON_TO_MMIO"
            return True
        if opcode in ["CRD","CRD_PREF", "DRD","DRD_PREF","DRD_OPT","DRD_NS","DRD_OPT_PREF", "DRDPTE", "MONITOR", "RFO","RFO_PREF", "ITOM", "SPEC_ITOM"] and "VGA" in mem_region:
            return True
        if opcode in ["WCIL","WCIL_NS", "WCILF","WCILF_NS", "CRD_UC","DRD_UC","DRDPTE_UC", "UCRDF", "CRD","CRD_PREF", "DRD", "DRDPTE","MONITOR","RFO_PREF", "RFO", "LLCPREFCODE", "LLCPREFDATA", "LLCPREFRFO", "CLFLUSH","CLFLUSHOPT", "CLWB",
                      "CLDEMOTE","ITOM","SPEC_ITOM", "MTOWBI", "WBMTOE","DRD_PREF","DRD_OPT","DRD_NS","DRD_OPT_PREF"] and "PCIE_MMCFG" in mem_region and self.si.pciexbar_en:
            self.sad_mca_case = "ERR_MMCFG"
            return True
        if flow.snoop_rsp_m() and "GSM" in mem_region:
            return True
        if flow.snoop_rsp_m() and "CRAB_ABORT" in mem_region:
            return True

        if (opcode in ["PRD",'WIL','WILF','WCIL','WCIL_NS', 'WCILF', "WCILF_NS",'CLDEMOTE', 'CRD_UC',"CRD_PREF",'UCRDF', 'CRD', 'DRD',"DRD_PREF",
                       "DRD_OPT","DRD_NS","DRD_OPT_PREF", 'DRDPTE', 'MONITOR', 'RFO',"RFO_PREF" ,'LLCPREFCODE', 'LLCPREFDATA', 'LLCPREFRFO',
                       'CLFLUSH', 'CLFLUSHOPT','CLWB','CLDEMOTE','ITOM',"SPEC_ITOM", 'WBMTOI', 'WBMTOE', 'MEMPUSHWR','MEMPUSHWR_NS'] or (flow.original_snoop_rsp_m())) and "IMR" in mem_region:
            self.read_register_later = True
            return True
        if flow.is_flow_origin_uxi_snp() and ("MMIO" in mem_region or "MMIO" in region_name):
            self.read_register_later = True
            return True
        if "0" in flow.response_table_row:
            self.read_register_later = True
            return True
        if self.si.is_nem_test and flow.wrote_data_to_mem():
            self.read_register_later = True
            VAL_UTDB_MSG(time=flow.initial_time_stamp,
                         msg=f'nem mca for uri: ' + flow.uri["TID"])
            return True


    def is_pam_and_dram(self, region, cbo_id_phys):
        if "PAM" in region:
            pam_num = region.split("PAM")[1]
            pam_num = int(pam_num.split("_")[0])
            hi = 0
            if "HI" in region or pam_num == 0:
                hi = 1
            pam_status = self.ccf_registers.pam_normal_dram_operation[cbo_id_phys][pam_num][hi]
            return pam_status == 3
        return False

    def is_pam_not_dram(self, region, cbo_id_phys):
        if "PAM" in region:
            pam_num = region.split("PAM")[1]
            pam_num = int(pam_num.split("_")[0])
            hi = 0
            if "HI" in region or pam_num == "0":
                hi = 1
            pam_status = self.ccf_registers.pam_normal_dram_operation[cbo_id_phys][pam_num][hi]
            return pam_status != 3
        return False

    def is_sad_mca_wb2mmio(self,flow, opcode ,mem_region,region_name,lac0_hienable,nem_mode):
        if opcode in ['WBMTOI', 'WBMTOE','MEMPUSHWR','MEMPUSHWR_NS','ITOM'] and ("VGA" in mem_region):
            return True
        if (opcode in ['WBMTOI', 'WBMTOE','MEMPUSHWR','MEMPUSHWR_NS'] or flow.original_snoop_rsp_m()) and (("ISA" in mem_region  and lac0_hienable ==1) or ("MMIO" in mem_region and not nem_mode) or ("MMIO" in region_name and "CRAB_ABORT" not in mem_region and not nem_mode)):
            return True
        if (opcode in ['WBMTOI', 'WBMTOE','MEMPUSHWR','MEMPUSHWR_NS'] or flow.original_snoop_rsp_m()) and ("PAM" in mem_region):
            return True
        if opcode in ['ITOM', 'SPEC_ITOM'] and ((self.ccf_registers.allowitom_to_mmio[flow.cbo_id_phys] == 0) and (("PAM" in mem_region) or ("ISA" in mem_region) or ("MMIO" in mem_region and not nem_mode) or ("MMIO" in region_name and "CRAB_ABORT" not in mem_region and not nem_mode))):
            return True
        if flow.original_snoop_rsp_m() and "PCIE_MMCFG" in mem_region:
            return True

    def is_sad_mca_non_corr_other(self,opcode,mem_region,region_name,cbo_id,lac0_hienable):
        if opcode in ["CLFLUSH","CLFLUSHOPT","CLWB", "CLDEMOTE"] and (("ISA" in str(mem_region) and lac0_hienable == 1) or ((("MMIO" in str(mem_region)) or ("MMIO" in region_name )) and ("PCIE_MMCFG" not in str(mem_region)) and("VGA" not in mem_region) and ("CRAB_ABORT" not in mem_region))or ("VGA" in str(mem_region))) :#or ("VGA" in str(mem_region)))):
            return True

    def is_sad_mca_ia_access_2_gsm(self, opcode, mem_region):
        if opcode in ["PRD",'WIL','WILF','WCIL','WCIL_NS', 'WCILF','WCILF_NS', 'CLDEMOTE', 'CRD_UC', 'UCRDF', 'CRD',"CRD_PREF", 'DRD',"DRD_PREF","DRD_OPT","DRD_NS","DRD_OPT_PREF",'DRDPTE', 'MONITOR', 'RFO', "RFO_PREF",'LLCPREFCODE', 'LLCPREFDATA', 'LLCPREFRFO',
                           'CLFLUSH', 'CLFLUSHOPT','CLWB','CLDEMOTE','ITOM', 'SPEC_ITOM','WBMTOI', 'WBMTOE'] and "GSM" in mem_region:
            return True


    def get_sad_mca(self,flow,opcode,mem_region,region_name,cbo_id):
        sad_mca_list =[]
        mca_last_final_stamp = flow.flow_progress[-1].rec_time
        nem_mode = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id), "CBO_COH_CONFIG_CLIENT", "NEM_MODE",mca_last_final_stamp)
        self.ccf_sad_mca_cg.sample(nem_mode=str(nem_mode))
        lac0_hi_enable = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id), "lac_0_0_0_pci", "hen")
        if self.is_sad_mca_corr_other(flow,opcode,mem_region,region_name,lac0_hi_enable):
            self.ccf_sad_mca_cg.sample(sad_mca="CORRUPTING_OTHER")
            sad_mca_list.append("CORRUPTING_OTHER")
        if self.is_sad_mca_non_corr_other(opcode, mem_region, region_name,cbo_id,lac0_hi_enable):
            self.ccf_sad_mca_cg.sample(sad_mca="NON_CORRUPTING_OTHER")
            sad_mca_list.append("NON_CORRUPTING_OTHER")
        if self.is_sad_mca_wb2mmio(flow, opcode, mem_region,region_name,lac0_hi_enable,nem_mode):
            self.ccf_sad_mca_cg.sample(sad_mca="WB2MMIO")
            sad_mca_list.append("WB2MMIO")
        if self.is_sad_mca_ia_access_2_gsm(opcode,mem_region):
            self.ccf_sad_mca_cg.sample(sad_mca="IA_ACCESS_2_GSM")
            sad_mca_list.append("IA_ACCESS_2_GSM")
        return sad_mca_list

    def read_cb_reg(self):
        for i in range(self.si.num_of_cbo):
            enable_sad_err_clflush = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(i),
                                                                  "cbregs_spare", "enable_sad_err_clflush")
            # need to take off commments when we will have informations on when a flow is rejected:>When this bit is cleared (default),
            #  SAD_ERROR for WB to MMIO is reported also when the pipeline pass that detects the error is rejected.
            #  This fixes SNB bug #2993111. When set, SAD_ERROR for WB to MMIO is not reported when the pipeline pass is rejected
            disable_sad_err_wb2mmio_on_reject = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i,
                                                                           "cbregs_all" + str(i), "cbregs_spare",
                                                                             "disable_sad_err_wb2mmio_on_reject")
            disable_iagtexc_imr_saderr_code = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i,
                                                                           "cbregs_all" + str(i), "cbregs_spare",
                                                                           "disable_iaexc_imr_saderr_code")

            disable_sad_err = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(i),
                                                           "cbomcaconfig", "disable_sad_err")
            new_sad_err_dis = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(i),
                                                           "cbomcaconfig", "new_sad_err_dis")
            monitor_mmio_sad_err_dis = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(i),
                                                                    "cbomcaconfig", "monitor_mmio_sad_err_dis")
            dis_wb2mmio_fix = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(i),
                                                                    "cbregs_spare", "dis_wb2mmio_fix")
            self.enable_sad_err_clflush_list.append(enable_sad_err_clflush)
            self.disable_sad_err_wb2mmio_on_reject_list.append(disable_sad_err_wb2mmio_on_reject)
            self.disable_iagtexc_imr_saderr_code_list.append(disable_iagtexc_imr_saderr_code)
            #comment it: want to check if it should influence only on SB message?

            self.disable_sad_err_list.append(disable_sad_err)
            self.new_sad_err_dis_list.append(new_sad_err_dis)
            self.monitor_mmio_sad_err_dis_list.append(monitor_mmio_sad_err_dis)
            self.dis_wb2mmio_fix_list.append(dis_wb2mmio_fix)
    def is_flow_llc_mca(self,flow):
        mca_last_final_stamp = flow.flow_progress[-1].rec_time + 2000
        sad_err_val = hex(ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,"cbregs_all"+ str(flow.cbo_id_phys),"cbomcastat","sad_error_code", mca_last_final_stamp))[2:]
        if sad_err_val in ["0","1""2","3","4","10","12"]:
            self.check_mca = False



    def flow_sad_mca(self, flow):
            bin_addr = bint(int(flow.address, 16))
            addr_without_mktme = str(hex(bin_addr[CCF_COH_DEFINES.mktme_lsb - 1:0]))
            addr = int(addr_without_mktme, 16)
            region = self.ccf_sm_db.get_region(addr)
            region_name =self.ccf_sm_db.get_memory_space(addr)
            sub_region = self.ccf_sm_db.get_sub_region(addr)
            should_check_cb = True

            if (not self.si.is_nem_test) and ((region is None) or (sub_region is None)):
                err_msg = "(flow_sad_mca): TID- {}, region or sub_region are None, region- {}, sub_region- {}, address- {} - please check your SM".format(flow.uri['TID'], region, sub_region, flow.address)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            else:
                if "0" in flow.response_table_row:
                    should_check_cb = False
                if not self.si.is_nem_test:
                    if self.is_pam_and_dram(sub_region, flow.cbo_id_phys):
                        region = "DRAM"

                    if region == "-" or region == "MCHBAR":
                        region = self.ccf_sm_db.get_memory_space(addr)
                    #if flow.opcode in ["LLCWB", "LLCWBINV", "LLCINV"]:
                    if flow.opcode in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes_on_idi and flow.initial_cache_state != "LLC_I":
                        real_address = self.ccf_addressless_db.get_real_address_by_uri(flow.uri["TID"])
                        bin_addr = bint(int(real_address, 16))
                        addr_without_mktme = str(hex(bin_addr[CCF_COH_DEFINES.mktme_lsb -1:0]))
                        addr = int(addr_without_mktme, 16)
                        region = self.ccf_sm_db.get_region(addr)
                        region_name = self.ccf_sm_db.get_memory_space(addr)
                #if flow.opcode in ['MEMPUSHWR', 'MEMPUSHWR_NS', "WBMTOI", "WBMTOE", "WBEFTOI", "WBEFTOE"] and "DRAM" not in region_name:
                #    region = "CRABABORT"
                else:
                    if flow.opcode in ["WBMTOE","WBMTOI"]:
                        region = "DRAM"
                        region_name = "DRAM"
                    else:
                        region = "MMIO"
                        region_name = 'MMIO'
                if "PCIE_MMCFG" in region and not self.si.pciexbar_en:
                    region = "MMIO"
                    region_name = 'MMIO'
                self.is_flow_llc_mca(flow)

                self.sad_mca_list = self.get_sad_mca(flow,flow.opcode, region,region_name,flow.cbo_id_phys)


                for i in range(len(self.sad_mca_list)):
                    if self.sad_mca_list[i] is not None and should_check_cb:
                        self.collect_cb_cov(flow.cbo_id_phys)
                        self.ccf_sad_mca_cg.sample(sad_mca=str(self.sad_mca_list[i]))
                        self.sad_mca_list[i] = self.check_cb(flow.opcode,region,region_name,self.sad_mca_list[i], flow.cbo_id_phys,flow.original_snoop_rsp_m())


            my_sad_mca_list = []
            for sad_mca in self.sad_mca_list:
                if sad_mca is not None:
                    my_sad_mca_list.append(sad_mca)
            return my_sad_mca_list

    def collect_cb_cov(self,cbo_id):
            self.ccf_sad_mca_cg.sample(disable_sad_err=str(self.disable_sad_err_list[cbo_id]))
            self.ccf_sad_mca_cg.sample(new_sad_err_dis=str(self.new_sad_err_dis_list[cbo_id]))
            self.ccf_sad_mca_cg.sample(monitor_mmio_sad_err_dis=str(self.monitor_mmio_sad_err_dis_list[cbo_id]))
            self.ccf_sad_mca_cg.sample(enable_sad_err_clflush=str(self.enable_sad_err_clflush_list[cbo_id]))
            self.ccf_sad_mca_cg.sample(disable_sad_err_wb2mmio_on_reject=str(self.disable_sad_err_wb2mmio_on_reject_list[cbo_id]))
            self.ccf_sad_mca_cg.sample(disable_iagtexc_imr_saderr_code=str(self.disable_iagtexc_imr_saderr_code_list[cbo_id]))
            self.ccf_sad_mca_cg.sample(dis_wb2mmio_fix=str(self.dis_wb2mmio_fix_list[cbo_id]))
    def sad_error(self,sad_err_val):
        sad_err = ""
        if sad_err_val == "2":
            sad_err = "IA_ACCESS_2_GSM"
        elif sad_err_val in ["1","6","7","a","b","c","12","14","f","1b","14"]:
            sad_err ="CORRUPTING_OTHER"
        elif sad_err_val in ["10","11"]:
            sad_err = "NON_CORRUPTING_OTHER"
        elif sad_err_val in ["3","4","5"]:
            sad_err = "WB2MMIO"
        else:
            sad_err = None

        return sad_err
    def check_cb(self, opcode, region,region_name, sad_mca, cbo_id,snoop_rsmp_m):
        if self.disable_sad_err_list[cbo_id] == 1:
            self.ccf_sad_mca_cg.sample(disable_sad_err = "1")
            sad_mca = None
        if self.new_sad_err_dis_list[cbo_id] == 1:
            if (not (opcode == "MONITOR" and "PCIE_MMCFG" in region) or self.monitor_mmio_sad_err_dis_list[cbo_id] == 1):
                self.ccf_sad_mca_cg.sample(new_sad_err_dis = "1")
                sad_mca = None
        if self.monitor_mmio_sad_err_dis_list[cbo_id] == 1 and opcode == "MONITOR" and ("MMIO" in region or "ISA" in region or "PAM" in region or "MMIO" in region_name) and (sad_mca == "CORRUPTING_OTHER" or sad_mca == "IA_ACCESS_2_GSM") and  self.sad_mca_case == "SETMON_TO_MMIO":
            if (not (opcode == "MONITOR" and "PCIE_MMCFG" in region) or self.new_sad_err_dis_list[cbo_id] == 1):
                self.ccf_sad_mca_cg.sample(monitor_mmio_sad_err_dis = "1")
                sad_mca = None
        if self.enable_sad_err_clflush_list[cbo_id] == 0 and opcode in ["CLFLUSH","CLFLUSHOPT","CLWB", "CLDEMOTE"] and (sad_mca != "WB2MMIO"):
            self.ccf_sad_mca_cg.sample(enable_sad_err_clflush = '0')
            sad_mca = None
        ## in clfush to PAM there is no reject since sad is HOM, also U2C req are always HOM for SAD purpose (but Modiofied for MCA) so disable_sad_err_wb2mmio_on_reject_list is not relevant for HBO snoops
        if (self.disable_sad_err_wb2mmio_on_reject_list[cbo_id] == 1) and ("Snp" not in opcode) and (sad_mca == "WB2MMIO") and (snoop_rsmp_m == 1) and (self.dis_wb2mmio_fix_list[cbo_id] == 0) and not (opcode in ["CLFLUSH","CLFLUSHOPT","CLWB", "CLDEMOTE"] and "PAM" in region):
            self.ccf_sad_mca_cg.sample(disable_sad_err_wb2mmio_on_reject = '1')
            sad_mca = None
        if self.disable_iagtexc_imr_saderr_code_list[cbo_id] == 1 and "IMR" in region and sad_mca == "CORRUPTING_OTHER":
            self.ccf_sad_mca_cg.sample(disable_iagtexc_imr_saderr_code = '1')
            sad_mca = None
        return sad_mca

    def removed_cleaned_mca_errors_from_dict(self, cbo_id, new_error_time):
        if cbo_id in self.old_error_dict.keys():
            for time in self.mca_old_error_clear_times[cbo_id]:
                if (time > self.old_error_time[cbo_id]) and (time < new_error_time):
                    if cbo_id in self.old_error_dict.keys(): ## in case we already clear the old error
                        self.old_error_dict.pop(cbo_id)

    def get_old_error(self, cbo_id):
        old_sad_mca = None
        if cbo_id in self.old_error_dict.keys():
            old_sad_mca = self.old_error_dict[cbo_id]
        return old_sad_mca

    def update_old_error(self,cbo_id,sad_mca, new_error_time):
        self.old_error_dict[cbo_id] = sad_mca
        self.old_error_time[cbo_id] = copy.copy(new_error_time)

    def collect_sad_mca_case_cov(self,sad_err):
        if sad_err == "0":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_NONE = "CBO_SAD_ERR_NONE")
        if sad_err == "1":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_RSO_NO_MATCH = "CBO_SAD_ERR_RSO_NO_MATCH")
        if sad_err == "2":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_IA_TO_GSM = "CBO_SAD_ERR_IA_TO_GSM")
        if sad_err == "3":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_MMIO_MODIFIED = "CBO_SAD_ERR_MMIO_MODIFIED")
        if sad_err == "4":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_VGA_MODIFIED = "CBO_SAD_ERR_VGA_MODIFIED")
        if sad_err == "5":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_PAM_MODIFIED = "CBO_SAD_ERR_PAM_MODIFIED")
        if sad_err == "6":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_SETMON_TO_MMIO = "CBO_SAD_ERR_SETMON_TO_MMIO")
        if sad_err == "7":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_SMM_C_RD = "CBO_SAD_ERR_SMM_C_RD")
        if sad_err == "a":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_MMCFG = "CBO_SAD_ERR_MMCFG")
        if sad_err == "b":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_CRAB_RSP = "CBO_SAD_ERR_CRAB_RSP")
        if sad_err == "c":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_IA_RSP_GSM = "CBO_SAD_ERR_IA_RSP_GSM")
        if sad_err == "d":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_LLC_NO_WAY = "CBO_SAD_ERR_LLC_NO_WAY")
        if sad_err == "e":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_LLCDATA_INV_WAY = "CBO_SAD_ERR_LLCDATA_INV_WAY")
        if sad_err == "f":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_EXT_SNP_NC = "CBO_SAD_ERR_EXT_SNP_NC")
        if sad_err == "10":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_MMIO_FLUSH = "CBO_SAD_ERR_MMIO_FLUSH")
        if sad_err == "11":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_VGA_FLUSH = "CBO_SAD_ERR_VGA_FLUSH")
        if sad_err == "12":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_IA_EXC_IMR = "CBO_SAD_ERR_IA_EXC_IMR")
        if sad_err == "14":
            self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_IA_RSPM_IMR = "CBO_SAD_ERR_IA_RSPM_IMR")
        if sad_err == "16":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_PCOMMIT_TO_MMIO = "CBO_SAD_ERR_PCOMMIT_TO_MMIO")
        if sad_err == "18":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_IMR = "CBO_SAD_ERR_IMR")
        if sad_err == "1b":
             self.ccf_sad_mca_cg.sample(CBO_SAD_ERR_EVICT_IN_NEM = "CBO_SAD_ERR_EVICT_IN_NEM")



    def ccf_sad_mca_checker(self, flow, sad_mca):
            mca_last_final_stamp = flow.flow_progress[-1].rec_time + 2000
            if self.read_register_later:
                mca_last_final_stamp = mca_last_final_stamp + 10000
            cbo_id = flow.cbo_id_phys
            if not (flow.opcode == "PORT_IN" or flow.opcode == "PORT_OUT" or flow.opcode == "NcMsgS" or flow.opcode == "IntLogical"
            or flow.opcode == "EOI" or flow.opcode == "NcMsgB" or "Nc" in flow.opcode or "Int" in flow.opcode):
                            sad_err_val = hex(ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,"cbregs_all"+ str(cbo_id),"cbomcastat","sad_error_code", mca_last_final_stamp))[2:]
                            sad_err_addr = int(ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,"cbregs_all"+ str(cbo_id),"mc_addr","address", mca_last_final_stamp))*64
                            sad_err_addr = sad_err_addr + int(ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,"cbregs_all"+ str(cbo_id),"mc_addr","address_offset", mca_last_final_stamp))
                            expected_addr_bint = bint(int(flow.address,16))
                            actual_addr_bint = bint(sad_err_addr)
                            sad_err = self.sad_error(sad_err_val)
                            self.collect_sad_mca_case_cov(sad_err_val)
                            if sad_mca is not None and self.check_mca:
                                if sad_mca != sad_err:
                                    VAL_UTDB_MSG(time=mca_last_final_stamp,
                                                msg=f'actual: ' + str(sad_err) + 'and expected : ' + str(sad_mca))
                                    VAL_UTDB_ERROR(time=mca_last_final_stamp, msg=f':actual: ' + str(sad_err) + ' and expected : ' + str(sad_mca)+
                                                                      ' Wrong sad mca error for flow ' + flow.uri["TID"])
                                if actual_addr_bint[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.set_lsb] != expected_addr_bint[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.set_lsb] and not (flow.original_snoop_rsp_m() and sad_mca == "WB2MMIO"): #when sad mca is wb2mmio sur to rspM - it's errir is in the rsp pass, so later transaction sad error can be recognized first
                                   VAL_UTDB_ERROR(time=mca_last_final_stamp, msg=f':actual address: ' + str(hex(sad_err_addr)) + ' and expected : ' + str(flow.address) +
                                                                      ' Wrong logged address for sad mca flow ' + flow.uri["TID"])

                                if actual_addr_bint[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.mktme_lsb] != 0:
                                    self.ccf_sad_mca_cg.sample(mca_logged_addr="with mktme")
                                else:
                                    self.ccf_sad_mca_cg.sample(mca_logged_addr="no mktme")



    def sad_err_change_check(self,flow):
        mca_initial_time = flow.first_accept_time
        cbo_id = flow.cbo_id_phys
        sad_err_val = hex(ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id), "cbomcastat",
                                                       "sad_error_code", mca_initial_time))[2:]
        if flow.cbo_id_phys not in self.cbo_mca_dict.keys():
            if self.sad_error(sad_err_val) != None:
                self.register_change_dict[cbo_id] = 1
                self.register_change_count += 1
                print("kmoses1: cbo id: " + str(cbo_id)+ " uri: " + flow.uri["TID"])
            self.cbo_mca_dict[cbo_id] = sad_err_val
        else:
            sad_err_val_dict = self.cbo_mca_dict[cbo_id]
            # self.cbo_mca_dict[flow.cbo_id_phys] = sad_err_val

            if sad_err_val != sad_err_val_dict:

                self.cbo_mca_dict[cbo_id] = sad_err_val
                self.register_change_count += 1
                print("kmoses1: cbo id: " + str(cbo_id)+ " uri: " + flow.uri["TID"])
                if cbo_id not in self.register_change_dict.keys():
                    self.register_change_dict[cbo_id] = 1
                else:
                    self.register_change_dict[cbo_id] += 1



    def check_mc_status_update(self,flow):
        cbo_id = flow.cbo_id_phys
        pcc_field = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                            "mc_status", "pcc")
        addr_field = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                            "mc_status", "addrv")
        uc_field = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                            "mc_status", "uc")
        if pcc_field != 1 or addr_field !=1 or uc_field != 1:
            VAL_UTDB_ERROR(time= flow.initial_time_stamp,msg = ":flow : "+str(flow.uri["TID"]) + " expected mc_status fields to be equal to 1 whereas actual pcc_field = " + str(pcc_field) +
                                                               ",addr_field = " + str(addr_field)+", uc_field = " + str(uc_field))


    def check_flow_mca_list(self,flow,flow_mca_list):
        mca_last_final_stamp = flow.flow_progress[-1].rec_time
        if self.read_register_later:
            mca_last_final_stamp = mca_last_final_stamp + 10000
        cbo_id = flow.cbo_id_phys
        if not (
                flow.opcode == "PORT_IN" or flow.opcode == "PORT_OUT" or flow.opcode == "NcMsgS" or flow.opcode == "IntLogical"
                or flow.opcode == "EOI" or flow.opcode == "NcMsgB" or "Nc" in flow.opcode or "Int" in flow.opcode):
            sad_err_val = hex(
                ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id), "cbomcastat",
                                             "sad_error_code", mca_last_final_stamp))[2:]
            sad_err = self.sad_error(sad_err_val)

            if (None not in flow_mca_list) and (cbo_id not in self.my_sad_mca_dict.keys()):
                self.my_sad_mca_dict[cbo_id] = flow_mca_list[0]
                self.sad_mca_count += 1
            if sad_err not in flow_mca_list:
                VAL_UTDB_ERROR(time=mca_last_final_stamp,
                                 msg=f':actual: ' + str(sad_err) + ' and expected to be in the flow_mca_list: ' + str(flow_mca_list) + ' for flow: ' + str(flow.uri["TID"]))
            else:
                print("kmoses1: expected cbo id: " + str(cbo_id)+ " uri: " + flow.uri["TID"] + "mca: " + sad_err)


    def should_check_opcode(self, flow: ccf_flow):
        exclude_opcode_list = ["NcMsgS", "IntLogical", "NcMsgB", "DPTEV", "Nc", "Int"]
        opcode_excluded = [True for opcode in exclude_opcode_list if opcode in flow.opcode]
        return (self.si.ccf_preload_tag_correctable_errs == 0) and (self.si.ccf_preload_data_correctable_errs == 0) \
               and not opcode_excluded and not flow.is_addressless_opcode()

    def count_sb_msg_from_cbo(self):
        msgs = self.sb_db.get_trans_at_time(SB.OPCODES.mclk_event, COH_GLOBAL.global_vars["START_OF_TEST"],COH_GLOBAL.global_vars["END_OF_TEST"])
        for msg in msgs:
            msg.treated = True
            is_to_ncevents = (msg.dest_pid == SB.EPS.ncevents)
            is_mca_event = (bint(msg.data[3])[3] ==1) or (bint(msg.data[3])[6] == 1) #If mc_misc2.mce_ctl == 0 (default):Bit[30] is on Else, bit[27] = 1
            if is_to_ncevents and is_mca_event:
                for i in range(self.si.num_of_cbo):
                    if msg.src_pid == SB.EPS.cbo[i]:
                        self.actual_sb_msg_count[i] = self.actual_sb_msg_count[i] + 1

    def sb_msg_is_excepted_for_specific_error(self, errors, cbo_id, time):
        sb_msg_is_excepted_for_specific_error = []
        for error in errors:
            if error == "WB2MMIO":
                sad_err_wb_to_mmio = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                                                  "mc_ctl", "sad_err_wb_to_mmio", time)
                sb_msg_is_excepted_for_specific_error.append(sad_err_wb_to_mmio == 1)
                self.ccf_sad_mca_cg.sample(sad_err_wb_to_mmio=str(sad_err_wb_to_mmio))
            if error == "IA_ACCESS_2_GSM":
                sad_err_ia_access_to_gsm = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                                                   "mc_ctl", "sad_err_ia_access_to_gsm", time)
                sb_msg_is_excepted_for_specific_error.append(sad_err_ia_access_to_gsm == 1)
                self.ccf_sad_mca_cg.sample(sad_err_ia_access_to_gsm=str(sad_err_ia_access_to_gsm))
            if error == "CORRUPTING_OTHER":
                sad_corruping_err_other = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                                                   "mc_ctl", "sad_corruping_err_other", time)
                sb_msg_is_excepted_for_specific_error.append(sad_corruping_err_other == 1)
                self.ccf_sad_mca_cg.sample(sad_corruping_err_other=str(sad_corruping_err_other))
            if error == "NON_CORRUPTING_OTHER":
                sad_non_corruping_err_other = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "cbregs_all" + str(cbo_id),
                                                                      "mc_ctl", "sad_non_corruping_err_other", time)
                sb_msg_is_excepted_for_specific_error.append(sad_non_corruping_err_other == 1)
                self.ccf_sad_mca_cg.sample(sad_non_corruping_err_other=str(sad_non_corruping_err_other))
        return sb_msg_is_excepted_for_specific_error



    def check_flow(self, flow: ccf_flow):
        if self.should_check_opcode(flow):
            self.check_this_flow = True
            cbo_id = flow.cbo_id_phys
            flow_mca_list = self.flow_sad_mca(flow)
            for i in range(len(flow_mca_list)):
                if len(flow_mca_list) > 0 and \
                        self.sb_msg_is_excepted_for_specific_error(flow_mca_list, flow.cbo_id_phys,
                                                                   flow.first_accept_time)[i] and self.check_mca:
                    print("kmoses1: expected SB MCLK message from cbo " + str(flow.cbo_id_phys) + " due to uri " +
                          flow.uri[
                              "TID"])
                    self.expected_sb_msg_count[flow.cbo_id_phys] = self.expected_sb_msg_count[
                                                                       flow.cbo_id_phys] + 1 + flow.number_of_rejects
            if len(flow_mca_list) <= 1:
                if len(flow_mca_list) == 0:
                    sad_mca = None
                else:
                    sad_mca = flow_mca_list[0]
                if sad_mca is not None:

                    new_time = copy.copy(flow.first_accept_time)
                    self.removed_cleaned_mca_errors_from_dict(cbo_id, new_time)
                    old_sad_mca = self.get_old_error(cbo_id)
                    #self.check_mc_status_update(flow)
                    if (cbo_id not in self.my_sad_mca_dict.keys()) or ((old_sad_mca is None) and ((cbo_id in self.my_sad_mca_dict.keys()) and (self.my_sad_mca_dict[cbo_id] != sad_mca))):
                        self.my_sad_mca_dict[cbo_id] = sad_mca
                        print("kmoses1: expected cbo id: " + str(cbo_id)+ " uri: " + flow.uri["TID"]+ "mca: " + sad_mca)
                        if sad_mca != old_sad_mca:
                            self.sad_mca_count += 1
                        self.ccf_sad_mca_checker(flow, sad_mca)
                        self.update_old_error(cbo_id, sad_mca, new_time)


            else:
                self.check_flow_mca_list(flow,flow_mca_list)
            self.sad_err_change_check(flow)
        if self.last_uri == flow.uri["TID"]:
            self.count_sb_msg_from_cbo()
            for i in range(self.si.num_of_cbo):
                last_sad_err_val_cbo = hex(
                ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i, "cbregs_all" + str(i),
                                                        "cbomcastat", "sad_error_code"))[2:]
                if i not in self.register_change_dict.keys():
                    if self.sad_error(last_sad_err_val_cbo) != None:
                        self.register_change_count += 1
                        self.register_change_dict[i] = 1
                        print("kmoses1: last cbo id: " + str(i)+ " uri: " + flow.uri["TID"])
                        self.cbo_mca_dict[i] = last_sad_err_val_cbo
                else:
                    if self.cbo_mca_dict[i] != last_sad_err_val_cbo:
                        self.register_change_count += 1
                        self.register_change_dict[i] += 1
                        print("kmoses1: last cbo id: " + str(i)+ " uri: " + flow.uri["TID"])
                        self.cbo_mca_dict[i] = last_sad_err_val_cbo
            if self.check_this_flow and self.check_mca:
                for cbo_id in self.expected_sb_msg_count.keys():
                    if (self.expected_sb_msg_count[cbo_id] > 0) and (self.expected_sb_msg_count[cbo_id] < self.actual_sb_msg_count[cbo_id] or (self.actual_sb_msg_count[cbo_id] == 0)):
                        VAL_UTDB_ERROR(time= flow.initial_time_stamp, msg = ":cbo {} sent {} MCA SB Msgs while we expected {}".format(str(cbo_id), str(self.actual_sb_msg_count[cbo_id]), str(self.expected_sb_msg_count[cbo_id])))
                if self.register_change_count != self.sad_mca_count:
                    VAL_UTDB_ERROR(time= flow.initial_time_stamp, msg = ":flow: "+ str(flow.uri["TID"]) +"register_change_dict" + str(self.register_change_dict)+ "sad_mca_count not equal register_change_count: "+
                                                                        "sad_mca_count = " + str(self.sad_mca_count) +
                                                                        " whereas, register_change_count = " + str(self.register_change_count))
        self.collect_coverage()



