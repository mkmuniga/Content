from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR
from val_utdb_base_components import EOT

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_types import BASE_TRANSACTION
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import flat_nested_lists, compare_trans, \
    find_tran, find_tran_and_idx, find_tran_idx, data_bytes_to_flat_data, DoNotCheck


class BASE_FLOW:

    @staticmethod
    def is_new_flow(tran):
        raise NotImplementedError()

    def __init__(self, flow):
        self._configure(flow)

    def _configure(self, flow):
        self.__set_initial_values()
        self._set_actual(flow)
        self._set_expected()

    def check(self):
        self.__check_trans_attributes()
        if self.checker_enabled():
            self.__check_flow()
            self._additional_checks()

    def sample_cov(self):
        pass

    def checker_enabled(self):
        raise NotImplementedError()

    def __set_initial_values(self):
        self._flow_fsm = dict()
        self._act_flow = list()
        self.__curr_fsm_state = 0

    def _set_actual(self, flow=None):
        self._set_act_flow(flow)
        self._set_flow_info(flow)

    def _set_expected(self):
        self._set_expected_values()
        self._set_flow_fsm()

    def _set_act_flow(self, flow):
        self._act_flow = flow

    def _set_flow_info(self, flow):
        if len(self._act_flow) > 0:
            self._initial_tran = self._get_flow_initial_tran()
            self._sai = self._get_flow_sai()
            self._byteen = self._get_flow_byteen()
            self._length = self._get_flow_length()
            self._data = self._get_flow_data()
            if self._data not in [None, DoNotCheck] and self._data != [DoNotCheck, DoNotCheck]:
                self._flat_data = bint(0)
                for i, data in enumerate(self._data):
                    self._flat_data[len(data) * (i + 1) * 8 - 1: len(data) * i * 8] = data_bytes_to_flat_data(data)

    def _set_expected_values(self):
        pass

    def _set_flow_fsm(self):
        raise NotImplementedError()

    def _additional_checks(self):
        pass

    def __check_trans_attributes(self):
        for state in self._flow_fsm:
            for tran in self._flow_fsm[state]:
                needed_attrs_without_values, non_needed_attrs_with_values = tran.check_tran_values()
                if len(needed_attrs_without_values) > 0:
                    VAL_UTDB_ERROR(time=0,
                                   msg="\n******** Attribute Error In Bubble #" + str(state) + " ********\n" +
                                       "Not all needed attributes were set\n\n" +
                                       "URI: " + self._uri +
                                       "\n\nMissing Attributes:\n" +
                                       ', '.join(needed_attrs_without_values) +
                                       "\n\nFull Packet:\n" + tran.to_string())
                if len(non_needed_attrs_with_values) > 0:
                    VAL_UTDB_ERROR(time=0,
                                   msg="\n******** Attribute Error In Bubble #" + str(state) + " ********\n" +
                                       "Not needed Attributes Were Set\n\nNot needed attributes:\n" +
                                       ', '.join(non_needed_attrs_with_values) +
                                       "\n\nFull Packet:\n" + tran.to_string())

    def __check_act_tran(self, act_tran):
        err_msg = "\n******** Flow Mismatch In Bubble #" + str(self.__curr_fsm_state) + " ********\n" + \
                  "\nTime: " + str(act_tran.time) + \
                  "\nURI: " + act_tran.uri + \
                  "\n\nDescription:\n"

        if len(self._flow_fsm) == 0:
            VAL_UTDB_ERROR(time=act_tran.get_time(),
                           msg=err_msg + "Got an actual transaction while we don't expected for more transactions\n" +
                               "\nActual transaction:\n" + self.__act_tran_str(act_tran))
            return False

        for i, exp_tran in enumerate(self._flow_fsm[self.__curr_fsm_state]):
            comp_res, hint = compare_trans(exp_tran, act_tran)
            err_msg += hint
            if comp_res:
                self._flow_fsm[self.__curr_fsm_state].pop(i)
                break
            elif i == len(self._flow_fsm[self.__curr_fsm_state]) - 1:
                VAL_UTDB_ERROR(time=act_tran.get_time(),
                               msg=err_msg +
                                   "\nActual transaction:\n" + self.__act_tran_str(act_tran) +
                                   "\nExpected transactions:\n" + self.__exp_trans_str())
                return False

        if len(self._flow_fsm[self.__curr_fsm_state]) == 0:
            del self._flow_fsm[self.__curr_fsm_state]
            self.__curr_fsm_state += 1
        return True

    def __check_flow(self):
        for tran in self._act_flow:
            if self.__check_act_tran(tran) is False:
                return
        if len(self._flow_fsm) > 0:
            VAL_UTDB_ERROR(time=EOT,
                           msg="\n******** Flow Did Not Complete ********\n" +
                               "\nURI: " + self._uri +
                               "\nStopped in FSM state: " + str(self.__curr_fsm_state) +
                               "\n\nTransaction in FSM:\n" +
                               self.__exp_trans_str(just_curr_state=False)
                           )

    def _add_fsm_bubble(self, *trans, add_new_bubble=True, append_to_last_bubble=False, append_to_idx=None):
        bubble_idx = append_to_idx
        if bubble_idx is None:
            if append_to_last_bubble:
                bubble_idx = len(self._flow_fsm) - 1
            elif add_new_bubble:
                bubble_idx = len(self._flow_fsm)
                self._flow_fsm[bubble_idx] = list()
            else:
                raise Exception("Must to provide any index indication")

        self._flow_fsm[bubble_idx] += flat_nested_lists(trans)

    def __get_exp_trans(self, just_curr_state=True):
        exp_trans = []
        if len(self._flow_fsm) != 0:
            if just_curr_state:
                for tran in self._flow_fsm[self.__curr_fsm_state]:
                    exp_trans.append(tran)
            else:
                for state in self._flow_fsm:
                    for tran in self._flow_fsm[state]:
                        exp_trans.append(tran)
        return exp_trans

    def __get_exp_attrs(self, just_curr_state=True):
        attrs = []
        for tran in self.__get_exp_trans(just_curr_state):
            attrs += tran.get_attrs()

        if len(attrs) > 0:
            return list(dict.fromkeys(attrs))
        return None

    def __act_tran_str(self, act_tran):
        return act_tran.to_string(self.__get_exp_attrs()) + "\n"

    def __exp_trans_str(self, just_curr_state=True):
        msg = ""
        for tran in self.__get_exp_trans(just_curr_state):
            msg += tran.to_string() + "\n"
        return msg

    def _find_tran_and_idx(self, tran: BASE_TRANSACTION, get_all_matches=False):
        return find_tran_and_idx(tran, self._act_flow, get_all_matches)

    def _find_tran(self, tran: BASE_TRANSACTION, get_all_matches=False):
        return find_tran(tran, self._act_flow, get_all_matches)

    def _find_tran_idx(self, tran: BASE_TRANSACTION, get_all_matches=False):
        return find_tran_idx(tran, self._act_flow, get_all_matches)

    def _check_arriving_order(self, before, after):
        not_in_order_dict = dict()
        before = before if type(before) is list else [before]
        after = after if type(after) is list else [after]

        for after_tran in after:
            after_tran = self._find_tran(after_tran)
            if after_tran is not None:
                for before_tran in before:
                    before_tran = self._find_tran(before_tran)
                    if before_tran is not None:
                        if after_tran.get_time() <= before_tran.get_time():
                            if after_tran not in not_in_order_dict.keys():
                                not_in_order_dict[after_tran] = list()
                            not_in_order_dict[after_tran].append(before_tran)

        if len(not_in_order_dict) > 0:
            msg_header = "\n****** Transactions Were Sent Not In The Right Order ******" + \
                         "\nURI: " + self._uri + "\n"
            err_msg = '\n\n'.join(["\nTransaction:\n" + after_tran.to_string() +
                                   "\n\nArrived before the transactions below:\n" +
                                   "\n".join([before_tran.to_string() for before_tran in not_in_order_dict[after_tran]])
                                   for after_tran in not_in_order_dict])
            VAL_UTDB_ERROR(time=0, msg=msg_header + err_msg)

    @property
    def _uri(self):
        return self._get_flow_uri()

    @property
    def _start_time(self):
        return self._get_flow_start_time()

    @property
    def _end_time(self):
        return self._get_flow_end_time()

    def _get_flow_initial_tran(self) -> BASE_TRANSACTION:
        return self._act_flow[0]

    def _get_flow_uri(self):
        return self._get_flow_initial_tran().get_uri()

    def _get_flow_start_time(self):
        return self._get_flow_initial_tran().get_time()

    def _get_flow_end_time(self):
        return self._act_flow[-1].get_time()

    def _get_flow_sai(self):
        raise NotImplementedError()

    def _get_flow_data(self):
        raise NotImplementedError()

    def _get_flow_byteen(self):
        raise NotImplementedError()

    def _get_flow_length(self):
        raise NotImplementedError()
