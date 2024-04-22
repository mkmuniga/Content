#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_data_analyzer.py
#
# Owner:              meirlevy
# Creation Date:      02.2021
#
# ###############################################
#
# Description:
#   This DB will describe the CCF flows and will take it's data from the CSV files
#################################################################################################
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
from agents.ccf_csv_flows_db.ccf_csv_base_db import ccf_csv_base_db


class ccf_csv_cms_db(ccf_csv_base_db):
    def __init__(self):
        super().__init__()
        self.FlowFileFolder = ccf_pp_params.get_pointer().params["ccf_root"] + "/src/val/utdb/agents/ccf_cms_csv/"
        self.list_of_csv_flow_files = [
                                       "rfo_cv_state.csv",
                                       "rfo_map.csv"
                                      ]


    def convert_llc_state(self, df):
        column = "initial_cache_state"
        column_exists = column in df.columns
        if column_exists:
            df['initial_cache_state'] = df['initial_cache_state'].apply(self.get_full_llc_exp_state)
        return df












