from val_utdb_bint import bint
from val_utdb_components import val_utdb_qry
from agents.ccf_agent.ccf_power_agent.common_power.ccf_power_sb_base_txn import SB_TRANSACTION


class CCF_POWER_SB_QRY(val_utdb_qry):

    def __init__(self):
        self.pmc_pmsb_sb_qry = None

    def queries(self):
        self.pmc_pmsb_sb_qry = (self.DB.all.TRACKER == "_pmsb_pmc_trk.log")

    def get_power_sb_records(self):
        return self.DB.execute(self.DB.flow(self.pmc_pmsb_sb_qry))

    class SB_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)

        def get_tran(self) -> SB_TRANSACTION:
            return SB_TRANSACTION(
                time=self.r.TIME,
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

        def __get_src_pid(self):
            return bint(int(self.r.SPID, 16))

        def __get_dest_pid(self):
            return bint(int(self.r.DPID, 16))

        def __get_eh(self):
            return int(self.r.EH)

        def __get_byte_en(self):
            if self.r.BE == "-":
                return None
            return bint(int(self.r.BE, 16))

        def __get_sai(self):
            if self.__get_eh() == 1:
                return bint(int(self.r.SAI[6:8], 16))
            return None

        def __get_fid(self):
            if self.r.FID == "-":
                return None
            return bint(int(self.r.FID, 16))

        def __get_bar(self):
            if self.r.BAR == "-":
                return None
            return bint(int(self.r.BAR, 16))

        def __get_data(self):
            if self.r.DATA == "-":
                return None
            return self.str_to_bytes(self.r.DATA)

        def str_to_bytes(self, hex_str: str):
            bytes_list = list()
            if len(hex_str) % 2 == 1:
                hex_str = '0' + hex_str
            for i in range(int(len(hex_str) / 2)):
                bytes_list.insert(0, bint(int(hex_str[(i * 2):(i * 2) + 2], 16)))
            return bytes_list

        def __get_addr(self):
            if self.r.ADDRESS == "-":
                return None
            return bint(int(self.r.ADDRESS, 16))

        def __get_addr_len(self):
            if self.r.ADDRLEN == "-":
                return None
            return int(self.r.ADDRLEN)

        def __get_rsp(self):
            if self.r.RSP == "-":
                return None
            return bint(int(self.r.RSP, 16))

        def __get_tag(self):
            return bint(int(self.r.TAG, 16))

        def __get_misc(self):
            if self.r.MISC == "-":
                return None
            return bint(int(self.r.MISC, 16))

        def __get_opcode(self):
            # if self.r.LOGDBHEADERSNAME == 'racu_sb':
            #     return self.r.OPCODE
            return self.r.OPC

        def __get_uri(self):
            # if self.r.LOGDBHEADERSNAME == 'racu_sb':
            #     return self.r.TID
            return None
