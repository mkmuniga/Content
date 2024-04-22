import os
from val_utdb_base_components import val_utdb_component


class ccf_pp_params(val_utdb_component):
    def __init__(self):
        self.params = dict()
        self.init_param_values()

    def init_param_values(self):
        
        #f = os.popen('cth_query --tool runtools envs CCF_ROOT')
        #self.params["ccf_root"] = f.read().strip()
        #f.close()
        self.params["test_path"] = os.environ["TEST_WORK_AREA"]
       
        if not self.si.ccf_soc_mode:
            self.params["ccf_root"] = os.environ["WORKAREA"]
            self.params["osal_path"] = self.params["ccf_root"] + '/output/ccf/crflow/spec2osal.ccf/'
            self.params["MAIN_PATH"] = "ccf_tb.CCF_TOP_INST"
            self.params["CBOB0_PATH"] = "ccf.ccf_par.cbob0.cbob_inst"
            self.params["CBOB1_PATH"] = "ccf.ccf_par.cbob1.cbob_inst"
            self.params["CBOB2_PATH"] = "ccf.ccf_par.cbob2.cbob_inst"
            self.params["CBOB3_PATH"] = "ccf.ccf_par.cbob3.cbob_inst"
            self.params["CBOB4_PATH"] = "ccf.ccf_par.cbob4.cbob_inst"
            self.params["CBOB5_PATH"] = "ccf.ccf_par.cbob5.cbob_inst"
            self.params["CBOB6_PATH"] = "ccf.ccf_par.cbob6.cbob_inst"
            self.params["CBOB7_PATH"] = "ccf.ccf_par.cbob7.cbob_inst"
            self.params["CBOB8_PATH"] = "ccf.ccf_par.cbob8.cbob_inst"
            self.params["CBOB9_PATH"] = "ccf.ccf_par.cbob9.cbob_inst"
            self.params["CBOB10_PATH"] = "ccf.ccf_par.cbob10.cbob_inst"
            self.params["CBOB11_PATH"] = "ccf.ccf_par.cbob11.cbob_inst"
            self.params["CBOA0_PATH"] = "ccf.ccf_par.cboa0.cboa_inst"
            self.params["CBOA1_PATH"] = "ccf.ccf_par.cboa1.cboa_inst"
            self.params["CBOA2_PATH"] = "ccf.ccf_par.cboa2.cboa_inst"
            self.params["CBOA3_PATH"] = "ccf.ccf_par.cboa3.cboa_inst"
            self.params["CBOA4_PATH"] = "ccf.ccf_par.cboa4.cboa_inst"
            self.params["CBOA5_PATH"] = "ccf.ccf_par.cboa5.cboa_inst"
            self.params["CBOA6_PATH"] = "ccf.ccf_par.cboa6.cboa_inst"
            self.params["CBOA7_PATH"] = "ccf.ccf_par.cboa7.cboa_inst"
            self.params["CBOA8_PATH"] = "ccf.ccf_par.cboa8.cboa_inst"
            self.params["CBOA9_PATH"] = "ccf.ccf_par.cboa9.cboa_inst"
            self.params["CBOA10_PATH"] = "ccf.ccf_par.cboa10.cboa_inst"
            self.params["CBOA11_PATH"] = "ccf.ccf_par.cboa11.cboa_inst"
            self.params["NCU_PATH"] = "ccf.ccf_par.ncu.ncu_inst"
            self.params["SANTA_PATH0"] = "ccf.ccf_par.santa0.santa0_inst"
            self.params["SANTA_PATH1"] = "ccf.ccf_par.santa1.santa1_inst"
            self.params["SBO_PATH"] = "ccf.ccf_par.sbo.sbo_inst"
            self.params["PMC_PATH"] = "ccf.ccf_par.ccf_pma.ccf_pma_inst.ccfpmcs"
        else:
            self.params["ccf_root"] = os.environ["CCF_ROOT"]
            if 'DEBUG_SOC_MODEL_PATH' in os.environ:
                self.params["osal_path"] = f"{os.path.join(os.environ['DEBUG_SOC_MODEL_PATH'],'target/soc/aceroot/soc/gen/registers/osxml2osal')}"
            else:
                self.params["osal_path"] = f"{os.path.join(os.environ['MODEL_ROOT'],'target/soc/aceroot/soc/gen/registers/OSALs/ccf')}"
            self.params["MAIN_PATH"]    = "soc_tb.soc.cbb_base"
            self.params["CBOB0_C0_P0"]  = "subfc_ccf_clst01_s0.par_ccf_cbo0.cbob"
            self.params["CBOB1_C0_P4"]  = "subfc_ccf_clst01_s0.par_ccf_cbo2.cbob"
            self.params["CBOB2_C0_P8"]  = "subfc_ccf_clst01_s1.par_ccf_cbo0.cbob"
            self.params["CBOB3_C0_P12"] = "subfc_ccf_clst01_s1.par_ccf_cbo2.cbob"
            self.params["CBOB4_C0_P16"] = "subfc_ccf_clst01_s2.par_ccf_cbo0.cbob"
            self.params["CBOB5_C0_P20"] = "subfc_ccf_clst01_s2.par_ccf_cbo2.cbob"
            self.params["CBOB6_C0_P24"] = "subfc_ccf_clst01_s3.par_ccf_cbo0.cbob"
            self.params["CBOB7_C0_P28"] = "subfc_ccf_clst01_s3.par_ccf_cbo2.cbob"
            self.params["CBOA0_C0_P0"]  = "subfc_ccf_clst01_s0.par_ccf_cbo0.cboa"
            self.params["CBOA1_C0_P4"]  = "subfc_ccf_clst01_s0.par_ccf_cbo2.cboa"
            self.params["CBOA2_C0_P8"]  = "subfc_ccf_clst01_s1.par_ccf_cbo0.cboa"
            self.params["CBOA3_C0_P12"] = "subfc_ccf_clst01_s1.par_ccf_cbo2.cboa"
            self.params["CBOA4_C0_P16"] = "subfc_ccf_clst01_s2.par_ccf_cbo0.cboa"
            self.params["CBOA5_C0_P20"] = "subfc_ccf_clst01_s2.par_ccf_cbo2.cboa"
            self.params["CBOA6_C0_P24"] = "subfc_ccf_clst01_s3.par_ccf_cbo0.cboa"
            self.params["CBOA7_C0_P28"] = "subfc_ccf_clst01_s3.par_ccf_cbo2.cboa"
            self.params["NCU_C0"] = "par_base_santa_clst0.ncu"
            self.params["SANTA0_C0_P0"] = "par_base_santa_clst0.santa0"            
            self.params["SBO_C0"] = "par_base_sbo_clst0.sbo"
            self.params["CCF_PMA"] = "par_base_fabric_sa_center.ccf_pma"
        self.params["ral_json"] = self.params["ccf_root"] + "/src/val/utdb/scripts/ccf_reg_dict.json.gz"





























