from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import bytes_to_str, str_to_bytes, \
    data_to_bytes, compare_trans
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION, UFI_TRANSACTION, CFI_TRANSACTION
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG

from agents.cncu_agent.common.cncu_defines import CFI, IDI, GLOBAL, BAR, TARGET_TYPE, SB


class CNCU_UTILS:

    @staticmethod
    def get_blank_data(num_of_chunks, num_of_bytes, is_filled_with_none=False):
        if num_of_chunks == 1:
            data = [bint(0) for i in range(num_of_bytes)]
        else:
            data = list()
            for i in range(num_of_chunks):
                if is_filled_with_none:
                    data.append([None for j in range(num_of_bytes)])
                else:
                    data.append([bint(0) for j in range(num_of_bytes)])
        return data

    @staticmethod
    def get_idi_data_from_cfi(data, offset, length):
        length = 1 if length == 0 else length

        read_data = [[], []]
        byte_num = 0

        for i, data_chunk in enumerate(data):
            for byte in data_chunk:
                if offset <= byte_num < offset + length:
                    read_data[i].append(byte)
                else:
                    read_data[i].append(None)
                byte_num += 1

        return read_data

    @staticmethod
    def get_idi_data_from_sb(data, offset, byte_en):
        read_data = CNCU_UTILS.get_blank_data(num_of_chunks=2, num_of_bytes=32)
        chunk_idx, data_idx = 0, offset if offset < 32 else 1, offset - 32

        for i, byte in enumerate(data):
            if byte_en[i] == 1:
                read_data[chunk_idx][data_idx] = byte

        return read_data

    @staticmethod
    def bytes_to_str(data_bytes):
        return bytes_to_str(data_bytes)

    @staticmethod
    def str_to_bytes(hex_str: str):
        return str_to_bytes(hex_str)

    @staticmethod
    def data_to_bytes(data):
        return data_to_bytes(data)

    @staticmethod
    def compare_trans(exp_tran, act_tran, class_name='NA', source='NA', print_msg=0, fail_on_mismatch=0):
        have_mismatch, msg = compare_trans(exp_tran, act_tran)
        if msg != "":
            if have_mismatch and fail_on_mismatch:
                VAL_UTDB_ERROR(class_name=class_name, source=source, time=act_tran.time, msg=msg)
            elif have_mismatch and print_msg:
                VAL_UTDB_MSG(class_name=source, source="NA", time=act_tran.time, msg=msg)
        return have_mismatch, msg

    @staticmethod
    def get_nc_flow_rctrl(ral_utils, time, pkt_type, is_interrupt=False):
        rctrl = bint(0)

        if is_interrupt and pkt_type in [CFI.PKT_TYPE.pw, CFI.PKT_TYPE.ncm]:
            rctrl[1] = ral_utils.read_reg_field(block_name="ncdecs",
                                                reg_name="NcuCfiPacketOrdering",
                                                field_name="Int_Ordering",
                                                time=time)
        elif pkt_type == CFI.PKT_TYPE.ncm:
            rctrl[1] = ral_utils.read_reg_field(block_name="ncdecs",
                                                reg_name="NcuCfiPacketOrdering",
                                                field_name="Ncm_Ordering",
                                                time=time)
        elif pkt_type == CFI.PKT_TYPE.pw:
            rctrl[1] = ral_utils.read_reg_field(block_name="ncdecs",
                                                reg_name="NcuCfiPacketOrdering",
                                                field_name="PW_Ordering",
                                                time=time)
        elif pkt_type == CFI.PKT_TYPE.pr:
            rctrl[1] = ral_utils.read_reg_field(block_name="ncdecs",
                                                reg_name="NcuCfiPacketOrdering",
                                                field_name="PR_Ordering",
                                                time=time)
        elif pkt_type == CFI.PKT_TYPE.sa_d:
            rctrl[1] = ral_utils.read_reg_field(block_name="ncdecs",
                                                reg_name="NcuCfiPacketOrdering",
                                                field_name="SA_D_Ordering",
                                                time=time)

        return rctrl

    @staticmethod
    def get_match_bar(addr):
        addr = addr[GLOBAL.addr_width-1:0]
        sm_bar = SM_DB.get_region(addr)
        si = NC_SI.get_pointer()
        if sm_bar == BAR.high_bios:
            return BAR.high_bios
        if sm_bar == BAR.lt0:
            return BAR.lt0
        if sm_bar == BAR.lt1:
            return BAR.lt1
        if sm_bar == BAR.crab_abort:
            return BAR.crab_abort
        if sm_bar == BAR.mchbar and si.mchbar_en:
            return BAR.mchbar
        if sm_bar == BAR.safbar and si.safbar_en:
            return BAR.safbar
        if sm_bar == BAR.regbar and si.regbar_en:
            return BAR.regbar
        if sm_bar == BAR.edrambar and si.edrambar_en:
            return BAR.edrambar
        if sm_bar == BAR.vtdbar and si.vtdbar_en != 0:
            vtdbar_sub = SM_DB.get_sub_region(addr)
            vtdbar_sub_num = int(vtdbar_sub[-1])
            vtdbar_abort = si.vtdbar_en[vtdbar_sub_num] == 0
            if vtdbar_abort:
                return BAR.vtdbar_abort
            return BAR.vtdbar
        if sm_bar == BAR.vgagsa and si.vgagsa_en:
            return BAR.vgagsa
        if sm_bar == BAR.tmbar and si.tmbar_en:
            return BAR.tmbar
        if sm_bar == BAR.membar2 and si.membar2_en and addr[si.membar2_size-1:0] < bint(0x1004):
            return BAR.membar2
        if sm_bar == BAR.gttmmadr and si.gttmmadr_en:
            return BAR.gttmmadr
        if sm_bar == BAR.lmembar and si.lmembar_en:
            return BAR.lmembar
        if sm_bar == BAR.sriov0 and si.sriov_en:
            return BAR.sriov0
        if sm_bar == BAR.pm_bar and si.pm_bar_en:
            return BAR.pm_bar
        if sm_bar == BAR.ipubar0 and si.ipubar_en:
            return BAR.ipubar0
        if sm_bar == BAR.ipubar2 and si.ipubar_en:
            return BAR.ipubar2
        if sm_bar == BAR.vpubar0 and si.vpubar_en:
            return BAR.vpubar0
        if sm_bar == BAR.vpubar2 and si.vpubar_en:
            return BAR.vpubar2
        if sm_bar == BAR.iaxbar0 and si.iaxbar_en:
            return BAR.iaxbar0
        if sm_bar == BAR.iaxbar2 and si.iaxbar_en:
            return BAR.iaxbar2
        return None

    @staticmethod
    def get_funnyio_0x3_match_bar(addr):
        si = NC_SI.get_pointer()
        bar = addr[26:24]
        device = addr[23:19]
        if bar == BAR.get_bar(BAR.mchbar) and device == BAR.get_device(BAR.mchbar):
            return BAR.mchbar
        if bar == BAR.get_bar(BAR.tmbar) and device == 4:
            return BAR.tmbar
        if bar == BAR.get_bar(BAR.vtdbar) and device == BAR.get_device(BAR.vtdbar):
            vtdbar_sub = SM_DB.get_sub_region_by_offset(BAR.vtdbar, addr[18:0])
            vtdbar_sub_num = int(vtdbar_sub[-1])
            vtdbar_abort = si.vtdbar_en[vtdbar_sub_num] == 0
            if vtdbar_abort:
                return BAR.vtdbar_abort
            return BAR.vtdbar
        if bar == BAR.get_bar(BAR.ipubar2) and device == BAR.get_device(BAR.ipubar2):
            return BAR.ipubar2
        if bar == BAR.get_bar(BAR.pm_bar) and device == BAR.get_device(BAR.pm_bar):
            return BAR.pm_bar
        if bar == BAR.get_bar(BAR.vpubar2) and device == BAR.get_device(BAR.vpubar2):
            return BAR.vpubar2
        if bar == BAR.get_bar(BAR.iaxbar0) and device == BAR.get_device(BAR.iaxbar0):
            return BAR.iaxbar0
        if bar == BAR.get_bar(BAR.iaxbar2) and device == BAR.get_device(BAR.iaxbar2):
            return BAR.iaxbar2
        if bar == BAR.get_bar(BAR.iaxbar2) and device == BAR.get_device(BAR.iaxbar2):
            return BAR.iaxbar2
        if bar == BAR.get_bar(BAR.membar2) and device == BAR.get_device(BAR.membar2):
            return BAR.membar2
        return None

    @staticmethod
    def is_nc_sb_target(addr, opcode, initial_tran_time):
        return CNCU_UTILS.is_funnyio_sb_target(addr, opcode, initial_tran_time) or \
               (CNCU_UTILS.is_idi_cfg_access_flow(addr, opcode) and CNCU_UTILS.is_cfg_sb_target(addr, initial_tran_time)) or \
               CNCU_UTILS.is_mmio_sb_target(addr, opcode)

    @staticmethod
    def is_funnyio_sb_target(addr, opcode, initial_tran_time):
        if not CNCU_UTILS.is_idi_funny_io_access_flow(opcode):
            return False
        funnyio_type = addr[31:28]
        if funnyio_type in [0x1, 0x2, 0x4, 0x5, 0x6]:
            return True
        elif funnyio_type == 0x3:
            match = CNCU_UTILS.get_funnyio_0x3_match_bar(addr)
            if match in [BAR.mchbar, BAR.tmbar, BAR.pm_bar, BAR.membar2, BAR.vtdbar_abort]:
                return True
        elif funnyio_type == 0x8:
            if CNCU_UTILS.is_cfg_sb_target(addr, initial_tran_time):
                return True
        return False

    @staticmethod
    def is_cfg_sb_target(addr, initial_tran_time):
        new_addr = CNCU_UTILS.get_clean_cfg_address(addr)
        bus = new_addr[27:20]
        dev = new_addr[19:15]
        func = new_addr[14:12]
        if bus == 0 and func == 0:
            if dev in [0, 10, 14]:
                return True
            if CNCU_UTILS.is_cfg_shadow_offset(new_addr, dev, initial_tran_time):
                return True
        return False

    @staticmethod
    def get_clean_cfg_address(addr):
        si = NC_SI.get_pointer()
        new_addr = addr[GLOBAL.addr_width-1:0]
        if si.mmcfgbar_en:
            if si.mmcfgbar_size == 0:
                new_addr[35:28] = 0
            elif si.mmcfgbar_size == 1:
                new_addr[35:29] = 0
            elif si.mmcfgbar_size == 2:
                new_addr[35:30] = 0
            elif si.mmcfgbar_size == 3:
                new_addr[35:31] = 0
            elif si.mmcfgbar_size == 4:
                new_addr[35:32] = 0
            elif si.mmcfgbar_size == 5:
                new_addr[35:33] = 0
            elif si.mmcfgbar_size == 6:
                new_addr[35:34] = 0
            elif si.mmcfgbar_size == 7:
                new_addr[35:35] = 0
        return new_addr

    @staticmethod
    def is_cfg_shadow_offset(addr, device, initial_tran_time):
        offset = bint(0x0)
        offset[11:2] = addr[11:2]
        si = NC_SI.get_pointer()

        always_shadow = CNCU_UTILS.is_always_cfg_shadow(device, initial_tran_time)

        is_dev2_shadow = (
                (device == 2 and si.dev_en[2] == 1) and (
                    offset in [0x4, 0xd4, 0x78, 0x328, 0x330, 0x10, 0x14, 0x18, 0x1c, 0x344, 0x348] or always_shadow))
        is_dev4_shadow = (device == 4 and si.dev_en[4] == 1) and (offset in [0x4, 0xd4, 0x10, 0x14] or always_shadow)
        is_dev5_shadow = (device == 5 and si.dev_en[5] == 1) and (offset in [0x4, 0x84, 0x48, 0x10, 0x14, 0x20, 0x24] or always_shadow)
        is_dev11_shadow = (device == 11 and si.dev_en[11] == 1) and (offset in [0x4, 0x84, 0x48, 0x10, 0x14, 0x20, 0x24] or always_shadow)
        is_dev12_shadow = (device == 12 and si.dev_en[12] == 1) and (offset in [0x4, 0x94, 0x48, 0x10, 0x14, 0x18, 0x1c] or always_shadow)

        if is_dev2_shadow or is_dev4_shadow or is_dev5_shadow or is_dev11_shadow or is_dev12_shadow:
            return True
        return False

    @staticmethod
    def is_always_cfg_shadow(device, time):
        ral_agent = NC_RAL_AGENT.get_pointer()

        field = ""
        if device == 2:
            field = "always_shadowmcast_dev2"
        elif device == 4:
            field = "always_shadowmcast_dev4"
        elif device == 5:
            field = "always_shadowmcast_dev5"
        elif device == 11:
            field = "always_shadowmcast_dev11"
        elif device == 12:
            field = "always_shadowmcast_dev12"
        else:
            return False

        return ral_agent.read_reg_field(block_name="ncdecs", reg_name="NCRADECS_OVRD", field_name=field,
                                             time=time) == 1

    @staticmethod
    def is_mmio_sb_target(addr, opcode):
        match = CNCU_UTILS.get_match_bar(addr)
        return opcode not in [IDI.OPCODES.port_in, IDI.OPCODES.port_out] and \
               (match in [BAR.mchbar,
                       BAR.safbar,
                       BAR.regbar,
                       BAR.edrambar,
                       BAR.tmbar,
                       BAR.pm_bar,
                       BAR.membar2,
                       BAR.vtdbar_abort])

    @staticmethod
    def is_in_mmio_low_range(address):
        si = NC_SI.get_pointer()
        return si.tolud <= address[GLOBAL.addr_width-1:0] <= GLOBAL.top_mmio_low_addr and \
               not SM_DB.is_address_inside_region(address, BAR.mmcfgbar)

    @staticmethod
    def is_in_mmio_high_range(address):
        si = NC_SI.get_pointer()
        mmio_high_hit = address[GLOBAL.addr_width-1:0] >= si.touud if si.dram_high_en else address[GLOBAL.addr_width-1:0] > GLOBAL.top_mmio_low_addr
        return mmio_high_hit and \
               not SM_DB.is_address_inside_region(address, BAR.mmcfgbar)

    @staticmethod
    def is_in_mmio_range(address):
        return CNCU_UTILS.is_in_mmio_low_range(address) or \
               CNCU_UTILS.is_in_mmio_high_range(address) or \
               SM_DB.get_region(address) == BAR.vgagsa

    @staticmethod
    def is_idi_mmio_access_flow(address, opcode):
        return opcode not in [IDI.OPCODES.port_out, IDI.OPCODES.port_in, IDI.OPCODES.spcyc, IDI.OPCODES.enqueue] and \
               CNCU_UTILS.is_in_mmio_range(address) and not CNCU_UTILS.is_idi_lock_flow(opcode) and \
               not CNCU_UTILS.is_idi_interrupt_flow(address, opcode)

    @staticmethod
    def is_idi_cfg_access_flow(address, opcode):
        si = NC_SI.get_pointer()
        return opcode in [IDI.OPCODES.wil, IDI.OPCODES.prd] and si.mmcfgbar_value <= address < si.mmio_h_base

    @staticmethod
    def is_idi_funny_io_access_flow(opcode):
        return opcode in [IDI.OPCODES.port_out, IDI.OPCODES.port_in]

    @staticmethod
    def is_idi_interrupt_flow(address, opcode):
        return (opcode in [IDI.OPCODES.int_prio_up, IDI.OPCODES.inta, IDI.OPCODES.eoi, IDI.OPCODES.dpt,
                           IDI.OPCODES.int_physical, IDI.OPCODES.int_logical]) or \
               (opcode == IDI.OPCODES.port_out and address[31:8] == GLOBAL.lt_doorbell_base_addr)

    @staticmethod
    def is_interrupt_for_rctrl(address, opcode):
        return (opcode in [IDI.OPCODES.int_physical, IDI.OPCODES.int_logical]) or \
               (opcode == IDI.OPCODES.port_out and
                address[31:8] == GLOBAL.lt_doorbell_base_addr)

    @staticmethod
    def is_idi_lock_flow(opcode):
        return opcode in [IDI.OPCODES.lock, IDI.OPCODES.split_lock, IDI.OPCODES.unlock]

    @staticmethod
    def is_idi_nc_flow(address, opcode):
        return CNCU_UTILS.is_idi_lock_flow(opcode) or \
               CNCU_UTILS.is_idi_interrupt_flow(address, opcode) or \
               CNCU_UTILS.is_idi_funny_io_access_flow(opcode) or \
               CNCU_UTILS.is_idi_cfg_access_flow(address=address, opcode=opcode) or \
               CNCU_UTILS.is_idi_mmio_access_flow(address=address, opcode=opcode)

    @staticmethod
    def is_flow_reached_nc(flow: list):
        for f in flow:
            if type(f) in [SB_TRANSACTION, CFI_TRANSACTION, UFI_TRANSACTION]:
                return True
        return False

    @staticmethod
    def is_nc_flow(flow: list):
        for f in flow:
            if type(f) in [SB_TRANSACTION, CFI_TRANSACTION, UFI_TRANSACTION]:
                return True
        return CNCU_UTILS.is_idi_interrupt_flow(flow[0].addr, flow[0].opcode)

    @staticmethod
    def is_creg_pla_flow(flow: list):
        return flow[0].opcode == IDI.OPCODES.port_in and flow[0].addr[31:28] == 0x6 and flow[0].addr[23:23] == 1

    @staticmethod
    def is_full_cl_read(is_read, length, opcode):
        return is_read and length == 0 and opcode != IDI.OPCODES.prd

    @staticmethod
    def is_cross_cl_read(is_read, addr, length):
        is_cross_cl = int(addr[5:0] + length) > GLOBAL.cacheline_size_in_bytes
        return is_read and is_cross_cl

    @staticmethod
    def is_cross_dw(offset, be, is_read, length, opcode):
        len = 0
        for i in range(8):
            if be[i] == 1:
                len = i + 1
        return offset[1:0] + len > 4 or be > 0xff or CNCU_UTILS.is_full_cl_read(is_read, length, opcode)

    @staticmethod
    def is_cross_qw(offset, be, is_read, length, opcode):
        len = 0
        for i in range(8):
            if be[i] == 1:
                len=i+1
        return offset[2:0] + len > 8 or be > 0xff or CNCU_UTILS.is_full_cl_read(is_read, length, opcode)

    @staticmethod
    def is_non_contiguous_be(be, addr):
        return (be >> addr[1:0]) not in [0,0x1,0x3,0x7,0xf,0x1f,0x3f,0x7f,0xff]

    @staticmethod
    def mmio_abort_detection(target, addr, offset, be, is_read, length, opcode):
        is_abort = False
        is_cross_qw = CNCU_UTILS.is_cross_qw(offset, be, is_read, length, opcode)
        is_read_cross_cl = CNCU_UTILS.is_cross_cl_read(is_read, addr, length)
        if is_cross_qw:
            if target in [TARGET_TYPE.SB]:
                is_abort = True
        if is_read_cross_cl:
            is_abort = True
            target = TARGET_TYPE.SB
        return is_abort, target

    @staticmethod
    def lt_abort_detection(target, addr, offset, be, is_read, length, opcode):
        is_abort = False
        is_cross_qw = CNCU_UTILS.is_cross_qw(offset, be, is_read, length, opcode)
        is_read_cross_cl = CNCU_UTILS.is_cross_cl_read(is_read, addr, length)
        if is_cross_qw or is_read_cross_cl:
            is_abort = True
            if is_read:
               target = TARGET_TYPE.SB
        return is_abort, target

    @staticmethod
    def io_abort_detection(target, addr, offset, be, is_read, length, opcode):
        is_abort = False

        is_cross_dw = CNCU_UTILS.is_cross_dw(offset, be, is_read, length, opcode)
        is_non_contiguous_be = CNCU_UTILS.is_non_contiguous_be(be, addr)
        is_read_cross_cl = CNCU_UTILS.is_cross_cl_read(is_read, addr, length)

        if is_cross_dw or is_read_cross_cl or is_non_contiguous_be:
            is_abort = True
            if is_read:
                target = TARGET_TYPE.SB
        return is_abort, target

    @staticmethod
    def cfg_abort_detection(target, addr, offset, be, is_read, length, opcode):
        is_abort = False
        is_cross_dw = CNCU_UTILS.is_cross_dw(offset, be, is_read, length, opcode)
        is_non_contiguous_be = CNCU_UTILS.is_non_contiguous_be(be, addr)
        is_read_cross_cl = CNCU_UTILS.is_cross_cl_read(is_read, addr, length)
        if is_read_cross_cl or is_non_contiguous_be:
            is_abort = True
        if is_cross_dw:
            is_abort = True
            if is_read and target == TARGET_TYPE.CFI:
                target = TARGET_TYPE.SB
        return is_abort, target

class REMAPPING:
    @staticmethod
    def set_remap_dict():
        si = NC_SI.get_pointer()
        next_logical = 0
        REMAPPING.physical2logical = dict()
        REMAPPING.logical2physical = dict()

        for i in range(si.num_of_cbo):
            if si.cbo_disable_mask[i] == 0:
                logical_id = next_logical
                REMAPPING.physical2logical[i] = logical_id
                REMAPPING.logical2physical[logical_id] = i
                next_logical+=1

        for i in range(si.num_of_cbo):
            if si.cbo_disable_mask[i] == 1:
                logical_id = next_logical
                REMAPPING.physical2logical[i] = logical_id
                REMAPPING.logical2physical[logical_id] = i
                next_logical+=1

        for i in range(17-si.num_of_cbo):
            REMAPPING.physical2logical[si.num_of_cbo + i] = si.num_of_cbo + i
            REMAPPING.logical2physical[si.num_of_cbo + i] = si.num_of_cbo + i


