from agents.ccf_common_base.ccf_common_base_class import ccf_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils

class ccf_windows_chk(ccf_base_chk):
    checker_enable = 1

    def __init__(self):
        self.ccf_cpipe_window_utils_i = ccf_cpipe_window_utils.get_pointer()

    def is_checker_enable(self):
        return self.checker_enable

    def do_check(self):
        self.ccf_cpipe_window_utils_i.check_windows()