from val_utdb_base_components import EOT
from val_utdb_components import val_utdb_chk
from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_types import COLORS
from agents.cncu_agent.common.ccf_nc_common_base import CCF_NC_CONFIG
from agents.cncu_agent.common.cncu_defines import SB, SAI
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.utils.nc_systeminit import NC_SI


def get_core_num(pid):
    for core_num, core_pid in enumerate(SB.EPS.internal_cores):
        if core_pid == pid:
            return core_num


def is_wake_on_any_event_update(tran: SB_TRANSACTION):
    return tran.opcode == SB.OPCODES.cr_wr and tran.dest_pid == SB.EPS.ncevents and tran.addr == 0x5330


def is_wake_on_pmi_update(tran: SB_TRANSACTION):
    return tran.opcode == SB.OPCODES.cr_wr and tran.dest_pid == SB.EPS.ncevents and tran.addr == 0x5240


def is_llb_wake_all_update(tran: SB_TRANSACTION):
    return tran.opcode == SB.OPCODES.cr_wr and tran.dest_pid == SB.EPS.ncevents and tran.addr == 0x5300


def is_core_update_msg(tran: SB_TRANSACTION):
    return tran.opcode == SB.OPCODES.cr_wr and tran.dest_pid in SB.EPS.internal_cores and \
           NC_SI.get_pointer().module_disable_mask[get_core_num(tran.dest_pid)] and \
           tran.addr == 0x40 and tran.msg_type == SB.MSG_TYPE.posted and tran.eh == 1 and tran.sai == SAI.hw_cpu and \
           (tran.byte_en[0] == 1 or tran.byte_en[1] == 1 or tran.byte_en[2] == 1)


def get_update_value_str(tran: SB_TRANSACTION, target, update_value):
    update_type = COLORS.YELLOW + "Incoming" if tran.dest_pid == SB.EPS.ncevents else COLORS.PURPLE + "Reported"
    return update_type + " Update - {0:<12} - {1:<12} - {2:<6} - {3:<30}".format(
        str(tran.get_start_time()), str(tran.get_end_time()), target,
        ", ".join([key.upper() + ": " + str(val) for key, val in update_value.items()]))


class CCF_NC_NCU_CONFIG_BITS_CHECKER(val_utdb_chk):
    def __init__(self):
        self.set_si(NC_SI.get_pointer())
        self.cfg: CCF_NC_CONFIG = CCF_NC_CONFIG.get_pointer()
        self.sb_db: CCF_NC_SB_DB = CCF_NC_SB_DB.get_pointer()

    def _get_ncu_config_bits_flow_sb_msgs(self, core_num):
        def is_ncu_config_bits_flow(tran: SB_TRANSACTION):
            return (is_core_update_msg(tran) and tran.dest_pid == SB.EPS.internal_cores[core_num]) or \
                   is_wake_on_any_event_update(tran) or \
                   is_wake_on_pmi_update(tran) or \
                   is_llb_wake_all_update(tran) or \
                   tran.opcode == SB.OPCODES.cmp

        sb_msgs = self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.cr_wr],
                                               start_time=0,
                                               end_time=EOT,
                                               filter_func=is_ncu_config_bits_flow)
        return sorted(sb_msgs, key=lambda msg: msg.get_time())

    def check_config_update_to_core(self, core_num):
        print(COLORS.RED + "************** NCU CFG BITS CORE" + str(core_num) + "  *********************")
        exp_update_values = list()
        cur_wake_on_any_event = 0
        cur_wake_on_pmi = 0
        cur_llb_wake_all = 0
        for tran in self._get_ncu_config_bits_flow_sb_msgs(core_num):
            if is_wake_on_any_event_update(tran) and self.si.module_disable_mask[core_num] == 0:
                if tran.byte_en[0] == 1:
                    cur_wake_on_any_event = tran.flat_data[6]
                    exp_update_values.append({"llb_wake_all": cur_llb_wake_all,
                                              "wake_on_pmi": cur_wake_on_pmi,
                                              "wake_on_any_event": cur_wake_on_any_event})
                    print(get_update_value_str(tran, "ANY", exp_update_values[-1]))
            elif is_wake_on_pmi_update(tran) and self.si.module_disable_mask[core_num] == 0:
                if tran.byte_en[3] == 1:
                    cur_wake_on_pmi = tran.flat_data[30]
                    exp_update_values.append({"llb_wake_all": cur_llb_wake_all,
                                              "wake_on_pmi": cur_wake_on_pmi,
                                              "wake_on_any_event": cur_wake_on_any_event})
                    print(get_update_value_str(tran, "PMI", exp_update_values[-1]))

            elif is_llb_wake_all_update(tran) and self.si.module_disable_mask[core_num] == 0:
                if tran.byte_en[3] == 1:
                    cur_llb_wake_all = tran.flat_data[30]
                    exp_update_values.append({"llb_wake_all": cur_llb_wake_all,
                                              "wake_on_pmi": cur_wake_on_pmi,
                                              "wake_on_any_event": cur_wake_on_any_event})
                    print(get_update_value_str(tran, "LLB", exp_update_values[-1]))

            elif is_core_update_msg(tran):
                act_update_value = {"llb_wake_all": tran.flat_data[0],
                                    "wake_on_pmi": tran.flat_data[1],
                                    "wake_on_any_event": tran.flat_data[2]}
                print(get_update_value_str(tran, "CORE", act_update_value))

                if len(exp_update_values) > 0:
                    exp_update_value = exp_update_values.pop(0)
                    if not all(exp_update_value[key] == act_update_value[key] for key in exp_update_value.keys()):
                        VAL_UTDB_ERROR(time=tran.get_time(),
                                       msg="\n********  NCU CFG BITS CORE" + str(
                                           core_num) + " VALUE MISMATCH ********\n\n" +
                                           "Time: " + str(tran.get_time()) + "\n\n" +
                                           "Expected:\n" + str(exp_update_value) + "\n" +
                                           "Actual:\n" + str(act_update_value))
                        return False
                else:
                    VAL_UTDB_ERROR(time=tran.get_time(),
                                   msg="\n********  NCU CFG BITS CORE" + str(
                                       core_num) + " VALUE MISMATCH ********\n\n" +
                                       "Time: " + str(tran.get_time()) + "\n\n" +
                                       "Module Disabled: " + str(self.si.module_disable_mask[core_num] == 1) + "\n" +
                                       "Got an update message while we do not expected to get any update")
                    return False

        if len(exp_update_values) > 0:
            VAL_UTDB_ERROR(time=EOT,
                           msg="\n********  NCU CFG BITS CORE" + str(core_num) + " STILL WAIT FOR UPDATE ********\n\n" +
                               "Expected:\n" + "\n".join(
                               [str(exp_update_value) for exp_update_value in exp_update_values]))
            return False

        return True
        print(COLORS.RED + "************** END *********************")

    def run(self):
        pass
        # for //    break
