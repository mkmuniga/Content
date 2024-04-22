import os
from val_utdb_bint import bint
from val_utdb_components import val_utdb_component
from val_utdb_saola_ral import get_ral_top

# from agents.ccf_agent.cncu_agent.utils.nc_systeminit import NC_SI
from agents.ccf_agent.ccf_power_agent.ccf_power_utils.ccf_power_si import POWER_SI
from py_ral_db import PyRalReg, PyRalCompBlock, PyRalField


class POWER_RAL_AGENT(val_utdb_component):

    def __init__(self):
        si: POWER_SI = POWER_SI.get_pointer()
        self.signal_path_write = ''
        self.signal_path_read = ''

        self.write_dic = {}
        self.read_dic = {}
        self.top = None
        self.get_ral_top()

    def get_ral_top(self):
        if not self.si.ccf_soc_mode:
            osal_path_suffix = '/output/ccf/crflow/spec2osal.ccf'
            path_prefix = "ccf.ccf_par."
            hdl_path_root = 'ccf_tb.CCF_TOP_INST'
        else:
            osal_path_suffix = "/target/soc/aceroot/soc/gen/registers/osxml2osal"
            path_prefix = "subfc_ccf."
            hdl_path_root = "soc_tb.soc"

        base_sbo_path = "sbo_sb.sbo_sb_inst"
        base_ccf_pma_path = "ccf_pma.ccf_pma_inst"
        osal_path = os.environ.get('WORKAREA') + osal_path_suffix
        config_dict = {
            '`SBO_SB_PATH': (path_prefix + base_sbo_path),
            '`PMC_PATH': (path_prefix + base_ccf_pma_path + ".ccfpmcs")
        }
        self.top = get_ral_top(hdl_path_root=hdl_path_root, bson_path=osal_path, hdl_macro_config=config_dict)

    def read_all_reg_field_changes(self, block_name: str, reg_name: str, field_name: str):
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        field: PyRalField = reg.get_field_by_name(field_name)
        return field.read_all(x_to_0=True)

    def read_all_reg_changes(self, block_name: str, reg_name: str):
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        reg_change_times = list()
        # all_field_names = list()
        fields = dict()
        reg_changes_at_time = dict()
        # field: all_field_names = reg.get_fields()
        for reg_f in reg.get_fields():
            field_name = reg_f.Name
            print(field_name)
            fields[field_name] = reg_f
            # all_field_names.append(reg_f.get_full_name)
        reg_change_times = reg.get_value_change_times()
        for time in reg_change_times:
            print(time)
            feild_values_at_time = dict()
            for field_name in fields.keys():
                # val = fields[field_name].read(time,True)
                feild_values_at_time[field_name] = fields[field_name].read(time,True)
                # print(time, field_name, val)
                # reg.get_field_by_name(reg_f)
            reg_changes_at_time[time] = feild_values_at_time
        # field: PyRalField = reg.get_field_by_name(field_name)
        return reg_changes_at_time

    def read_reg_field(self, block_name: str, reg_name: str, field_name: str, time: int) -> bint:
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        field: PyRalField = reg.get_field_by_name(field_name)
        return bint(field.read(time))

    def read_reg(self, block_name: str, reg_name: str, time: int) -> bint:
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        return bint(reg.read(time))

    def get_reg_change_time_for_later_event(self, block_name: str, reg_name: str, event_time: int, max_time_delta: int = None) -> bint:
        reg: PyRalReg = self.get_reg_ptr(block_name=block_name, reg_name=reg_name)
        first_reg_change_time = None
        reg_change_times = reg.get_value_change_times()
        for time_changed in reg_change_times:
            if time_changed >= event_time:
                if max_time_delta is not None:
                    time_delta = time_changed - event_time
                    if time_delta > max_time_delta:
                        first_reg_change_time = event_time
                        break
                first_reg_change_time = time_changed
                break
        if first_reg_change_time is None:
            first_reg_change_time = event_time
        # print("event_time", event_time, "first_change_time", first_reg_change_time, "diff", first_reg_change_time - event_time, reg_change_times)
        return first_reg_change_time

    def get_reg_ptr(self, block_name: str, reg_name: str) -> PyRalReg:
        block: PyRalCompBlock = self.top.get_block_by_name(block_name)
        return block.get_reg_by_name(reg_name)
