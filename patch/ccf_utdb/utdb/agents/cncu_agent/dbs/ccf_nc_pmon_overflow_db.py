from val_utdb_components import val_utdb_qry


def signal_to_src_name(signal):
    if "Sbo2NcuRingPmonUnnnH_up" in signal:
        return "CBO"
    if "IDPPmonOverFlowUnn0H" in signal:
        return "SANTA0"
    if "IDP1PmonOverFlowUnn0H" in signal:
        return "SANTA1"
    if "EVPmonFIxedCntOverflowU921H" in signal:
        return "NCU"


class NC_PMON_OVERFLOW_DB(val_utdb_qry):

    def __init__(self):
        self._pmon_overflow_indications = list()
        self._all_recs = None
        self._valid_recs = None
        self._overflow_indication = None
        self._cbo_overflow = None
        self._santa0_overflow = None
        self._santa1_overflow = None
        self._ncu_overflow = None
        self._any_overflow_indication = None
        self._all_pmon_overflow_indications = None

    def queries(self):
        self._all_recs = self.DB.all.TIME >= 0
        self._valid_recs = self.DB.all.REC_TYPE.inList("valid")
        self._overflow_indication = self.DB.all.DATA0 == 1
        self._cbo_overflow = self.DB.all.SIGNAL_NAME.contains("Sbo2NcuRingPmonUnnnH_up")
        self._santa0_overflow = self.DB.all.SIGNAL_NAME.contains("IDPPmonOverFlowUnn0H")
        self._santa1_overflow = self.DB.all.SIGNAL_NAME.contains("IDP1PmonOverFlowUnn0H")
        self._ncu_overflow = self.DB.all.SIGNAL_NAME.contains("EVPmonFIxedCntOverflowU921H")
        self._any_overflow_indication = (self._cbo_overflow | self._santa0_overflow |
                                         self._santa1_overflow | self._ncu_overflow)
        self._all_pmon_overflow_indications = self._all_recs & self._valid_recs & self._overflow_indication & self._any_overflow_indication

    def build_db(self):
        for pmon_indications in self.DB.execute(self.DB.flow(self._all_pmon_overflow_indications['+'])):
            for event in pmon_indications.EVENTS:
                pmi_src = signal_to_src_name(event.SIGNAL_NAME)
                self._pmon_overflow_indications.append({'src': pmi_src, 'time': event.TIME})
        pass

    def get_pmon_overflow_indications(self):
        return self._pmon_overflow_indications
