from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base_class import ccf_base_component
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_queries.ccf_corrupted_llc_preload_qry import ccf_corrupted_llc_preload_qry

class addressless_info:
    def __init__(self, address, llc_slice, half, tag_ecc, set, way, state):
        self.address = address
        self.llc_slice = llc_slice
        self.half = half
        self.tag_ecc = tag_ecc
        self.way = way
        self.set = set
        self.state = state

class ccf_addressless_db(ccf_base_component):
    def __init__(self):
        self.ccf_corrupted_llc_preload_qry = ccf_corrupted_llc_preload_qry.get_pointer()
        self.ccf_llc_db_agent = ccf_llc_db_agent.get_pointer()
        self.address_tag_correction = []

        for cbo_id in range(self.si.num_of_cbo):
            self.address_tag_correction.append([dict(), dict()]) #One dict for half0 and the other half1

    def populate_addressless_db(self, record):
        if (record.TID not in self.addressless_db.keys()) and (record.ARBCMD in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes) and (record.STATE != "LLC_I"):
            address = record.ADDRESS.lstrip("0") or "0"
            self.addressless_db[record.TID] = addressless_info(address, int(record.UNIT[4]), int(record.HALF), record.TAG_ECC, record.SET, record.WAY, record.STATE)

    def get_corruption_type(self, record):
        if record.ORIG_ADDR != "-":
            return "TAG_ERROR"
        elif record.ORIG_ECC != "-":
            return "ECC_ERROR"
        else:
            VAL_UTDB_ERROR(time=record.TIME, msg="We didn't expect to see this kind of preload corruption injection.")
            return ""

    ##DB functions
    def get_addressless_state_by_uri(self,uri_tid):
        return self.addressless_db[uri_tid].state

    def get_real_address_by_uri(self, uri_tid, time_for_err_print=0):
        addressless_record = self.addressless_db[uri_tid]

        correct_tag_ecc = self.ccf_llc_db_agent.check_and_correct_tag(slice_num=addressless_record.llc_slice,
                                                                      half=addressless_record.half,
                                                                      set=addressless_record.set,
                                                                      tag_ecc=addressless_record.tag_ecc,
                                                                      time_for_err_print=time_for_err_print)

        bint_correct_tag = bint(int(correct_tag_ecc.split("(")[0],16))
        bint_orig_tag = bint(int(addressless_record.tag_ecc.split("(")[0],16))

        if bint_correct_tag == bint_orig_tag:
            return self.addressless_db[uri_tid].address
        else:
            correct_address = bint(int(self.addressless_db[uri_tid].address, 16))
            correct_address[CCF_COH_DEFINES.mktme_msb:CCF_COH_DEFINES.tag_lsb] = bint_correct_tag[(CCF_COH_DEFINES.mktme_msb-CCF_COH_DEFINES.tag_lsb):0]
            return hex(correct_address)[2:]

    def tid_exist_in_address_db(self, uri_tid):
        return uri_tid in self.addressless_db.keys()
