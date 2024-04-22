from val_utdb_bint import bint
from val_utdb_components import val_utdb_chk
from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.common.cncu_defines import SB, CFI
from agents.cncu_agent.dbs.ccf_nc_mcast_qry import CCF_NC_MCAST_QRY
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_MCAST_TOKEN_CCF_ALL_CHECKER(val_utdb_chk):

    def __init__(self):
        self.qry: CCF_NC_MCAST_QRY = CCF_NC_MCAST_QRY.get_pointer()

    def run(self):
        own_mcast_token          = False
        pending_mcast_token_release  = False
        pending_mcast_token_ack  = False
        one_time_use_mcast_token = False
        token_was_used           = False
        is_shadow_offset_uri     = False
        is_shadow_offset_sent    = False
        last_shadow_offset_uri   = None
        all_trans = self.qry.get_all_trans()

        shadow_offset_uri = self.get_all_shadow_offsets_uri(all_trans)

        for tran in all_trans:
            if tran.r.SELECTOR == 'aligned_sb' and "NCEVENTS" in tran.r.PORT:
                if tran.r.OPC == SB.OPCODES.ncu_ncu_msg:
                    data = bint(int(tran.r.DATA, 16))
                    sent_from_sncu = bint(int(tran.r.LSPID, 16)) == SB.EPS.sncu[7:0] and bint(int(tran.r.SPID, 16)) == SB.EPS.sncu[15:8]
                    sent_from_ccf  = bint(int(tran.r.LSPID, 16)) == SB.EPS.ncevents[7:0] and bint(int(tran.r.SPID, 16)) == SB.EPS.ncevents[15:8]
                    mcast_token_req = data[31:31] == 1
                    mcast_token_ack = data[30:30] == 1
                    ccf_num = data[9:8]
                    if sent_from_ccf and ccf_num != UNIQUE_DEFINES.ccf_id:
                        VAL_UTDB_ERROR(time=tran.r.TIME,
                                       msg="CCF is sending NCU NCU message with wrong ccf_num")
                    if mcast_token_ack:
                        if sent_from_sncu:
                            if own_mcast_token:
                                VAL_UTDB_ERROR(time=tran.r.TIME,
                                               msg="CCF already own MCAST token")
                            pending_mcast_token_ack = False
                            own_mcast_token = True
                            token_was_used  = False
                            is_shadow_offset_uri  = False
                            is_shadow_offset_sent = False
                            one_time_use_mcast_token = data[31:31] == 1
                        if sent_from_ccf:
                            if not own_mcast_token:
                                VAL_UTDB_ERROR(time=tran.r.TIME,
                                               msg="Unexpected CCF MCAST token release")
                            pending_mcast_token_release = False
                            own_mcast_token = False
                            one_time_use_mcast_token = False
                            if is_shadow_offset_uri and not is_shadow_offset_sent:
                                VAL_UTDB_ERROR(time=tran.r.TIME,
                                               msg="MCAST token was released before writing the shadow offset over CFI")
                    if mcast_token_req:
                        if sent_from_ccf:
                            if pending_mcast_token_ack and not mcast_token_ack:
                                VAL_UTDB_ERROR(time=tran.r.TIME,
                                               msg="CCF is already waiting for MCAST token ack and is sending a new MCAST token req")
                            if own_mcast_token:
                                VAL_UTDB_ERROR(time=tran.r.TIME,
                                               msg="CCF already own the MCAST token and is asking again")
                            pending_mcast_token_ack = True
                        elif sent_from_sncu:
                            pending_mcast_token_release = True
            elif tran.r.SELECTOR == 'racu_sb':
                dest_pid = bint(int(tran.r.LDPID, 16))
                dest_seg_pid = bint(int(tran.r.DPID, 16))

                is_mcast = self.is_mcast(dest_pid, dest_seg_pid)

                # mcast token
                if is_mcast:
                    is_mcast_comp = tran.r.OPCODE in [SB.OPCODES.cmpd, SB.OPCODES.cmp]
                    if not own_mcast_token:
                        VAL_UTDB_ERROR(time=tran.r.TIME,
                                       msg="CCF is sending MCAST without MCAST token")
                    if one_time_use_mcast_token and token_was_used and not is_mcast_comp:
                        VAL_UTDB_ERROR(time=tran.r.TIME,
                                       msg="One use MCAST token was already used")
                    if tran.r.TID in shadow_offset_uri:
                        is_shadow_offset_uri = True
                        last_shadow_offset_uri = tran.r.TID
                    if not is_mcast_comp:
                        token_was_used = True

            elif tran.r.SELECTOR == 'cfi':
                if is_shadow_offset_uri and tran.r.TID == last_shadow_offset_uri and tran.r.OPCODE == CFI.OPCODES.nccmpu:
                    is_shadow_offset_sent = True
        if pending_mcast_token_release:
            VAL_UTDB_ERROR(time=tran.r.TIME,
                           msg="CCF didn't return the MCAST token after sNCU's request")

    def get_all_shadow_offsets_uri(self, trans):
        shadow_offset_uri = list()
        mcast_uri = list()
        for tran in trans:
            if tran.r.SELECTOR == 'racu_sb':
                dest_pid = bint(int(tran.r.LDPID, 16))
                dest_seg_pid = bint(int(tran.r.DPID, 16))
                is_mcast = self.is_mcast(dest_pid, dest_seg_pid)
                if is_mcast:
                    mcast_uri.append(tran.r.TID)
            if tran.r.SELECTOR == 'cfi':
                if tran.r.TID in mcast_uri:
                    shadow_offset_uri.append(tran.r.TID)
        return shadow_offset_uri


    def is_mcast(self, dest_pid, dest_seg_pid):
        if dest_pid > 200 or 224 <= dest_seg_pid <= 237:
            return True
        return False

    def is_ccf_all_needed(self, dest_pid, dest_seg_pid):
        ccf_all_mcasts = [SB.EPS.mcast_ltctrlsts, SB.EPS.mcast_dev0cfg, SB.EPS.mcast_cfi_host, SB.EPS.mcast_sad_all]
        if UNIQUE_DEFINES.is_low_power_ccf:
            ccf_all_mcasts.append(SB.EPS.mcast_cbo_all)

        for dest in ccf_all_mcasts:
            if dest[15:8] == dest_seg_pid and dest[7:0] == dest_pid:
                return True
        if UNIQUE_DEFINES.ccf_id == 0:
            return dest_seg_pid == SB.EPS.compute_seg_pid and dest_pid in [SB.EPS.idi_bridge[7:0], SB.EPS.idi_bridge_ncevents[7:0]]
        else:
            full_dest = dest_pid
            full_dest[15:8] = dest_seg_pid
            ccf_eps = [SB.EPS.santa0, SB.EPS.santa1, SB.EPS.pmc, SB.EPS.ccf_ncevents]
            return full_dest in SB.EPS.cbo[0:self.si.num_of_cbo] or full_dest in ccf_eps
