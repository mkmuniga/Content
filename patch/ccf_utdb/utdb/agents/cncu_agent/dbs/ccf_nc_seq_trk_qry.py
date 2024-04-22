from val_utdb_bint import bint
from val_utdb_components import val_utdb_qry

from agents.cncu_agent.common.cncu_types import SB_TRANSACTION, SEQ_TRK_ITEM


class CCF_NC_SEQ_TRK_QRY(val_utdb_qry):

    def __init__(self):
        self.pmi_wire_ev_qry = None

    def queries(self):
        self.pmi_wire_ev_qry = (self.DB.all.SEQ_NAME.contains("ccf_nc_pmi_event_seq") &
                                self.DB.all.SEQ_STATUS.contains("overflow = 1"))

    def get_nc_pmi_wire_ev_records(self):
        pmi_wire_events = list()
        for group in self.DB.execute(self.DB.flow(self.pmi_wire_ev_qry)):
            for record in group.EVENTS:
                pmi_wire_events.append(self.SEQ_TRK_REC(record).get_tran())
        return pmi_wire_events


    class SEQ_TRK_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)

        def get_tran(self) -> SEQ_TRK_ITEM:
            return SEQ_TRK_ITEM(
                time=int(self.r.TIME),
                parent_name=self.r.PARENT_NAME,
                seq_name=self.r.SEQ_NAME,
                cmd=self.r.CMD,
                addr=self.__get_addr(),
                sqr_name=self.r.SQR_NAME,
                env_phase=self.r.ENV_PHASE,
                seq_status=self.r.SEQ_STATUS
            )

        def __get_addr(self):
            if self.r.ADDRESS == "-":
                return None
            return bint(int(self.r.ADDRESS))
