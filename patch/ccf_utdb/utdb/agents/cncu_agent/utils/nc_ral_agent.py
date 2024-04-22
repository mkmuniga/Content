#!/usr/bin/env python3.6.3a

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
import os
from val_utdb_base_components import EOT
from val_utdb_bint import bint
from val_utdb_components import val_utdb_component
from py_ral_db import PyRalReg, PyRalCompBlock, PyRalField
from val_utdb_saola_ral import get_ral_top

from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class NC_RAL_AGENT(val_utdb_component):

    def __init__(self):
        si: NC_SI = NC_SI.get_pointer()
        self.signal_path_write = ''
        self.signal_path_read = ''
        self.write_dic ={}
        self.read_dic = {}
        if not si.soc_mode:
            osal_path = os.environ.get('WORKAREA') + '/output/' + UNIQUE_DEFINES.ip_name.lower() + '/crflow/spec2osal.' + UNIQUE_DEFINES.ip_name.lower()
            config_dict = {
                           '`NCU_PATH': "subfc_ccf.par_santa_ncu.ncu.ncu_inst",
                           '`IDIB_NCU_PATH': UNIQUE_DEFINES.ncu_inst_hdl_path
                           }
            hdl_path_root = UNIQUE_DEFINES.hdl_path_root
        else:
            osal_path = os.environ.get('MODEL_ROOT') + "/target/soc/aceroot/soc/gen/registers/OSALs/ccf" # f"{os.path.join(os.environ['MODEL_ROOT'],'target/soc/aceroot/soc/gen/registers/osxml2osal')}"
            config_dict = {
                '`NCU_C0': UNIQUE_DEFINES.ncu0_inst_hdl_path,
                '`NCU_C1': UNIQUE_DEFINES.ncu1_inst_hdl_path,
                '`NCU_C2': UNIQUE_DEFINES.ncu2_inst_hdl_path,
                '`NCU_C3': UNIQUE_DEFINES.ncu3_inst_hdl_path,
            }
            hdl_path_root = "soc_tb.soc.cbb_base"

        self.top = get_ral_top(hdl_path_root, osal_path, config_dict)

    def read_reg_field(self, block_name: str, reg_name: str, field_name: str, time: int) -> bint:
        field: PyRalField = self.get_reg_field_ptr(block_name=block_name, reg_name=reg_name, field_name=field_name)
        return bint(field.read(self.__get_read_time(time)))

    def read_reg_fields(self, block_name: str, reg_name: str, field_names: list, time: int) -> dict:
        vals = dict()
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        for field_name in field_names:
            field: PyRalField = reg.get_field_by_name(field_name)
            vals[field_name] = bint(field.read(time))
        return vals

    def read_reg(self, block_name: str, reg_name: str, time: int) -> bint:
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        return bint(reg.read(self.__get_read_time(time)))

    def get_reg_ptr(self, block_name: str, reg_name: str) -> PyRalReg:
        block: PyRalCompBlock = self.top.get_block_by_name(block_name)
        return block.get_reg_by_name(reg_name)

    def get_reg_field_ptr(self, block_name: str, reg_name: str, field_name: str) -> PyRalField:
        field: PyRalField = self.get_reg_ptr(block_name=block_name, reg_name=reg_name).get_field_by_name(field_name)
        return field

    def get_reg_field_change_times(self,block_name :str, reg_name: str, field_name: str):
        field: PyRalField = self.get_reg_ptr(block_name=block_name, reg_name=reg_name).get_field_by_name(field_name)
        return field.get_value_change_times()

    def __get_read_time(self, time):
        return 200000000000000000000 if time == EOT else time
