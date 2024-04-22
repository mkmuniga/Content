#!/usr/bin/env python3.6.3a
#################################################################################################
# cncu_types.py
#
# Owner: ranzohar & mlugassi
# Creation Date:      5/2020
#
# ###############################################
#
# Description:
#
#################################################################################################
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import bytes_to_str, DoNotCheck


class BASE_TRANSACTION:

    def __repr__(self):
        return self.to_string()

    def to_string(self, attrs=None):
        self_str = ""
        for attr, value in vars(self).items():
            if attrs is None or attr in attrs:
                if value is not None and value is not DoNotCheck:
                    if attr in self._get_attr_to_print_in_hex():
                        self_str += attr.upper() + ": " + hex(value) + ", "
                    elif attr in self._get_attr_to_print_in_bytes():
                        self_str += attr.upper() + ": " + bytes_to_str(value) + ", "
                    else:
                        self_str += attr.upper() + ": " + str(value) + ", "

        return "{0:<16} {1}".format(type(self).__name__ + ":", self_str.rstrip(", "))

    def _get_attr_to_print_in_hex(self):
        return []

    def _get_attr_to_print_in_bytes(self):
        return []

    def _get_needed_attributes(self):
        return None

    def check_tran_values(self):
            needed_attrs_without_values = list()
            non_needed_attrs_with_values = list()
            needed_attrs = self._get_needed_attributes()

            if needed_attrs is not None:
                for attr, value in vars(self).items():
                    if attr in needed_attrs and value is None:
                        needed_attrs_without_values.append(attr.upper())
                    elif attr not in needed_attrs and value is not None and value is not DoNotCheck:
                        non_needed_attrs_with_values.append(attr.upper())

            return needed_attrs_without_values, non_needed_attrs_with_values

    def get_attrs(self):
        return [attr for attr, value in vars(self).items() if (value is not DoNotCheck and value is not None)]

    def get_uri(self):
        raise NotImplementedError()

    def get_time(self):
        raise NotImplementedError()
