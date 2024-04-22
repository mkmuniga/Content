from val_utdb_base_components import EOT
from val_utdb_components import val_utdb_qry

from agents.nc_common.ccf_nc_unique_defines import UNIQUE_DEFINES

def do_not_set(value, bar_mode):
    return (bar_mode and value == 1) or (not bar_mode and value == 0)

class NC_RESET_DB(val_utdb_qry):

    def __init__(self):
        self.ccf_id = UNIQUE_DEFINES.ccf_id
        self._reset_db = list()
        self._q_restore_db = list()
        self._sleep_db = list()
        self._not_power_good_db = list()
        self._all_recs = None
        self._valid_recs = None
        self._reset_recs = None
        self._q_restore_recs = None
        self._sleep_recs = None
        self._power_good_recs = None
        self._all_valid_reset_recs = None
        self._all_valid_q_restore_recs = None
        self._all_valid_sleep_recs = None
        self._all_valid_power_good_recs = None

    def queries(self):
        self._all_recs = self.DB.all.TIME >= 0
        self._valid_recs = self.DB.all.REC_TYPE == ("valid")
        self._reset_recs = self.DB.all.SIGNAL_NAME.contains("NCRadecsResetU004H")
        self._sleep_recs = self.DB.all.SIGNAL_NAME.contains("pm_idi_bridge_sleep")
        self._q_restore_recs = self.DB.all.SIGNAL_NAME.contains("QRestoreU002H")
        self._power_good_recs = self.DB.all.SIGNAL_NAME.contains("NCpwrgoodU004H")
        self._all_valid_reset_recs = self._all_recs & self._valid_recs & self._reset_recs
        self._all_valid_q_restore_recs = self._all_recs & self._valid_recs & self._q_restore_recs
        self._all_valid_sleep_recs = self._all_recs & self._valid_recs & self._sleep_recs
        self._all_valid_power_good_recs = self._all_recs & self._valid_recs & self._power_good_recs

    def build_db(self):
        self._set_dbs(self._not_power_good_db, self._all_valid_power_good_recs, bar_mode=True)
        self._set_dbs(self._reset_db, self._all_valid_reset_recs, bar_mode=False)
        if self.ccf_id == 0:
            self._set_dbs(self._q_restore_db, self._all_valid_q_restore_recs, bar_mode=False)
        else:
            self._set_dbs(self._sleep_db, self._all_valid_sleep_recs, bar_mode=False)

    def get_start_reset_times(self, detect_warm_reset=True, detect_cold_reset=True, detect_pkg_c=True):
        start_reset_times = list()
        for times_range in self._reset_db:
            if (detect_warm_reset and self._is_warm_reset(start_time=times_range[0], end_time=times_range[1])) or \
                    (detect_cold_reset and self._is_cold_reset(start_time=times_range[0],
                                                               end_time=times_range[1])) or \
                    (detect_pkg_c and self._is_pkg_c_reset(start_time=times_range[0], end_time=times_range[1])):
                start_reset_times.append(times_range[0])
        return start_reset_times

    def get_out_of_reset_times(self, detect_warm_reset=True, detect_cold_reset=True, detect_pkg_c=True):
        out_of_reset_times = list()
        for times_range in self._reset_db:
            if (detect_warm_reset and self._is_warm_reset(start_time=times_range[0], end_time=times_range[1])) or \
                (detect_cold_reset and self._is_cold_reset(start_time=times_range[0], end_time=times_range[1])) or \
                    (detect_pkg_c and self._is_pkg_c_reset(start_time=times_range[0], end_time=times_range[1])):
                if times_range[1] != EOT:
                    out_of_reset_times.append(times_range[1] + 1)
                else:
                    out_of_reset_times.append(times_range[1])
        return out_of_reset_times

    def had_reset(self, start_time, end_time, detect_warm_reset=True, detect_cold_reset=True, detect_pkg_c=True):
        for time_range in self._reset_db:
            reset_start_time = time_range[0]
            reset_end_time = end_time + 1 if time_range[1] == EOT else time_range[1]
            if reset_start_time <= start_time <= reset_end_time or \
                    reset_start_time <= end_time <= reset_end_time or \
                    start_time <= reset_start_time <= reset_end_time <= end_time:
                if (detect_warm_reset and self._is_warm_reset(reset_start_time, reset_end_time)) or \
                        (detect_cold_reset and self._is_cold_reset(reset_start_time, reset_end_time)) or \
                        (detect_pkg_c and self._is_pkg_c_reset(reset_start_time, reset_end_time)):
                    return True
        return False

    def _set_dbs(self, db, qry, bar_mode=False):
        last_change = None
        for events in self.DB.execute(self.DB.flow(qry['+'])):
            for event in events.EVENTS:
                if last_change is not None:
                    if last_change[1] != event.DATA0:
                        if do_not_set(event.DATA0, bar_mode):
                            db.append((last_change[0], event.TIME - 1))
                        last_change = (event.TIME, event.DATA0)
                else:
                    last_change = (event.TIME, event.DATA0)
        if not do_not_set(last_change[1], bar_mode):
            db.append((last_change[0], EOT))

    def _had_no_power_good(self, start_time, end_time):
        for times_range in self._not_power_good_db:
            if EOT in [times_range[1], end_time]:
                return start_time <= times_range[0] and (times_range[1] == end_time or times_range[1] == EOT)
            elif start_time <= times_range[0] <= times_range[1] <= end_time:
                return True
        return False

    def _during_sleep(self, start_time, end_time):
        for times_range in self._sleep_db:
            if times_range[1] == EOT:
                return times_range[0] < start_time
            elif end_time != EOT and (times_range[0] < start_time <= end_time < times_range[1]):
                return True
        return False

    def _during_q_restore(self, start_time, end_time):
        for times_range in self._q_restore_db:
            if start_time < times_range[0] and (end_time == EOT or times_range[0] < end_time):
                return True
        return False

    def _is_warm_reset(self, start_time, end_time):
        during_sleep = self._during_sleep(start_time, end_time) if self.ccf_id == 1 else self._during_q_restore(start_time, end_time)
        return not self._had_no_power_good(start_time, end_time) and not during_sleep

    def _is_cold_reset(self, start_time, end_time):
        during_sleep = self._during_sleep(start_time, end_time) if self.ccf_id == 1 else self._during_q_restore(start_time, end_time)
        return self._had_no_power_good(start_time, end_time) and not during_sleep

    def _is_pkg_c_reset(self, start_time, end_time):
        during_sleep = self._during_sleep(start_time, end_time) if self.ccf_id == 1 else self._during_q_restore(start_time, end_time)
        return self._had_no_power_good(start_time, end_time) and during_sleep
