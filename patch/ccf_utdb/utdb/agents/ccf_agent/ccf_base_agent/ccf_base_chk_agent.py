from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from agents.cncu_agent.dbs.cncu_flow_qry import CNCU_FLOW_QRY
from agents.cncu_agent.dbs.ccf_sm_db import SM_DB
from agents.cncu_agent.dbs.ccf_sm_qry import CCF_SM_QRY
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_power_state_agent import ccf_power_state_agent
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_data_bases.ccf_llc_db_agent import ccf_llc_db_agent
from agents.ccf_queries.ccf_power_qry import ccf_power_qry


class ccf_base_chk_agent(ccf_base_agent):

    def create_ccf_coherency_queries(self):
        self.ccf_power_qry_i = ccf_power_qry.create()
        if self.sm_logdb_exist:  # emulation doesn't have this database
            self.ccf_sm_db_i = SM_DB.get_pointer()
            self.ccf_sm_qry_i = CCF_SM_QRY.create()
        if self.merged_ccf_nc_logdb_exist:
            self.ccf_nc_flow_qry = CNCU_FLOW_QRY.create()

    def build_checkers(self):
        pass

    def build_coverage(self):
        pass

    def connect_logdbs_to_queries(self):
        self.ccf_power_qry_i.connect_to_db('pmc_logdb')
        if self.sm_logdb_exist:
            self.ccf_sm_qry_i.connect_to_db('ccf_sm_logdb')
        if self.merged_ccf_nc_logdb_exist:
            self.ccf_nc_flow_qry.connect_to_db('merged_ccf_nc_logdb')

    def build(self):
        super().build()

        # initial CCF_UTILS values
        CCF_UTILS.initial_ccf_utils(self.si)

        # Create all agent queries
        self.create_ccf_coherency_queries()

        # Flow Checkers
        self.build_checkers()

        # Cov
        self.build_coverage()

        # Build agents that will help get data from LOGDBs
        self.ccf_llc_db_agent_i = ccf_llc_db_agent.create()

    def connect(self):
        super().connect()
        self.connect_logdbs_to_queries()

    def run(self):
        ccf_power_state_agent.run_db_builder(self.ccf_power_qry_i)
        ccf_power_state_agent.initialize_test_power_flow_db()

        for idx in range(len(ccf_power_state_agent.test_power_flow_db)):
            COH_GLOBAL.global_vars["POWER_DB_INDEX"] = idx
            COH_GLOBAL.global_vars["START_OF_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["START_TEST"]
            COH_GLOBAL.global_vars["END_OF_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["END_TEST"]
            COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"] = ccf_power_state_agent.test_power_flow_db[idx]["C6_TIME_IN_RANGE"]
            self.run_test(is_cold_reset=ccf_power_state_agent.test_power_flow_db[idx]["COLD_RESET"])

    def reset_db(self, is_cold_reset):
        ccf_dbs.reset_ccf_flows()
        ccf_dbs.reset_mem_db()

        if self.si.ccf_dump_chk_en:
            ccf_dbs.reset_dump_db()

        self.ccf_llc_db_agent_i.reset()

    def run_test(self, is_cold_reset):
        self.reset_db(is_cold_reset)
        ccf_registers.get_pointer().get_registers_value()

        # Load all ccf dbs for that test.
        ccf_dbs.load_all_ccf_dbs()

        #Build SM in case it is being used in the test
        if self.sm_logdb_exist:
            SM_DB.run_db_builder(self.ccf_sm_qry_i)

class ccf_flow_base_chk_agent(ccf_base_chk_agent):

    def pre_flow_requirements_for_pp_checking(self, flow: ccf_flow):
        time = flow.initial_time_stamp
        err_msg = ""
        if flow.initial_time_stamp is None:
            time = 0
            err_msg += "(pre_flow_requirements_for_pp_checking): initial_time_stamp is None we cannot check this flow - TID {}\n".format(flow.uri['TID'])
        if flow.flow_is_hom() and flow.first_accept_time is None:
            err_msg += "(pre_flow_requirements_for_pp_checking): it seems that the follow trasnaction (TID {}) wasn't accepted in the pipe till EOT\n".format(flow.uri['TID'])

        if(err_msg != ""):
            err_msg += "We will skip the checking of the transaction TID -{} because of the errors that was found in the pre checking stage".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=time, msg=err_msg)
            return False
        else:
            return True

    def pre_check_flow_conditions(self, checker_ptr, flow: ccf_flow):
        return self.pre_flow_requirements_for_pp_checking(flow) and checker_ptr.should_check_flow(flow)

    def run_checker_on_each_flow(self, checker_ptr):
        for flow_key, flow in self.ccf_flows.items():
            if self.pre_check_flow_conditions(checker_ptr, flow):
                checker_ptr.check_flow(flow)


