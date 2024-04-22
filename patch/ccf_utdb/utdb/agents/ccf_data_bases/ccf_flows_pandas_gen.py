from agents.ccf_common_base.ccf_common_base_class import ccf_base_chk
from val_utdb_report import VAL_UTDB_MSG
import UsrIntel.R1
import pandas as pd
import os

class ccf_flows_pandas_gen(ccf_base_chk):

    def __init__(self):
        self.flows_df = None

    def run(self):
        if self.si.ccf_pp_flow_to_df_en:
            self.convert_flows_to_df()

    def convert_flows_to_df(self):
        VAL_UTDB_MSG(time=0, msg='Converting CCF Flows into a pandas data base')
        self.flows_df = pd.DataFrame([flow.__dict__ for flow in self.ccf_flows.values()])

        #clean and orginize the data
        self.flows_df["TID"] = ""
        self.flows_df["LID"] = ""
        self.flows_df["PID"] = ""

        for i in range(len(self.flows_df)):
            uri = self.flows_df.loc[i].uri
            self.flows_df.at[i, "TID"] = uri["TID"]
            self.flows_df.at[i, "LID"] = uri["LID"]
            self.flows_df.at[i, "PID"] = uri["PID"]
            self.flows_df.at[i,"llc_uops"] = ','.join([str(uop) for uop in self.flows_df.at[i, "llc_uops"]])
            self.flows_df.at[i,"snooped_cores"] = ','.join([str(core) for core in self.flows_df.at[i, "snooped_cores"]])
            rej_list_flat = [item for sublist in self.flows_df.at[i,"rejected_reasons"] for item in sublist]
            self.flows_df.at[i, "rejected_reasons"] = ",".join([str(rej) for rej in rej_list_flat])
            self.flows_df.at[i, "pipe_arbcommands"] = ",".join([str(arbcom.arbcommand_opcode) for arbcom in self.flows_df.at[i, "pipe_arbcommands"]])
            self.flows_df.at[i, "snoop_responses"] = ",".join([str(snp_rsp.snoop_rsp_opcode) for snp_rsp in self.flows_df.at[i, "snoop_responses"]])
            self.flows_df.at[i, "flow_progress"] = ",".join([str(rec.rec_unit)+"_"+str(rec.rec_time)+"_"+str(rec.rec_opcode) for rec in self.flows_df.at[i, "flow_progress"]])


        #Drop unnesessary columns
        self.flows_df.drop('uri', axis='columns', inplace=True)
        self.flows_df.drop('flow_info_str', axis='columns', inplace=True)
        self.flows_df.drop('snoop_requests', axis='columns', inplace=True)

        #generate a csv file from the pandas df
        file_path = os.path.join(os.environ.get('OUTPUT_DIR', ""), 'flows_df.csv')
        #print(file_path)
        VAL_UTDB_MSG(time=0,msg="file: {}".format(file_path))
        self.flows_df.to_csv(file_path)

