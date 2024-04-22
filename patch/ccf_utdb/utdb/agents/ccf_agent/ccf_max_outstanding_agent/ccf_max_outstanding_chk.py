from agents.ccf_agent.ccf_max_outstanding_agent.ccf_max_outstanding_qry import ccf_max_outstanding_qry,ccf_max_outstanding_custom_qry
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_common_base.coh_global import COH_GLOBAL
from val_utdb_base_components import val_utdb_component, EOT
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent

class ccf_max_outstanding_chk(val_utdb_component):
    def __init__(self):
        self.ccf_max_outstanding_qry = ccf_max_outstanding_qry.get_pointer()
        self.ccf_ral_agent_i = ccf_ral_agent.create()
        self.check_wr_ifa = False
        self.ccf_max_outstanding_custom_qry= ccf_max_outstanding_custom_qry.get_pointer()
        self.ifa_entries_dict = {"rd_ifa":{"SANTA0":0,"SANTA1":0},"wr_ifa":{"SANTA0":0,"SANTA1":0}}
        self.uri_completions_dict = {"rd_ifa":{"SANTA0": {}, "SANTA1": {}}, "wr_ifa":{"SANTA0": {}, "SANTA1": {}}}
        self.nc_uri_dict = {"general":[],"specific":[]}
        self.last_max_outstanding_threshold = {"rd_ifa":{"SANTA0":0, "SANTA1":0}, "wr_ifa":{"SANTA0":0, "SANTA1":0}}
        self.max_oustanding_threshold = {"rd_ifa":{"SANTA0":0, "SANTA1":0}, "wr_ifa":{"SANTA0":0, "SANTA1":0}}
        self.nc_max_outstanding_threshold = {"general":0,"specific":0}
        self.nc_max_outstanding_en = {'general':0,"specific":0}
        self.max_oustanding_CB = {"rd_ifa": {"SANTA0": 1, "SANTA1": 1}, "wr_ifa": {"SANTA0": 1, "SANTA1": 1}}
        self.start_time_to_not_check = {"rd_ifa":{"SANTA0":0,"SANTA1":0},"wr_ifa":{"SANTA0":0,"SANTA1":0}}
        self.block_signal = {"rd_ifa":{"SANTA0":0,"SANTA1":0},"wr_ifa":{"SANTA0":0,"SANTA1":0}}
        self.number_of_trans_to_not_check = {"rd_ifa":{"SANTA0":0,"SANTA1":0},"wr_ifa":{"SANTA0":0,"SANTA1":0}}
        self.number_of_nc_trans_to_not_check = {"general":0,"specific":0}
        self.cncu_counter = {"general": 0, "specific": 0}
        self.last_nc_max_outstanding_threshold = {"general": 0, "specific": 0}
        self.nc_start_time_to_not_check = {"general": 0, "specific": 0}
        self.block_signal = {"general":0,"specific":0}
        self.nc_decreased_val = {"general":0,"specific":0}
        #self.active_entries_and_block_entries = None
        #self.get_all_nc_actives_entries_and_nc_block_records = None


    def reset(self):
        self.ifa_entries_dict = {"rd_ifa": {"SANTA0": 0, "SANTA1": 0}, "wr_ifa": {"SANTA0": 0, "SANTA1": 0}}
        self.uri_completions_dict = {"rd_ifa": {"SANTA0": {}, "SANTA1": {}}, "wr_ifa": {"SANTA0": {}, "SANTA1": {}}}
        self.nc_uri_dict = {"general": [], "specific": []}
        self.last_max_outstanding_threshold = {"rd_ifa": {"SANTA0": 0, "SANTA1": 0}, "wr_ifa": {"SANTA0": 0, "SANTA1": 0}}
        self.max_oustanding_threshold = {"rd_ifa": {"SANTA0": 0, "SANTA1": 0}, "wr_ifa": {"SANTA0": 0, "SANTA1": 0}}
        self.max_oustanding_CB = {"rd_ifa": {"SANTA0": 1, "SANTA1": 1}, "wr_ifa": {"SANTA0": 1, "SANTA1": 1}}
        self.start_time_to_not_check = {"rd_ifa": {"SANTA0": 0, "SANTA1": 0}, "wr_ifa": {"SANTA0": 0, "SANTA1": 0}}
        self.number_of_trans_to_not_check = {"rd_ifa": {"SANTA0": 0, "SANTA1": 0}, "wr_ifa": {"SANTA0": 0, "SANTA1": 0}}
        #self.active_entries_and_block_entries = None
        self.block_signal = {"rd_ifa": {"SANTA0": 0, "SANTA1": 0}, "wr_ifa": {"SANTA0": 0, "SANTA1": 0}}
        self.nc_max_outstanding_threshold = {'general': 0, "specific": 0}
        self.nc_max_outstanding_en = {'general': 0, "specific": 0}
        self.cncu_counter = {"general": 0, "specific": 0}
        self.nc_block_signal = {"general": 0, "specific": 0}
        self.number_of_nc_trans_to_not_check = {"general": 0, "specific": 0}
        #self.get_all_nc_actives_entries_and_nc_block_records = None

    def count_ifa_entries(self):
        self.all_records_cfi_trk = self.ccf_max_outstanding_qry.get_santa_and_upi_c_cxm_records()
        self.active_entries_and_block_entries = self.ccf_max_outstanding_custom_qry.get_all_actives_entries_and_block_records()

        for rec in self.all_records_cfi_trk:
            for rec_entry in rec.EVENTS:
                self.track_ifa(rec_entry,"rd_ifa")
                if self.check_wr_ifa:
                    self.track_ifa(rec_entry,"wr_ifa")

    def track_ifa(self, rec_entry,ifa_type):
        if rec_entry.TIME > COH_GLOBAL.global_vars["START_OF_TEST"] and rec_entry.TIME <= COH_GLOBAL.global_vars["END_OF_TEST"]:
            if 'SANTA' in rec_entry.UNIT:
                santa_name = self.get_santa_name_from_entry(rec_entry)
                self.populate_max_outstanding_CB_and_TH_values(santa_name, rec_entry.TIME,ifa_type)
                self.check_if_need_checking(santa_name, ifa_type, rec_entry.TIME)
                if self.should_increase_max_outstanding_counter(rec_entry,ifa_type):
                    self.increase_max_outstanding_counter(santa_name, rec_entry,ifa_type)
                elif self.should_decrease_max_outstanding_counter(rec_entry, ifa_type):
                    if ifa_type == 'rd_ifa':
                        self.decrease_max_outstanding_read_counter(santa_name, rec_entry)
                    if ifa_type == 'wr_ifa':
                        self.decrease_max_outstanding_write_counter(santa_name, rec_entry)
                self.last_max_outstanding_threshold[ifa_type][santa_name] = self.max_oustanding_threshold[ifa_type][santa_name]

            else:
                VAL_UTDB_ERROR(time=rec_entry.TIME,
                               msg="We didn't expect to have any record that didn't come from SANTA CFI interface.")


    def increase_max_outstanding_counter(self, santa_name, rec_entry,ifa_type):
        increment_value = 1 if ifa_type == "rd_ifa" else 0.5 # if we are in wr ifa case we will have two lines of write opcode in cfi traker so we can add 0.5
        self.ifa_entries_dict[ifa_type][santa_name] += increment_value
        self.update_ifa_dict(rec_entry, santa_name,ifa_type)
        if self.is_feature_enable(santa_name,ifa_type)and self.need_check(ifa_type, santa_name):
            self.chk_reach_max_outstanding(self.ifa_entries_dict[ifa_type][santa_name], santa_name, rec_entry, ifa_type)
        if self.number_of_trans_to_not_check[ifa_type][santa_name] > 0:
            self.number_of_trans_to_not_check[ifa_type][santa_name] -= increment_value




    def decrease_max_outstanding_read_counter(self, santa_name, rec_entry):
            if rec_entry.TID in self.uri_completions_dict['rd_ifa'][santa_name].keys():
                if "CmpO" in rec_entry.OPCODE or "Data_" in rec_entry.OPCODE or 'MemData' in rec_entry.OPCODE:
                    self.uri_completions_dict['rd_ifa'][santa_name][rec_entry.TID] -= 1
                    if self.uri_completions_dict['rd_ifa'][santa_name][rec_entry.TID] == 0:
                        self.ifa_entries_dict["rd_ifa"][santa_name] -= 1
                        if self.number_of_trans_to_not_check["rd_ifa"][santa_name] > 0:
                            self.number_of_trans_to_not_check["rd_ifa"][santa_name] -= 1
                        self.uri_completions_dict['rd_ifa'][santa_name].pop(rec_entry.TID)

    def decrease_max_outstanding_write_counter(self, santa_name, rec_entry):
            if rec_entry.TID in self.uri_completions_dict['wr_ifa'][santa_name].keys():
                if "CmpU" in rec_entry.OPCODE:
                    self.uri_completions_dict['wr_ifa'][santa_name][rec_entry.TID] -= 1
                    self.ifa_entries_dict["wr_ifa"][santa_name] -= 1
                    if self.uri_completions_dict['wr_ifa'][santa_name][rec_entry.TID] == 0:
                        self.uri_completions_dict['wr_ifa'][santa_name].pop(rec_entry.TID)
                    if self.number_of_trans_to_not_check["wr_ifa"][santa_name] > 0:
                        self.number_of_trans_to_not_check["wr_ifa"][santa_name] -= 1


    def get_santa_name_from_entry(self, rec_entry):
        return "SANTA" + str(rec_entry.UNIT[-1])

    def populate_max_outstanding_CB_and_TH_values(self, santa_name, time,ifa_type):
        if ifa_type == 'rd_ifa':
            self.max_oustanding_CB[ifa_type][santa_name] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "santa" + str(santa_name[-1]) + "_regs", "rd_ifa_config", "max_outstanding_reads_CB", time)

            self.max_oustanding_threshold[ifa_type][santa_name] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "santa" + str(santa_name[-1]) + "_regs", "rd_ifa_config", "max_outstanding_reads", time)
        if ifa_type == "wr_ifa":
            self.max_oustanding_CB[ifa_type][santa_name] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "santa" + str(santa_name[-1]) + "_regs", "wr_ifa_config", "max_outstanding_writes_CB", time)
            self.max_oustanding_threshold[ifa_type][santa_name] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i, "santa" + str(santa_name[-1]) + "_regs", "wr_ifa_config", "max_outstanding_writes", time)

    def should_increase_max_outstanding_counter(self, rec_entry,ifa_type):
        if ifa_type == "rd_ifa":
            return self.is_upi_c_read_opcode(rec_entry.OPCODE)
        if ifa_type == "wr_ifa":
            return self.is_upi_c_write_opcode(rec_entry.OPCODE)




    def should_decrease_max_outstanding_counter(self, rec_entry, ifa_type):
        santa_name = self.get_santa_name_from_entry(rec_entry)
        return rec_entry.TID in self.uri_completions_dict[ifa_type][santa_name].keys()

    def is_feature_enable(self, santa_name, ifa_type):
        return not self.max_oustanding_CB[ifa_type][santa_name]

    def is_nc_feature_enable(self,nc_max_out_type):
        return self.nc_max_outstanding_en[nc_max_out_type]

    def get_number_of_completions_needed(self,opcode):
        if opcode in ["InvXtoI", "InvItoE", "InvItoM"]:
            return 1
        else:
            return 3

    def get_nc_number_of_completions_needed(self,opcode):
        if opcode in ["NcRd", "NcRdPtl", "NcCfgRd", "NcIORd"]:
            return 2
        else:
            return 1

    def update_ifa_dict(self,rec_entry,santa_name,ifa_type):
        if ifa_type == "rd_ifa":
            self.uri_completions_dict['rd_ifa'][santa_name][rec_entry.TID] = self.get_number_of_completions_needed(rec_entry.OPCODE)
        else:
            self.uri_completions_dict['wr_ifa'][santa_name][rec_entry.TID] = 1

    def update_nc_dict(self,rec_entry,nc_max_out_type):
        if nc_max_out_type == "general":
            if rec_entry.TID not in self.nc_uri_dict['general']:
                self.nc_uri_dict['general'].append(rec_entry.TID)
        else:
            if rec_entry.TID not in self.nc_uri_dict['specific']:
                self.nc_uri_dict['specific'].append(rec_entry.TID)

    def check_if_need_checking(self, santa_name, ifa_type, time):
        if self.threshold_decreased(santa_name, ifa_type):
                    self.start_time_to_not_check[ifa_type][santa_name] = time
                    self.number_of_trans_to_not_check[ifa_type][santa_name] = self.get_number_of_trans_to_not_check_and_block_st(santa_name, ifa_type, time)

    def check_if_need_nc_checking(self,nc_max_out_type , time):
            if self.nc_threshold_decreased(nc_max_out_type):
                        self.nc_start_time_to_not_check[nc_max_out_type] = time
                        self.number_of_nc_trans_to_not_check[nc_max_out_type] = self.get_nc_number_of_trans_to_not_check_and_nc_block_st(nc_max_out_type,time)



    def need_check(self, ifa_type, santa_id):
        return not(self.number_of_trans_to_not_check[ifa_type][santa_id] and self.block_signal[ifa_type][santa_id] == 1)

    def nc_need_check(self,nc_max_out_ifa):
        return not(self.number_of_nc_trans_to_not_check[nc_max_out_ifa] and self.nc_block_signal[nc_max_out_ifa] == 1)




    def get_block_status(self,santa_id,event):
        if "Block" in event.r.SIGNAL_NAME:
            if "santa" + santa_id[-1] in event.r.SIGNAL_NAME:
                if "Read" in event.r.SIGNAL_NAME:
                    if event.r.DATA0 == 1:
                        self.block_signal['rd_ifa'][santa_id] = 1
                    else:
                        self.block_signal['rd_ifa'][santa_id] = 0
                if "Write" in event.r.SIGNAL_NAME:
                    if event.r.DATA0 == 1:
                        self.block_signal['wr_ifa'][santa_id] = 1
                    else:
                        self.block_signal['wr_ifa'][santa_id] = 0

    def get_nc_block_status(self,event):
        if "Block" in event.r.SIGNAL_NAME:
            if "NCUMaxOutStandingGBlock" in event.r.SIGNAL_NAME:
                if event.r.DATA0 == 1:
                    self.nc_block_signal['general'] = 1
                else:
                    self.nc_block_signal['general'] = 0
            if "NCUMaxOutStandingSBlock" in event.r.SIGNAL_NAME:
                if event.r.DATA0 == 1:
                    self.nc_block_signal['specific'] = 1
                else:
                    self.nc_block_signal['specific'] = 0

    def threshold_decreased(self, santa_name, type_ifa):
        return self.last_max_outstanding_threshold[type_ifa][santa_name] > self.max_oustanding_threshold[type_ifa][santa_name]

    def nc_threshold_decreased(self,nc_max_out_type):
        return self.last_nc_max_outstanding_threshold[nc_max_out_type] > self.nc_max_outstanding_threshold[nc_max_out_type]

    def get_number_of_trans_to_not_check_and_block_st(self, santa_name, ifa_type, time_for_th_change):
        signal_name = "RdIfaActiveEntries" if ifa_type == 'rd_ifa' else "WrIfaActiveEntries"
        for rec in self.active_entries_and_block_entries:
            for rec_entry in rec.EVENTS:
                event = self.ccf_max_outstanding_custom_qry.rec(rec_entry)
                self.get_block_status(santa_name,event)
                if signal_name in event.r.SIGNAL_NAME and "santa" + santa_name[-1] in event.r.SIGNAL_NAME and event.r.TIME >= time_for_th_change and \
                        self.max_oustanding_threshold[ifa_type][santa_name] <= event.r.DATA0:
                     return event.r.DATA0 - self.max_oustanding_threshold[ifa_type][santa_name]
        return self.number_of_trans_to_not_check[ifa_type][santa_name]

    def get_nc_number_of_trans_to_not_check_and_nc_block_st(self,nc_max_out_type, time_for_th_change):
        signal_name = "NCUMaxOutStandingGCounterUnnnH" if nc_max_out_type == 'general' else "NCUMaxOutStandingSCounterUnnnH"
        for rec in self.active_nc_entries_and_block_entries:
            for rec_entry in rec.EVENTS:
                event = self.ccf_max_outstanding_custom_qry.rec(rec_entry)
                self.get_nc_block_status(event)
                if signal_name in event.r.SIGNAL_NAME and event.r.TIME >= time_for_th_change and self.nc_max_outstanding_threshold[nc_max_out_type] <= event.r.DATA0:
                     return event.r.DATA0 - self.nc_max_outstanding_threshold[nc_max_out_type]
        return self.number_of_nc_trans_to_not_check[nc_max_out_type]



    def chk_reach_max_outstanding(self, ifa_entries, santa_id, rec_entry, ifa_type):
        if (ifa_entries > self.max_oustanding_threshold[ifa_type][santa_id] + 2): # it can be1-2 cycles between where we block and the IFA and so 2 transactions can pass the threshold. this is good enough for the feature
            err_msg = "(max_outstanding_" + str(ifa_type) + " santa_id-{}. We reached the max_outstanding threshold-{}, at URI-{}, when ifa_entries equals-{}.".format(santa_id,
                                                                                                                                                                       self.max_oustanding_threshold[ifa_type][santa_id], rec_entry.TID, ifa_entries)
            VAL_UTDB_ERROR(time=rec_entry.TIME,
                         msg=err_msg)



    def is_cfi_target(self,rec_entry):
        return rec_entry.MSG_CLASS in ["NCB","NCS","RSP"]

    def should_increase_nc_counter(self,nc_max_out_type,rec_entry):
        if nc_max_out_type == 'general':
            return self.is_upi_nc_write_opcode(rec_entry.OPCODE) or self.is_upi_nc_read_opcode(rec_entry.OPCODE)
        else:
            return (self.is_upi_nc_write_opcode(rec_entry.OPCODE) or self.is_upi_nc_read_opcode(rec_entry.OPCODE)) and self.is_specific_network_id(rec_entry.DSTID, rec_entry.TIME)

    def increase_nc_counter(self,rec_entry,nc_max_out_type):
        self.cncu_counter[nc_max_out_type] += 0.5
        self.update_nc_dict(rec_entry,nc_max_out_type)
        if self.is_nc_feature_enable(nc_max_out_type) and self.nc_need_check(nc_max_out_type):
            self.reach_nc_max_outstanding_threshold(self.cncu_counter[nc_max_out_type], rec_entry, nc_max_out_type)
        if self.number_of_nc_trans_to_not_check[nc_max_out_type] > 0:
            self.number_of_nc_trans_to_not_check[nc_max_out_type] -= 0.5

    def should_decrease_nc_counter(self,nc_opcode,rec_entry, nc_max_out_type):
        return (self.is_upi_nc_cmp(nc_opcode,rec_entry.VC_ID) or nc_opcode == 'NcData') and rec_entry.TID in self.nc_uri_dict[nc_max_out_type]

    def decrease_nc_counter(self,nc_max_out_type,rec_entry):
        if "CmpU" in rec_entry.OPCODE:
            self.cncu_counter[nc_max_out_type] -= 1
        if "Data" in rec_entry.OPCODE:
            self.cncu_counter[nc_max_out_type] -= 0.5

    def cncu_count(self,nc_max_out_type):
        self.all_nc_cfi_trk = self.ccf_max_outstanding_qry.get_upi_nc_records()
        self.active_nc_entries_and_block_entries = self.ccf_max_outstanding_custom_qry.get_all_nc_actives_entries_and_nc_block_records()

        for rec in self.all_nc_cfi_trk:
            for rec_entry in rec.EVENTS:
                if self.is_cfi_target(rec_entry):
                    self.populate_nc_max_outstanding_TH_CB_regs(nc_max_out_type, rec_entry.TIME)
                    self.check_if_need_nc_checking(nc_max_out_type, rec_entry.TIME)
                    if self.should_increase_nc_counter(nc_max_out_type,rec_entry):
                        self.increase_nc_counter(rec_entry,nc_max_out_type)
                    if self.should_decrease_nc_counter(rec_entry.OPCODE,rec_entry,nc_max_out_type):
                        self.decrease_nc_counter(nc_max_out_type,rec_entry)
                    self.last_nc_max_outstanding_threshold[nc_max_out_type] = self.nc_max_outstanding_threshold[nc_max_out_type]
        print(self.cncu_counter)

    def is_specific_network_id(self,transaction_network_id,time):
        max_oustanding_specific_network_id_mask = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                              "ncdecs", "NcuMaxoutstandingCtl",
                                                                              "SpecificCounterIdMask",time)
        max_oustanding_specific_network_id = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                                      "ncdecs", "NcuMaxoutstandingCtl",
                                                                                      "SpecificCounterNetworkId",time)
        transaction_network_id = transaction_network_id[transaction_network_id.find("(") + 1:transaction_network_id.find(")")]

        if max_oustanding_specific_network_id == int(transaction_network_id,16) & max_oustanding_specific_network_id_mask:
           return True

    def populate_nc_max_outstanding_TH_CB_regs(self,nc_max_out_type,time):
        if nc_max_out_type == "general":
            self.nc_max_outstanding_threshold['general'] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                        "ncdecs", "NcuMaxoutstandingCtl",
                                                                        "GeneralCounterThreshold", time)
            self.nc_max_outstanding_en['general'] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                 "ncdecs", "NcuMaxoutstandingCtl",
                                                                 "GeneralCounterEn", time)
        if nc_max_out_type == 'specific':
            self.nc_max_outstanding_threshold['specific'] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                            "ncdecs", "NcuMaxoutstandingCtl",
                                                                            "SpecificCounterThreshold", time)
            self.nc_max_outstanding_en['specific'] = ccf_ral_agent.read_reg_field(self.ccf_ral_agent_i,
                                                                      "ncdecs", "NcuMaxoutstandingCtl",
                                                                      "SpecificCounterEn", time)

    def reach_nc_max_outstanding_threshold(self,counter,rec_entry,nc_max_out_type):
        if (counter > self.nc_max_outstanding_threshold[nc_max_out_type] + 32) and self.nc_need_check(nc_max_out_type):
            err_msg = "(max_outstanding_general)We reached the max oustanding general threshold - {} at time  - {} ,at URI-{}, when counter equals-{}.".format(self.nc_max_outstanding_threshold[nc_max_out_type], rec_entry.TIME,rec_entry.TID,counter)
            VAL_UTDB_ERROR(time=rec_entry.TIME,
                         msg=err_msg)



    def is_upi_nc_cmp(self,opcode,vc_id):
        upi_nc_cmp_opcode = ["NCCmpU"]
        return ("NDR" in vc_id) and (opcode.lower().strip() in (string.lower().strip() for string in upi_nc_cmp_opcode))

    def is_upi_nc_write_opcode(self,opcode):
        upi_nc_write_opcodes = ["NcWr", "WcWrPtl", "NcCfgWr", "NcLTWr", "NcIOWr","WcWr","NcWrPtl"]
        return opcode in upi_nc_write_opcodes

    def is_upi_nc_read_opcode(self,opcode):
        upi_nc_read_opcodes = ["NcRd", "NcRdPtl", "NcCfgRd", "NcIORd"]
        return opcode in upi_nc_read_opcodes

    def is_upi_c_read_opcode(self,opcode):
        return opcode in ["RdCode", "RdData", "RdDataMig", "RdInvOwn", "InvXtoI", "RemMemSpecRd", "InvItoE",
                                   "RdInv", "InvItoM", "NonSnpRd"]

    def is_upi_c_write_opcode(self,opcode):
        return opcode in ["WbMtoI", "WbMtoS", "WbMtoE", "WbEtoI", "NonSnpWr", "WbMtoIPush", "EvctCln", "WbMtoIPtl", "WbMtoEPtl", "NonSnpWrPtl"]


    def run(self):
        self.count_ifa_entries()
        self.cncu_count('general')
        self.cncu_count('specific')



