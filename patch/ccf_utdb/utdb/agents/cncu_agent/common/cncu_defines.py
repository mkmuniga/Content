from agents.cncu_agent.utils.nc_systeminit import NC_SI
from val_utdb_bint import bint

from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES

class GLOBAL:
    ip_name = UNIQUE_DEFINES.ip_name
    vcr_pla_msb = 20
    vcr_pla_lsb = 3
    lt_doorbell_base_addr = 0xfed20e
    mktme_lsb = 41 #TODO: when we are using dynamic MKTME this value is not correct
    mktme_msb = 51
    top_mmio_low_addr = bint(0xffffffff)
    cr_sink_addr = bint(0x5628)
    addr_width = 42 # width without mktme
    cacheline_size_in_bytes = 64
    num_of_qw_in_cacheline = int(cacheline_size_in_bytes/8)


class SB:
    class OPCODES:
        mem_rd = "(00) MEMRD"
        mem_wr = "(01) MEMWR"
        io_rd = "(02) IORD"
        io_wr = "(03) IOWR"
        cfg_rd = "(04) CFGRD"
        cfg_wr = "(05) CFGWR"
        cr_rd = "(06) CRRD"
        cr_wr = "(07) CRWR"
        cmp = "(20) CMP"
        cmpd = "(21) CMPD"
        cbo_drain = "(79) UNDEF_79"
        cbo_ack = "(C0) CBO_ACK_MSG"
        ncu_ncu_msg = "(71) UNDEF_71"
        pcu_ncu_msg = "(72) UNDEF_72"
        ncu_pcu_msg = "(73) UNDEF_73"
        fclk_event = "(7B) FCLK_E_BCST"
        mclk_event = "(7A) MCLK_EVENTS"

    class EPS:
        si = NC_SI.get_pointer()
        compute_seg_pid = bint(0xee)
        gt_seg_pid = bint(0xf0)
        chipset_s0_seg_pid = bint(0xf2)
        chipset_s1_seg_pid = bint(0xf3)
        if si.cluster_id == 0:
            ncevents = bint(0xf60a)
            ncracu = bint(0xf60d)
        elif si.cluster_id == 1:
            ncevents = bint(0xf61a)
            ncracu = bint(0xf61d)
        elif si.cluster_id == 2:
            ncevents = bint(0xf70a)
            ncracu = bint(0xf70d)
        elif si.cluster_id == 3:
            ncevents = bint(0xf71a)
            ncracu = bint(0xf71d)
        ccf_ncevents = bint(0xee31)
        idi_bridge_ncevents = bint(0xee86)
        idi_bridge = bint(0xee45)
        mcast_sad_all = bint(0xe4d5)
        mcast_cbo_all = bint(0xe4d6)
        mcast_boot_cfg_all = bint(0xe5d7)
        mcast_ncevents = bint(0xe5d8)
        mcast_ltctrlsts = bint(0xe5d9)
        mcast_santa_all = bint(0xe5da)
        mcast_ese2cores = bint(0xe6dc)
        mcast_core_all = bint(0xe6dd)

        cbo0 = bint(0xf601)

        cbo = [bint(0xee03),
               bint(0xee06),
               bint(0xee09),
               bint(0xee0c),
               bint(0xee0f),
               bint(0xee12),
               bint(0xee15),
               bint(0xee18)]
        cores = [bint(0xf002),
                 bint(0xf005),
                 bint(0xf008),
                 bint(0xf00b),
                 bint(0xf00e),
                 bint(0xf011),
                 bint(0xf014),
                 bint(0xf017),
                 bint(0xf102),
                 bint(0xf105),
                 bint(0xf108),
                 bint(0xf10b),
                 bint(0xf10e),
                 bint(0xf111),
                 bint(0xf114),
                 bint(0xf117),
                 bint(0xf202),
                 bint(0xf205),
                 bint(0xf208),
                 bint(0xf20b),
                 bint(0xf20e),
                 bint(0xf211),
                 bint(0xf214),
                 bint(0xf217),
                 bint(0xf302),
                 bint(0xf305),
                 bint(0xf308),
                 bint(0xf30b),
                 bint(0xf30e),
                 bint(0xf311),
                 bint(0xf314),
                 bint(0xf317)
                 ]
        idib_cores = [bint(0xee4c)]
        all_core = cores
        internal_cores = cores
        sink = bint(0xee3f)
        ddr    = bint(0xeea3)
        ddr_ucss = bint(0xeea5)
        ddrpm  = bint(0xeeab)
        sncu   = bint(0xee32)
        punit  = bint(0xee46)
        santa0 = bint(0xf60c)
        pmc = bint(0xee35)

    class MSG_TYPE:
        posted = "POSTED"
        non_posted = "NON_POSTED"

    @staticmethod
    def has_data(opcode):
        return opcode in [SB.OPCODES.cmpd]

    @staticmethod
    def get_read_master(port_id):
        if port_id == SB.EPS.mcast_sad_all:      return SB.EPS.cbo0
        if port_id == SB.EPS.mcast_cbo_all:      return SB.EPS.cbo0
        if port_id == SB.EPS.mcast_boot_cfg_all: return SB.EPS.sncu
        if port_id == SB.EPS.mcast_ncevents:     return SB.EPS.sncu
        if port_id == SB.EPS.mcast_ltctrlsts:    return SB.EPS.sncu
        if port_id == SB.EPS.mcast_santa_all:    return SB.EPS.santa0
        if port_id == SB.EPS.mcast_core_all:     return SB.EPS.sncu
        return port_id


class UFI:

    class EPS:
        si = NC_SI.get_pointer()
        ccf = bint(0)
        ccf[7:4] = si.ccf_socket_id[3:0]
        ccf[3:0] = si.ccf_cbb_id[3:0]

    class OPCODES:
        int_ack = "IntAck"
        int_physical = "IntPhysical"
        int_logical = "IntLogical"
        int_prio_up = "IntPrioUpd"
        nc_msg_b = "NcMsgB"
        nc_msg_s = "NcMsgS"
        nc_data = "NcData"
        wc_wr_ptl = "WcWrPtl"
        wc_wr = "WcWr"
        nc_rd = "NcRd"
        nc_rd_ptl = "NcRdPtl"
        nc_wr = "NcWr"
        nc_wr_ptl = "NcWrPtl"
        nc_cfg_wr = "NcCfgWr"
        nc_cfg_rd = "NcCfgRd"
        nc_mem_wr = "NcMemWr"
        nc_mem_rd = "NcMemRd"
        nc_lt_wr = "NcLTWr"
        nc_lt_rd = "NcLtRd"
        nc_io_wr = "NcIOWr"
        nc_io_rd = "NCIORd"
        nccmpu = "NCCmpU"
        ncenqueue = "NcEnqueue"

    class PKT_TYPE:
        pr = "PR"
        pw = "PW"
        ncm = "NCM"
        sr_cd = "SR-CD"
        sr_u = "SR-U"
        sa_d = "SA-D"
        sr_h = "SR-H"

    class IFCS:
        data = "DATA"
        rsp = "RSP"

    class VC_IDS:
        vc0_ncs = "VN0_NCS"
        vc0_ncb = "VN0_NCB"
        vc0_drs = "VC0_DRS"
        vc0_ndr = "VC0_NDR"
        vc1_ndr = "VC1_NDR"
        vc1_rwd = "VC1_RwD"


class CFI:
    class EPS:
        ccf = UNIQUE_DEFINES.ccf_cfi_ep
        ioc0 = "IOC_0_L0(48)"
        media0 = "MEDIA_0(2c)"
        punit = "PUNIT(23)"
        vpu0 = "VPU_0(28)"
        iax = "IAX(2f)"
        ipu = "IPU_0(34)"
        sncu = "sNCU(21)"
        svtu = "sVTU(22)"
        ioc_vtu = "IOC_0_VTU(41)"

    class OPCODES:
        int_ack = "IntAck"
        int_physical = "IntPhysical"
        int_logical = "IntLogical"
        int_prio_up = "IntPrioUpd"
        nc_msg_b = "NcMsgB"
        nc_msg_s = "NcMsgS"
        nc_data = "NcData"
        wc_wr_ptl = "WcWrPtl"
        wc_wr = "WcWr"
        nc_rd = "NcRd"
        nc_rd_ptl = "NcRdPtl"
        nc_wr = "NcWr"
        nc_wr_ptl = "NcWrPtl"
        nc_cfg_wr = "NcCfgWr"
        nc_cfg_rd = "NcCfgRd"
        nc_mem_wr = "NcMemWr"
        nc_mem_rd = "NcMemRd"
        nc_lt_wr = "NcLTWr"
        nc_lt_rd = "NcLtRd"
        nc_io_wr = "NcIOWr"
        nc_io_rd = "NCIORd"
        nccmpu = "NCCmpU"
        ncenqueue = "NcEnqueue"

    class VC_IDS:
        vc0_ncs = "VC0_NCS"
        vc0_ncb = "VC0_NCB"
        vc0_drs = "VC0_DRS"
        vc0_ndr = "VC0_NDR"
        vc1_ndr = "VC1_NDR"
        vc1_rwd = "VC1_RwD"

    class IFCS:
        tx_data = "TRANSMIT_DATA_0"
        rx_data = "RECEIVE_DATA_0"
        tx_rsp = "TRANSMIT_RSP_0"
        rx_rsp = "RECEIVE_RSP_0"

    class PKT_TYPE:
        pr = "PR"
        pw = "PW"
        ncm = "NCM"
        sr_cd = "SR-CD"
        sr_u = "SR-U"
        sa_d = "SA-D"
        sr_h = "SR-H"

    class MSG_TYPE:
        eoi = "EOI(20)"
        vlw = "VLW(21)"
        lock = "Lock(4)"
        split_lock = "SplitLock(5)"
        stop_req1 = "StopReq1(20)"
        stop_req3 = "StopReq3(22)"
        unlock = "Unlock(3)"
        start_req1 = "StartReq1(9)"
        shutdown = "Shutdown(0)"

    @staticmethod
    def has_data(pkt_type):
        return pkt_type in [CFI.PKT_TYPE.pw, CFI.PKT_TYPE.sr_cd, CFI.PKT_TYPE.sa_d, CFI.PKT_TYPE.ncm, CFI.PKT_TYPE.pr]

    @staticmethod
    def has_byteen(pkt_type):
        return pkt_type == CFI.PKT_TYPE.pw

    @staticmethod
    def has_length(pkt_type):
        return pkt_type == CFI.PKT_TYPE.pr


class IDI:
    class TYPES:
        c2u_req = "C2U REQ"
        c2u_rsp = "C2U RSP"
        c2u_data = "C2U DATA"
        u2c_req = "U2C REQ"
        u2c_rsp = "U2C RSP"
        u2c_data = "U2C DATA"

    class OPCODES:
        go = "IDI_GO"
        rsp_i_hit_i = "RspIHitI"
        writepull = "WRITEPULL"
        unlock = "UNLOCK"
        lock = "LOCK"
        split_lock = "SPLITLOCK"
        stop_req = "STOPREQ"
        start_req = "STARTREQ"
        rsp_stop_done = "RspStopDone"
        rsp_start_done = "RspStartDone"
        inta = "INTA"
        dpt = "DPTEV"
        wil = "WIL"
        prd = "PRD"
        crd = "CRD"
        crd_pref = "CRD_PREF"
        crd_uc = "CRD_UC"
        drd = "DRD"
        drd_opt = "DRD_OPT"
        drd_ns = "DRD_NS"
        drd_pref = "DRD_PREF"
        drd_opt_pref = "DRD_OPT_PREF"
        rdcurr = "RDCURR"
        drdpte = "DRDPTE"
        rfo = "RFO"
        rfo_pref = "RFO_PREF"
        wilf = "WILF"
        wcil = "WCIL"
        wcil_ns = "WCIL_NS"
        wcilf = "WCILF"
        wcilf_ns = "WCILF_NS"
        ucrdf = "UCRDF"
        enqueue = "ENQUEUE"
        eoi = "EOI"
        vlw = "VLW"
        int_physical = "INTPHY"
        int_logical = "INTLOG"
        int_prio_up = "INTPRIUP"
        lt_write = "LTWRITE"
        port_in = "PORT_IN"
        port_out = "PORT_OUT"
        mem_push_wr_ns = "MEMPUSHWR_NS"
        spcyc = "SPCYC"

    @staticmethod
    def has_sai(tran_type):
        return tran_type in [IDI.TYPES.c2u_req]

    @staticmethod
    def has_data(tran_type):
        return tran_type in [IDI.TYPES.c2u_data, IDI.TYPES.u2c_data]

    @staticmethod
    def has_byteen(tran_type):
        return tran_type == IDI.TYPES.c2u_data

    @staticmethod
    def has_length(tran_type):
        return tran_type == IDI.TYPES.c2u_req


class SAI:
    lt_sai = 0x5a
    hw_cpu = 0x14
    pm_pcs = 0x12
    sunpass = 0x7
    ucode = 0x3
    core_event_proxy = 0x68


class TARGET_TYPE:
    SB = 1
    CFI = 2
    UFI = 3


class BAR:
    high_bios = "HIGH_BIOS"
    lt0 = "MMIO_LT0"
    lt1 = "MMIO_LT1"
    crab_abort = "CRAB_ABORT"
    mmcfgbar = "PCIE_MMCFG"
    mchbar = "MCHBAR"
    safbar = "SAFBAR"
    regbar = "REGBAR"
    edrambar = "EDRAMBAR"
    vtdbar = "VTDBAR"
    vtdbar_abort = "VTDBAR**abort**"
    vgagsa = "VGAGSA"
    tmbar = "TMBAR"
    membar2 = "MEMBAR2"
    gttmmadr = "GTTMMADR"
    lmembar = "LMEMBAR"
    sriov0 = "SRIOV0"
    pm_bar = "PM_BAR"
    ipubar0 = "ISPMBAR"
    ipubar2 = "IPUBAR2"
    vpubar0 = "VPUBAR0"
    vpubar2 = "VPUBAR2"
    iaxbar0 = "IAXBAR0"
    iaxbar2 = "IAXBAR2"

    @staticmethod
    def get_device(bar_name):
        if bar_name == BAR.mchbar: return 0
        if bar_name == BAR.safbar: return 0
        if bar_name == BAR.regbar: return 0
        if bar_name == BAR.edrambar: return 0
        if bar_name == BAR.vtdbar: return 0
        if bar_name == BAR.lmembar: return 2
        if bar_name == BAR.gttmmadr: return 2
        if bar_name == BAR.sriov0: return 2
        if bar_name == BAR.vgagsa: return 2
        if bar_name == BAR.tmbar: return 0 #TMBAR which aliases into MCHBAR for MMIO accesses (so dev 0 instead of 4)
        if bar_name == BAR.ipubar0: return 5
        if bar_name == BAR.ipubar2: return 5
        if bar_name == BAR.pm_bar: return 10
        if bar_name == BAR.vpubar0: return 11
        if bar_name == BAR.vpubar2: return 11
        if bar_name == BAR.iaxbar0: return 12
        if bar_name == BAR.iaxbar2: return 12
        if bar_name == BAR.membar2: return 14

    @staticmethod
    def get_bar(bar_name):
        if bar_name == BAR.mchbar: return 0
        if bar_name == BAR.safbar: return 2
        if bar_name == BAR.regbar: return 4
        if bar_name == BAR.edrambar: return 3
        if bar_name == BAR.vtdbar: return 5
        if bar_name == BAR.lmembar: return 2
        if bar_name == BAR.gttmmadr: return 0
        if bar_name == BAR.sriov0: return 0
        if bar_name == BAR.vgagsa: return 6
        if bar_name == BAR.tmbar: return 0
        if bar_name == BAR.ipubar0: return 0
        if bar_name == BAR.ipubar2: return 2
        if bar_name == BAR.pm_bar: return 0
        if bar_name == BAR.vpubar0: return 0
        if bar_name == BAR.vpubar2: return 2
        if bar_name == BAR.iaxbar0: return 0
        if bar_name == BAR.iaxbar2: return 2
        if bar_name == BAR.membar2: return 2


class EVENTS_TYPES:
    msmi = "MSMI"
    csmi = "CSMI"
    llbbrk = "LLBRK"
    lterr = "LTERR"
    cmci = "CMCI"
    psmi = "PSMI"
    pcusmi = "PCUSMI"
    ncu_pmi_wire = "NCU_PMI_WIRE"
    unctrap = "UNCTRAP"
    umcnf = "UMCNF"
    umcf = "UMCF"
    rmsmi = "rMSMI"
    rmca = "rMCA"
    ierr = "IERR"
    exterr = "EXTERR"
    mcerr = "MCERR"

    @staticmethod
    def get_events_types():
        events_types = list()

        for attr, value in vars(EVENTS_TYPES).items():
            if not attr.startswith('_') and attr != 'get_events_types':
                events_types.append(value)
        return sorted(events_types)
