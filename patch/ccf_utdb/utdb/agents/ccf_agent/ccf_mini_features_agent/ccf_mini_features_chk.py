#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from agents.ccf_queries.ccf_hw_col_qry import ccf_hw_col_qry
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG,EOT
from agents.ccf_agent.ccf_base_agent.ccf_base_chk_agent import ccf_base_chk_agent
from agents.ccf_common_base.coh_global import COH_GLOBAL
from agents.ccf_agent.ccf_mini_features_agent.ccf_mini_features_qry import ccf_mini_features_qry

class ccf_mini_features_chk(ccf_base_chk_agent):

    def __init__(self):
        self.ccf_ral_agent_i = ccf_ral_agent.create()
        self.ccf_coherency_qry_i = ccf_coherency_qry.create()
        self.ccf_mini_features_qry_i = ccf_mini_features_qry.create()
        #self.ccf_hw_col_qry_i = ccf_hw_col_qry.create()
        self.peer_clk_req_cnt_dict = {"santa0":0,"santa1":0}


    def reset(self):
        self.peer_clk_req_cnt_dict = {"santa0": 0, "santa1": 0}


    def is_checker_enable(self):
        return True


    def peer_clk_req_count_chk(self):
            self.all_records_peer_clk_hw_col = self.ccf_mini_features_qry_i.get_peer_clk_sig()
            peer_clk_req_cnt_reg_santa = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i,"santa_regs","PEER_CLK_REQ_CNT","clk_req_cnt")


            for rec in self.all_records_peer_clk_hw_col:
                #print("all_records_peer_clk_hw_col", len(self.all_records_peer_clk_hw_col))
                for rec_entry in rec.EVENTS: ##TO
                    #print("rec_entry",rec_entry)
                    event = self.ccf_mini_features_qry_i.rec(rec_entry)
                    if event.r.DATA_STR == "1":
                        if "santa0" in event.r.SIGNAL_NAME:
                            peer_clk_req_en_santa_0 = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "santa_regs",
                                                                                   "TELEMETRY_CONTROL",
                                                                                   "PeerClkReqCntEn", event.r.TIME)
                            if peer_clk_req_en_santa_0 and event.r.TIME >= COH_GLOBAL.global_vars["START_OF_TEST"] and event.r.TIME <=  COH_GLOBAL.global_vars["END_OF_TEST"]:
                                self.peer_clk_req_cnt_dict["santa0"] += 1

                                #self.reset()



            if peer_clk_req_cnt_reg_santa != self.peer_clk_req_cnt_dict["santa0"]:
                err_msg = "SANTA0: the peer clk req actual does't match the expected: actual:{} whereas expected :{}.".format(peer_clk_req_cnt_reg_santa,self.peer_clk_req_cnt_dict["santa0"])
                VAL_UTDB_ERROR(msg=err_msg,time=EOT)

    def run(self):
        if COH_GLOBAL.global_vars["C6_TIMES_IN_TEST"] == []: # TODO: remove this when the ctate bug with HSD: 13010498579 will be fix
            self.peer_clk_req_count_chk()
