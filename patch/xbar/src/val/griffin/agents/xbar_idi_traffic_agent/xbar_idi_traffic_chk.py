#!/usr/intel/bin/python3

##################################################################
#
# File name: xbar_idi_traffic_chk.py
# Owner:     dshurin
# Date:      02-15-2023
#
# Description:
# FIXME - dshurin - fill your description here
#
#
##################################################################

from griffin_collaterals.griffin_report import GRIFFIN_DEBUG, GRIFFIN_MSG, GRIFFIN_CHECK, GRIFFIN_ERROR
from queue import Queue

from agents.xbar_common_base.xbar_common_base.xbar_cfg import XbarCfg
from agents.xbar_common_base.xbar_common_base.xbar_common_base import XbarBaseChk
from agents.xbar_common_base.xbar_common_utils.xbar_common_utils import XbarCommonUtils
from agents.xbar_idi_traffic_agent.xbar_idi_traffic_qry import XbarIdiTrafficQry
from agents.xbar_idi_traffic_agent.xbar_idi_traffic_params import XBAR_IDI_TRAFFIC_DB, XBAR_IDI_TRAFFIC_CHK_EN


class XbarIdiTrafficChk(XbarBaseChk):

    def __init__(self):
        self.cfg: XbarCfg = XbarCommonUtils.get_cfg()

        #if not self.cfg.get_val_by_name(XBAR_IDI_TRAFFIC_CHK_EN):
        #    self.griffin_exit()

        self.xbar_idi_traffic_qry: XbarIdiTrafficQry = XbarIdiTrafficQry()
        

    def connect(self):
        self.xbar_idi_traffic_qry.connect_to_db(XBAR_IDI_TRAFFIC_DB)

    def get_cbo_by_uqid(self, entry):
        return int((entry.UQID >> 7) & 31)


    def get_cbo_by_tid(self, entry):
        return int(str(entry.TID.split('_')[2].split('T')[0]), 16)

    def get_cbo_by_unit_id(self, entry):
        return int(entry.UNIT.split('_')[1])
    
    def run(self):
        print("Hi")
        #self.xbar_idi_traffic_qry.queries()
        uncore_c2u_reqs = self.xbar_idi_traffic_qry.get_uncore_c2u_req()
        for k in uncore_c2u_reqs:
            GRIFFIN_CHECK(cond=(k.HASH == str(int(k.UNIT.split('_')[1])%4)), time=k.TIME, bucket=f'Wrong target for C2U REQ',
                              debug_msg=f'{k.TID} went to {k.UNIT} instead UNCORE_{k.HASH}\n')
   
        uncore_c2u_rsps = self.xbar_idi_traffic_qry.get_uncore_c2u_rsp()
        for k in uncore_c2u_rsps:
            GRIFFIN_CHECK(cond=((str(self.get_cbo_by_uqid(k)) == str(int(k.UNIT.split('_')[1])%4)) or (k.UQID == 0x1fff)), time=k.TIME, bucket=f'Wrong target for C2U RSP',
                              debug_msg=f'{k.TID} went to {k.UNIT} instead UNCORE_{str(self.get_cbo_by_uqid(k))}\n')
        self.snp_bypass_go()
        self.c2u_data_continuity()
        self.u2c_data_continuity()


    def snp_bypass_go(self):
        # go_snp_seq_dict will contain all transactions that left UNCORE side, but didn't reach CORE side
        go_snp_seq_dict = {}
        fail_suspect_dict = {}
        # Dictionary for special case t0: GO @UNCORE, t1: SNP @UNCORE, t2: (GO & SNP) @CORE (t0<t1<t2)
        # It is forbidden, but if in tracker GO at t2 appears before SNP, it will be cleared from go_snp_seq_dict before check is made
        # Therefore need to save all GO transaction till timepoint ends
        completed_go_dict = {}
        go_snp_seq = self.xbar_idi_traffic_qry.get_go_snp_seq()
        for k in go_snp_seq:
            # GO transactions are registered according to TID, snoop transactions are registered according to LID.
            if(k.OPCODE == 'IDI_GO'):
                key_name = k.TID
            else:
                key_name = k.LID
            # Register transaction as ongoing. Nothing to check, therefore continue to next.
            if(go_snp_seq_dict.get(key_name) == None and (k.UNIT.startswith('UNCORE'))):
                go_snp_seq_dict[key_name] = k
                continue
            # When transaction reached core side need to check ordering
            if(go_snp_seq_dict.get(key_name) != None and (k.UNIT.startswith('CORE'))):
                if(len(completed_go_dict) > 0):
                    if(k.TIME > last_core_go_time):
                        completed_go_dict.clear()
                if(k.OPCODE != 'IDI_GO'):
                    # snp_core_trgt contains target core value for snp transaction
                    snp_core_trgt = k.UNIT.split('_')[1]
                    # Iterate through all completed GO transactions at current time point
                    for j in completed_go_dict:
                        # go_core_trgt contains target core value for GO transaction
                        go_core_trgt = completed_go_dict[j].TID[8]
                        if((snp_core_trgt == go_core_trgt) and (go_snp_seq_dict[key_name].UNIT.split("_")[1] == completed_go_dict[j].UNIT.split("_")[1]) and (go_snp_seq_dict[key_name].TIME > completed_go_dict[j].TIME)):
                            GRIFFIN_ERROR(time=last_core_go_time, bucket='Snoop bypassed GO', debug_msg=f"Snp {k.LID} bypassed GO {completed_go_dict[j].TID}\n")
                    # Iterate through all ongoing transaction that still didn't reach CORE side
                    for j in go_snp_seq_dict:
                        # go_core_trgt contains target core value for GO transaction
                        go_core_trgt = go_snp_seq_dict[j].TID[8]
                        # All ongoing transactions that were sent after transaction under test don't need to be checked
                        if(go_snp_seq_dict[j].TIME > go_snp_seq_dict[key_name].TIME):
                            break
                        # If ongoing transaction is snp, nothing to check. Continue to next ongoing transaction.
                        if(go_snp_seq_dict[j].OPCODE != 'IDI_GO'):
                            continue
                        # For GO transaction check that GO and Snp were sent from same CBO cluster and reached the same core.
                        # If so, then it's a candidate for possible rule violation
                        if((snp_core_trgt == go_core_trgt) and (go_snp_seq_dict[key_name].UNIT.split("_")[1] == go_snp_seq_dict[j].UNIT.split("_")[1])):
                            # Error should be issued only when snoop appears on uncore side later than GO
                            if(go_snp_seq_dict[key_name].TIME > go_snp_seq_dict[j].TIME):
                                fail_suspect_dict[j] = k
                else:
                    completed_go_dict[key_name] = go_snp_seq_dict.get(key_name)
                    last_core_go_time = k.TIME
                    if(fail_suspect_dict.get(k.TID) != None):
                        # Error when GO finishes after snoop
                        if(k.TIME > fail_suspect_dict[k.TID].TIME):
                            GRIFFIN_ERROR(time=fail_suspect_dict[k.TID].TIME, bucket='Snoop bypassed GO', debug_msg=f"Snp {fail_suspect_dict[k.TID].LID} bypassed GO {k.TID}\n")
                        fail_suspect_dict.pop(k.TID)
                # Remove transaction from ongoing list
                go_snp_seq_dict.pop(key_name)

        # If go_snp_seq_dict is not empty, then not all transactions passed to other side of XBAR
        for k in go_snp_seq_dict:
            if(go_snp_seq_dict[k].OPCODE == 'IDI_GO'):
                tr_id = go_snp_seq_dict[k].TID
            else:
                tr_id = go_snp_seq_dict[k].LID
            GRIFFIN_ERROR(time=go_snp_seq_dict[k].TIME, bucket='Transaction stuck at EOS', debug_msg=f"Transaction {tr_id} is stuck in XBAR\n")

    def c2u_data_continuity(self):
        c2u_data_seq = self.xbar_idi_traffic_qry.get_c2u_data()
        xbar_c2u_data_dict = {}

        for k in c2u_data_seq:
            key_name = k.TID + k.CHUNK
            # Register transaction as ongoing. Nothing to check, therefore continue to next.
            if(xbar_c2u_data_dict.get(key_name) == None and (k.UNIT.startswith('CORE'))):
                xbar_c2u_data_dict[key_name] = k
                continue

            if(xbar_c2u_data_dict.get(key_name) != None and (k.UNIT.startswith('UNCORE'))):
                GRIFFIN_CHECK(cond=(self.get_cbo_by_uqid(k)%4 == self.get_cbo_by_unit_id(k)%4), time=k.TIME, bucket=f'Wrong target for C2U DATA',
                              debug_msg=f'{k.TID} chunk {k.CHUNK} went to {k.UNIT} instead UNCORE_{str(self.get_cbo_by_uqid(k))}\n')
                GRIFFIN_CHECK(cond=(xbar_c2u_data_dict[key_name].DATA == k.DATA), time=k.TIME, bucket=f'Data continuity error on C2U DATA',
                              debug_msg=f'{k.TID} chunk {k.CHUNK} data core side vs. uncore:\n{k.DATA}\n{xbar_c2u_data_dict[key_name].DATA}\n')
                # Remove transaction from ongoing list
                xbar_c2u_data_dict.pop(key_name)

        # If go_snp_seq_dict is not empty, then not all transactions passed to other side of XBAR
        for k in xbar_c2u_data_dict:
            GRIFFIN_ERROR(time=xbar_c2u_data_dict[k].TIME, bucket='C2U DATA Transaction stuck at EOS', debug_msg=f"Transaction {xbar_c2u_data_dict[k].TID} chunk {xbar_c2u_data_dict[k].CHUNK} is stuck in XBAR\n")


    def u2c_data_continuity(self):
        u2c_data_seq = self.xbar_idi_traffic_qry.get_u2c_data()
        xbar_u2c_data_dict = {}

        for k in u2c_data_seq:
            key_name = k.TID + k.CHUNK
            # Register transaction as ongoing. Nothing to check, therefore continue to next.
            if(xbar_u2c_data_dict.get(key_name) == None and (k.UNIT.startswith('UNCORE'))):
                xbar_u2c_data_dict[key_name] = k
                continue

            if(xbar_u2c_data_dict.get(key_name) != None and (k.UNIT.startswith('CORE'))):
                GRIFFIN_CHECK(cond=(self.get_cbo_by_tid(xbar_u2c_data_dict.get(key_name)) == self.get_cbo_by_unit_id(k)), time=k.TIME, bucket=f'Wrong target for U2C DATA',
                              debug_msg=f'{k.TID} chunk {k.CHUNK} went to {k.UNIT} instead CORE_{str(xbar_u2c_data_dict[key_name].TID[8])}\n')
                GRIFFIN_CHECK(cond=(xbar_u2c_data_dict[key_name].DATA == k.DATA), time=k.TIME, bucket=f'Data continuity error on U2C DATA',
                              debug_msg=f'{k.TID} chunk {k.CHUNK} data uncore side vs. core:\n{k.DATA}\n{xbar_u2c_data_dict[key_name].DATA}\n')
                # Remove transaction from ongoing list
                xbar_u2c_data_dict.pop(key_name)

        # If go_snp_seq_dict is not empty, then not all transactions passed to other side of XBAR
        for k in xbar_u2c_data_dict:
            GRIFFIN_ERROR(time=xbar_u2c_data_dict[k].TIME, bucket='U2C DATA Transaction stuck at EOS', debug_msg=f"Transaction {xbar_u2c_data_dict[k].TID} chunk {xbar_u2c_data_dict[k].CHUNK} is stuck in XBAR\n")


if __name__ == "__main__":
    XbarIdiTrafficChk.execute()
