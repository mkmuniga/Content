from val_utdb_bint import bint
from val_utdb_components import val_utdb_qry

from agents.cncu_agent.common.cncu_defines import SB
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


class CCF_NC_SB_QRY(val_utdb_qry):

    def __init__(self):
        self.ncevents_sb_qry = None
        self.ncu_pcu_msgs_qry = None

    def queries(self):
        self.ncevents_sb_qry = (self.DB.all.PORT.contains("NCEVENTS"))
        self.ncu_pcu_msgs_qry = (self.DB.all.PORT.contains("PMC_GPSB") &\
                                 (self.DB.all.OPC.inList(SB.OPCODES.ncu_pcu_msg, SB.OPCODES.pcu_ncu_msg)))

    def get_nc_sb_records(self):
        return self.DB.execute(self.DB.flow(self.ncevents_sb_qry | self.ncu_pcu_msgs_qry))

    class SB_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)

        def get_tran(self) -> SB_TRANSACTION:
            return SB_TRANSACTION(
                time=self.__get_time(),
                start_time=self.__get_start_time(),
                uri=self.__get_uri(),
                msg_type=self.r.TYPE,
                opcode=self.__get_opcode(),
                src_pid=self.__get_src_pid(),
                dest_pid=self.__get_dest_pid(),
                tag=self.__get_tag(),
                misc=self.__get_misc(),
                eh=self.__get_eh(),
                byte_en=self.__get_byte_en(),
                fid=self.__get_fid(),
                bar=self.__get_bar(),
                addr_len=self.__get_addr_len(),
                rsp=self.__get_rsp(),
                sai=self.__get_sai(),
                addr=self.__get_addr(),
                data=self.__get_data()
            )

        def __get_time(self):
            if self.r.LOGDBHEADERSNAME == 'racu_sb':
                return self.r.TIME
            return self.r.TIMESTAMP

        def __get_start_time(self):
            if self.r.LOGDBHEADERSNAME == 'racu_sb':
                return None
            return int(self.r.START_TIME)

        def __get_src_pid(self):
            return bint(int(self.r.SPID + self.r.LSPID, 16))

        def __get_dest_pid(self):
            return bint(int(self.r.DPID + self.r.LDPID, 16))

        def __get_eh(self):
            return int(self.r.EH)

        def __get_byte_en(self):
            if  "-" in self.r.BE:
                return None
            return bint(int(self.r.BE, 16))

        def __get_sai(self):
            if self.__get_eh() == 1:
                return bint(int(self.r.SAI[6:8], 16))
            return None

        def __get_fid(self):
            if "-" in self.r.FID:
                return None
            return bint(int(self.r.FID, 16))

        def __get_bar(self):
            if "-" in self.r.BAR:
                return None
            return bint(int(self.r.BAR, 16))

        def __get_data(self):
            if "-" in self.r.DATA:
                return None
            return CNCU_UTILS.str_to_bytes(self.r.DATA)

        def __get_addr(self):
            if "-" in self.r.ADDRESS:
                return None
            return bint(int(self.r.ADDRESS, 16))

        def __get_addr_len(self):
            if self.r.ADDRLEN == "-":
                return None
            return int(self.r.ADDRLEN)

        def __get_rsp(self):
            if "-" in self.r.RSP:
                return None
            return bint(int(self.r.RSP, 16))

        def __get_tag(self):
            return bint(int(self.r.TAG, 16))

        def __get_misc(self):
            if "-" in self.r.MISC:
                return None
            return bint(int(self.r.MISC, 16))

        def __get_opcode(self):
            if self.r.LOGDBHEADERSNAME == 'racu_sb':
                return self.r.OPCODE
            return self.r.OPC

        def __get_uri(self):
            if self.r.LOGDBHEADERSNAME == 'racu_sb':
                return self.r.TID
            return None
