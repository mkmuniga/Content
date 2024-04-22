from val_utdb_components import val_utdb_chk

from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_crashlog_checker import CCF_NC_CRASHLOG_CHECKER
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_flow_checker import \
    SNCU_EVENTS_FLOW_CHECKER
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_ncu_config_bits_checker import \
    CCF_NC_NCU_CONFIG_BITS_CHECKER
from agents.cncu_agent.utils.nc_systeminit import NC_SI


class CCF_NC_EVENTS_CHECKER(val_utdb_chk):

    def __init__(self):
        self.set_si(NC_SI.get_pointer())
        self.ccf_nc_events_flow_checker = SNCU_EVENTS_FLOW_CHECKER.get_pointer()
        self.ccf_nc_crashlog_checker = CCF_NC_CRASHLOG_CHECKER.create()
        self.ccf_nc_ncu_config_bits_checker = CCF_NC_NCU_CONFIG_BITS_CHECKER.create()

    def run(self):
        if self.si.events_chk_en:
            self.ccf_nc_events_flow_checker.run()
            #TODO ranzo enable self.ccf_nc_crashlog_checker.run()
            # self.ccf_nc_ncu_config_bits_checker.run()
