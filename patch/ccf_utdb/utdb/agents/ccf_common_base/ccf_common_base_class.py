from val_utdb_base_components import val_utdb_component, EOT
from val_utdb_components import val_utdb_qry, val_utdb_chk
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from agents.ccf_data_bases.ccf_dbs import ccf_dbs

class ccf_base_qry(val_utdb_qry):

    class ccf_base_rec(val_utdb_qry.val_utdb_rec):
        def __init__(self, record):
            super().__init__(record)


class ccf_base_component(val_utdb_component):

    @property
    def ccf_flows(self):
        if ccf_dbs.ccf_flows:
            return ccf_dbs.ccf_flows
        else:
            VAL_UTDB_ERROR(time=EOT, msg="Tried to get ccf_flows but it's empty dict.")
            return ccf_dbs.ccf_flows

    @property
    def ref_monitor_per_cbo_db(self):
        return ccf_dbs.ref_monitor_per_cbo_db

    @property
    def ccf_addr_flows(self):
        return ccf_dbs.ccf_addr_flows

    @property
    def ccf_reject_accurate_times(self):
        return ccf_dbs.ccf_reject_accurate_times

    @property
    def addressless_db(self):
        return ccf_dbs.addressless_db

    @property
    def llc_ref_db(self):
        return ccf_dbs.llc_ref_db

    @property
    def pmc_gpsb_msgs_db(self):
        return ccf_dbs.pmc_gpsb_msgs_db

    @property
    def power_sb_msgs_db(self):
        return ccf_dbs.power_sb_msgs_db


class ccf_base_analyzer(ccf_base_agent):

    def is_record_valid(self,record):
        raise NotImplementedError("Subclass must implement abstract method")

    def create_flow_point(self,record):
        raise NotImplementedError("Subclass must implement abstract method")

    def get_record_info(self,record):
        raise NotImplementedError("Subclass must implement abstract method")

    def update_ccf_flow(self, ccf_flow, flow_point):
        pass

    def get_ccf_flow(self,record):
        pass

    def analyze_record(self,record):
        raise NotImplementedError("Subclass must implement abstract method")

    def is_field_valid(self,field):
        return ("-" not in field)

    @property
    def ccf_flows(self):
        return ccf_dbs.ccf_flows


class ccf_base_chk(val_utdb_chk):

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

    @property
    def dump_db(self):
        return ccf_dbs.dump_db
