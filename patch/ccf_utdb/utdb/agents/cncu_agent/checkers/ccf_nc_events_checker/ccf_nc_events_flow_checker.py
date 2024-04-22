from itertools import combinations_with_replacement

from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from griffin_collaterals.griffin_bint import bint

from val_utdb_base_components import EOT
from val_utdb_components import val_utdb_chk

from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_decoder import EVENTS_DECODER
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_reference_model import \
    EVENTS_REFERENCE_MODEL
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_types import COLORS, EVENT_INFO
from agents.cncu_agent.common.ccf_nc_common_base import CCF_NC_CONFIG
from agents.cncu_agent.common.cncu_defines import EVENTS_TYPES, SB, SAI
from agents.cncu_agent.common.cncu_types import SEQ_TRK_ITEM, SB_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_pmon_overflow_db import NC_PMON_OVERFLOW_DB
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.dbs.ccf_nc_seq_trk_qry import CCF_NC_SEQ_TRK_QRY
from agents.cncu_agent.utils.nc_systeminit import NC_SI


def _get_events_with_unite_mcerr_events(events):
    events_with_unite_mcerr_events = list()
    for ev in events:
        if ev in [EVENTS_TYPES.umcnf, EVENTS_TYPES.umcf, EVENTS_TYPES.ierr, EVENTS_TYPES.exterr]:
            if EVENTS_TYPES.mcerr not in events_with_unite_mcerr_events:
                events_with_unite_mcerr_events.append(EVENTS_TYPES.mcerr)
        else:
            events_with_unite_mcerr_events.append(ev)
    return events_with_unite_mcerr_events


class SNCU_EVENTS_FLOW_CHECKER(val_utdb_chk):

    def __init__(self):
        self.set_si(NC_SI.get_pointer())
        self.ral_utils: NC_RAL_AGENT = NC_RAL_AGENT.get_pointer()
        self.cfg: CCF_NC_CONFIG = CCF_NC_CONFIG.get_pointer()
        self.sb_db: CCF_NC_SB_DB = CCF_NC_SB_DB.get_pointer()
        self.events_decoder = EVENTS_DECODER()

    def _get_downstream_sb_events_msgs(self):
        def is_downstream_event(sb_msg: SB_TRANSACTION):
            return (sb_msg.opcode == SB.OPCODES.mclk_event) or \
                   (sb_msg.opcode == SB.OPCODES.cr_wr and sb_msg.addr == 0x48 and sb_msg.dest_pid == SB.EPS.ncevents)

        sb_msgs = self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.mclk_event, SB.OPCODES.cr_wr],
                                               start_time=0,
                                               end_time=EOT,
                                               filter_func=is_downstream_event)


        return sb_msgs

    def _get_upstream_sb_events_msgs(self, core_num):
        def is_upstream_event(sb_msg: SB_TRANSACTION):
            return (sb_msg.opcode == SB.OPCODES.fclk_event) or \
                   (sb_msg.opcode == SB.OPCODES.cr_wr and sb_msg.sai == SAI.hw_cpu and
                    sb_msg.addr == 0x48 and sb_msg.dest_pid == SB.EPS.internal_cores[core_num]) or \
                   (sb_msg.opcode == SB.OPCODES.cr_wr and sb_msg.addr == 0x5070 and sb_msg.dest_pid == SB.EPS.ncevents)

        return self.sb_db.get_trans_at_time(opcodes=[SB.OPCODES.fclk_event, SB.OPCODES.cr_wr],
                                            start_time=0,
                                            end_time=EOT,
                                            filter_func=is_upstream_event)

    def _get_events_info(self, flow_name, events_items):
        events_info = list()

        for i, ev in enumerate(events_items):
            if type(ev) == SB_TRANSACTION:
                event_info: EVENT_INFO = EVENT_INFO(
                    flow_name=flow_name,
                    start_time=ev.get_start_time(),
                    end_time=ev.get_time(),
                    src_pid=ev.get_src(),
                    dest_pid=ev.get_dest(),
                    opcode=ev.opcode,
                    events=self.events_decoder.decode(ev)
                )
            events_info.append(event_info)
        return sorted(events_info, key=lambda info: info.get_time())

    def _check_downstream_events_flows(self):
        ds_incoming_events = self._get_events_info(flow_name="Downstream",
                                                   events_items=self._get_downstream_sb_events_msgs())
        ds_ref_model: EVENTS_REFERENCE_MODEL = EVENTS_REFERENCE_MODEL(name="DOWNSTREAM_REF_MODEL",
                                                                      defeatured_bits={
                                                                      },
                                                                      events_types=EVENTS_TYPES.get_events_types())
        print(COLORS.RED + "****** Checking Downstream Events Flow ******")

        for i, ev in enumerate(ds_incoming_events):
            ev.print(color=True)
            if ev.is_incoming_event():
                ds_ref_model.add_exp_events(event_info=ev)
            else:
                if not ds_ref_model.update(report_info=ev):
                    pass
                    # break

        print(COLORS.RED + "****** End ******\n")

    def _check_upstream_events_flows(self, core_num):
        a = bint(self.ral_utils.read_reg_field("ncevents", "NCUOWNIAMVECTOR", "COREVEC", EOT))[core_num]
        print(f"aaaaaaaaa {core_num} {self.si.module_disable_mask[core_num]} {a} ")
        us_incoming_events = self._get_events_info(flow_name="Upstream Core" + str(core_num),
                                                   events_items=self._get_upstream_sb_events_msgs(core_num=core_num))
        us_ref_model: EVENTS_REFERENCE_MODEL = EVENTS_REFERENCE_MODEL(
            name="UPSTREAM_CORE" + str(core_num) + "_REF_MODEL",
            defeatured_bits={
                EVENTS_TYPES.llbbrk: self.cfg.dis_llb_to_cores,
            },
            events_types=EVENTS_TYPES.get_events_types(),
            enabled=(
                (self.si.module_disable_mask[core_num] == 0) and
                (bint(self.ral_utils.read_reg_field("ncevents", "NCUOWNIAMVECTOR", "COREVEC", EOT))[core_num] == 1)
            )
        )

        print(COLORS.RED + "****** Checking Upstream Events Flow Core" + str(core_num) + " ******")

        for i, ev in enumerate(us_incoming_events):
            ev.print(color=True)
            if ev.is_incoming_event():
                ev.events = _get_events_with_unite_mcerr_events(events=ev.events)
                us_ref_model.add_exp_events(event_info=ev)
            else:
                if not us_ref_model.update(report_info=ev):
                    pass
                    # break
        print(COLORS.RED + "****** End ******\n")

    def run(self):
        self._check_downstream_events_flows()
        for core_num in range(self.cfg.num_of_modules*4):#TODO make sysinit value - ranzo num of clusters
            self._check_upstream_events_flows(core_num)
