#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_ral_chk.py
#
# Owner:              ekupietz
# Creation Date:      10.2020
#
# ###############################################
#
# Description:
#   This file contain all ccf ral checkers
#################################################################################################
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG, EOT
from val_utdb_ral import val_utdb_ral
from val_utdb_components import val_utdb_component
from py_ral_db import PyRalDb, PyRalReg, PyRalCompBlock, PyRalField, PyRalSystemBlock
from agents.ccf_common_base.ccf_cbregs_all_registers_cov import ccf_cbregs_all_registers_cov
from agents.ccf_common_base.ccf_egress_registers_cov import ccf_egress_registers_cov
from agents.ccf_common_base.ccf_ingress_registers_cov import ccf_ingress_registers_cov
from agents.ccf_common_base.ccf_ncdecs_registers_cov import ccf_ncdecs_registers_cov

from val_utdb_saola_ral import get_ral_top


class ccf_ral_agent(val_utdb_component):

    def __init__(self):
        self.ccf_pp_params = ccf_pp_params.get_pointer()
        self.ral_inst = val_utdb_ral.initial(self.ccf_pp_params.params["ral_json"], "registers_logdb")

        self.signal_path_write = ''
        self.signal_path_read = ''
        self.write_dic ={}
        self.read_dic = {}

        hdl_path_root = self.ccf_pp_params.params["MAIN_PATH"]
        config_dict = {'`CBOB0_C0_P0': self.ccf_pp_params.params["CBOB0_C0_P0"],
                       '`CBOB1_C0_P4': self.ccf_pp_params.params["CBOB1_C0_P4"],
                       '`CBOB2_C0_P8': self.ccf_pp_params.params["CBOB2_C0_P8"],
                       '`CBOB3_C0_P12': self.ccf_pp_params.params["CBOB3_C0_P12"],
                       '`CBOB4_C0_P16': self.ccf_pp_params.params["CBOB4_C0_P16"],
                       '`CBOB5_C0_P20': self.ccf_pp_params.params["CBOB5_C0_P20"],
                       '`CBOB6_C0_P24': self.ccf_pp_params.params["CBOB6_C0_P24"],
                       '`CBOB7_C0_P28': self.ccf_pp_params.params["CBOB7_C0_P28"],
                       '`CBOA0_C0_P0': self.ccf_pp_params.params["CBOA0_C0_P0"],
                       '`CBOA1_C0_P4': self.ccf_pp_params.params["CBOA1_C0_P4"],
                       '`CBOA2_C0_P8': self.ccf_pp_params.params["CBOA2_C0_P8"],
                       '`CBOA3_C0_P12': self.ccf_pp_params.params["CBOA3_C0_P12"],
                       '`CBOA4_C0_P16': self.ccf_pp_params.params["CBOA4_C0_P16"],
                       '`CBOA5_C0_P20': self.ccf_pp_params.params["CBOA5_C0_P20"],
                       '`CBOA6_C0_P24': self.ccf_pp_params.params["CBOA6_C0_P24"],
                       '`CBOA7_C0_P28': self.ccf_pp_params.params["CBOA7_C0_P28"],
                       '`NCU_C0': self.ccf_pp_params.params["NCU_C0"],
                       '`SANTA0_C0_P0': self.ccf_pp_params.params["SANTA0_C0_P0"],
                       '`SBO_C0':  self.ccf_pp_params.params["SBO_C0"],
                       '`CCF_PMA':  self.ccf_pp_params.params["CCF_PMA"]
                       }

        osal_path = self.ccf_pp_params.params["osal_path"]
        self.top = get_ral_top(hdl_path_root=hdl_path_root, bson_path=osal_path, hdl_macro_config=config_dict)

        self.block_registers_cov = {
            'ingress_'   : ccf_ingress_registers_cov.get_pointer(),
            'cbregs_all' : ccf_cbregs_all_registers_cov.get_pointer(),
            'egress'     : ccf_egress_registers_cov.get_pointer(),
            'ncdecs'     : ccf_ncdecs_registers_cov.get_pointer()
        }

    def get_block_name(self,block_name :str ):
        block_array = block_name.split('_')
        block_index = block_array[-1]
        if block_index.isnumeric():
            new_block_index = int(int(block_index)/4)
            block_array[-1] = str(new_block_index)
            new_block_name = ""
            for s in block_array:
                new_block_name += s
                new_block_name += "_"
            new_block_name = new_block_name[:-1]    
            block_name = new_block_name           
        elif block_index == "all":
            block_name += "_all" 
            
        

    def get_regs_bank_block(self, regs_bank_name) -> PyRalCompBlock:
        block_name = self.get_block_name(regs_bank_name)
        return self.top.get_block_by_name(block_name)

    def read_reg_field(self, block_name :str, reg_name: str, field_name: str, time: int, x_to_0=True) -> int:
        block: PyRalCompBlock = self.get_regs_bank_block(block_name)
        reg: PyRalReg = block.get_reg_by_name(reg_name)
        field: PyRalField = reg.get_field_by_name(field_name)
        reg_value = field.read(time, x_to_0=x_to_0)

        # sample reg_value for coverage
        cur_block = ''.join((i for i in block_name if not i.isdigit()))
        reg_name_field = '_'.join([reg_name, field_name])
        if cur_block in self.block_registers_cov.keys():
            if reg_name_field in self.block_registers_cov[cur_block].registers_cov.keys():
                self.block_registers_cov[cur_block].registers_cov[reg_name_field].sample(reg_val_cp=reg_value)

        return reg_value

    def read_reg(self, block_name :str, reg_name: str, time: int) -> int:
        block: PyRalCompBlock = self.get_regs_bank_block(block_name)
        reg: PyRalReg = block.get_reg_by_name(reg_name)
        return reg.read(time)

    # def read_reg_all(self, block_name :str, reg_name: str) -> Tuple[int,int]:
    #     block: PyRalCompBlock = self.get_regs_bank_block(block_name)
    #     reg: PyRalReg = block.get_reg_by_name(reg_name)
    #     return reg.read_all()


    def read_reg_field_at_eot(self, block_name :str, reg_name: str, field_name: str):      
        block: PyRalCompBlock = self.get_regs_bank_block(block_name)
        reg: PyRalReg = block.get_reg_by_name(reg_name)
        field: PyRalField = reg.get_field_by_name(field_name)
        return field.read(COH_GLOBAL.global_vars["END_OF_TEST"])

    def get_register_change_times(self,block_name :str, reg_name: str):
        block: PyRalCompBlock = self.get_regs_bank_block(block_name)
        reg: PyRalReg = block.get_reg_by_name(reg_name)
        return reg.get_value_change_times()

    def get_field_change_times(self,block_name :str, reg_name: str, field_name: str):
        block: PyRalCompBlock = self.get_regs_bank_block(block_name)
        reg: PyRalReg = block.get_reg_by_name(reg_name)
        field: PyRalField = reg.get_field_by_name(field_name)
        return field.get_value_change_times()

 #### using reg_tlm (not PyRal)

    def get_eot_field_value_NOT_PYRAL(self,cbo_id_phys, reg_name,field_name):
        reg_CCF_CR = self.ral_inst.get_reg_type('ccf_regs', reg_name )
        signal_path = 'ccf_regs.cbo' + str(cbo_id_phys) + '_' + reg_name
        reg_CCF_CR.sync(EOT, signal_path)
        return reg_CCF_CR[field_name].get()

    def get_field_value_at_time_NOT_PYRAL(self, cbo_id_phys,reg_name,field_name,time):
        self.reg_CCF_CR = self.ral_inst.get_reg_type('ccf_regs', reg_name)
        self.signal_path = 'ccf_regs.cbo' + str(cbo_id_phys) + '_' + reg_name
        self.reg_CCF_CR.sync(time, self.signal_path)
        return self.reg_CCF_CR[field_name].get()

    def get_reg_value_at_time_NOT_PYRAL(self, cbo_id_phys,reg_name,time):
        self.reg_CCF_CR  = self.ral_inst.get_reg_type('ccf_regs', reg_name)
        self.signal_path = 'ccf_regs.cbo' + str(cbo_id_phys) + '_' + reg_name
        self.reg_CCF_CR.sync(time, self.signal_path)
        return self.reg_CCF_CR

    def get_final_ymm_mask_NOT_PYRAL(self, cbo_id_phys):
        return self.get_eot_field_value_NOT_PYRAL(cbo_id_phys, "L3_PROTECTED_WAY", "YMM_MASK")


    def get_final_mktme_mask_NOT_PYRAL(self, cbo_id_phys):
        return self.get_eot_field_value_NOT_PYRAL(cbo_id_phys, "MKTME_KEYID_MASK", "MASK")


    def get_always_cachenear_at_specific_time_NOT_PYRAL(self, cbo_id_phys, time):
        return self.get_reg_value_at_time(cbo_id_phys, "NI_CONTROL", time)

    def get_drd_always_cachenear_at_specific_time_NOT_PYRAL(self, cbo_id_phys, time):
        reg = self.get_always_cachenear_at_specific_time_NOT_PYRAL(cbo_id_phys, time)
        return reg["DRD_ALWAYS_CN"].get()

    def get_crd_always_cachenear_at_specific_time_NOT_PYRAL(self, cbo_id_phys, time):
        reg = self.get_always_cachenear_at_specific_time_NOT_PYRAL(cbo_id_phys, time)
        return reg["DRD_ALWAYS_CN"].get()

    def get_rfo_always_cachenear_at_specific_time_NOT_PYRAL(self, cbo_id_phys, time):
        reg = self.get_always_cachenear_at_specific_time_NOT_PYRAL(cbo_id_phys, time)
        return reg["DRD_ALWAYS_CN"].get()

