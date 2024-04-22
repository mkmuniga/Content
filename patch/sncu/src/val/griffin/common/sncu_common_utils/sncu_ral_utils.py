#!/usr/bin/env python3.6.3

import os, sys
from jem_py_rt import jem_py_rt
from griffin_collaterals.griffin_bint import bint
from griffin_collaterals.griffin_utils import GriffinUtils
from griffin_collaterals.griffin_base_components.griffin_base_components import run_once, EOT
from griffin_collaterals.griffin_base_components.griffin_component import GriffinSingletonComponent
from py_ral_db import PyRalReg, PyRalCompBlock, PyRalField, PyRalSystemBlock, PyRalDb


@run_once
def get_ral_top(hdl_path_root, bson_path, hdl_macro_config={}, block_filter_func=lambda block_name: True) -> PyRalSystemBlock:
    # block_filter_func is an user-defined function to include specific blocks only when building RAL
    # (required to allow faster build in big models)

    def get_tlm_jem_path(path):
        if os.path.isfile(path):
            return path
        elif os.path.isfile(path + ".gz"):
            return path + ".gz"
        else:
            raise AttributeError(f'tlm_map.txt file was not found {path}')

    ral = PyRalDb()
    ral.set_block_filter(block_filter_func)
    hdl_path_root = hdl_path_root
    ral.config_hdlpath(hdl_macro_config, hdl_path_root)
    ral.build_regmodel(bson_path)
    # jem_py_rt.jem_use_register_trace(get_tlm_jem_path(os.environ["TEST_WORK_AREA"] + '/jem/tlm_map.txt'))
    jem_py_rt.jem_use_register_trace(get_tlm_jem_path(GriffinUtils.get_test_work_area() + '/jem/tlm_map.txt'))
    ral_top: PyRalSystemBlock = ral.get_regmodel()
    return ral_top


class SNCU_RAL_UTILS(GriffinSingletonComponent):

    def __init__(self):
        self.signal_path_write = ''
        self.signal_path_read = ''
        self.write_dic ={}
        self.read_dic = {}

        #osal_path = os.environ['WORKAREA'] + '/output/sncu/crflow/spec2osal.sncu/'
        osal_path = os.environ['MODEL_ROOT'] + '/target/soc/aceroot/soc/gen/registers/OSALs/sncu/'
        #hdl_path_root = 'sncu_tb'
        hdl_path_root = "soc_tb.soc"
        #config_dict = {'`SNCU_TOP': 'sncu',
        #               '`SNCU': 'sncu',
        #               '\[\]': '[0]'}
        config_dict = {
                '`SNCU_TOP': "cbb_base.par_base_fabric_sa_center.sncu.sncu_inst" ,
                '`SNCU': "cbb_base.par_base_fabric_sa_center.sncu.sncu_inst" ,
                '\[\]': '[0]'
        }
        self.top = get_ral_top(hdl_path_root, osal_path, config_dict)
        pass

    def read_reg_field(self, block_name: str, reg_name: str, field_name: str, time: int,  x_to_0=False) -> bint:
        field: PyRalField = self.get_reg_field_ptr(block_name=block_name, reg_name=reg_name, field_name=field_name)
        return bint(field.read(time, x_to_0=x_to_0))

    @staticmethod
    def get_last_change_time_of_reg_inst(reg_inst):
        return reg_inst.get_value_change_times()[-1]

    def get_last_reg_field_value(self, block_name: str, reg_name: str, field_name: str,  x_to_0=False) -> bint:
        field = self.get_reg_field_ptr(block_name, reg_name, field_name)
        last_change_time = self.get_last_change_time_of_reg_inst(field)
        return bint(field.read(last_change_time + 1, x_to_0))

    def get_last_reg_value(self, block_name: str, reg_name: str, x_to_0=False) -> bint:
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        last_change_time = self.get_last_change_time_of_reg_inst(reg)
        return bint(reg.read(last_change_time + 1, x_to_0))

    def read_reg(self, block_name: str, reg_name: str, time: int, x_to_0=False) -> bint:
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        return bint(reg.read(time, x_to_0=x_to_0))

    def get_reg_ptr(self, block_name: str, reg_name: str) -> PyRalReg:
        block: PyRalCompBlock = self.top.get_block_by_name(block_name)
        return block.get_reg_by_name(reg_name)

    def get_reg_field_ptr(self, block_name: str, reg_name: str, field_name: str) -> PyRalField:
        field: PyRalField = self.get_reg_ptr(block_name=block_name, reg_name=reg_name).get_field_by_name(field_name)
        return field

    def get_all_changes_for_field(self, register_name, field_name, block_name=None, x_to_0=False):
        value_list =[]
        field = self.get_field_by_name(register_name, field_name, block_name=block_name)
        time_list  =field.get_value_change_times()
        for time_ind in time_list:
            try:
                val = self.read_reg_field(block_name=block_name,reg_name=register_name,field_name=field_name,time=time_ind)
                value_list.append([val,time_ind])
            except:
                continue
        return value_list

    def get_field_by_name(self, register_name, field_name, block_name=None):
        register = self.get_register_by_name(register_name, block_name=block_name)
        return register.get_field_by_name(field_name)
    def get_register_by_name(self, register_name, block_name=None):
        if block_name is not None:
            return self.get_block_by_name(block_name).get_reg_by_name(register_name)
        return self.get_regmodel().get_reg_by_name(register_name)
    def get_block_by_name(self, block_name):
        return self.get_regmodel().get_block_by_name(block_name)

    @staticmethod
    def get_regmodel():
        return PyRalDb().get_regmodel()
