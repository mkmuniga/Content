from val_utdb_components import val_utdb_chk
from agents.ccf_agent.ccf_power_agent.ccf_power_checkers.ccf_punit_pmc_if_checkers import \
    ccf_power_virtual_signals_writes_to_punit_checker
    # , ccf_power_virtual_signals_checker
    # ccf_power_virtual_signals_checker
from val_utdb_report import VAL_UTDB_ERROR


class CCF_POWER_CHECKER(val_utdb_chk):

    def __init__(self):
        super().__init__()
        self.ccf_power_virtual_signals_writes_to_punit_checker = ccf_power_virtual_signals_writes_to_punit_checker.create()

    def run(self):
        self.ccf_power_virtual_signals_writes_to_punit_checker.run()
