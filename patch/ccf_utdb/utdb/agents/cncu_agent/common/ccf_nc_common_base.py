from val_utdb_base_components import val_utdb_component, EOT
from val_utdb_components import val_utdb_agent

from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_CONFIG(val_utdb_component):
    def __init__(self):
        self.set_si(NC_SI.get_pointer())
        self.ral_utils: NC_RAL_AGENT = NC_RAL_AGENT.get_pointer()
        self.num_of_modules = 1 if UNIQUE_DEFINES.is_low_power_ccf else self.si.num_of_cbo
        self.set_fixed_chicken_bits()

    def set_fixed_chicken_bits(self):
        self.dis_ncu_pmi_wire = self.ral_utils.read_reg_field("ncevents", "NcuPMONCtlFix", "OvfEn", EOT) == 0
        self.dis_llb_to_cores = self.ral_utils.read_reg_field("ncevents", "NcuEvOveride", "dis_llb_event_to_cores", EOT) == 1
        self.dis_pmi_to_cores = self.ral_utils.read_reg_field("ncevents", "NcuPMONGlCtrl", "PMIAllIACores", EOT) == 0
        # if LTPmonCtrClr is written during test it will update the defeature pmi bit. We  wont check pmi event in this case
        self.ignore_pmi = len(self.ral_utils.get_reg_field_change_times("ncevents", "LTCtrlSts", "LTPmonCtrClr")) > 0

class CCF_NC_BASE_AGENT(val_utdb_agent):
    ccf_nc_config: CCF_NC_CONFIG
    ral_utils: NC_RAL_AGENT

    def __init__(self):
        self.configure()

    def configure(self):
        self.set_si(NC_SI.get_pointer())
        self.ccf_nc_config = CCF_NC_CONFIG.create()
        self.ral_utils = NC_RAL_AGENT.create()

    def build(self):
        pass

    def connect(self):
        pass

    def run(self):
        pass

