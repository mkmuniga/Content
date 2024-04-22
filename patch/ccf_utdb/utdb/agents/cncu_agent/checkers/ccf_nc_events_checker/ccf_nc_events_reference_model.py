from val_utdb_base_components import EOT
from val_utdb_report import VAL_UTDB_ERROR
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from agents.cncu_agent.checkers.ccf_nc_events_checker.ccf_nc_events_types import EXPECTED_ITEM, EVENT_INFO
from agents.cncu_agent.common.cncu_defines import EVENTS_TYPES


class EVENTS_REFERENCE_MODEL:
    def __init__(self, name="EVENTS_REFERENCE_MODEL", events_types=list(), counter=4, defeatured_bits={}, enabled=True):
        self.name = name
        self.ral_utils: NC_RAL_AGENT = NC_RAL_AGENT.get_pointer()
        self.ref_model = dict()
        self.counter = counter
        self.defeatured_bits = defeatured_bits
        self.enabled = enabled
        for ev_type in events_types:
            self.ref_model[ev_type] = list()

    def __del__(self):
        pending_events = list()
        for ev_type in self.ref_model:
            for exp_item in self.ref_model[ev_type]:
                if not exp_item.may_reported:
                    pending_events.append(ev_type)
                    break

        if len(pending_events) > 0:
            VAL_UTDB_ERROR(time=EOT,
                           msg=self._get_err_msg(
                               event_info=None,
                               err_msg="Pending events at EOT:\n" + ", ".join(pending_events))
                           )

    def add_exp_events(self, event_info: EVENT_INFO):
        if self.enabled:
            for ev in event_info.events:
                if not (ev in self.defeatured_bits and self.defeatured_bits[ev]):
                    ev = ev
                    self.ref_model[ev].append(EXPECTED_ITEM(info=event_info, counter=self.counter))

    def update(self, report_info: EVENT_INFO):
        if self.enabled:
            return self._check_reported_in_expected_items(report_info=report_info) and \
                   self._remove_reported_from_expected_items(report_info=report_info) and \
                   self._update_reported_expected_status(report_info=report_info) and \
                   self._update_counters(report_info=report_info)
        else:
            VAL_UTDB_ERROR(time=report_info.get_time(),
                           msg=self._get_err_msg(
                               event_info=report_info,
                               err_msg="Report to disabled EP(" + hex(report_info.dest_pid) + ")")
                           )
            return False

    def _check_reported_in_expected_items(self, report_info: EVENT_INFO):
       for ev in report_info.events:
                if ev in self.ref_model and len(self.ref_model[ev]) == 0:
                    VAL_UTDB_ERROR(time=report_info.get_time(),
                                   msg=self._get_err_msg(
                                       event_info=report_info,
                                       err_msg="Got " + ev + " event, which is not in expected")
                                   )
                    return False
       return True

    def _get_first_not_may_reported_channel(self, ev):
        for exp_item in self.ref_model[ev]:
            if not exp_item.may_reported:
                return exp_item.get_channel()
        return self.ref_model[ev][0].get_channel()

    def _get_slowest_channel(self):
        slowest_channel = None
        for ev in self.ref_model:
            if len(self.ref_model[ev]) > 0:
                cur_channel = self._get_first_not_may_reported_channel(ev)
                if slowest_channel is None or cur_channel < slowest_channel:
                    slowest_channel = cur_channel
        return slowest_channel

    def _get_smallest_event_time_in_ref_model(self):
        smallest_time = None
        for ev in self.ref_model:
            if len(self.ref_model[ev]) > 0 and \
                    (smallest_time is None or self.ref_model[ev][0].get_time() < smallest_time):
                smallest_time = self.ref_model[ev][0].get_time()
        return smallest_time

    def _get_last_reported_event_time(self, report_info: EVENT_INFO) -> EVENT_INFO:
        biggest_time = -1
        slowest_channel = self._get_slowest_channel()

        for ev in report_info.events:
            if ev in self.ref_model:
                if len(self.ref_model[ev]) > 0 and slowest_channel == self.ref_model[ev][0].get_channel() and \
                        self.ref_model[ev][0].get_time() > biggest_time:
                    biggest_time = self.ref_model[ev][0].get_time()

        return biggest_time if biggest_time != -1 else self._get_smallest_event_time_in_ref_model()

    def _remove_reported_from_expected_items(self, report_info: EVENT_INFO):
        last_reported_event_time = self._get_last_reported_event_time(report_info=report_info)

        for ev_type in self.ref_model:
            update_exp_items_list = list()
            for i, exp_item in enumerate(self.ref_model[ev_type]):
                if exp_item.get_time() == last_reported_event_time and (i > 0 or ev_type not in report_info.events):
                    update_exp_items_list.append(exp_item)
                elif exp_item.get_time() > last_reported_event_time:  # TODO PTL mlugassi remove the '=' after using real pmon overflow (not wire) - if exp_item.get_time() > last_reported_event_time:
                    update_exp_items_list.append(exp_item)
                elif ev_type not in report_info.events and not exp_item.may_reported:
                    VAL_UTDB_ERROR(time=report_info.get_time(),
                               msg=self._get_err_msg(
                                   event_info=report_info,
                                   err_msg="Expected that " + ev_type + " event to be reported, since RTL has "
                                                                        "reported on event which arrived at "
                                           + str(last_reported_event_time))
                               )
                    return False
            self.ref_model[ev_type] = update_exp_items_list
        return True

    def _update_reported_expected_status(self, report_info: EVENT_INFO):
        for ev in report_info.events:
            if ev in self.ref_model:
                for exp_item in self.ref_model[ev]:
                    exp_item.may_reported = True
        return True

    def _update_counters(self, report_info: EVENT_INFO):
        for ev_type in self.ref_model:
            update_exp_items_list = list()
            for exp_item in self.ref_model[ev_type]:
                if exp_item.counter > 0:
                    exp_item.counter -= 1
                    update_exp_items_list.append(exp_item)
                elif not exp_item.may_reported:
                    VAL_UTDB_ERROR(time=report_info.get_time(),
                                   msg=self._get_err_msg(
                                       event_info=report_info,
                                       err_msg="Expected that " + ev_type + " event to be reported, since RTL didn't report on"
                                                                            " it in the last " + str(self.counter) +
                                               " reporting messages")
                                   )
                    return False
            self.ref_model[ev_type] = update_exp_items_list
        return True

    def _get_err_msg(self, event_info: EVENT_INFO, err_msg):
        event_info_msg = "\nEvent Info:\n" + event_info.to_string() + "\n" if event_info is not None else ""

        return "\n" + self.name + ":\n\n" + \
               event_info_msg + \
               "\nError Message:\n" + err_msg + \
               "\n\nDefeatured Bits:\n" + self._defeature_bits_to_string() + \
               "\n\nReferece Model:\n" + self._ref_model_to_string()

    def _ref_model_to_string(self):
        ref_model_str_list = [ev_type + ": " + ",".join([str(item) for item in exp_items])
                              for ev_type, exp_items in self.ref_model.items() if len(exp_items) > 0]
        if len(ref_model_str_list) > 0:
            return "\n".join(ref_model_str_list)
        return "Reference Model Is Empty"

    def _defeature_bits_to_string(self):
        defeature_bits_str_list = [ev_type + ": " + str(val) for ev_type, val in self.defeatured_bits.items()]
        if len(defeature_bits_str_list) > 0:
            return "\n".join(defeature_bits_str_list)
        return "No Defeature bits Were Set"
