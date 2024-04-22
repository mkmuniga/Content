from random import randrange
from val_utdb_systeminit import val_utdb_systeminit

from agents.ccf_agent.ccf_save_restore_agent.ccf_save_restore_agent import SaveRestoreAgent
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker import CcfSaveRestoreChecker
from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_srfsm_sb_qry import CcfSrfsmSbQry
from agents.ccf_common_base.ccf_utils import ccf_config

#need to mock ral env
def my_read_reg(hdl_path,time,x_to_0=False,obj=None):
    return 10


# needed to build systeminit in inial_agent_under_test function
class MockCcfSystemInit(val_utdb_systeminit):
    def __init__(self):
        pass
    def si_knobs_declaration(self):
        self.ccf_soc_mode = 0

# need to set self.ccf_config in agent
class MockCcfConfig(ccf_config):
    def __init__(self):
        pass

# I dont want to constantly building the entire systemInit and a getting paths to files I'm not going to be usesing
# because I'm not really building systemInit I need to overrided the get_si_type because pre_run will call this function
# in the agent

class TestableSaveRestoreAgent(SaveRestoreAgent):
    def __init__(self):
        self.ccf_sr_checker = None

    def configure(self):
        self.ccf_config = MockCcfConfig.create()

    def get_si_type(self):
        return MockCcfSystemInit