import os
from val_utdb_base_components import EOT
from val_utdb_components import val_utdb_agent
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_systeminit.ccf_systeminit import ccf_systeminit
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_queries.ccf_ral_qry import ccf_ral_qry


class ccf_base_agent(val_utdb_agent):
    def configure(self):
        self.set_si(ccf_systeminit.get_pointer())

    def build(self):
        self.ccf_ral_qry_i = ccf_ral_qry.get_pointer()
        self.ccf_ral_agent_i = ccf_ral_agent.get_pointer()
        self.ccf_pp_params_ptr = ccf_pp_params.get_pointer()
        CCF_UTILS.initial_ccf_utils(self.si)


    def connect(self):
        self.ccf_ral_qry_i.connect_to_db('registers_logdb')

    def run(self):
        pass

    @property
    def preload_logdb_exist(self):
        return os.path.exists(self.ccf_pp_params_ptr.params["test_path"] + "/LOGDB/preload_logdb")

    @property
    def sm_logdb_exist(self):
        return os.path.exists(self.ccf_pp_params_ptr.params["test_path"] + "/LOGDB/ccf_sm_logdb")

    @property
    def merged_ccf_nc_logdb_exist(self):
        return os.path.exists(self.ccf_pp_params_ptr.params["test_path"] + "/LOGDB/merged_ccf_nc_logdb")

    @property
    def ccf_flows(self):
        if ccf_dbs.ccf_flows:
            return ccf_dbs.ccf_flows
        else:
            VAL_UTDB_ERROR(time=EOT, msg="Tried to get ccf_flows but it's empty dict.")
            return ccf_dbs.ccf_flows

    @property
    def mem_db(self):
        return ccf_dbs.mem_db

    @property
    def llc_ref_db(self):
        return ccf_dbs.llc_ref_db

    @llc_ref_db.setter
    def llc_ref_db(self, llc_ref_db):
        ccf_dbs.llc_ref_db = llc_ref_db

    @property
    def llc_rtl_db(self):
        return ccf_dbs.llc_rtl_db

    @llc_rtl_db.setter
    def llc_rtl_db(self, llc_rtl_db):
        ccf_dbs.llc_rtl_db = llc_rtl_db

    @property
    def dump_db(self):
        return ccf_dbs.dump_db

    @dump_db.setter
    def dump_db(self, dump_db):
        ccf_dbs.dump_db = dump_db
