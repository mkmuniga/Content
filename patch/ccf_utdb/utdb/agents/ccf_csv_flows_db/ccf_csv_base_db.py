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
import os
import UsrIntel.R1
from agents.ccf_common_base.ccf_pp_params import ccf_pp_params
import sys
sys_path = sys.path
for item in sys_path:
    print(item)
sys.path.remove(None)
from tabulate import tabulate
import pandas as pd
from val_utdb_base_components import val_utdb_component

class ccf_csv_base_db(val_utdb_component):
    def __init__(self):
        super().__init__()
        self.FlowFileFolder = ""
        self.list_of_csv_flow_files = []


    def clean_df(self,df):
        # Clean columns
        df.columns = df.columns.str.strip()
        # clean data base
        df_obj = df.select_dtypes(['object'])
        df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        return df

    def get_full_llc_exp_state(self, llc_state):
        llc_state_tmp = llc_state.replace('LLC_', '')
        if "!" in llc_state_tmp:
            state_to_remove = llc_state_tmp.replace('!', '')
            mesi = ['M', 'E', 'S', 'I']
            mesi.remove(state_to_remove)
            return "/".join(mesi)
        else:
            return llc_state_tmp

    def convert_llc_state(self, df):
        df['LLC State'] = df['LLC State'].apply(self.get_full_llc_exp_state)
        return df

    def __create_csv_dataframe(self):
        self.__csv_db = dict()
        for file_name in self.list_of_csv_flow_files:
            file_path = self.FlowFileFolder + file_name
            csv_table = pd.read_csv(file_path, header=1, dtype=str, keep_default_na=False)
            csv_table = self.clean_df(csv_table)
            csv_table = self.convert_llc_state(csv_table)

            #print(tabulate(csv_table, headers='keys', tablefmt='psql'))
            key = csv_table.loc[0, 'Flow']
            self.__csv_db[key] = csv_table


    @property
    def csv_db(self):
        if hasattr(self, "__csv_db"):
            return self.__csv_db
        else:
            self.__create_csv_dataframe()
            return self.__csv_db













