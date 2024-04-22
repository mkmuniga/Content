from val_utdb_components import val_utdb_chk
from val_utdb_base_components import EOT
from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.common.cncu_defines import SB, SAI
from agents.cncu_agent.common.ccf_nc_run_info import CCF_NC_RUN_INFO
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB


def is_nc_during_lock_msg(sb_msg: SB_TRANSACTION):
    return sb_msg.msg_type == SB.MSG_TYPE.posted and sb_msg.sai == SAI.hw_cpu and sb_msg.src_pid == SB.EPS.ncevents \
           and sb_msg.dest_pid == SB.EPS.sncu and sb_msg.eh == 1 and sb_msg.data[3][5] == 1


def is_nc_during_lock_ack_msg(sb_msg: SB_TRANSACTION):
    return sb_msg.msg_type == SB.MSG_TYPE.posted and sb_msg.sai == SAI.hw_cpu and sb_msg.src_pid == SB.EPS.sncu \
           and sb_msg.dest_pid == SB.EPS.ncevents and sb_msg.eh == 1 and sb_msg.data[3][4] == 1


def is_valid_ncu_ncu_msg(lock_info, err_msg, msg_type, sb_msgs):
    if len(sb_msgs) == 0:
        err_msg = err_msg.format("Missing " + msg_type + " message"
                                                         "\n\nUnlock time: " + str(lock_info.unlock_time) +
                                 "\nUnlock URI: " + lock_info.unlock_uri)
        return False, err_msg

    elif len(sb_msgs) > 1:
        err_msg = err_msg.format("More than one " + msg_type + " message"
                                                               "\n\nUnlock time: " + str(lock_info.unlock_time) +
                                 "\nUnlock URI: " + lock_info.unlock_uri +
                                 "\n\nMessages:\n" + "\n".join([msg.to_string() for msg in sb_msgs]))
        return False, err_msg

    sb_msgs[0].uri = lock_info.lock_uri
    return True, err_msg


class CCF_NC_LOCK_CHECKER(val_utdb_chk):

    def __init__(self):
        self.sorted_locks_info = CCF_NC_RUN_INFO.get_pointer().lock_flows_info
        self.sorted_locks_info.sort(key=lambda li: li.lock_time)
        self.sb_db = CCF_NC_SB_DB.get_pointer()

    def run(self):
        err_msg = "\n****** {0} ******" + "\n\nLock time: {1}" + "\nLock URI: {2}"
        err_description_msg = "\n\nDescription:\n{0}"

        last_unlock_time = None
        last_lock_uri = None
        last_unlock_uri = None

        for lock_info in self.sorted_locks_info:
            if lock_info.unlock_time is None:
                VAL_UTDB_ERROR(time=EOT,
                               msg=err_msg.format("LOCK WITHOUT UNLOCK", lock_info.lock_time, lock_info.lock_uri) +
                                   err_description_msg.format("Lock flow was started without unlocking at EOT"))
                break

            if not lock_info.from_ccf() and lock_info.stop_req3_time is None:
                VAL_UTDB_ERROR(time=EOT,
                               msg=err_msg.format("LOCK WITHOUT STOPREQ3", lock_info.lock_time, lock_info.lock_uri) +
                                   err_description_msg.format("sNCU lock flow was started without sending STOPREQ3 at "
                                                              "EOT"))
                break

            if lock_info.lock_time > lock_info.unlock_time:
                VAL_UTDB_ERROR(time=EOT,
                               msg=err_msg.format("UNLOCK BEFORE LOCK", lock_info.lock_time, lock_info.lock_uri) +
                                   err_description_msg.format("Unlock flow was started before lock was started"
                                                              "\n\nUnlock time: " + str(lock_info.unlock_time) +
                                                              "\nUnlock URI: " + lock_info.unlock_uri))
                break

            if not lock_info.from_ccf() and not (
                    lock_info.lock_time < lock_info.stop_req3_time < lock_info.unlock_time):
                VAL_UTDB_ERROR(time=lock_info.stop_req3_time,
                               msg=err_msg.format("STOPREQ3 NOT AT TIME", lock_info.lock_time, lock_info.lock_uri) +
                                   err_description_msg.format("StopReq3 message as part of sNCU lock flow arrived not "
                                                              "between lock and unlock messages"
                                                              "\n\nStopReq3 time: " + str(lock_info.stop_req3_time) +
                                                              "\nStopReq3 URI: " + str(lock_info.stop_req3_uri) +
                                                              "\nUnlock time: " + str(lock_info.unlock_time) +
                                                              "\nUnlock URI: " + lock_info.unlock_uri))
                break

            if last_unlock_time is not None and lock_info.lock_time < last_unlock_time:
                VAL_UTDB_ERROR(time=lock_info.lock_time,
                               msg=err_msg.format("TWO LOCKS IN PARALLEL", lock_info.lock_time, lock_info.lock_uri) +
                                   err_description_msg.format("Two lock flows was started at a time "
                                                              "between lock and unlock messages"
                                                              "\n\nUnlock time: " + str(lock_info.unlock_time) +
                                                              "\nUnlock URI: " + lock_info.unlock_uri +
                                                              "\n\nLast lock URI: " + last_lock_uri +
                                                              "\nLast unlock time: " + str(last_unlock_time) +
                                                              "\nLast unlock URI: " + last_unlock_uri))
                break

            if lock_info.from_ccf() and len(lock_info.atomic_actions) == 0:
                VAL_UTDB_ERROR(time=lock_info.lock_time,
                               msg=err_msg.format("LOCK WITHOUT ATOMIC ACTION", lock_info.lock_time,
                                                  lock_info.lock_uri) +
                                   err_description_msg.format("No atomic action was detect as part of the lock flow"
                                                              "\n\nUnlock time: " + str(lock_info.unlock_time) +
                                                              "\nUnlock URI: " + lock_info.unlock_uri))
                break

            if lock_info.required_nc_during_lock:
                nc_during_lock_msg = self.sb_db.get_trans_at_time(opcodes=SB.OPCODES.ncu_ncu_msg,
                                                                           start_time=lock_info.lock_time,
                                                                           end_time=lock_info.unlock_time,
                                                                           filter_func=is_nc_during_lock_msg)

                nc_during_lock_ack_msg = self.sb_db.get_trans_at_time(opcodes=SB.OPCODES.ncu_ncu_msg,
                                                                               start_time=lock_info.lock_time,
                                                                               end_time=lock_info.unlock_time,
                                                                               filter_func=is_nc_during_lock_ack_msg)

                is_nc_during_lock_valid, err_description_msg = is_valid_ncu_ncu_msg(lock_info, err_description_msg,
                                                                                    "NC_DURING_LOCK",
                                                                                    nc_during_lock_msg)
                if is_nc_during_lock_valid:
                    is_nc_during_lock_ack_valid, err_description_msg = is_valid_ncu_ncu_msg(lock_info,
                                                                                            err_description_msg,
                                                                                            "NC_DURING_ACK_LOCK",
                                                                                            nc_during_lock_ack_msg)
                if not is_nc_during_lock_valid or not is_nc_during_lock_ack_valid:
                    VAL_UTDB_ERROR(time=lock_info.lock_time,
                                   msg=err_msg.format("NC DURING LOCK MISMATCH", lock_info.lock_time,
                                                      lock_info.lock_uri) + err_description_msg)

            last_unlock_time = lock_info.unlock_time
            last_lock_uri = lock_info.lock_uri
            last_unlock_uri = lock_info.unlock_uri
