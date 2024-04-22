from agents.ccf_agent.ccf_power_agent.common_power.ccf_power_sb_base_txn import BASE_TRANSACTION

class VIRTUAL_SIGNAL(BASE_TRANSACTION):
    def __init__(self):
        self.time = None
        self.curr_llc_ways = None
        self.curr_llc_ceiling = None
        self.curr_llc_floor = None
        self.llc_command_ack = None
        self.flush_ack = None
        self.monitor_overflow = None
        self.monitor_copied = None
        self.ccf_blocked = None
        self.ccf_fsm_pwr_up_surv_halt = None
        self.ccf_fsm_pwr_dn_surv_halt = None
        self.ccf_fsm_gv_ctl_surv_halt = None

    def get_time(self):
        return self.time

    def __eq__(self, other):
        if self.curr_llc_ways != other.curr_llc_ways:
            return 0
        if self.curr_llc_ceiling != other.curr_llc_ceiling:
            return 0
        if self.curr_llc_floor != other.curr_llc_floor:
            return 0
        #if self.llc_command_ack != other.llc_command_ack:
        #    return 0
        #if self.flush_ack != other.flush_ack:
        #    return 0
        #if self.monitor_overflow != other.monitor_overflow:
        #    return 0
        #if self.monitor_copied != other.monitor_copied:
        #    return 0
        if self.ccf_blocked != other.ccf_blocked:
            return 0
        if self.ccf_fsm_pwr_up_surv_halt != other.ccf_fsm_pwr_up_surv_halt:
            return 0
        if self.ccf_fsm_pwr_dn_surv_halt != other.ccf_fsm_pwr_dn_surv_halt:
            return 0
        if self.ccf_fsm_gv_ctl_surv_halt != other.ccf_fsm_gv_ctl_surv_halt:
            return 0
        return 1

    def __ne__(self, other):
        if self == other:
            return 0
        else:
            return 1

class CCF_PMA_COMMAND(BASE_TRANSACTION):
    def __init__(self):
        self.time = None
        self.block_req = None
        self.unblock_req = None
        self.monitor_copy = None

    def get_time(self):
        return self.time

