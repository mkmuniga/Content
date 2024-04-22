#!/usr/bin/env python3.6.3a

#################################################################################################
# ccf_coherency_qry.py 
#
# Owner:              ranzohar & mlugassi
# Creation Date:      6.2021
#
# ###############################################
#
# Description:
#   This file contain all ccf NC queries and flow definitions
#################################################################################################

from val_utdb_bint import bint
from val_utdb_components import val_utdb_qry, pred_t

from agents.cncu_agent.common.cncu_defines import CFI, UFI
from agents.cncu_agent.common.cncu_types import IDI_TRANSACTION, CFI_TRANSACTION, UFI_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_sb_qry import CCF_NC_SB_QRY
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS


def is_victim_rec(nc_rec):
    return not nc_rec.is_racu_sb() and ("_VIC_" in nc_rec.r.LID or "_VIC_" in nc_rec.r.PID)


def execute_to_flows(execute_res):
    flows = list()
    for uri_groups in execute_res:
        flow = list()
        for event in uri_groups.EVENTS:
            nc_rec = CNCU_FLOW_QRY.NC_REC(event)
            if not is_victim_rec(nc_rec):
                tran = nc_rec.get_tran()
                flow.append(tran)
        if flow[0] is not None:
            flows.append(flow)

    return flows


class CNCU_FLOW_QRY(val_utdb_qry):
    nc_dbs: pred_t
    uri_stitch: pred_t
    cfi_ccf_only: pred_t
        
    def queries(self):

        self.nc_dbs = self.DB.all.LOGDBHEADERSNAME.inList('idi', 'cfi', 'ufi', 'racu_sb')
        self.uri_stitch = (self.DB.all.TID == '@tid')

    def __execute_nc_flows_qry(self):
        all = self.uri_stitch & self.nc_dbs

        uri_groups = self.DB.flow(all['+'])
        return self.DB.execute(uri_groups)

    def __execute_lock_flows_qry(self):
        all = self.uri_stitch & self.nc_dbs
        lock = all & (self.DB.all.OPCODE.contains("LOCK"))
        stopreq = all & (self.DB.all.MISC.contains("StopReq"))
        startreq = all & (self.DB.all.MISC.contains("StartReq"))

        uri_groups = self.DB.flow(lock | stopreq | startreq, all['+'])
        return self.DB.execute(uri_groups)

    def get_lock_flows_trans(self):
        return execute_to_flows(self.__execute_lock_flows_qry())

    def get_nc_flows(self):
        for uri_groups in self.__execute_nc_flows_qry():
            for event in uri_groups.EVENTS:
                print(event)
        return execute_to_flows(self.__execute_nc_flows_qry())

    class NC_REC(val_utdb_qry.val_utdb_rec):

        def __init__(self, rec):
            super().__init__(rec)

        def get_tran(self):
            if self.is_idi():
                return self.get_idi_transaction()

            elif self.is_cfi():
                return self.get_cfi_transaction()

            elif self.is_ufi():
                return self.get_ufi_transaction()

            elif self.is_racu_sb():
                return CCF_NC_SB_QRY.SB_REC(self.r).get_tran()

            return None

        def is_cfi(self):
            return self.DB_NAME == 'cfi'

        def is_ufi(self):
            return self.DB_NAME == 'ufi' and self.r.UFI_ID == "0"

        def is_idi(self):
            return self.DB_NAME == 'idi'

        def is_racu_sb(self):
            return self.DB_NAME == 'racu_sb'

        def get_addr_in_hex(self):
            if self.r.ADDRESS is not None and self.r.ADDRESS.lower() not in ['', '-', '0000deadbeef'] and "xx" not in self.r.ADDRESS:
                return bint(int(self.r.ADDRESS, 16))
            return None

        def get_length(self):
            metadata = []
            if self.is_cfi() and self.r.PKT_TYPE:
                metadata = self.r.MISC.split(' ')
            elif self.is_idi() and self.r.TYPE.endswith('REQ'):
                metadata = self.r.DATA.split(' ')

            for attr in metadata:
                if attr.startswith('len'):
                    return int(attr.split('=')[1], 16)
            return None

        def get_idi_byteen(self):
            metadata = []
            if self.r.TYPE.endswith("DATA"):
                metadata = self.r.ATTRIBUTES.split(' ')

            for attr in metadata:
                if attr.startswith('byteen'):
                    return bint(int(attr.split('=')[1], 16))
            return None

        def get_sai(self):
            metadata = []
            if self.is_cfi() and self.r.PKT_TYPE:
                metadata = self.r.MISC.split(' ')
            elif self.is_idi() and self.r.TYPE.endswith('REQ'):
                metadata = self.r.DATA.split(' ')

            for attr in metadata:
                if attr.startswith('sai'):
                    return bint(int(attr.split('=')[1], 16))
            return None

        def get_idi_int_data(self):
            if "Intdata" in self.r.DATA:
                metadata = self.r.DATA.split(" ")
                int_data = metadata[0].split("=")[1]
                return bint(int(int_data, 16))
            return None

        def get_cfi_msg_type(self):
            if "msg_type" in self.r.MISC:
                metadata = self.r.MISC.split(" ")
                msg_type = metadata[1].split("=")[1]
                return msg_type
            return None

        def get_cfi_param_a(self):
            if "paramA" in self.r.MISC:
                metadata = self.r.MISC.split(" ")
                param_a = metadata[0].split("=")[1]
                return bint(int(param_a, 16))
            return None

        def get_module_id(self):
            return 0 #TODO: In CBB need to give the right module ID as it should be for CBB

        def get_lp_id(self):
            if self.r.LPID == '-':
                return None
            return int(self.r.LPID)

        def get_idi_transaction(self):
            tran_type = self.r.TYPE
            chunk = None
            data = None
            if tran_type.endswith('DATA'):
                if self.r.CHUNK == '1100':
                    chunk = 1
                else:
                    chunk = 0
            if tran_type.endswith('DATA'):
                data = CNCU_UTILS.data_to_bytes(self.r.DATA)

            return IDI_TRANSACTION(
                time=self.r.TIME,
                uri=self.r.TID,
                lid=self.r.LID,
                module_id=self.get_module_id(),
                lp_id=self.get_lp_id(),
                addr=self.get_addr_in_hex(),
                opcode=self.r.OPCODE,
                tran_type=tran_type,
                data=data,
                length=self.get_length(),
                byteen=self.get_idi_byteen(),
                sai=self.get_sai(),
                int_data=self.get_idi_int_data(),
                chunk=chunk,
                unit=self.r.UNIT)

        def get_cfi_transaction(self):
            interface = self.r.INTERFACE
            rctrl = self.string_to_bint(self.r.RCTRL)
            msg_type = self.get_cfi_msg_type()
            param_a = self.get_cfi_param_a()
            chunk = None
            data = None
            if interface in [CFI.IFCS.tx_data, CFI.IFCS.rx_data]:
                data = CNCU_UTILS.data_to_bytes(self.r.DATA_3 + self.r.DATA_2 + self.r.DATA_1 + self.r.DATA_0)
                if self.r.EOP:
                    chunk = 1
                else:
                    chunk = 0

            return CFI_TRANSACTION(
                time=self.r.TIME,
                uri=self.r.TID,
                addr=self.get_addr_in_hex(),
                opcode=self.r.OPCODE,
                rsp_id=self.r.RSPID,
                dest_id=self.r.DSTID,
                crnid=self.r.CRNID,
                cdnid=self.r.CDNID,
                data=data,
                interface=interface,
                pkt_type=self.r.PKT_TYPE,
                vc_id=self.r.VC_ID,
                length=self.get_length(),
                sai=self.get_sai(),
                param_a=param_a,
                msg_type=msg_type,
                rctrl=rctrl,
                chunk=chunk)

        def get_ufi_transaction(self):
            interface = self.r.CHANNEL
            opcode = self.r.OPCODE
            data = None
            chunk = self.string_to_bint(self.r.CHUNK)
            msg_type = self.string_to_bint(self.r.MSG_TYPE)
            sai = self.string_to_bint(self.r.SAI)
            length = self.string_to_bint(self.r.LENGTH)
            crnid = self.string_to_bint(self.r.CRNID)
            cdnid = self.string_to_bint(self.r.CDNID)

            if interface == UFI.IFCS.data:
                data = CNCU_UTILS.data_to_bytes(self.r.PAYLOAD_DATA)

            return UFI_TRANSACTION(
                    time=self.r.TIME,
                    uri=self.r.TID,
                    addr=self.get_addr_in_hex(),
                    opcode=opcode,
                    crnid=crnid,
                    cdnid=cdnid,
                    data=data,
                    interface=interface,
                    pkt_type=self.r.HEADER_TYPE,
                    vc_id=self.r.VC_ID,
                    length=length,
                    sai=sai,
                    param_a=None, # TODO: ranzohar - fixme
                    msg_type=msg_type,
                    chunk=chunk)

        def string_to_bint(self, str):
            if str != "" and str != "-":
                return bint(int(str, 16))
            return None
