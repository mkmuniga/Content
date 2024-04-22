from val_utdb_bint import bint

class POWER_SB:
    class OPCODES:
        mem_rd = "00"
        mem_wr = "01"
        io_rd = "02"
        io_wr = "03"
        cfg_rd = "04"
        cfg_wr = "05"
        cr_rd = "06"
        cr_wr = "07"
        cmp = "20"
        cmpd = "21"
        cbo_drain = "79 UNSPECIFIED"
        cbo_ack = "c0 CBO_ACK_MSG"
        ncu_ncu_msg = "71 NCU_NCU_MSG"
        pcu_ncu_msg = "72 PCU_NCU_MSG"
        ncu_pcu_msg = "73 NCU_PCU_MSG"

    class EPS:
        compute_seg_pid = bint(0xee)
        chipset16_seg_pid = bint(0xf2)
        ncracu =  bint(0xee32)
        ncevents = bint(0xee31)
        mcast_dev0cfg = bint(0xe6d9)
        mcast_dev2shadow = bint(0xe6dc)
        mcast_dev10cfg = bint(0xeecd)
        mcast_ncevents = bint(0xeece)
        mcast_sad_all = bint(0xeec9)
        mcast_cbo_all = bint(0xeeca)
        mcast_hbo_all = bint(0xeecf)
        mcast_imr = bint(0xe6de)
        mcast_ltctrlsts = bint(0xeed0)
        mcast_cfi_host = bint(0xe6df)

        cbo = [bint(0xee03), bint(0xee06), bint(0xee09), bint(0xee0c), bint(0xee0f), bint(0xee12), bint(0xee15), bint(0xee18)]
        sink = bint(0xee3f)
        ddr    = bint(0xeea3)
        ddrpm  = bint(0xeeab)
        sncu   = bint(0xee4b)
        punit  = bint(0xee46)
        santa0 = bint(0xee34)
        santa1 = bint(0xee33)
        ioc    = bint(0xf2a8)
        mc0    = bint(0xee5a)
        mc1    = bint(0xee5c)
        ibecc0 = bint(0xee5b)
        ibecc1 = bint(0xee5d)
        hbo0 = bint(0xee54)
        hbo1 = bint(0xee53)
        iocce = bint(0xf2ad)
        mem_switch = bint(0xee9c)
        cce0 = bint(0xee60)
        cce1 = bint(0xee61)
        mem_pma = bint(0xee7a)
        pmc = bint(0xee38)

    class MSG_TYPE:
        posted_msgd = "POSTED_MSGD"
        posted_simple_msg = "POSTED_SIMPLE"
        posted_regio = "POSTED_REGIO"
        posted_cmp = "POSTED_COMP"
        non_posted_regio = "NON_POSTED_REGIO"

    @staticmethod
    def has_data(opcode):
        return opcode in [SB.OPCODES.cmpd]

    @staticmethod
    def get_read_master(port_id):
        if port_id == SB.EPS.mcast_sad_all:    return bint(0xee03)
        if port_id == SB.EPS.mcast_cbo_all:    return SB.EPS.cbo[0]
        if port_id == SB.EPS.mcast_ltctrlsts:  return SB.EPS.sncu
        if port_id == SB.EPS.mcast_ncevents:   return bint(0xee31)
        if port_id == SB.EPS.mcast_dev10cfg:   return SB.EPS.punit
        if port_id == SB.EPS.mcast_dev0cfg:    return SB.EPS.sncu
        if port_id == SB.EPS.mcast_dev2shadow: return SB.EPS.ioc
        if port_id == SB.EPS.mcast_hbo_all:    return SB.EPS.hbo0
        if port_id == SB.EPS.mcast_imr:        return SB.EPS.ioc
        if port_id == SB.EPS.mcast_cfi_host:   return SB.EPS.sncu
        return port_id


