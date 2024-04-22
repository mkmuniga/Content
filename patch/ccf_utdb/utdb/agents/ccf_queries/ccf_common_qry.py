from val_utdb_bint import bint
from val_utdb_components import val_utdb_qry
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry
# from agents.ccf_common_base.ccf_sb_agent import SB_TRANSACTION

class CCF_COMMON_QRY(val_utdb_qry):

    def __init__(self):
        self.common_qry = None


    def queries(self):
       # self.common_qry = (self.DB.all.TRACKER == "try.log")
       # self.CLK=self.common_qry.CLK
       # self.TIMEPERIOD=(self.DB.all.TIMEPERIOD == '@Timeperiod')
        self.CLK=(self.DB.all.CLK == 'uclk')
        self.only_santa_q_trk = (self.DB.all.SELECTOR == "santaq")
        self.santa_0=(self.DB.all.UNIT=='SANTA_0')
        self.santa_1=(self.DB.all.UNIT=='SANTA_1')

    def get_common_records(self):
        return self.DB.execute(self.DB.flow(self.CLK))

    def get_santa_q_records(self, santa_inst):
        if(santa_inst=="SANTA_0"):
            block=self.only_santa_q_trk & self.santa_0
        else:
            block=self.only_santa_q_trk & self.santa_1
        return self.DB.execute(self.DB.flow(block))

    class COMMON_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)


        def get_timeperiod(self):
            return int(self.r.TIMEPERIOD)

        def get_clk_name(self):
            return self.r.CLK

class ccf_common_custom_qry(ccf_base_qry):

    def queries(self):
        self.cbo_ingress_arbiterstate_ha0 = self.DB.all.SIGNAL_NAME.contains('ArbiterStateHA0U109H')
        self.cbo_ingress_arbiterstate_ha1 = self.DB.all.SIGNAL_NAME.contains('ArbiterStateHA1U109H')
        self.cbo_ingress_qbid = self.DB.all.SIGNAL_NAME.contains('QBidU110H')
        self.cbo_qbid_ha0 = self.DB.all.SIGNAL_NAME.contains('arbiter0')
        self.cbo_qbid_ha1 = self.DB.all.SIGNAL_NAME.contains('arbiter1')
        self.rdifaactiveentries=self.DB.all.SIGNAL_NAME.contains('RdIfaActiveEntries')
        self.is_santa0=self.DB.all.SIGNAL_NAME.contains('santa0_inst')
        self.is_santa1=self.DB.all.SIGNAL_NAME.contains('santa1_inst')
        self.rec_type_is_valid = self.DB.all.REC_TYPE == 'valid'



    def get_cbo_ingress_arbiterstate_ha0(self):
        block = self.cbo_ingress_arbiterstate_ha0 & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(block))

    def get_cbo_ingress_arbiterstate_ha1(self):
        block = self.cbo_ingress_arbiterstate_ha1 & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(block))

    def get_cbo_ingress_qbid_ha0(self):
        block = self.cbo_ingress_qbid & self.rec_type_is_valid & self.cbo_qbid_ha0
        return self.DB.execute(self.DB.flow(block))

    def get_cbo_ingress_qbid_ha1(self):
        block = self.cbo_ingress_qbid & self.rec_type_is_valid & self.cbo_qbid_ha1
        return self.DB.execute(self.DB.flow(block))

    def get_santa_rdifaactiveentry_value(self, santa_num):
        if(santa_num==0):
            block = self.is_santa0 & self.rec_type_is_valid & self.rdifaactiveentries 
        else:
            block = self.is_santa1 & self.rec_type_is_valid & self.rdifaactiveentries 
        return self.DB.execute(self.DB.flow(block))

    class ccf_common_custom_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass
