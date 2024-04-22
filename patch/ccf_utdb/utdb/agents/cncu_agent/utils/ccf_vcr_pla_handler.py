import yaml

from agents.cncu_agent.common.cncu_defines import GLOBAL
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES
from val_utdb_bint import bint


class VCR_PLA_REGISTER:
    def __init__(self, reg_name=None, port_id=None, vcrpla_addr=None, reg_offset=None, reg_size=None, reg_file=None, trusted=None, valid=None):
        self.reg_name = reg_name
        self.port_id = port_id
        self.vcrpla_addr = vcrpla_addr
        self.reg_offset = reg_offset
        self.trusted = trusted
        self.reg_size = reg_size
        self.reg_file = reg_file
        self.valid = valid


class VCR_PLA_HANDLER:
    __reg_list = list()

    @staticmethod
    def build():
        VCR_PLA_HANDLER.__get_vcr_pla_registers()

    @staticmethod
    def get_pla_reg(address, time):
        si = NC_SI.get_pointer()
        ral_agent = NC_RAL_AGENT.get_pointer()
        if si.vcrpla_patching_chk_en:
            for i in range(0, 8):
                patch = ral_agent.read_reg(block_name="ncdecs",
                                           reg_name=f"ncu_patchcr_vcrpla[{i}]",
                                           time=time)
                patch_valid = patch[0:0]
                if patch_valid == 0:
                    continue
                vcr_addr = patch[GLOBAL.vcr_pla_msb:0]
                vcr_addr[GLOBAL.vcr_pla_lsb-1:0] = 0
                if vcr_addr[GLOBAL.vcr_pla_msb:GLOBAL.vcr_pla_lsb] == address[GLOBAL.vcr_pla_msb:GLOBAL.vcr_pla_lsb]:
                    entry_valid = patch[1:1]
                    if entry_valid == 0:
                        return None
                    offset = bint(0)
                    offset[15:2] = patch[61:48]
                    return VCR_PLA_REGISTER(port_id=patch[47:32],
                                            vcrpla_addr=vcr_addr,
                                            reg_offset=offset,
                                            trusted=patch[21:21],
                                            valid=patch[2:2])
        for reg in VCR_PLA_HANDLER.__reg_list:
            if (reg.vcrpla_addr[GLOBAL.vcr_pla_msb:GLOBAL.vcr_pla_lsb] == address[GLOBAL.vcr_pla_msb:GLOBAL.vcr_pla_lsb] and reg.reg_size == 64) or reg.vcrpla_addr[GLOBAL.vcr_pla_msb:0] == address[GLOBAL.vcr_pla_msb:0]:
                return reg

        return None

    @staticmethod
    def __get_vcr_pla_registers():
        with open(UNIQUE_DEFINES.vcr_pla_file_path, 'r') as yaml_file:
            vcr_list = yaml.load(yaml_file, Loader=yaml.FullLoader)
            for reg, values in vcr_list.items():
                if "CCFID_{}".format(1-UNIQUE_DEFINES.ccf_id) in reg:
                    continue
                pla_reg = VCR_PLA_HANDLER.__create_pla_register(values)
                VCR_PLA_HANDLER.__reg_list.append(pla_reg)

    @staticmethod
    def __create_pla_register(values):
        pla_reg = VCR_PLA_REGISTER()
        pla_reg.port_id = bint(int(values["port_id"][2:], 16))
        pla_reg.vcrpla_addr = bint(int(values["vcr_address"][2:], 16))
        pla_reg.reg_offset = bint(int(values["offset"][2:], 16))
        pla_reg.reg_size = bint(int(values["core_size"]))
        pla_reg.trusted = int(values["trusted"])
        pla_reg.reg_file = VCR_PLA_HANDLER.__extract_block_name(values["uncore_path"])
        pla_reg.reg_name = values["uncore_name"]
        pla_reg.valid = int(values["vcr_addr_valid"])
        return pla_reg

    @staticmethod
    def __extract_block_name(uncore_path):
        path_arr = uncore_path.split("/")
        if len(path_arr) > 1:
            return path_arr[-2]
        return ""

