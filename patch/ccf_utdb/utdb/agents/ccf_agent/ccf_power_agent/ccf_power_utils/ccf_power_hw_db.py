from val_utdb_bint import bint
from val_utdb_components import val_utdb_qry

from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class POWER_HW_DB(ccf_base_qry):

    #def __init__(self):

        #self._meom_db = list()
        #self._pmsb_meom = None


    def queries(self):
        self._pmsb_meom = self.DB.all.SIGNAL_NAME.contains("ccfpma_pmsb_ep_meom")
        self.value_is_1 = self.DB.all.DATA_STR == "1"
        self.value_is_0 = self.DB.all.DATA_STR == "0"
        self.value_is_x = self.DB.all.DATA_STR == "x"
        self._pmsb_cput = self.DB.all.SIGNAL_NAME.contains("ccfpma_pmsb_ep_mpcput")
        self.rec_type_is_valid = self.DB.all.REC_TYPE == "valid"
        self.rec_type_is_invalid = self.DB.all.REC_TYPE == "invalid"


    def get_list_of_eom_times(self):
        eom_time_list = list()
        e = self._pmsb_meom & self.value_is_1
        for events in self.DB.execute(self.DB.flow(e)):
            for event in events.EVENTS:
                eom_time_list.append(event.TIME)

        eom_time_list.sort()
        return eom_time_list


    def get_dict_of_pcput_times(self):
        pcput_time_dict = dict()
        e = self._pmsb_cput &  self.rec_type_is_valid
        for events in self.DB.execute(self.DB.flow(e)):
            for event in events.EVENTS:
                pcput_time_dict[event.TIME] = event.DATA_STR

        return pcput_time_dict

    def get_list_of_asserted_pcput_times(self):
        asserted_pcput_time = list()
        e = self._pmsb_cput &  self.rec_type_is_valid & self.value_is_1
        for events in self.DB.execute(self.DB.flow(e)):
            for event in events.EVENTS:
                asserted_pcput_time.append(event.TIME)

        asserted_pcput_time.sort()
        return asserted_pcput_time


    def get_list_of_de_asserted_pcput_times(self):
        de_asserted_pcput_time = list()
        ignore_next_line=0
        e = self._pmsb_cput & (self.value_is_0 |self.value_is_x)
        for events in self.DB.execute(self.DB.flow(e)):
            for event in events.EVENTS:
                if event.REC_TYPE == 'invalid':
                    ignore_next_line=1
                    break
                if ignore_next_line==1:
                    print ("Next Line is invalid so we won;t append it")
                    ignore_next_line=0
                else:
                     de_asserted_pcput_time.append(event.TIME)

        de_asserted_pcput_time.sort()
        #de_asserted_pcput_time.pop(0) #the first argument indicates start of test and not first de-assert
        return de_asserted_pcput_time