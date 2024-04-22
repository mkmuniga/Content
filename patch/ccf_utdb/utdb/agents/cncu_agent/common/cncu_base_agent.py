from val_utdb_components import val_utdb_agent

from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT


class CNCU_BASE_AGENT(val_utdb_agent):
    # ccf_nc_config: CCF_NC_CONFIG
    ral_utils: NC_RAL_AGENT

    def __init__(self):
        self.configure()

    def configure(self):
        self.set_si(NC_SI.get_pointer())
        # self.ccf_nc_config = CCF_NC_CONFIG.create()
        self.ral_utils = NC_RAL_AGENT.create()

    def build(self):
        pass

    def connect(self):
        pass

    def run(self):
        pass

