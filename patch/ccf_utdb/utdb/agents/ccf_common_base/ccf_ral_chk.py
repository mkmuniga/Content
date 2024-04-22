#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_ral_chk.py
#
# Owner:              ekupietz
# Creation Date:      10.2020
#
# ###############################################
#
# Description:
#   This file contain all ccf ral checkers
#################################################################################################
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_report import VAL_UTDB_ERROR, EOT
from val_utdb_ral import val_utdb_ral, val_utdb_chk

class ccf_ral_chk(val_utdb_chk):


    def __init__(self):
        self.ral_json = ccf_pp_params.get_pointer().params["ral_json"]
        self.ral_inst = val_utdb_ral.initial(self.ral_json, "registers_logdb")

        self.signal_path_write = ''
        self.signal_path_read = ''
        self.write_dic ={}
        self.read_dic = {}
        self.ccf_ral_agent_i = ccf_ral_agent.get_pointer()

    def run(self):
        self.ccf_alive_ral_checker()


    def ccf_alive_ral_checker(self):
        cbo_id = CCF_UTILS.get_physical_id_by_logical_id(0)

        end_value = ccf_registers.get_pointer().get_eot_mktme_mask(cbo_id)
        #TODO meirlevy - need to return this check once we fix the MKTME or choose a diffrent register once we enable the cr_randomiztion again.
        # if ((end_value != self.si.ccf_mktme_mask) and self.si.enable_cr_randomization == 1):
        #     VAL_UTDB_ERROR(time=EOT, msg='Expected register value to be modified by the end of test')



