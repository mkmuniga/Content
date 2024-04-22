from val_utdb_bint import bint
from val_utdb_components import val_utdb_chk
from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.common.cncu_defines import SB, CFI
from agents.cncu_agent.dbs.ccf_nc_mcast_qry import CCF_NC_MCAST_QRY
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CCF_NC_SEMAPHORES_CHECKER(val_utdb_chk):

    def __init__(self):
        self.qry: CCF_NC_MCAST_QRY = CCF_NC_MCAST_QRY.get_pointer()

    def run(self):
        aquire_reg_addr     = ["0x5400", "0x5404"]
        aquire_imp_reg_addr = ["0x5420", "0x5424"]
        head_reg_addr       = ["0x5440", "0x5444"]
        tail_reg_addr       = ["0x5460", "0x5464"]
        rel_reg_addr        = ["0x5480", "0x5484"]
        all_trans = self.qry.get_all_trans()


        tail = [0, 0]
        head = [0, 0]

        tag_req = dict()

        for tran in all_trans:
            if tran.r.LOGDBHEADERSNAME == 'events_sb':
                tag = tran.r.TAG

                is_aquire = False
                is_aquire_imp = False
                is_release = False
                is_head_req = False
                is_tail_req = False
                semaphore = -1

                if tran.r.OPC == SB.OPCODES.cr_rd:
                    addr = tran.r.ADDRESS

                    if addr in aquire_reg_addr:
                        is_aquire = True
                        semaphore = aquire_reg_addr.index(addr)
                    elif addr in aquire_imp_reg_addr:
                        is_aquire_imp = True
                        semaphore = aquire_imp_reg_addr.index(addr)
                    elif addr in head_reg_addr:
                        is_head_req = True
                        semaphore = head_reg_addr.index(addr)
                    elif addr in tail_reg_addr:
                        is_tail_req = True
                        semaphore = tail_reg_addr.index(addr)
                    tag_req[tag] = {"sem_num": semaphore,
                                    "is_aquire": is_aquire,
                                    "is_aquire_imp": is_aquire_imp,
                                    "is_head_req": is_head_req,
                                    "is_tail_req": is_tail_req,
                                    "is_release": False}
                elif tran.r.OPC == SB.OPCODES.cmpd and tag in tag_req:
                    data = bint(int(tran.r.DATA, 16))
                    semaphore = tag_req[tag]["sem_num"]
                    sempowned = data[30] == 1
                    if tag_req[tag]["is_aquire"] or tag_req[tag]["is_aquire_imp"]:
                        if tail[semaphore] != data[15:0]:
                            VAL_UTDB_ERROR(time=tran.r.TIME,
                                           msg="Aquire IMP={} semaphore {} wrong count returned {}, expected {}".format(tag_req[tag]["is_aquire_imp"], semaphore, data[15:0], tail[semaphore]))
                        if tail[semaphore] == head[semaphore] and not sempowned:
                            VAL_UTDB_ERROR(time=tran.r.TIME,
                                           msg="Aquire IMP={} semaphore {} SempOwned=0 while tail{}=head{}".format(tag_req[tag]["is_aquire_imp"], semaphore, tail[semaphore], head[semaphore]))
                        if tag_req[tag]["is_aquire_imp"]:
                            if tail[semaphore] == head[semaphore] and sempowned:
                                tail[semaphore] += 1
                        else:
                            tail[semaphore] += 1
                    elif tag_req[tag]["is_head_req"]:
                        if head[semaphore] != data[15:0]:
                            VAL_UTDB_ERROR(time=tran.r.TIME,
                                           msg="Head of semaphore {} is wrong. actual={}, expected={}".format(
                                               semaphore, data[15:0], head[semaphore]))
                    elif tag_req[tag]["is_tail_req"]:
                        if tail[semaphore] != data[15:0]:
                            VAL_UTDB_ERROR(time=tran.r.TIME,
                                           msg="Tail of semaphore {} is wrong. actual={}, expected={}".format(
                                               semaphore, data[15:0], tail[semaphore]))
                    tag_req.pop(tag, None)
                if tran.r.OPC == SB.OPCODES.cr_wr:
                    addr = tran.r.ADDRESS
                    if addr in rel_reg_addr:
                        semaphore = rel_reg_addr.index(addr)
                        tag_req[tag] = {"sem_num": semaphore,
                                        "is_aquire": is_aquire,
                                        "is_aquire_imp": is_aquire_imp,
                                        "is_head_req": is_head_req,
                                        "is_tail_req": is_tail_req,
                                        "is_release": True}
                elif tran.r.OPC == SB.OPCODES.cmp and tag in tag_req:
                    semaphore = tag_req[tag]["sem_num"]
                    if tag_req[tag]["is_release"]:
                        head[semaphore] += 1
                        tag_req.pop(tag, None)
