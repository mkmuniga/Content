import yaml

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import str_to_bytes
from agents.cncu_agent.common.cncu_defines import GLOBAL, BAR, IDI
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES
from val_utdb_bint import bint


class MMIO_PATCH_ACTION:
    abort0 = 0x1
    abort1 = 0x2
    data_mask = 0x3
    abort_dw = 0x4

class MMIO_PATCH_DETECT_TYPE:
    IO = 0
    CFG = 0x1
    MMIO = 0x2
    BAR = 0x3


class MMIO_PATCHING_HANDLER:
    patch_control = list()

    @staticmethod
    def __get_patching_configurations(time):
        MMIO_PATCHING_HANDLER.num_of_patches = 4

        ral_agent = NC_RAL_AGENT.get_pointer()
        patch_control = list()
        patch_addr_mask = list()
        patch_data_or_mask = list()
        patch_data_and_mask = list()

        for i in reversed(range(MMIO_PATCHING_HANDLER.num_of_patches)):
            patch_control.append(ral_agent.read_reg(block_name="ncdecs",
                                                    reg_name=f"mmio_patching_controls[{i}]",
                                                    time=time))

            patch_addr_mask.append(ral_agent.read_reg(block_name="ncdecs",
                                                      reg_name=f"mmio_patching_address_mask[{i}]",
                                                      time=time))

            patch_data_or_mask_reg = ral_agent.read_reg(block_name="ncdecs",
                                                      reg_name=f"mmio_patching_data_or_mask[{i}]",
                                                      time=time)

            patch_data_and_mask_reg = ral_agent.read_reg(block_name="ncdecs",
                                                      reg_name=f"mmio_patching_data_and_mask[{i}]",
                                                      time=time)

            for j in range(1, 8):
                patch_data_and_mask_reg[64*j+63:64*j] = patch_data_and_mask_reg[63:0]
                patch_data_or_mask_reg[64*j+63:64*j] = patch_data_or_mask_reg[63:0]

            patch_data_and_mask.append(patch_data_and_mask_reg)
            patch_data_or_mask.append(patch_data_or_mask_reg)

        return patch_control, patch_addr_mask, patch_data_or_mask, patch_data_and_mask


    @staticmethod
    def get_mmio_patching_detection_and_action(addr, opcode, time):
        patch_control, patch_addr_mask, patch_data_or_mask, patch_data_and_mask = MMIO_PATCHING_HANDLER.__get_patching_configurations(time)

        is_read = opcode in [IDI.OPCODES.prd,
                             IDI.OPCODES.crd,
                             IDI.OPCODES.crd_pref,
                             IDI.OPCODES.crd_uc,
                             IDI.OPCODES.drd,
                             IDI.OPCODES.drd_opt,
                             IDI.OPCODES.drd_ns,
                             IDI.OPCODES.drd_pref,
                             IDI.OPCODES.drd_opt_pref,
                             IDI.OPCODES.rdcurr,
                             IDI.OPCODES.drdpte,
                             IDI.OPCODES.rfo,
                             IDI.OPCODES.rfo_pref,
                             IDI.OPCODES.ucrdf,
                             IDI.OPCODES.port_in]

        hit_bar_name = CNCU_UTILS.get_match_bar(addr)

        for i, patch in enumerate(patch_control):
            clean_addr = addr
            if not is_read:
                clean_addr[1:0] = 0
            patch_detect_type = patch[4:3]
            patch_action = patch[63:61]

            detect_valid = patch[0:0] == 1
            detect_rw = (is_read and patch[1:1] == 1) or (not is_read and patch[2:2] == 1)
            detect_type_mmio = patch_detect_type == MMIO_PATCH_DETECT_TYPE.MMIO and CNCU_UTILS.is_idi_mmio_access_flow(
                addr, opcode)
            detect_type_cfg = patch_detect_type == MMIO_PATCH_DETECT_TYPE.CFG and CNCU_UTILS.is_idi_cfg_access_flow(
                addr, opcode) and patch_action != MMIO_PATCH_ACTION.abort_dw
            detect_type_io = patch_detect_type == MMIO_PATCH_DETECT_TYPE.IO and CNCU_UTILS.is_idi_funny_io_access_flow(
                opcode) and patch_action != MMIO_PATCH_ACTION.abort_dw
            detect_type_bar = patch_detect_type == MMIO_PATCH_DETECT_TYPE.BAR and patch[7:5] == BAR.get_bar(
                hit_bar_name) and patch[12:8] == BAR.get_device(hit_bar_name)
            detect_addr = (clean_addr & patch_addr_mask[i]) == patch[13 + GLOBAL.mktme_lsb-1:13]
            detect_type = (detect_addr and (detect_type_mmio or detect_type_cfg or detect_type_io)) or detect_type_bar

            if detect_valid and detect_rw and detect_type:
                return patch_detect_type, patch_action, patch_data_or_mask[i], patch_data_and_mask[i]

        return None, None, None, None

    @staticmethod
    def mask_data_idi(flat_data, data, mmio_patch_and_mask, mmio_patch_or_mask):
        returned_data = list()
        masked_data = str(hex((flat_data & mmio_patch_and_mask) | mmio_patch_or_mask))[2:]
        masked_data_bytes = str_to_bytes(masked_data)
        for i, byte in enumerate(masked_data_bytes[:32]):
            masked_data_bytes[i] = None if data[0][i] is None else byte
        returned_data.append(masked_data_bytes[:32])
        for i, byte in enumerate(masked_data_bytes[32:]):
            masked_data_bytes[i+32] = None if data[1][i] is None else byte
        returned_data.append(masked_data_bytes[32:])
        return returned_data

    @staticmethod
    def mask_data_sb(flat_data, be, mmio_patch_and_mask, mmio_patch_or_mask):
        amount_of_bytes = 0
        for n in range(8):
            if be[n] != 0:
                amount_of_bytes = n

        returned_data = [bint(0) for i in range(amount_of_bytes)]

        masked_data = str_to_bytes(str((flat_data & mmio_patch_and_mask) | mmio_patch_or_mask))

        for i, data in enumerate(masked_data):
            returned_data[i] = data
        return returned_data

