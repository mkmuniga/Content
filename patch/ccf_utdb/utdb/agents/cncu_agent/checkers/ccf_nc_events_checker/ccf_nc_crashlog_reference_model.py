from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_reference_model import \
    EVENTS_REFERENCE_MODEL
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_types import EVENT_INFO, CRASHLOG_INFO
from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES


class CRASHLOG_REFERENCE_MODEL(EVENTS_REFERENCE_MODEL):
    def __init__(self, name="CRASHLOG_REFERENCE_MODEL", counter=2, defeatured_bits={}, mcerr_types=list(),
                 enabled=True):
        super().__init__(name=name, counter=counter, defeatured_bits=defeatured_bits,
                         enabled=enabled, events_types=mcerr_types)
        self.counter = counter
        self.reporters_info = [{"valid": 0, "ccf_id": UNIQUE_DEFINES.ccf_id, "module_id": 0, "counter": counter}]

    def add_exp_events(self, crashlog_info: CRASHLOG_INFO):
        self._update_ccf_and_module_info(crashlog_info=crashlog_info)
        super().add_exp_events(event_info=crashlog_info)

    def reset_ccf_and_module_id_info(self):
        self.reporters_info.insert(0, {"valid": 0, "ccf_id": UNIQUE_DEFINES.ccf_id, "module_id": 0,
                                       "counter": self.counter})

    def update(self, report_info: EVENT_INFO):
        if self.enabled:
            check_ccf_and_module_info_res = self._check_ccf_and_module_info(report_info=report_info)
            update_reporters_info_counters_res = self._update_reporters_info_counters()

            for ev in report_info.events:
                if ev in self.ref_model:
                    return check_ccf_and_module_info_res and update_reporters_info_counters_res and \
                           super().update(report_info=report_info)
            return check_ccf_and_module_info_res and update_reporters_info_counters_res
        else:
            VAL_UTDB_ERROR(time=report_info.get_time(),
                           msg=self._get_err_msg(
                               event_info=report_info,
                               err_msg="Report to disabled EP(" + hex(report_info.dest_pid) + ")")
                           )
            return False

    def _update_ccf_and_module_info(self, crashlog_info: CRASHLOG_INFO):
        if crashlog_info.valid == 1 and self.reporters_info[0]["valid"] == 0:
            self.reporters_info.insert(0, {"valid": crashlog_info.valid,
                                           "ccf_id": crashlog_info.ccf_id,
                                           "module_id": crashlog_info.module_id,
                                           "counter": self.counter})

    def _check_ccf_and_module_info(self, report_info: CRASHLOG_INFO):
        err_msgs = list()
        for i, reporter_info in enumerate(self.reporters_info):
            if (reporter_info["valid"] == report_info.valid and reporter_info["ccf_id"] == report_info.ccf_id and
                    reporter_info["module_id"] == report_info.module_id):
                for j in range(len(self.reporters_info[i + 1:])):
                    self.reporters_info.pop()
                return True
            else:
                do_not_match_fields = list()
                if reporter_info["valid"] != report_info.valid:
                    do_not_match_fields.append("VALID = " + str(reporter_info["valid"]))
                if reporter_info["ccf_id"] != report_info.ccf_id:
                    do_not_match_fields.append("CCF_ID = " + str(reporter_info["ccf_id"]))
                if reporter_info["module_id"] != report_info.module_id:
                    do_not_match_fields.append("MODULE_ID = " + str(reporter_info["module_id"]))
                err_msgs.append(", ".join(do_not_match_fields))

        VAL_UTDB_ERROR(time=report_info.get_time(),
                       msg=self._get_err_msg(
                           event_info=report_info,
                           err_msg="CCF and ModuleId Info Mismatch:\n" + "\n".join(err_msgs)))
        return False

    def _update_reporters_info_counters(self):
        new_reporters_info = [self.reporters_info[0]]
        for reporter_info in self.reporters_info[1:]:
            if reporter_info["counter"] > 0:
                reporter_info["counter"] = reporter_info["counter"] - 1
                new_reporters_info.append(reporter_info)
        self.reporters_info = new_reporters_info
        return True
