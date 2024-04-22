from agents.cncu_agent.utils.cncu_utils import REMAPPING
from val_utdb_base_components import EOT
from val_utdb_components import val_utdb_chk

from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_crashlog_reference_model import \
    CRASHLOG_REFERENCE_MODEL
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_decoder import EVENTS_DECODER
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_types import COLORS, CRASHLOG_INFO
from agents.cncu_agent.common.cncu_defines import EVENTS_TYPES, SB
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_reset_db import NC_RESET_DB
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.utils.nc_systeminit import NC_SI
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES

mcerr_types = [EVENTS_TYPES.umcnf, EVENTS_TYPES.umcf, EVENTS_TYPES.ierr, EVENTS_TYPES.mcerr]


def get_mcerr_type(events):
    for ev in events:
        if ev in mcerr_types:
            return ev
    return None


def is_ccf_info_reset(tran: SB_TRANSACTION):
    return tran.opcode == SB.OPCODES.cr_wr and tran.addr == 0x5348 and \
           tran.dest_pid == SB.EPS.ncevents and tran.flat_data == 0


def is_mcerr_msg(tran: SB_TRANSACTION):
    return (tran.opcode == SB.OPCODES.mclk_event and tran.dest_pid == SB.EPS.ncevents) or \
           (tran.opcode == SB.OPCODES.cr_wr and tran.addr == 0x48 and tran.dest_pid == SB.EPS.ncevents) and \
           any(mcerr_type in EVENTS_DECODER().decode(tran) for mcerr_type in mcerr_types)


def is_crashlog_msg(tran: SB_TRANSACTION):
    return tran.opcode == SB.OPCODES.mclk_event and tran.dest_pid == SB.EPS.sncu


def get_core_num(src_pid):
    for core_num, core_pid in enumerate(SB.EPS.internal_cores):
        if core_pid == src_pid:
            return REMAPPING.physical2logical[core_num]
    return 0


class CCF_NC_CRASHLOG_CHECKER(val_utdb_chk):
    def __init__(self):
        self.set_si(NC_SI.get_pointer())
        self.sb_db: CCF_NC_SB_DB = CCF_NC_SB_DB.get_pointer()
        self.events_decoder = EVENTS_DECODER()
        self.reset_db: NC_RESET_DB = NC_RESET_DB.get_pointer()

    def _get_crashlog_flow_msgs(self):
        def is_crashlog_flow_msg(sb_msg):
            return is_crashlog_msg(sb_msg) or is_mcerr_msg(sb_msg) or is_ccf_info_reset(sb_msg)

        sb_msgs = self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.fclk_event, SB.OPCODES.mclk_event,
                                                        SB.OPCODES.cr_wr],
                                               start_time=0,
                                               end_time=EOT,
                                               filter_func=is_crashlog_flow_msg)
        return sorted(sb_msgs, key=lambda msg: msg.get_time())

    def run(self):
        crashlog_ref_model = CRASHLOG_REFERENCE_MODEL(mcerr_types=mcerr_types, counter=3)
        last_tran_time = 0

        print(COLORS.RED + "****** Checking Crashlog Flow ******")

        for tran in self._get_crashlog_flow_msgs():
            if self.reset_db.had_reset(last_tran_time, tran.get_time(), detect_warm_reset=False, detect_pkg_c=False):
                crashlog_ref_model.reset_ccf_and_module_id_info()
                print(COLORS.PURPLE + "RESET  - Crashlog - SYSTEM")

            if is_ccf_info_reset(tran):
                crashlog_ref_model.reset_ccf_and_module_id_info()
                print(COLORS.PURPLE + "RESET  - Crashlog - SB MSG")
            elif is_mcerr_msg(tran):
                crashlog_info = CRASHLOG_INFO(
                    src_pid=tran.src_pid,
                    dest_pid=tran.dest_pid,
                    opcode=tran.opcode,
                    start_time=tran.start_time,
                    end_time=tran.time,
                    valid=1 if tran.src_pid in SB.EPS.internal_cores else 0,
                    ccf_id=UNIQUE_DEFINES.ccf_id,
                    module_id=get_core_num(tran.src_pid),
                    events=list(filter(lambda ev: ev in mcerr_types, self.events_decoder.decode(tran)))
                )
                crashlog_ref_model.add_exp_events(crashlog_info=crashlog_info)
                print(COLORS.YELLOW + crashlog_info.to_string())
            elif is_crashlog_msg(tran):
                crashlog_info = CRASHLOG_INFO(
                    src_pid=tran.src_pid,
                    dest_pid=tran.dest_pid,
                    opcode=tran.opcode,
                    start_time=tran.start_time,
                    end_time=tran.time,
                    valid=tran.flat_data[7],
                    ccf_id=tran.flat_data[9:8],
                    module_id=tran.flat_data[6:0],
                    events=self.events_decoder.decode(tran)
                )
                print(COLORS.LIGHT_PURPLE + crashlog_info.to_string())
                if not crashlog_ref_model.update(report_info=crashlog_info):
                    pass
                    # break
            last_tran_time = tran.get_time()
        print(COLORS.RED + "****** End ******\n")
