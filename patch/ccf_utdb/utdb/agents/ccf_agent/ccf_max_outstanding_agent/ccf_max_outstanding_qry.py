from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_max_outstanding_qry(ccf_base_qry):

    def queries(self):
        self.cfi_dbs = self.DB.all.SELECTOR == 'cfi'
        self.santa = self.DB.all.UNIT.contains('CCF_VC_SANTA')
        self.upi_c = self.DB.all.PROTOCOL_ID.contains('UPI_C')
        self.cxm = self.DB.all.PROTOCOL_ID.contains('CXM')
        self.upi_nc = (self.DB.all.PROTOCOL_ID.contains('UPI_NC'))
        self.msg_class_ncs = self.DB.all.MSG_CLASS.contains('NCS')
        self.msg_class_ncb = self.DB.all.MSG_CLASS.contains('NCB')
        self.msg_class_rsp = self.DB.all.MSG_CLASS.contains('RSP')



    def get_santa_and_upi_c_cxm_records(self):
        santa_entry = self.santa
        upi_c_entry = self.upi_c
        cxm_entry = self.cxm
        upi_c_santa = (santa_entry & upi_c_entry)
        cxm_and_santa = (santa_entry & cxm_entry)
        santa_and_upi_c_cxm_entry = self.DB.flow(upi_c_santa | cxm_and_santa)
        return self.DB.execute(santa_and_upi_c_cxm_entry)

    def get_upi_nc_records(self):
        upi_nc_entry = self.DB.flow(self.cfi_dbs & self.upi_nc)
        return self.DB.execute(upi_nc_entry)

    class ccf_max_outstanding_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass


class ccf_max_outstanding_custom_qry(ccf_base_qry):

    def queries(self):
        self.signal_is_max_outstanding_wr_ifa_block = (self.DB.all.SIGNAL_NAME.contains('MaxOutstandingWritesBlock'))
        self.signal_is_max_outstanding_rd_ifa_block = (self.DB.all.SIGNAL_NAME.contains('MaxOutstandingReadsBlock'))
        self.signal_is_max_outstanding_general_block = (self.DB.all.SIGNAL_NAME.contains('MaxOutStandingGBlock'))
        self.signal_is_max_outstanding_specific_block = (self.DB.all.SIGNAL_NAME.contains('MaxOutStandingSBlock'))
        self.rd_ifa_entries = self.DB.all.SIGNAL_NAME.contains('RdIfaActiveEntries')
        self.wr_ifa_entries = self.DB.all.SIGNAL_NAME.contains('WrIfaActiveEntries')
        self.general_counter = self.DB.all.SIGNAL_NAME.contains('NCUMaxOutStandingGCounterUnnnH')
        self.specific_counter = self.DB.all.SIGNAL_NAME.contains('NCUMaxOutStandingSCounterUnnnH')
        self.signal_is_santa_0 = self.DB.all.SIGNAL_NAME.contains('santa0_inst')
        self.signal_is_santa_1 = self.DB.all.SIGNAL_NAME.contains('santa1_inst')
        self.rec_type_is_valid = self.DB.all.REC_TYPE == 'valid'


    def get_all_max_outstanding_wr_block(self):
        wr_block = self.DB.flow(self.DB.flow(self.signal_is_max_outstanding_wr_ifa_block & self.rec_type_is_valid))
        return self.DB.execute(self.DB.flow(wr_block))
    def get_all_rd_active_entries(self):
        rd_active_entries = self.rd_ifa_entries & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(rd_active_entries))
    def get_rd_active_entries_santa0(self):
        rd_active_entries = self.rd_ifa_entries & self.signal_is_santa_0 & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(rd_active_entries))
    def get_rd_active_entries_santa1(self):
        rd_active_entries = self.rd_ifa_entries & self.signal_is_santa_1 & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(rd_active_entries))
    def get_wr_active_entries_santa0(self):
        wr_active_entries = self.wr_ifa_entries & self.signal_is_santa_0 & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(wr_active_entries))
    def get_wr_active_entries_santa1(self):
        wr_active_entries = self.wr_ifa_entries & self.signal_is_santa_1 & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(wr_active_entries))
    def get_all_max_outstanding_rd_block(self):
        rd_block = self.signal_is_max_outstanding_rd_ifa_block & self.rec_type_is_valid
        return self.DB.execute(self.DB.flow(rd_block))

    def get_all_actives_entries_and_block_records(self):
        rd_active_entries =  self.rd_ifa_entries & self.rec_type_is_valid
        wr_active_entries = self.wr_ifa_entries & self.rec_type_is_valid
        rd_block = self.signal_is_max_outstanding_rd_ifa_block & self.rec_type_is_valid
        wr_block = self.signal_is_max_outstanding_wr_ifa_block & self.rec_type_is_valid
        active_entries_and_block = self.DB.flow(rd_active_entries | rd_block | wr_active_entries | wr_block)
        return self.DB.execute(active_entries_and_block)

    def get_all_nc_actives_entries_and_nc_block_records(self):
        general_counter =  self.general_counter & self.rec_type_is_valid
        specific_counter = self.specific_counter & self.rec_type_is_valid
        general_block = self.signal_is_max_outstanding_general_block & self.rec_type_is_valid
        specific_block = self.signal_is_max_outstanding_specific_block & self.rec_type_is_valid
        nc_active_entries_and_block = self.DB.flow(general_counter | specific_counter | general_block | specific_block)
        return self.DB.execute(nc_active_entries_and_block)

    def get_santa0_max_outstanding_rd_block(self):
        rd_block = self.signal_is_max_outstanding_rd_ifa_block & self.rec_type_is_valid & self.signal_is_santa_0
        return self.DB.execute(self.DB.flow(rd_block))

    def get_santa1_max_outstanding_rd_block(self):
        rd_block = self.signal_is_max_outstanding_rd_ifa_block & self.rec_type_is_valid & self.signal_is_santa_1
        return self.DB.execute(self.DB.flow(rd_block))

    def get_all_max_outstanding_block(self):
        rd_wr_block = self.DB.flow(self.DB.flow((self.signal_is_max_outstanding_wr_ifa_block | self.signal_is_max_outstanding_rd_ifa_block) & self.rec_type_is_valid))
        return self.DB.execute(self.DB.flow(rd_wr_block))

    def get_all_max_outstanding_specific_general_block(self):
        specif_general_block = self.DB.flow(self.DB.flow((self.signal_is_max_outstanding_specific_block | self.signal_is_max_outstanding_general_block) & self.rec_type_is_valid))
        return self.DB.execute(self.DB.flow(specif_general_block))

    class ccf_max_outstanding_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass


