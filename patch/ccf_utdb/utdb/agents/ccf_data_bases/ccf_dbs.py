import shutil

import gzip
import pickle
from collections.__init__ import OrderedDict

import os
from val_utdb_base_components import val_utdb_component

from agents.ccf_common_base.coh_global import COH_GLOBAL


class ccf_dbs(val_utdb_component):
    #DBs:
    ccf_flows = dict()
    mem_db = dict()
    llc_ref_db = dict()
    llc_rtl_db = dict()
    dump_db = dict()
    ref_monitor_per_cbo_db = dict()
    ccf_addr_flows = dict()
    ccf_reject_accurate_times = dict()
    addressless_db = dict()
    pmc_gpsb_msgs_db = dict()
    power_sb_msgs_db = dict()

    #DBs dir name
    pickle_dbs_dir_name = "ccf_pickle_dbs"

    @staticmethod
    def reset_ccf_flows():
        ccf_dbs.ccf_flows = {}

    @staticmethod
    def reset_mem_db():
        ccf_dbs.mem_db = {}

    @staticmethod
    def reset_llc_ref_db():
        ccf_dbs.llc_ref_db = {}

    @staticmethod
    def reset_llc_rtl_db():
        ccf_dbs.llc_rtl_db = {}

    @staticmethod
    def reset_dump_db():
        ccf_dbs.dump_db = {}

    @staticmethod
    def reset_ref_monitor_per_cbo_db():
        ccf_dbs.ref_monitor_per_cbo_db = {}

    @staticmethod
    def reset_ccf_addr_flows_db():
        ccf_dbs.ccf_addr_flows = {}

    @staticmethod
    def reset_ccf_reject_accurate_times_db():
        ccf_dbs.ccf_reject_accurate_times = {}

    @staticmethod
    def reset_addressless_db():
        ccf_dbs.addressless_db = {}

    @staticmethod
    def reset_pmc_gpsb_msgs_db():
        ccf_dbs.pmc_gpsb_msgs_db = {}

    @staticmethod
    def reset_power_sb_msgs_db():
        ccf_dbs.power_sb_msgs_db = {}

    @staticmethod
    def sort_ccf_flows():
        ccf_dbs.ccf_flows = OrderedDict(sorted(ccf_dbs.ccf_flows.items(), key=lambda x: x[1].get_sort_time()))

    @staticmethod
    def sort_mem_db():
        ccf_dbs.mem_db = OrderedDict(sorted(ccf_dbs.mem_db.items()))

    @staticmethod
    def sort_dump_db():
        ccf_dbs.dump_db = OrderedDict(sorted(ccf_dbs.dump_db.items()))

    @staticmethod
    def dump_ccf_db(ccf_db, file_name):
        with open(file_name, 'wb') as ccf_db_file:
            pickle.dump(ccf_db, ccf_db_file)
            ccf_db_file.close()

    @staticmethod
    def decompress_gz_file(gz_file, new_file):
        with gzip.open(gz_file, 'rb') as f_in:
            with open(new_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    @staticmethod
    def load_ccf_db(file_name):
        if os.path.exists(file_name + ".gz"):
            ccf_dbs.decompress_gz_file(gz_file=file_name + ".gz", new_file=file_name)
            os.remove(file_name + ".gz")
        ccf_db_file = open(file_name, 'rb')
        ccf_db = pickle.load(ccf_db_file)
        ccf_db_file.close()
        return ccf_db

    @staticmethod
    def get_db_file_name_with_timestamp(basic_file_name):
        db_time_stamp = "_{}_till_{}".format(COH_GLOBAL.global_vars["START_OF_TEST"], COH_GLOBAL.global_vars["END_OF_TEST"])
        if 'DEBUG_SOC_RESULTS_PATH' in os.environ:
            return os.environ["DEBUG_SOC_RESULTS_PATH"] + "/tlm_post/" + ccf_dbs.pickle_dbs_dir_name + "/" + basic_file_name + db_time_stamp + ".db"
        else:
            return os.environ["TEST_WORK_AREA"] + "/tlm_post/" + ccf_dbs.pickle_dbs_dir_name + "/" + basic_file_name + db_time_stamp + ".db"

    @staticmethod
    def create_pickle_db_dir():
        if 'DEBUG_SOC_RESULTS_PATH' in os.environ:
            results_path = os.environ["DEBUG_SOC_RESULTS_PATH"]
        else:
            results_path = os.environ["TEST_WORK_AREA"]

        isExist = os.path.exists(results_path + "/tlm_post/" + ccf_dbs.pickle_dbs_dir_name)
        if not isExist:
            os.makedirs(results_path + "/tlm_post/" + ccf_dbs.pickle_dbs_dir_name)

    @staticmethod
    def dump_all_ccf_dbs():
        ccf_dbs.create_pickle_db_dir()
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.ccf_flows, file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_sim_flow'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.mem_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_mem_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.llc_ref_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('llc_ref'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.llc_rtl_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('llc_rtl'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.dump_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('dump_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.ref_monitor_per_cbo_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('ref_monitor_per_cbo_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.ccf_addr_flows, file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_addr_flows_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.ccf_reject_accurate_times, file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_reject_accurate_times_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.addressless_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('addressless_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.pmc_gpsb_msgs_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('pmc_gpsb_msgs_db'))
        ccf_dbs.dump_ccf_db(ccf_db=ccf_dbs.power_sb_msgs_db, file_name=ccf_dbs.get_db_file_name_with_timestamp('power_sb_msgs_db'))

    @staticmethod
    def load_all_ccf_dbs():
        ccf_dbs.ccf_flows = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_sim_flow'))
        ccf_dbs.mem_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_mem_db'))
        ccf_dbs.llc_ref_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('llc_ref'))
        ccf_dbs.llc_rtl_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('llc_rtl'))
        ccf_dbs.dump_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('dump_db'))
        ccf_dbs.ref_monitor_per_cbo_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('ref_monitor_per_cbo_db'))
        ccf_dbs.ccf_addr_flows = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_addr_flows_db'))
        ccf_dbs.ccf_reject_accurate_times = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('ccf_reject_accurate_times_db'))
        ccf_dbs.addressless_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('addressless_db'))
        ccf_dbs.pmc_gpsb_msgs_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('pmc_gpsb_msgs_db'))
        ccf_dbs.power_sb_msgs_db = ccf_dbs.load_ccf_db(file_name=ccf_dbs.get_db_file_name_with_timestamp('power_sb_msgs_db'))
