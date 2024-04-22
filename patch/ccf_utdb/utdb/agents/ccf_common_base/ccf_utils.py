from val_utdb_bint import bint

from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_systeminit.ccf_systeminit import ccf_systeminit

class CCF_UTILS:
    CCF_SI = ccf_systeminit.get_pointer()
    physical_id_by_logical_id_map = {}
    logical_id_by_physical_id_map = {}
    atom_mask_bint = None

    @staticmethod
    def initial_ccf_utils(si):
        CCF_UTILS.create_core_logical_and_physical_maps()
        CCF_UTILS.atom_mask_bint = bint(CCF_UTILS.CCF_SI.atom_mask)

    @staticmethod
    def is_module_enable(core_phy_id):
        module_disable_mask_bint = bint(CCF_UTILS.CCF_SI.module_disable_mask)
        return (module_disable_mask_bint[core_phy_id] == 0)

    @staticmethod
    def get_num_of_cbo_enable():
        num_of_cbo_enable = 0
        cbo_disable_mask_bint = bint(CCF_UTILS.CCF_SI.cbo_disable_mask)
        for cbo_num in range(CCF_UTILS.CCF_SI.num_of_cbo):
            if cbo_disable_mask_bint[cbo_num] == 0:
                num_of_cbo_enable += 1
        return num_of_cbo_enable

    @staticmethod
    def is_slice_enable(core_phy_id):
        slice_disable_mask_bint = bint(CCF_UTILS.CCF_SI.cbo_disable_mask)
        return (slice_disable_mask_bint[core_phy_id] == 0)

    @staticmethod
    def get_list_of_enabled_core_phy_id():
        enabled_core_id_list = list()
        for core_id in range(CCF_UTILS.CCF_SI.num_of_cbo):
            if CCF_UTILS.is_module_enable(core_phy_id=core_id):
                enabled_core_id_list.append(core_id)
        return enabled_core_id_list

    @staticmethod
    def create_core_logical_and_physical_maps():
        next_enabled_logical = 0
        binary_cbo_disable_mask = format(CCF_UTILS.CCF_SI.cbo_disable_mask, '032b')
        next_disabled_logical = CCF_UTILS.CCF_SI.num_of_cbo - len([ones for ones in binary_cbo_disable_mask if ones == '1'])
        for cbo_num in range(CCF_UTILS.CCF_SI.num_of_cbo):
            if binary_cbo_disable_mask[::-1][cbo_num] == "1":
                logical_id = next_disabled_logical
                next_disabled_logical += 1
            else:
                logical_id = next_enabled_logical
                next_enabled_logical +=1
            CCF_UTILS.physical_id_by_logical_id_map[logical_id] = cbo_num
            CCF_UTILS.logical_id_by_physical_id_map[cbo_num] = logical_id

    @staticmethod
    def get_physical_id_by_logical_id(logical_id):
        return CCF_UTILS.physical_id_by_logical_id_map[logical_id]

    @staticmethod
    def get_logical_id_by_physical_id(physical_id):
        return CCF_UTILS.logical_id_by_physical_id_map[physical_id]

    @staticmethod
    def is_atom_module_by_physical_id(physical_id):
        return CCF_UTILS.atom_mask_bint[physical_id] == 1


    # CFI interface
    ###############
    @staticmethod
    def is_cfi_c2u_dir(interface):
        return CCF_UTILS.get_cfi_c2u_dir_str() in interface

    @staticmethod
    def is_cfi_u2c_dir(interface):
        return CCF_UTILS.get_cfi_u2c_dir_str() in interface

    @staticmethod
    def get_cfi_c2u_dir_str():
        if CCF_UTILS.CCF_SI.ccf_soc_mode:
            return "TRANSMIT"
        else:
            return "RECEIVE"

    @staticmethod
    def get_cfi_u2c_dir_str():
        if CCF_UTILS.CCF_SI.ccf_soc_mode:
            return "RECEIVE"
        else:
            return "TRANSMIT"

    # UFI interface
    ################
    @staticmethod
    def is_ufi_c2u_dir(interface):
        return CCF_UTILS.get_ufi_c2u_dir_str() in interface

    @staticmethod
    def is_ufi_u2c_dir(interface):
        return CCF_UTILS.get_ufi_u2c_dir_str() in interface

    @staticmethod
    def get_ufi_c2u_dir_str():
        return "A2F"

    @staticmethod
    def get_ufi_u2c_dir_str():
        return "F2A"

    @staticmethod
    def get_hbo_dest_id_name(hbo_id):
        if int(hbo_id) == 1:
            return "HBO_1(9)"
        else:
            return "HBO_0(8)"

    @staticmethod
    def get_santa_rsp_id_name(santa_id):
        if int(santa_id) == 1:
            return "CCF_1(11)"
        else:
            return "CCF_0(10)"

    @staticmethod
    def get_santa_name(santa_num):
        if int(santa_num) == 1:
            if CCF_UTILS.CCF_SI.ccf_soc_mode:
                return "SOC_CCF_LINK1"
            else:
                return "CCF_VC_SANTA1"
        else:
            if CCF_UTILS.CCF_SI.ccf_soc_mode:
                return "SOC_CCF_LINK0"
            else:
                return "CCF_VC_SANTA0"

    @staticmethod
    def get_ufi_name():
        return "HW_COLLECTOR_UFI_BFM"

    @staticmethod
    def get_sbo_id(sbo_id):
        if sbo_id == 1:
            return "15" #[3:0] -> "1111"
        else:
            return "14" #[3:0] -> "1110"

    @staticmethod
    def get_max_num_of_dways():
        return CCF_COH_DEFINES.max_num_of_data_ways

    @staticmethod
    def get_ufi_vc_valid_ids():
        return [0]

    @staticmethod
    def convert_addr_to_hex_format(addr: str):
        return hex(int(addr, 16))

    @staticmethod
    def covert_addr_to_str_addr(addr):
        if type(addr) != str:
            return str(hex(addr))
        elif "0x" not in addr:
            return CCF_UTILS.convert_addr_to_hex_format(addr)
        else:
            return addr

    @staticmethod
    def get_cl_align_address(addr):
        addr = CCF_UTILS.covert_addr_to_str_addr(addr)
        int_addr = bint(int(addr, 16))
        int_addr[CCF_COH_DEFINES.set_lsb - 1:0] = 0
        return str(hex(int_addr))

    @staticmethod
    def get_address_without_mktme(addr):
        addr = CCF_UTILS.covert_addr_to_str_addr(addr)
        int_addr = bint(int(addr, 16))
        int_addr[51:41] = 0 #TODO: need to remove mktme bit according to the CCF_MKTME_WIDTH systeminit parameter and not hard coded to 11.
        return str(hex(int_addr))

    @staticmethod
    def get_address_align_and_without_mktme(addr):
        addr = CCF_UTILS.covert_addr_to_str_addr(addr)
        int_addr = bint(int(addr, 16))
        int_addr[CCF_COH_DEFINES.set_lsb - 1:0] = 0
        int_addr[51:41] = 0  # TODO: need to remove mktme bit according to the CCF_MKTME_WIDTH systeminit parameter and not hard coded to 11.
        return str(hex(int_addr))

    @staticmethod
    def are_addresses_equal_without_mktme(addr_a: str, addr_b: str):
        return (bint(int(addr_a, 16))[(CCF_COH_DEFINES.mktme_lsb - 1):0]) == (bint(int(addr_b, 16))[(CCF_COH_DEFINES.mktme_lsb - 1):0])

    @staticmethod
    def are_addresses_equal_with_mktme(addr_a: str, addr_b: str, cl_align=True):
        if cl_align:
            return (bint(int(addr_a, 16))[CCF_COH_DEFINES.address_msb:CCF_COH_DEFINES.set_lsb]) == (bint(int(addr_b, 16))[CCF_COH_DEFINES.address_msb:CCF_COH_DEFINES.set_lsb])
        else:
            return (bint(int(addr_a, 16))[CCF_COH_DEFINES.address_msb:0]) == (bint(int(addr_b, 16))[CCF_COH_DEFINES.address_msb:0])
    ## Core H functions
    ###################
    @staticmethod
    def calculate_core_H_functions(address, H_function):
        # Define the bit positions for XOR
        H_func_position_xor = {"H6": [6, 8, 10, 13, 15, 18, 22, 24, 26, 28, 30, 32]}

        result = 0  # Initialize the result

        # Apply XOR operation to the specified bit positions
        for pos in H_func_position_xor[H_function]:
            result ^= address[pos]  # Subtract 1 because bit positions are 1-indexed

        return result

    @staticmethod
    def address_half_calculation(address):
        return CCF_UTILS.calculate_core_H_functions(address, "H6")
