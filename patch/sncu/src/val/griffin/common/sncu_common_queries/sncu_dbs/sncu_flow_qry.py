#!/usr/bin/env python3.6.3
#
# Description:
#   This file contain all ccf NC queries and flow definitions
#################################################################################################
from griffin_collaterals.griffin_bint import bint
from common.sncu_common_base.sncu_common_base import SncuBaseQry
from dbWrapper import pred_t
from UTDB import *
from common.sncu_common_base.sncu_defines import CFI
from common.sncu_common_base.sncu_types import UXI_TRANSACTION
from common.sncu_common_queries.sncu_dbs.sncu_sb_db import SNCU_SB_DB
from common.sncu_common_utils.sncu_common_utils import SNCU_COMMON_UTILS

# def execute_to_flows(execute_res):
#     txn_flows = dict()
#     for ev in execute_res:
#         curr_uri = ev.URI_TID
#         if(curr_uri not in txn_flows.keys()):
#             txn_flows[curr_uri] = list()
#         txn_flows[curr_uri].append(SNCU_FLOW_QRY.REC(ev).get_tran())
#
#     return list(txn_flows.values())


def execute_to_flows(execute_res, is_match_func_first_txn=lambda event: True):
    """

    :param execute_res: data sorted first by uri (or unique id and then by time)
    :param is_match_func_first_txn: the first txn of flow is usually the start of a new flow.
    We want to identify the txn according to some condition specified in the func returning boolean value.
    :return: list of lists - each inner list is a flow - while between the lists we sort according to the start fo each
    flow. for example:
    flow A first rec  time 0
    flow B first rec  time 1
    flow B second rec time 2
    flow A second rec time 3

    The output will be: [[flow A first rec, flow A second rec],
                         [flow B first rec, flow B second rec]]
    """
    txn_flows = dict()
    for ev in execute_res:
        curr_uri = ev.URI_TID
        if (curr_uri not in txn_flows.keys()):
            if(is_match_func_first_txn(ev)):
                txn_flows[curr_uri] = list()
        try:
            txn_flows[curr_uri].append(SNCU_FLOW_QRY.REC(ev).get_tran())
        except KeyError as e:
            continue
    res =list(txn_flows.values())
    res.sort(key=lambda flow: flow[0].get_time())
    return res


def is_match_for_lock_unlock_flow(event):
    lock = ("NcMsgS" in event.OPCODE) and (event.MSG_TYPE == CFI.MSG_TYPES.stop_req)
    unlock = ("NcMsgS" in event.OPCODE) and (event.MSG_TYPE == CFI.MSG_TYPES.start_req)
    return lock or unlock


class SNCU_FLOW_QRY(SncuBaseQry):
    nc_dbs: pred_t
    uri_stitch: pred_t

    def queries(self):
        self.uri_stitch = self.DB.all.URI_TID == V('URI_TID')
        self.__all_trans = (self.DB.all.TIME >= 0) and (self.DB.all.VC_NAME == "SOC_SNCU")

    def __execute_all_flows_qry(self):
        results = fetch(from_(self.DB).where(self.DB.all.VC_NAME == "SOC_SNCU").sort_by((self.DB.all.URI_TID, ASC), (self.DB.all.TIME, ASC)))
        r = execute_to_flows(results)
        return r

    def __execute_lock_flows_qry(self):
        results = fetch(from_(self.DB).where(self.DB.all.VC_NAME == "SOC_SNCU").sort_by((self.DB.all.URI_TID, ASC), (self.DB.all.TIME, ASC)))
        r = execute_to_flows(results, is_match_for_lock_unlock_flow)
        return r

    def get_lock_flows(self):
        res = self.__execute_lock_flows_qry()
        return res

    def get_all_flows(self):
        res = self.__execute_all_flows_qry()
        return res


    class REC(SncuBaseQry.Rec):
        def __init__(self, rec):
            super().__init__(rec)

        def get_tran(self):
            if self.is_uxi_nc():
                return self.get_uxi_tran()
            elif self.is_racu_sb():
                return self.get_racu_sb_tran()

        def is_uxi_nc(self):
            return self.db_name in ['uxi_data', 'uxi_rsp']

        def is_racu_sb(self):
            return self.db_name == 'racu'

        def get_racu_sb_tran(self):
            return SNCU_SB_DB.REC(self.r).get_tran()

        def get_uxi_tran(self):
            return UXI_TRANSACTION(
                    time=self.r.TIME,
                    uri=self.r.URI_TID,
                    uri_lid=self.r.URI_LID,
                    protocol_id = self.r.PROTOCOL_ID,
                    addr=self.get_addr(),
                    opcode=self.r.OPCODE,
                    rctrl=self.r.RCTRL,
                    rsp_id=self.get_rsp_id(),
                    dest_id=self.get_dest_id(),
                    data=self.get_data(),
                    byteen=self.get_byteen(),
                    interface=self.get_interface(),
                    pkt_type=self.r.PKT_TYPE,
                    trace_packet=self.r.TRACE_PKT,
                    vc_id=self.r.VC_ID,
                    length=self.get_length(),
                    sai=self.get_sai(),
                    chunk=self.get_chunk(),
                    msg_type=self.get_msg_type(),
                    param_a=self.get_pram_a(),
                    rtid= self.r.RTID,
                    tee=self.get_tee(),
                    pcls=self.get_pcls(),
                    mem_loc=self.get_mem_loc(),
                    crnid=self.get_crnid(),
                    cdnid=self.get_cdind(),
                    a_par=self.get_a_par(),
                    d_par=self.get_d_par(),
                    i_par=self.get_i_par(),
                    posion=self.get_posion()
                    )

        def get_rsp_id(self):
            if hasattr(self.r, 'RSP_ID_VAL') and self.r.RSP_ID_VAL is not None:
                return CFI.get_ep_name(self.r.RSP_ID_VAL)
            return None

        def get_dest_id(self):
            if hasattr(self.r, 'DST_ID_VAL') and self.r.DST_ID_VAL is not None:
                return CFI.get_ep_name(self.r.DST_ID_VAL)
            return None

        def get_addr(self):
            if self.r.ADDRESS != 0xdeadbeef:
                return bint(self.r.ADDRESS)
            return None

        def get_data(self):
            if hasattr(self.r, 'DATA0') and self.r.DATA0 is not None:
                return SNCU_COMMON_UTILS.data_to_bytes([self.r.DATA0, self.r.DATA1, self.r.DATA2, self.r.DATA3])
            return None

        def get_byteen(self):
            if hasattr(self.r, 'DATA0') and self.r.DATA0 is not None:
                return bint(int(self.r.BE))
            return None

        def get_length(self):
            if hasattr(self.r, 'DATA0') and self.r.LEN is not None:
                return bint(int(self.r.LEN))
            return None

        def get_sai(self):
            if hasattr(self.r, 'DATA0') and self.r.SAI is not None:
                return int(self.r.SAI)
            return None

        def get_msg_type(self):
            if hasattr(self.r, 'DATA0'):
                return self.r.MSG_TYPE
            return None

        def get_pram_a(self):
            if hasattr(self.r, 'DATA0') and self.r.PARAMA is not None:
                return bint(self.r.PARAMA)
            return None

        def get_chunk(self):
            if hasattr(self.r, 'DATA0'):
                return self.r.CHUNK
            return None

        def get_tee(self):
            if hasattr(self.r, 'TEE'):
                return self.r.TEE
            return None

        def get_pcls(self):
            if hasattr(self.r, 'PCLS'):
                return self.r.PCLS
            return None

        def get_mem_loc(self):
            if hasattr(self.r, 'MEM_LOC'):
                return self.r.MEM_LOC
            return None

        def get_crnid(self):
            if hasattr(self.r, 'CRNID_VAL') and self.r.CRNID_VAL is not None:
                return CFI.get_ep_name(self.r.CRNID_VAL)
            return None

        def get_cdind(self):
            if hasattr(self.r, 'CDNID_VAL') and self.r.CDNID_VAL is not None:
                return CFI.get_ep_name(self.r.CDNID_VAL)
            return None

        def get_a_par(self):
            if hasattr(self.r, 'A_PAR') and self.r.A_PAR is not None:
                return int(self.r.A_PAR)
            return None

        def get_d_par(self):
            if hasattr(self.r, 'D_PAR') and self.r.D_PAR is not None:
                return int(self.r.D_PAR)
            return None

        def get_i_par(self):
            if hasattr(self.r, 'I_PAR') and self.r.I_PAR is not None:
                return int(self.r.I_PAR)
            return None

        def get_posion(self):
            if hasattr(self.r, 'POSION'):
                return int(self.r.POSION)
            return None
        def get_interface(self):
            if self.r.INTERFACE == "RECEIVE_DATA_0":
                return "TRANSMIT_DATA_0"
            elif self.r.INTERFACE == "TRANSMIT_DATA_0":
                return "RECEIVE_DATA_0"
            elif self.r.INTERFACE == "TRANSMIT_RSP_0":
                return "RECEIVE_RSP_0"
            elif self.r.INTERFACE == "RECEIVE_RSP_0":
                return "TRANSMIT_RSP_0"
            return None
