#!/usr/bin/env python3.6.3
from agents.ccf_common_base.ccf_monitor_agent import monitor_array_snapshot
from agents.ccf_queries.ccf_coherency_qry import ccf_coherency_qry
from val_utdb_bint import bint
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_flow_chk_agent.ccf_flow_chk_cov import ccf_flow_chk_cov_sample
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from agents.ccf_common_base.ccf_common_base import ccf_idi_record_info, ccf_cfi_record_info, \
    ccf_cbo_record_info, ccf_llc_record_info, ccf_ufi_record_info
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.uxi_utils import UXI_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_csv_flows_db.ccf_csv_common import expected_interfaces
from agents.ccf_agent.ccf_coherency_agent.ccf_transition_chk import transition_chk
from agents.ccf_csv_flows_db.ccf_csv_flow_db import ccf_csv_flow_db
from agents.ccf_agent.ccf_coherency_agent.ccf_cpipe_window_utils import ccf_cpipe_window_utils
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG
from tabulate import tabulate
import UsrIntel.R1
import pandas as pd
import re

class ccf_flow_chk(ccf_coherency_base_chk):
    def __init__(self):
        self.debug_prints = True
        #self.debug_prints = False
        self.flow_bubble_trace = []
        self.flow_pipe_trace = []
        self.current_bubble = None
        self.current_arbcommand = None
        self.previous_pipe_pass_start_time = 0
        self.pipe_pass_start_time = 0
        self.pipe_pass_end_time = None
        self.next_arbcommand = None
        self.expected_activity_in_cpipe_pass = expected_interfaces()
        self.disable_interval_checker = True
        self.transition_chk = transition_chk.get_pointer()
        self.flow_csv_db = ccf_csv_flow_db.get_pointer().csv_db
        self.ccf_cpipe_window_utils = ccf_cpipe_window_utils.get_pointer()
        self.ccf_addressless_db = ccf_addressless_db.get_pointer()
        self.ccf_flow_chk_cov_sample_ptr = ccf_flow_chk_cov_sample.get_pointer()
        self.ccf_registers = ccf_registers.get_pointer()
        self.ccf_coherency_qry = ccf_coherency_qry.get_pointer()

    def reset_expected_activity_in_cpipe_pass(self):
        self.expected_activity_in_cpipe_pass.idi_u2c_req = False
        self.expected_activity_in_cpipe_pass.idi_u2c_rsp = False
        if self.expected_activity_in_cpipe_pass.direct2core_indication is False:
            self.expected_activity_in_cpipe_pass.idi_u2c_data = False
        self.expected_activity_in_cpipe_pass.idi_c2u_data = False
        self.expected_activity_in_cpipe_pass.idi_c2u_rsp = False
        self.expected_activity_in_cpipe_pass.uxi_u2c_req = False
        self.expected_activity_in_cpipe_pass.uxi_u2c_rsp = False
        self.expected_activity_in_cpipe_pass.uxi_u2c_data = False
        self.expected_activity_in_cpipe_pass.uxi_c2u_req = False
        self.expected_activity_in_cpipe_pass.uxi_c2u_data = False
        self.expected_activity_in_cpipe_pass.uxi_c2u_rsp = False

    # TODO meirlevy - we should remove this as soon as we can.
    def is_temp_exlude_coh_opcode(self, flow: ccf_flow):
        in_exclude_opcode_list = flow.opcode is not None and flow.opcode in ["SnpLDataMig"]
        return in_exclude_opcode_list or flow.is_llcwbinv() or flow.is_drd() or flow.is_non_coherent_flow()

    def should_check_flow(self, flow: ccf_flow):
        should_exclude_flow_temp = self.is_temp_exlude_coh_opcode(flow) #TODO meirlevy - we should remove this as soon as we can.
        return super().should_check_flow(flow) and not should_exclude_flow_temp \
               and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_flusher() and not flow.is_u2c_dpt_req()

    def is_dont_care(self, field):
        if type(field) is not list:
            field = [field]
        return field[0].lower() == "x"

    def is_expected_if_valid(self, field):
        return (field is not None) and (field != "0")

    def is_nc_flow_that_should_use_sideband_access(self, flow: ccf_flow):
        return (flow.is_non_coherent_flow() and CNCU_UTILS.is_nc_sb_target(bint(flow.get_address_wo_mktme_int()), flow.opcode, flow.initial_time_stamp))

    def get_opcode_and_operation(self, field):
        field_split = field.split("(")
        opcode = field_split[0].lower().strip()
        if len(field_split) > 1:
            operation = field_split[1].strip(")").lower().strip()
        else:
            operation = None
        return opcode, operation

    def df_column_can_be_merge(self, df_column, do_not_care_str='x'):
        column_valid_value = None
        a = df_column.values
        for item in a:
            item_string = str(item).lower().strip()
            if item_string != do_not_care_str and column_valid_value is None:
                column_valid_value = item_string
            elif item_string != do_not_care_str and item_string != column_valid_value:
                return False
        return True

    def llc_state_column_can_be_merge(self, df_column, llc_state, do_not_care_str='x'):
        llc_state_char = llc_state.replace('LLC_', '').lower().strip()
        a = df_column.values
        for item in a:
            item_string = str(item).lower().strip()
            if (item_string != do_not_care_str) and (llc_state_char not in item_string):
                return False
        return True

    def cv_column_can_be_merge(self, df_column, do_not_care_str='x'):
        cv_global_condition = None
        a = df_column.values
        for item in a:
            if cv_global_condition is None:
                cv_global_condition = item
            elif ((cv_global_condition == "0" and item in [">0", ">1", "1"])\
                    or (cv_global_condition == "1" and item in ["!1", ">1", "0"])\
                    or (cv_global_condition == ">0" and item in ["0"])\
                    or (cv_global_condition == ">1" and item in ["0", "1"])\
                    or (cv_global_condition == "!1" and item in ["1"])) and (item.lower().strip() != do_not_care_str):
                return False
        return True

    def column_split_and_check_merge(self, df_column, exp_str, do_not_care_str='x'):
        if exp_str is None:
            exp_snoop = "no_snoop_sent"
        else:
            exp_snoop = exp_str

        a = df_column.values
        status_l = []
        for item in a:
            tmp_status = False
            inv_status = False
            if (item.lower().strip()[0:2] == "!(") and (item.lower().strip()[-1] == ")"):
                split_item = item.strip("!(").strip(")").split("/")
                inv_status = True
            else:
                split_item = item.split("/")

            if (split_item[0].lower().strip() != do_not_care_str.lower().strip()):
                for it in split_item:
                    if ".*" in it:
                        if "!" in it:
                            tmp_status |= (not re.fullmatch(it.replace("!", "").lower().strip(), exp_snoop.lower().strip()))
                        else:
                            tmp_status |= (re.fullmatch(it.lower().strip(), exp_snoop.lower().strip()) is not None)
                    else:
                        if "!" in it:
                            tmp_status |= (not (it.replace("!", "").lower().strip() == exp_snoop.lower().strip()))
                        else:
                            tmp_status |= (it.lower().strip() == exp_snoop.lower().strip())
            else:
                #In case of don't care we consider it True
                tmp_status = True

            if(inv_status):
                tmp_status = not tmp_status

            status_l.append(tmp_status)

        return all(status_l)

    def curr_opcode_column_can_be_merge(self, df_column, current_arbcommand, do_not_care_str='x'):
        if any([True for snp_rsp in CCF_FLOW_UTILS.SNP_RSP_arbcommand if snp_rsp.lower().strip() == current_arbcommand.lower().strip()]):
            exp_table_arbcommand = "SNP_RSP"
        else:
            exp_table_arbcommand = current_arbcommand

        return self.column_split_and_check_merge(df_column, exp_table_arbcommand, do_not_care_str)

    def check_if_df_columns_can_be_merge(self, flow, df, do_not_care_str='x'):
        skip_columns = ["Row Number", "Flow Section"]
        can_merge = True
        for column in df:
            if column == "Curr Opcode":
                can_merge &= self.curr_opcode_column_can_be_merge(df[column], self.current_arbcommand)
            elif column == "LLC State":
                can_merge &= self.llc_state_column_can_be_merge(df[column], flow.initial_cache_state)
            elif column == "CV":
                can_merge &= self.cv_column_can_be_merge(df[column])
            elif column == "Snoop response":
                can_merge &= self.column_split_and_check_merge(df[column], flow.final_snp_rsp, 'x')
            elif (column not in skip_columns):
                can_merge &= self.df_column_can_be_merge(df[column], 'x')
        return can_merge

    def get_system_mode(self):
        return "ScaleUp"

    ###########################################################

    def is_non_coherent_table(self, df):
        non_coherent_list = ["NC_", "port", "int", "eoi", "clrmonitor", "nop", "LOCK", "SPLITLOCK", "UNLOCK", "Enqueue", "SpCyc"]
        return any(True for nc_str in non_coherent_list if nc_str.lower().strip() in str(df.iloc[0]["Flow"]).lower().strip())


    def is_csv_flow_table_fit_to_flow_type(self, flow, df):
        if flow.sad_results is None and not flow.is_victim():
            err_msg = "Val_Assert (is_csv_flow_table_fit_to_flow_type): sad_results is None check your code something wrong happened here."
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return False, "Fatal Assert"
        return (flow.is_victim()
                or (flow.sad_results.upper().strip() == "HOM") and not self.is_non_coherent_table(df)) \
                or ((flow.sad_results.upper().strip() != "HOM") and self.is_non_coherent_table(df)), "No Assert"


    def get_right_flow_from_csv_db(self, flow):
        for key in self.flow_csv_db.keys():
            table_opcode_list = key.split("/")
            if any(True for table_opcode in table_opcode_list if flow.opcode.lower().strip() == table_opcode.lower().strip()):
                status, val_assert = self.is_csv_flow_table_fit_to_flow_type(flow, self.flow_csv_db[key])
                if status:
                    return self.flow_csv_db[key]
                elif val_assert == "Fatal Assert":
                    return None

        return None

    ###########################################################
    def add_row_to_current_bubble_list_of_options(self, curr_state, list_of_options):
        list_of_options.append([curr_state.bubble, curr_state.snoop_response, curr_state.mode, curr_state.llc_state,
                                curr_state.cv, curr_state.map, curr_state.MonHit, curr_state.cn, curr_state.avail_data, curr_state.curr_opcode])

    def print_current_bubble_list_of_options(self,flow,list_of_options):
        titles = ["Bubble", "Sad", "Snoop response", "Mode", "LLC_state", "CV", "Map", "MonHit", "CN", "Avail_Data", "Curr_opcode"]
        table_string = "\n"
        list_of_options = [titles] + list_of_options

        for i, d in enumerate(list_of_options):
             line = '|'.join(str(x).ljust(20) for x in d)
             table_string += line + "\n"
             if i == 0:
                 table_string += '-' * len(line) + "\n"
        VAL_UTDB_MSG(time=0, msg=table_string + "\n" + flow.get_flow_info_str())

    def condition_test_all_column_rows_and_return_results_list(self, df, column_name, condition, do_not_care_str=None):
        bool_results_list = []
        for item in df[column_name]:
            condition_status = condition(item)
            bool_results_list.append(condition_status)

        return bool_results_list

    def split_and_check_value(self, input_condition, delimiter, expected_value, use_regex, do_not_care_str=None):
        inv_results = False
        results = False
        if (input_condition[0:2] == "!(") and (input_condition[-1] == ")"):
            expected_list = input_condition.strip("!(").strip(")").split(delimiter)
            inv_results = True
        else:
            expected_list = input_condition.split(delimiter)
        if expected_value is not None:
            if use_regex:
                results = any([True for exp_item in expected_list
                            if (("!" in exp_item) and (
                                re.fullmatch(exp_item.lower().strip("!"), expected_value.lower().strip()) is None))
                            or (("!" not in exp_item) and (
                                re.fullmatch(exp_item.lower().strip("!"), expected_value.lower().strip()) is not None))])

            else:
                results = any([True for exp_item in expected_list if
                            (("!" in exp_item) and (exp_item.lower().strip("!") != expected_value.lower().strip())) or (
                            ("!" not in exp_item) and (
                            exp_item.lower().strip() == expected_value.lower().strip()))])

            if inv_results:
                return (not results)
            else:
                return results

        else:
            return False

    def split_and_filter(self, item, delimiter, expected_value, use_regex, do_not_care_str=None):
        cell_value = item.lower()
        if cell_value == 'x':
            return True
        elif "&" in cell_value:
            condition_list = cell_value.replace(" ", "").split("&") #if we have spaces in the string it can cause issues.
            results_l = []
            for condition in condition_list:
                results_l.append(self.split_and_check_value(condition, delimiter, expected_value, use_regex, do_not_care_str))
            return all(results_l)
        else:
            return self.split_and_check_value(cell_value, delimiter, expected_value, use_regex, do_not_care_str)

    def create_split_and_filter_condition(self, df, column_name, exp_flow, use_regex, do_not_care_str=None):
        condition_f = lambda item: self.split_and_filter(item, "/", exp_flow, use_regex, do_not_care_str)
        return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def create_arbcommand_condition(self, df, column_name, expected_arbcommand, do_not_care_str=None):
        if any([True for snp_rsp in CCF_FLOW_UTILS.SNP_RSP_arbcommand if snp_rsp.lower().strip() == expected_arbcommand.lower().strip()]):
            expected_arbcommand = "SNP_RSP"

        condition_f = lambda item: self.split_and_filter(item, "/", expected_arbcommand, True, do_not_care_str)
        return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def create_snoop_response_condition(self, df, column_name, flow_snp_rsp, do_not_care_str=None):
        snoop_response = "no_snoop_sent" if flow_snp_rsp is None else flow_snp_rsp

        condition_f = lambda item: self.split_and_filter(item, "/", snoop_response, True, do_not_care_str)
        return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def create_df_llc_state_condition(self, df, column_name, exp_llc_state, do_not_care_str=None):
        bool_list = []
        if exp_llc_state is not None:
            llc_state = exp_llc_state.replace('LLC_', '')
            condition_f = lambda item: ((llc_state in item) or (item.lower() == do_not_care_str))
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()
        else:
            condition_f = lambda item: (item.lower() == do_not_care_str)
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def get_cv_options_from_flow(self, flow):
        if flow.initial_cv is None and flow.initial_cache_state == "LLC_I":
            return ["0", "!1"]
        #In case we have CV ERR we will consider the CV>1 or CV=1 in cases it fit the flow and snoop all cores
        elif flow.has_cv_err():
            return[">0", ">1"]
        #If force_snoop_all_cb CB is enable we will consider our transaction as CV=1 and ReqCV=0.
        elif flow.is_force_snoop_all_cb_en():
            return [">0", "1"]
        #If selfsnoop = 1 we will ignore cv_shared indication. otherwise we will consider it as >1 in case we actually have any CV that is not zero(not case where slfsnp=0 and only ReqCV=1).
        #In case of a flow that send snoop invalide like RFO we will send snoop anyway and ignore cv_is_shared.
        elif flow.flow_should_not_snoop_due_to_cv_shared_indication():
            return [">1"]
        elif flow.initial_cv_more_than_one():
            return [">0", ">1", "!1"]
        elif flow.initial_cv_zero():
            return ["0", "!1"]
        elif flow.initial_cv_one():
            # if we are not IDI req flow or we are Victim we don't need any selfsnoop calculation and we return True.
            if flow.is_victim() or flow.flow_origin != "IDI REQ":
                return [">0","1"]
            elif flow.need_to_selfsnoop_req_core() or not flow.req_core_initial_cv_bit_is_one():
                return [">0", "1"]
            # If we are IDI req there is a case using selfsnoop calculation that even if we have one CV bit up we still consider it as CV=0 or CV != 1
            elif flow.flow_origin == "IDI REQ" and (not flow.need_to_selfsnoop_req_core() and flow.req_core_initial_cv_bit_is_one()):
                return ["0", "!1"]
        else:
            err_msg = "Val_Assert (get_cv_options_from_flow): Default Answer is false but we shouldn't got to default answer in this function. check it."
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return []


    def create_df_cv_condition(self, df, column_name, flow, do_not_care_str=None):
        non_coherent_opcode_without_cv_support = ["PORT_OUT", "PORT_IN", "INTLOG", "INTPHY", "INTPRIUP", "INTA", "NOP", "EOI", "CLRMONITOR", "LOCK", "SPLITLOCK", "UNLOCK", "ENQUEUE","SPCYC"]
        if flow.initial_cv is None and (flow.opcode in non_coherent_opcode_without_cv_support):
            condition_f = lambda item: (item.lower() == do_not_care_str)
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()
        else:
            cv_option_list = self.get_cv_options_from_flow(flow)
            condition_f = lambda item: ((item in cv_option_list) or (item.lower() == do_not_care_str))
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def create_map_condition(self, df, column_name, flow, do_not_care_str=None):
        if flow.initial_map_sf():
            map_option_list = ["SF"]
        else:
            map_option_list = ["Data", "D", "DATA"]

        condition_f = lambda item: ((item in map_option_list) or (item.lower() == do_not_care_str))
        return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def prefetch_upi_rd_misc_condition(self, flow: ccf_flow, item):
        actual_trans = self.ccf_flows[flow.promotion_flow_orig_pref_uri].get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="REQ")
        if (len(actual_trans) != 1):
            err_msg = "Val_Assert (prefetch_upi_rd_misc_condition): we didn't expect to have more then 1 UXI C2U REQ at this flow"
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return False
        else:
            upi_opcode = item.split("=")[1]
            return actual_trans[0].rec_opcode == upi_opcode

    def is_partial_monitor_hit(self, flow):
        monitor_snapshot = monitor_array_snapshot()
        if flow.current_monitor_array is not None:
            monitor_snapshot = flow.current_monitor_array
            return monitor_snapshot.does_array_contain_partial_monitor_hit(flow.address, flow.initial_tag_way, flow.cbo_half_id)

    def is_evict_clean_throttle(self, flow: ccf_flow):
        for arb in flow.get_list_of_arbcommand_opcodes():
            if (CCF_FLOW_UTILS.is_arbcommand_in_SNP_RSP_arbcommand_list(arb)):
                return flow.is_evict_clean_throttle("SNP_RSP")
        else:
            return flow.is_evict_clean_throttle()

    def check_misc_conditions(self, item, flow, do_not_care_str=None):
        valid_user_misc_conditions = ["TorOccupAboveTH", "TorOccupBelowTH", "NcRetry", "NcCmpU", "prefetch_upi_rd",
                                      "prefetch_elimination", "had_promotion", "is_nc_partial_write", "is_lt_doorbell",
                                      "had_cv_err", "is_0x3", "ParitalMonitorHit", "EvctClnThrottle"]
        bool_l = []
        item_list =item.split(",")
        for m_item in item_list:
            item = m_item.strip()
            if item.lower() == do_not_care_str:
                bool_l.append(True)
            elif (item == "TorOccupAboveTH" and flow.TorOccupAboveTH) or (item == "TorOccupBelowTH" and not flow.TorOccupAboveTH):
                bool_l.append(True)
            elif (item == "NcRetry" and flow.cbo_got_upi_NCretry()) or (item == "NcCmpU" and flow.cbo_got_upi_NCmpu()):
                bool_l.append(True)
            elif ((item == "Flusher" and flow.is_flusher_origin()) or (item == "!Flusher" and not flow.is_flusher_origin())):
                bool_l.append(True)
            elif ((item == "Flusher" and not flow.is_flusher_origin()) or (item == "!Flusher" and flow.is_flusher_origin())):
                bool_l.append(False)
            elif ((item == "Addr[11:6]==0" and flow.is_spcyc_addr_zero()) or (item == "Addr[11:6]!=0" and not flow.is_spcyc_addr_zero())):
                bool_l.append(True)
            elif ((item == "Addr[11:6]==0" and not flow.is_spcyc_addr_zero()) or (item == "Addr[11:6]!=0" and flow.is_spcyc_addr_zero())):
                bool_l.append(False)
            elif ("prefetch_upi_rd" in item) and (self.prefetch_upi_rd_misc_condition(flow, item)):
                bool_l.append(True)
            elif (item == "prefetch_elimination=0" and not flow.is_prefetch_elimination_flow()) or (item == "prefetch_elimination=1" and flow.is_prefetch_elimination_flow()):
                bool_l.append(True)
            elif (item == "had_promotion=1" and flow.is_flow_promoted()) or (item == "had_promotion=0" and not flow.is_flow_promoted()):
                bool_l.append(True)
            elif (item == "is_nc_partial_write=1" and flow.is_nc_partial_write_flow()) or (item == "is_nc_partial_write=0" and not flow.is_nc_partial_write_flow()):
                bool_l.append(True)
            elif (item == "is_lt_doorbell=1" and flow.is_lt_doorbell()) or (item == "is_lt_doorbell=0" and not flow.is_lt_doorbell()):
                bool_l.append(True)
            elif (item == "is_0x3=1" and flow.is_0x3()) or (item == "is_0x3=0" and not flow.is_0x3()):
                bool_l.append(True)
            elif (item == "had_cv_err=1" and flow.has_cv_err()) or (item == "had_cv_err=0" and not flow.has_cv_err()):
                bool_l.append(True)
            elif ((item == "ParitalMonitorHit=1") and self.is_partial_monitor_hit(flow)) or ((item == "ParitalMonitorHit=0") and not self.is_partial_monitor_hit(flow)):
                bool_l.append(True)
            elif ((item == "EvctClnThrottle=1") and self.is_evict_clean_throttle(flow)) or ((item == "EvctClnThrottle=0") and not self.is_evict_clean_throttle(flow)):
                bool_l.append(True)
            elif any([True for valid_item in valid_user_misc_conditions if valid_item in item]):
                bool_l.append(False)
            else:
                bool_l.append(False)
                err_msg = "User use misc condition: {} Default answer is None but we shouldn't got to default answer in this function. check it.".format(item)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
        return all(bool_l)

    def create_misc_condition(self, df, column_name, flow, do_not_care_str=None):
        condition_f = lambda item: self.check_misc_conditions(item, flow, do_not_care_str)
        return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def create_condition_using_true_false_indication(self, df, column_name, is_true, do_not_care_str=None):
        if is_true:
            expected_value = "1"
        else:
            expected_value = "0"
        return self.create_df_simple_condition(df, column_name, expected_value, do_not_care_str)

    def create_clean_evict_condition(self, df, column_name, flow, do_not_care_str=None):
        if flow.is_victim():
            exp_clean_evict = flow.get_clean_evict_for_victim(self.ccf_flows[flow.uri['TID']])
        else:
            exp_clean_evict = flow.get_clean_evict_value()

        return self.create_df_simple_condition(df, column_name, exp_clean_evict, do_not_care_str)


    def return_list_of_monitor_hit_sample_point(self, df, flow):
        mon_hit_l = []
        for index, row in df.iterrows():
            #if we got Snp_Rsp and we need Monitor Hit indication we want to take the MonHit indication from the pipe pass of SNP RSP.
            #We have two kind of row in our Tables:
            #1. if we will choose the row we will be in SNP_RSP pipe stage (and that mean the indication should be taken after the snoop response arrive to Cpipe)
            #2. We are using fake row (for validation use to make life easy) and we are still on the same SNP_RSP stage
            if not flow.is_drd() and (((row['CPIPE_REQ'] == "SNP_RSP") and flow.snoop_sent()) or \
                    ((row['CPIPE_REQ'].lower() == "x") and ("SNP_RSP" in row['Curr Opcode']) and CCF_FLOW_UTILS.is_arbcommand_in_SNP_RSP_arbcommand_list(self.current_arbcommand))):
                mon_hit_l.append(flow.get_monitor_hit_value("SNP_RSP"))
            else:
                if flow.had_conflict:
                    # When we have conflict flow we should do second LookUp and that LookUp happen at FwdCnfltO pipe state
                    mon_hit_l.append(flow.get_monitor_hit_value("FakeCycle"))
                else:
                    mon_hit_l.append(flow.get_monitor_hit_value())
        return mon_hit_l

    def create_monitor_hit_condition(self, df, column_name, flow, do_not_care_str=None):
        return_list = []
        list_index = 0
        mon_hit_l = self.return_list_of_monitor_hit_sample_point(df, flow)
        for index, row in df.iterrows():
            if(row[column_name].lower() == 'x'):
                return_list.append(True)
            elif (row[column_name] == mon_hit_l[list_index]):
                return_list.append(True)
            else:
                return_list.append(False)
            list_index = list_index + 1
        return return_list

    def create_had_reject_condition(self, df, column_name, flow, do_not_care_str=None):
        if flow.is_victim():
            if any([True for reject in flow.rejected_reasons if reject.rejected_at_victim_first_pipe_pass()]):
                had_reject = "1"
            else:
                had_reject = "0"
        else:
            if flow.number_of_rejects > 0:
                had_reject = "1"
            elif flow.number_of_rejects == 0:
                had_reject = "0"
            else:
                had_reject = None
                err_msg = "Val_Assert (create_had_reject_condition): Default Answer is had_reject=None but we shouldn't got to default answer in this function. check it."
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

        return self.create_df_simple_condition(df, column_name, had_reject, do_not_care_str)

    def create_df_simple_condition(self, df, column_name, expected_value, do_not_care_str=None):
        if do_not_care_str is None:
            condition_f = lambda item: (item.lower() == expected_value.lower().strip())
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

        if expected_value is None:
            condition_f = lambda item: (item.lower() == do_not_care_str)
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

        if df[column_name].str.contains('!', regex=False).any():
            condition_f = lambda item: ("!" in item and expected_value.lower().strip() != item.lower().strip("!")) or \
                                        (expected_value.lower().strip() == item.lower().strip()) or \
                                        (item.lower().strip() == do_not_care_str.lower().strip())
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f,do_not_care_str).copy()

        else:
            condition_f = lambda item: ((item.lower() == do_not_care_str) | (item.lower() == expected_value.lower().strip()))
            return self.condition_test_all_column_rows_and_return_results_list(df, column_name, condition_f, do_not_care_str).copy()

    def get_current_flow_table_row(self, flow, flow_table_df, current_bubble_name):
        bubble_condition_list = self.create_df_simple_condition(flow_table_df, "Bubble", current_bubble_name.lower().strip())
        df_indexs = flow_table_df["Bubble"].index.tolist()
        bubble_condition = pd.Series(bubble_condition_list, index=df_indexs)

        bubble_row_df = flow_table_df.loc[bubble_condition]

        condiction_dict = dict()
        condiction_dict["flow_condition"] = self.create_split_and_filter_condition(bubble_row_df, "Flow", flow.opcode, False, "x")
        condiction_dict["sad_condition"] = self.create_split_and_filter_condition(bubble_row_df, "Sad", flow.sad_results, False, "x")
        condiction_dict["arbcommand_condition"] = self.create_arbcommand_condition(bubble_row_df, "Curr Opcode", self.current_arbcommand, "x")
        condiction_dict["snoop_response_condition"] = self.create_snoop_response_condition(bubble_row_df, "Snoop response", flow.final_snp_rsp, "x")
        condiction_dict["llc_state_condition"] = self.create_df_llc_state_condition(bubble_row_df, "LLC State", flow.initial_cache_state, "x")
        condiction_dict["cv_condition"] = self.create_df_cv_condition(bubble_row_df, "CV", flow, "x")
        condiction_dict["map_condition"] = self.create_map_condition(bubble_row_df, "Map", flow, "x")
        condiction_dict["monitor_hit_condition"] = self.create_monitor_hit_condition(bubble_row_df, "MonHit", flow, "x")
        condiction_dict["cn_condition"] = self.create_df_simple_condition(bubble_row_df, "CN", flow.get_effective_cache_near_value(), "x")
        condiction_dict["avail_data_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "AvailData", flow.is_available_data(), "x")
        condiction_dict["selfsnoop_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "SelfSnoop", flow.need_to_selfsnoop_req_core(), "x")
        condiction_dict["snoop_conflict_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "SnoopConflict", flow.had_conflict, "x")
        condiction_dict["fwdcnflto_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "FwdCnfltO", flow.got_fwdcnflto, "x")
        condiction_dict["freeinvway_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "FreeInvWay", flow.is_free_inv_way(), "x")
        condiction_dict["had_reject_condition"] = self.create_had_reject_condition(bubble_row_df, "HadReject", flow, "x")
        condiction_dict["clean_evict_condition"] = self.create_clean_evict_condition(bubble_row_df, "CleanEvict", flow, "x")
        condiction_dict["deaddbp_condition"] = self.create_df_simple_condition(bubble_row_df, "DeadDBP", str(flow.dead_dbp), "x")
        condiction_dict["reqcv_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "ReqCV", flow.is_selfsnoop_and_req_cv(), "x")
        condiction_dict["had_bogus_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "HadBogus", flow.core_flow_is_bogus, "x")
        condiction_dict["srp_en_condition"] = self.create_df_simple_condition(bubble_row_df, "SRP_en", flow.srp_en, "x")
        condiction_dict["srp_hr_fill_condition"] = self.create_df_simple_condition(bubble_row_df, "SRP_HR_Fill", str(flow.srp_hr_fill), "x")
        condiction_dict["pref_promotion_condition"] = self.create_condition_using_true_false_indication(bubble_row_df, "Pref_Promotion", flow.pref_used_for_promotion, "x")
        condiction_dict["misc_condition"] = self.create_misc_condition(bubble_row_df, "MiscCondition", flow, "x")

        zipped_list = list(zip(*condiction_dict.values()))

        decision_list = []
        for i in range(len(zipped_list)):
            decision_list.append(all(zipped_list[i]))

        df_indexs = bubble_row_df["Flow"].index.tolist() #take original indexes of the rows we are using in the DF
        bubble_condition = pd.Series(decision_list, index=df_indexs)
        selected_row_df = bubble_row_df.loc[bubble_condition]

        selected_row_df = selected_row_df.reset_index(drop=True)
        num_of_row_found = len(selected_row_df.index)

        if num_of_row_found == 0:
            err_msg = "{} flow (get_current_flow_table_row): We didn't found any row that fit to bubble: {} with our flow conditions".format(flow.opcode, current_bubble_name)
            VAL_UTDB_ERROR(time=self.pipe_pass_start_time, msg=err_msg)
            if self.debug_prints:
                d = {'Row Number': bubble_row_df['Row Number'].values,
                     'flow_condition': condiction_dict["flow_condition"],
                     'sad_condition': condiction_dict["sad_condition"],
                     'arbcommand_condition': condiction_dict["arbcommand_condition"],
                     'snoop_response_condition': condiction_dict["snoop_response_condition"],
                     'llc_state_condition': condiction_dict["llc_state_condition"],
                     'cv_condition': condiction_dict["cv_condition"],
                     'map_condition': condiction_dict["map_condition"],
                     'monitor_hit_condition': condiction_dict["monitor_hit_condition"],
                     'cn_condition': condiction_dict["cn_condition"],
                     'avail_data_condition': condiction_dict["avail_data_condition"],
                     'selfsnoop_condition': condiction_dict["selfsnoop_condition"],
                     'snoop_conflict_condition': condiction_dict["snoop_conflict_condition"],
                     'fwdcnflto_condition': condiction_dict["fwdcnflto_condition"],
                     'freeinvway_condition': condiction_dict["freeinvway_condition"],
                     'clean_evict_condition': condiction_dict["clean_evict_condition"],
                     'had_reject_condition': condiction_dict["had_reject_condition"],
                     'had_bogus_condition': condiction_dict["had_bogus_condition"],
                     'misc_condition': condiction_dict["misc_condition"]
                     }
                condition_df = pd.DataFrame(data=d)
                info_msg = "Our bubble options were:\n{}\nThe follow table will show the decision that was made for each cell:\n {}\n{}"\
                    .format(tabulate(bubble_row_df, headers='keys', tablefmt='psql'), tabulate(condition_df, headers='keys', tablefmt='psql'), flow.get_flow_info_str())
                VAL_UTDB_MSG(time=self.pipe_pass_start_time, msg=info_msg)

        elif num_of_row_found > 1:
            if self.check_if_df_columns_can_be_merge(flow, selected_row_df):
                if self.debug_prints:
                    info_msg = "We found more then one row that fit to our current situation but those line can be merged without contradiction."
                    VAL_UTDB_MSG(time=self.pipe_pass_start_time, msg=info_msg)
                    info_msg = "Filtered Rows for TID: {} bubble: {}\n{}\n" \
                        .format(flow.uri["TID"],
                                current_bubble_name,
                                tabulate(selected_row_df, headers='keys', tablefmt='psql'))
                    VAL_UTDB_MSG(time=self.pipe_pass_start_time, msg=info_msg)
            else:
                err_msg = "{} flow (get_current_flow_table_row): We found more then one row that fit to our current situation this should be review if this is HAS issue or verification table issue.\n".format(flow.opcode)
                err_msg += "Filtered Rows for TID: {} bubble: {}\n{}\n{}"\
                            .format(flow.uri["TID"],
                               current_bubble_name,
                               tabulate(selected_row_df, headers='keys', tablefmt='psql'), 
                               flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=self.pipe_pass_start_time, msg=err_msg)

        elif self.debug_prints:
            info_msg = "Filtered Rows for TID: {} bubble: {}\n{}\n"\
                       .format(flow.uri["TID"],
                               current_bubble_name,
                               tabulate(selected_row_df, headers='keys', tablefmt='psql'))
            VAL_UTDB_MSG(time=self.pipe_pass_start_time, msg=info_msg)

        return selected_row_df

    def get_cldemote_expected_core_for_snoop(self, flow):
        if flow.initial_cv[::-1][flow.requestor_logic_id] == '1':
            xbar_id = flow.requestor_logic_id//CCF_COH_DEFINES.num_of_ccf_clusters
            normalize_coreid = flow.requestor_logic_id%CCF_COH_DEFINES.num_of_ccf_clusters
            physical_core_id = CCF_UTILS.get_physical_id_by_logical_id(xbar_id)*CCF_COH_DEFINES.num_of_ccf_clusters+ normalize_coreid
            return ["CORE_{}".format(str(physical_core_id))]
        else:
            return []

    def get_core_valid_list_from_cv_vector(self, cv, exclude_logical_id_cores):
        logical_core_id = 0
        cv_array = []
        if cv is not None:
            for bit in cv[::-1]:
                if bit == "1" and (logical_core_id not in exclude_logical_id_cores):
                    xbar_id = logical_core_id//CCF_COH_DEFINES.num_of_ccf_clusters
                    normalize_coreid = logical_core_id%CCF_COH_DEFINES.num_of_ccf_clusters
                    physical_core_id = CCF_UTILS.get_physical_id_by_logical_id(xbar_id)*CCF_COH_DEFINES.num_of_ccf_clusters+ normalize_coreid
                    cv_array.insert(0, "CORE_" + str(physical_core_id))
                logical_core_id += 1
        return cv_array

    def get_expected_snooped_core_list(self, flow):
        exclude_logical_id_cores = []
        if not flow.need_to_selfsnoop_req_core():
            exclude_logical_id_cores.append(flow.requestor_logic_id)

        # CLDemote flow is not considering the CV and send snoop only to the requestor core
        if flow.is_cldemote():
            exp_snooped_cores = self.get_cldemote_expected_core_for_snoop(flow)
        else:
            exp_snooped_cores = self.get_core_valid_list_from_cv_vector(flow.initial_cv, exclude_logical_id_cores)

        if (flow.flow_is_hom() or exp_snooped_cores):
            if CCF_FLOW_UTILS.should_trigger_monitor(flow.opcode, flow.sad_results) and flow.current_monitor_array is not None:
                monitor_array = flow.current_monitor_array.get_monitor_vector(flow.address)
                for core in monitor_array:
                    if ("CORE_" + str(core) not in exp_snooped_cores):
                        exp_snooped_cores.insert(0, "CORE_" + str(core))
                if self.si.ccf_cov_en:
                    self.ccf_flow_chk_cov_sample_ptr.collect_mon_hit_coverage(len(monitor_array))

        return exp_snooped_cores

    def get_excepted_snoop_to_all_cores_list(self):
        exp_snoop_core_id_list = list()
        for index in range(self.si.num_of_cbo*CCF_COH_DEFINES.num_of_ccf_clusters):
            if CCF_UTILS.is_slice_enable(index):
                exp_snoop_core_id_list.append("CORE_{}".format(index))
        return exp_snoop_core_id_list

    def get_excepted_snoop_to_enabled_cores_list(self):
        exp_snoop_core_id_list = list()
        for index in range(self.si.num_of_cbo*CCF_COH_DEFINES.num_of_ccf_clusters):
            if CCF_UTILS.is_module_enable(index/CCF_COH_DEFINES.num_of_ccf_clusters):
                exp_snoop_core_id_list.append("CORE_{}".format(index))
        return exp_snoop_core_id_list

    def compare_actual_snoop_to_cv_bits(self, flow):
        if flow.should_snoop_to_all_cores():
            exp_snooped_cores = self.get_excepted_snoop_to_all_cores_list()
        elif not flow.flow_should_not_snoop_due_to_cv_shared_indication():
            exp_snooped_cores = self.get_expected_snooped_core_list(flow)
        else:
            exp_snooped_cores = []

        return self.compare_actual_snoop_to_expected(flow, exp_snooped_cores)

    def get_core_type(self, core_phy_id):
        if CCF_UTILS.is_atom_module_by_physical_id(core_phy_id):
            return "AT"
        else:
            return "IA"

    def compare_actual_snoop_to_all_cores(self, flow):
        exp_snooped_cores = self.get_excepted_snoop_to_enabled_cores_list()
        return self.compare_actual_snoop_to_expected(flow, exp_snooped_cores)

    def compare_actual_snoop_to_no_snoop(self, flow):
        exp_snooped_cores = []
        return self.compare_actual_snoop_to_expected(flow, exp_snooped_cores)

    def compare_actual_snoop_to_expected(self, flow, exp_snooped_cores):
        num_of_errors_found = 0
        should_snoop_all_cores = flow.should_snoop_to_all_cores()
        #Checking that all expected snoops happend on IDI interface
        for exp_snooped_core in exp_snooped_cores:
            if not any(exp_snooped_core in act_snooped_core for act_snooped_core in flow.snooped_cores):

                if should_snoop_all_cores:
                    err_msg = "{} Flow: should_snoop_all_cores_cb is enable, we expected to see Snoop transaction getting to Core: {} but we didn't find it.".format(flow.opcode, exp_snooped_core)
                else:
                    err_msg = "{} Flow: According to CV bits and monitor array we expected to see Snoop transaction getting to Core: {} but we didn't find it.".format(flow.opcode, exp_snooped_core)
               
                err_msg += "\n\nActual snoops:"
                for act_snp in flow.snooped_cores:
                    err_msg += "\n" + act_snp
                err_msg += "\n\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

        #Check if the amount of actual snoops is like we expected.
        if len(exp_snooped_cores) != len(flow.snooped_cores):
            if should_snoop_all_cores:
                err_msg = "{} Flow: should_snoop_all_cores_cb is enable, We expected to have - {} snoops, but the actual number of snoops is - {}".format(flow.opcode, str(len(exp_snooped_cores)), str(len(flow.snooped_cores)))
            else:
                err_msg = "{} Flow: We expected to have - {} snoops, but the actual number of snoops is - {}".format(flow.opcode, str(len(exp_snooped_cores)), str(len(flow.snooped_cores)))
            err_msg += "\n\nExpected snoops:"
            for exp_snp in exp_snooped_cores:
                err_msg += "\n" + exp_snp
            err_msg += "\n\nActual snoops:"
            for act_snp in flow.snooped_cores:
                err_msg += "\n" + act_snp
            err_msg += "\n\n" + flow.get_flow_info_str()

            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            num_of_errors_found += 1

        return num_of_errors_found

    def check_that_each_snoop_got_snoop_response(self, flow):
        num_of_errors_found = 0

        if len(flow.snoop_requests) != len(flow.snoop_responses):
            err_msg = "{} Flow: We expected to have- {} snoop responses, but the actual number of snoops is - {}".format(flow.opcode, str(len(flow.snoop_requests)), str(len(flow.snoop_responses)))
            err_msg += "\n\n" + flow.get_flow_info_str()

            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            num_of_errors_found += 1

        for snoop_req in flow.snoop_requests:
            if not any([True for snoop_rsp in flow.snoop_responses if snoop_req.get_req_core() == snoop_rsp.get_rsp_core()]):
                err_msg = "{} Flow: We didn't found any response for snoop_req core number- {}".format(flow.opcode, str(snoop_req.get_req_core()))
                err_msg += "\n\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

        return num_of_errors_found

    def print_out_of_interval_error_msg(self, trans_opcode, trans_timestemp, tid, trans_type):
        err_msg = "{} Flow: TID - {} transaction type - {} timestemp - {} is not inside the current Cpipe pass, " \
                  "it should have been inside the Cpipe pass time interval, Start - {} End- {}"\
            .format(trans_opcode, tid, trans_type, str(trans_timestemp), str(self.pipe_pass_start_time), str(self.pipe_pass_end_time))
        VAL_UTDB_ERROR(time=trans_timestemp, msg=err_msg)

    def check_that_snoop_trans_are_in_cpipe_pass_time_interval(self, snoop_list):
        num_of_errors_found = 0
        if not self.disable_interval_checker:
            for snp in snoop_list:
                if self.is_trans_not_in_cpipe_pass_time_interval(snp.time_on_idi_if):
                    num_of_errors_found += 1
                    self.print_out_of_interval_error_msg(snp.opcode, snp.time_on_idi_if)

        return num_of_errors_found

    def is_trans_not_in_cpipe_pass_time_interval(self, trans_timestemp):
        return ((self.pipe_pass_end_time is not None) and (trans_timestemp > self.pipe_pass_end_time)) or (trans_timestemp < self.pipe_pass_start_time)

    def handle_core_logic_id_op(self, flow, actual_trans):
        num_of_errors = 0
        for trans in actual_trans:
            if trans.rec_logic_id != flow.requestor_logic_id:
                num_of_errors += 1
                err_msg = "{} Flow: The Requestor logic ID is- {} But the actual transaction sent to core- {}\n{}"\
                    .format(flow.opcode, str(flow.requestor_logic_id), str(trans.rec_logic_id), trans.print_idi_info())
                VAL_UTDB_ERROR(time=trans.rec_time, msg=err_msg)
        return num_of_errors

    def is_next_pipe_arbcommand_fit_to_flow(self, pipe_arbcommands_flow, current_arbcommand, next_exp_arbcommand_list):
        current_arbcommand_index = 0
        actual_next_arbcommand = None
        actual_next_arbcommand_time = []

        lower_case_pipe_arbcommand_list = [arbcommand.arbcommand_opcode.lower() for arbcommand in pipe_arbcommands_flow]

        if "SNP_RSP" in current_arbcommand:
            for snp_rsp in CCF_FLOW_UTILS.SNP_RSP_arbcommand:
                if snp_rsp.lower().strip() in lower_case_pipe_arbcommand_list:
                    current_arbcommand_index = lower_case_pipe_arbcommand_list.index(snp_rsp.lower().strip())
        else:
            current_arbcommand_index = lower_case_pipe_arbcommand_list.index(current_arbcommand.lower().strip())

        if (current_arbcommand_index + 1) < len(lower_case_pipe_arbcommand_list):
            actual_next_arbcommand = lower_case_pipe_arbcommand_list[current_arbcommand_index + 1]
            actual_next_arbcommand_time.append(pipe_arbcommands_flow[current_arbcommand_index + 1].arbcommand_time) #next arbcommand start time.
            if (current_arbcommand_index + 2) < len(lower_case_pipe_arbcommand_list):
                actual_next_arbcommand_time.append(pipe_arbcommands_flow[current_arbcommand_index + 2].arbcommand_time) #next arbcommand end time.
            else:
                actual_next_arbcommand_time.append(None)
        else:
            msg = ""
            for arbcmd in pipe_arbcommands_flow:
                msg += arbcmd.arbcommand_opcode + ", "
            return False, actual_next_arbcommand, actual_next_arbcommand_time

        #if "SNP_RSP" in next_arbcommand:
        if any([True for next_exp_command in next_exp_arbcommand_list if "SNP_RSP" in next_exp_command]):
            return any([True for snp_rsp in CCF_FLOW_UTILS.SNP_RSP_arbcommand if
                        snp_rsp.lower().strip() == actual_next_arbcommand.lower().strip()]), actual_next_arbcommand, actual_next_arbcommand_time
        else:
            next_arbcommand_status = any([True for next_exp_commd in next_exp_arbcommand_list if actual_next_arbcommand.lower().strip() == next_exp_commd.lower().strip()])
            return next_arbcommand_status, actual_next_arbcommand, actual_next_arbcommand_time

    def idi_interface_no_transaction_recorded_exceptions(self, actual_trans):
        for trans in actual_trans:
            #GO can get to the IDI interface long after the cpipe will go to the next arbcommand
            #The conclusion was that we shouldn't check it.
            if trans.rec_opcode == "IDI_GO":
                actual_trans.remove(trans)
            #LLCMiss can get to the IDI very quickly.
            elif trans.rec_opcode == "LLCMiss":
                actual_trans.remove(trans)
        return actual_trans

    def check_no_transaction_recored_on_interface(self, flow, direction_str, channel_str, record_info_type):
        num_of_errors_found = 0
        actual_trans = flow.get_flow_progress(record_type=record_info_type,
                                              direction=direction_str,
                                              channel=channel_str,
                                              start_time=self.pipe_pass_start_time,
                                              end_time=self.pipe_pass_end_time)

        if record_info_type is ccf_idi_record_info:
            actual_trans = self.idi_interface_no_transaction_recorded_exceptions(actual_trans)


        if (len(actual_trans) is not 0) and (flow.flow_is_hom() or not self.is_nc_flow_that_should_use_sideband_access(flow)):
                    err_msg = "{} Flow: According to Flow table we didn't expect to see transaction on channel-" \
                              " {} direction- {} in this pipe pass.\n{}".format(flow.opcode, channel_str, direction_str, flow.get_flow_info_str())
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                    num_of_errors_found += 1

        return num_of_errors_found

    def check_spcyc_ncmsgs_special_fields(self, flow, msg_type, actual_trans: ccf_cfi_record_info):
        if msg_type != "shutdown":
            err_msg = "(check_spcyc_ncmsgs_special_fields): We didn't expect to see the follow message type with spcyc opcode: {}".format(msg_type)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def check_lock_or_unlock_ncmsgs_special_fields_flow(self, flow, msg_type, actual_trans: ccf_cfi_record_info):
        local_paramA = 0
        local_msg_type_enc = 0

        if msg_type == "proclock":
            local_paramA = 0
            local_msg_type_enc = 4
        elif msg_type == "procsplitlock":
            #we are checking only the lock/splitlock/unlock opcodes and not stopreq and etc since they are not part of
            # the response table flow the full flow will be checked by NCU agent.
            local_paramA = 0
            local_msg_type_enc = 5
        elif msg_type == "unlock":
            local_paramA = 0
            local_msg_type_enc = 3
        else:
            err_msg = "Val_Assert (check_lock_or_unlock_ncmsgs_special_fields_flow): Unvalid message type: {}".format(msg_type)
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

        for trans in actual_trans:
            if int(trans.paramA) != local_paramA or trans.get_msg_type_num() != local_msg_type_enc:
                err_msg = "{} Flow: Unexpected message parameters:\nActual ParamA: {}, msg_type_enc: {}\n" \
                          "Expected ParamA: {}, msg_type_enc: {}".format(flow.opcode, trans.paramA, trans.msg_type, local_paramA,
                                                                         local_msg_type_enc)
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def end_of_pipe_pass_checks(self, flow):
        num_of_errors_found = 0

        if not self.expected_activity_in_cpipe_pass.idi_u2c_req:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "U2C", "REQ", ccf_idi_record_info)

        if not self.expected_activity_in_cpipe_pass.idi_u2c_rsp:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "U2C", "RSP", ccf_idi_record_info)

        #When we have direct2core indication the data can come to IDI U2C interface at a diffrent cpipe pass
        if not self.expected_activity_in_cpipe_pass.idi_u2c_data and not self.expected_activity_in_cpipe_pass.direct2core_indication:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "U2C", "DATA", ccf_idi_record_info)

        if not self.expected_activity_in_cpipe_pass.idi_c2u_data:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "C2U", "DATA", ccf_idi_record_info)

        if not self.expected_activity_in_cpipe_pass.idi_c2u_rsp:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "C2U", "RSP", ccf_idi_record_info)

        if not self.expected_activity_in_cpipe_pass.uxi_u2c_req:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "S2C", "REQ", ccf_ufi_record_info)

        if not self.expected_activity_in_cpipe_pass.uxi_u2c_rsp:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "S2C", "RSP", ccf_ufi_record_info)

        if not self.expected_activity_in_cpipe_pass.uxi_u2c_data and not self.expected_activity_in_cpipe_pass.direct2core_indication:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "S2C", "DATA", ccf_ufi_record_info)

        if not self.expected_activity_in_cpipe_pass.uxi_c2u_req:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "C2S", "REQ", ccf_ufi_record_info)

        if not self.expected_activity_in_cpipe_pass.uxi_c2u_data:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "C2S", "DATA", ccf_ufi_record_info)

        if not self.expected_activity_in_cpipe_pass.uxi_c2u_rsp:
            num_of_errors_found += self.check_no_transaction_recored_on_interface(flow, "C2S", "RSP", ccf_ufi_record_info)

        #TODO: need to add the support to check that we are not having CFI messages that we didn't intended

        return num_of_errors_found

    def is_cpipe_req_as_expected(self, flow : ccf_flow, cpipe_req, next_bubble):
        num_of_errors_found = 0

        if self.is_dont_care(cpipe_req):
            #meirlevy to enable without it it's not checking the last pipe stage
             if next_bubble in ["Done", "done"]:
                 #None indicate infinite time
                 self.pipe_pass_end_time = None #self.ccf_coherency_qry.get_tor_dealloc_time(tid_uri=flow.uri['TID'])
                 num_of_errors_found += self.end_of_pipe_pass_checks(flow)
             else:
                return True
        else:
            #Check if according to the csv flow table we supposed to continue to the next arbcommand.
            if self.current_arbcommand.lower().strip() is not cpipe_req.lower().strip():

                cpipe_req_list = cpipe_req.split("/")
                status, actual_next_arbcommand, actual_next_arbcommand_time = self.is_next_pipe_arbcommand_fit_to_flow(flow.pipe_passes_information, self.current_arbcommand, cpipe_req_list)
                if not status and actual_next_arbcommand is not None and "victim" in actual_next_arbcommand:
                    status, actual_next_arbcommand, actual_next_arbcommand_time = self.is_next_pipe_arbcommand_fit_to_flow(flow.pipe_passes_information, actual_next_arbcommand, cpipe_req_list)
                   
                num_of_errors_found += self.end_of_pipe_pass_checks(flow)

                if not status:
                    num_of_errors_found += 1
                    err_msg = "{} Flow: The actual next arbcommand is- {} but the expected next arbcommand was- {}.\n{}"\
                        .format(flow.opcode, str(actual_next_arbcommand), cpipe_req, flow.get_flow_info_str())
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

                #If all goes as planed we can continue to the next arbcommand
                if status:
                    self.current_arbcommand = actual_next_arbcommand
                    self.previous_pipe_pass_start_time = self.pipe_pass_start_time
                    self.pipe_pass_start_time = actual_next_arbcommand_time[0] - 1500# TODO: need to use clk and number of cycles
                    self.pipe_pass_end_time = actual_next_arbcommand_time[1]

                    # TODO: need to substruct the number of clks from the start of the next pipe pass till the moment we wrote it in the tracker (for U2C to IDI)
                    if self.pipe_pass_end_time is not None:
                        self.pipe_pass_end_time = self.pipe_pass_end_time  - 1500 #TODO: need to use clk and number of cycles

                    self.reset_expected_activity_in_cpipe_pass() #since cpipe pass ended.

        return num_of_errors_found == 0

    def run_transition_check(self, flow: ccf_flow, actual_trans: list, external_condition=True, parent_name="NA"):
        if actual_trans:
            if self.si.ccf_transition_chk_en and external_condition:
                self.transition_chk.transition_check(flow, actual_trans)
        else:
            err_msg = "Val_Assert ({}): We skiped transition checker since we didn't find any actual transaction. TID-{}".format(parent_name, flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)



    def got_idi_u2c_req_as_expected(self, flow, idi_u2c_req):
        num_of_errors_found = 0
        interrupt_with_u2c_req = True
        if flow.is_ipi_interrupt() or flow.is_portout():
            fastipi = self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp)
            interrupt_with_u2c_req = flow.is_ipi_interrupt() and (fastipi == 1) or (self.si.ccf_soc_mode and flow.snoop_requests)
            lt_write_req = flow.is_portout() and flow.is_lt_doorbell() and self.si.ccf_soc_mode and flow.snoop_requests
        if self.is_expected_if_valid(idi_u2c_req) and (interrupt_with_u2c_req or lt_write_req):
            opcode, check_op = self.get_opcode_and_operation(idi_u2c_req)
            self.expected_activity_in_cpipe_pass.idi_u2c_req = True

            if opcode.lower().strip() == "snoop":
                #check what is the last transaction time
                num_of_errors_found += self.check_that_snoop_trans_are_in_cpipe_pass_time_interval(flow.snoop_requests)

                actual_trans = flow.get_flow_progress(record_type=ccf_idi_record_info, direction="U2C", channel="REQ")

                if len(actual_trans) == 0:
                    num_of_errors_found += 1
                    err_msg = "According to flow Table we expect to have snoop in this flow but we didn't found any snoop transaction"
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

                if check_op == "cv_vector":
                    num_of_errors_found += self.compare_actual_snoop_to_cv_bits(flow)
                if check_op == "all_cores":
                    num_of_errors_found += self.compare_actual_snoop_to_all_cores(flow)

            else:
                err_msg = "Val_Assert (got_idi_u2c_req_as_expected): The Opcode in the CSV table is unknown Opcode " \
                          "please fix the table or add support for the new Opcode, input Opcode: {}.\n{}"\
                          .format(opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=(num_of_errors_found == 0),
                                      parent_name="got_idi_u2c_req_as_expected")

        return num_of_errors_found == 0

    def got_idi_u2c_rsp_as_expected(self, flow, idi_u2c_rsp):
        num_of_errors_found = 0

        if self.is_expected_if_valid(idi_u2c_rsp):
            self.expected_activity_in_cpipe_pass.idi_u2c_rsp = True
            opcode, check_op = self.get_opcode_and_operation(idi_u2c_rsp)
            if not CCF_FLOW_UTILS.is_u2c_rsp_supported(flow.opcode, opcode):
                err_msg = "{} Flow: we got u2c rsp that not supported according to idi has. u2c_rsp- {}.\n{}".format(flow.opcode, opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

            actual_trans = list()

            #We are not going to check the type of the GO - this will be done by GO checker.
            if ("go" in opcode) or ("extcmp" in opcode) or ("writepull" in opcode) or ("llcmiss" in opcode):

                #in the tables we are writing GO but in the log it's written as IDI_GO
                if opcode in ["go", "go_nogo"]:
                    opcode = "IDI_GO"
                if "fastgo" == opcode:
                    opcode = "FAST_GO"

                # Global handling for GO and ExtCmp
                actual_trans = flow.get_flow_progress(record_type=ccf_idi_record_info,
                                                      direction="U2C",
                                                      channel="RSP",
                                                      opcode=opcode,
                                                      start_time=self.pipe_pass_start_time)

                if (len(actual_trans) == 1):
                    if check_op.lower() == "core_logic_id":
                       num_of_errors_found += self.handle_core_logic_id_op(flow, actual_trans)
                    elif check_op is not None:
                        err_msg = "We got unexpected operation: {}".format(check_op)
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                else:
                   err_msg = "{} Flow: We expected one actual transaction with opcode- {} but we found- {}.\n{}".format(flow.opcode, opcode, str(len(actual_trans)), flow.get_flow_info_str())
                   VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                   num_of_errors_found+= 1

            else:
                err_msg = "Val_Assert (got_idi_u2c_rsp_as_expected): The Opcode in the CSV table is unknown Opcode " \
                          "please fix the table or add support for the new Opcode, input Opcode- {}.\n{}".format(opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=(num_of_errors_found == 0),
                                      parent_name="got_idi_u2c_rsp_as_expected")

        return num_of_errors_found == 0


    def got_idi_u2c_data_as_expected(self, flow, idi_u2c_data):
        num_of_errors_found = 0
        if self.is_expected_if_valid(idi_u2c_data):
            self.expected_activity_in_cpipe_pass.idi_u2c_data = True

            opcode, check_op = self.get_opcode_and_operation(idi_u2c_data)

            actual_trans = flow.get_flow_progress(record_type=ccf_idi_record_info, direction="U2C", channel="DATA")

            if (len(actual_trans) == CCF_COH_DEFINES.num_of_data_chunk): #We are expecting 2 DATA chunks.
                if "core_logic_id" in check_op.lower():
                     num_of_errors_found += self.handle_core_logic_id_op(flow, actual_trans)
            else:
                err_msg = "{} Flow: The flow table expect: {} transactions with the type- U2C_DATA but we found- {}.\n{}"\
                    .format(flow.opcode, str(CCF_COH_DEFINES.num_of_data_chunk), str(len(actual_trans)), flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=(num_of_errors_found == 0),
                                      parent_name="got_idi_u2c_data_as_expected")

        return num_of_errors_found == 0

    def got_idi_c2u_rsp_as_expected(self, flow, idi_c2u_rsp):
        num_of_errors_found = 0
        interrupt_with_u2c_req = True
        if flow.is_ipi_interrupt() or flow.is_portout():
            fastipi = self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp)
            interrupt_with_u2c_req = flow.is_ipi_interrupt() and (fastipi == 1) or (self.si.ccf_soc_mode and flow.snoop_requests)
            lt_write_req = flow.is_portout() and flow.is_lt_doorbell() and self.si.ccf_soc_mode and flow.snoop_requests
        if self.is_expected_if_valid(idi_c2u_rsp) and (interrupt_with_u2c_req or lt_write_req):
            self.expected_activity_in_cpipe_pass.idi_c2u_rsp = True
            opcode, check_op = self.get_opcode_and_operation(idi_c2u_rsp)

            if opcode.lower().strip() == "snoop_response":

                if check_op.lower() == "cv_vector":
                    num_of_errors_found += self.check_that_each_snoop_got_snoop_response(flow)
                if check_op.lower() == "all_cores":
                    num_of_errors_found += self.check_that_each_snoop_got_snoop_response(flow)
                #Get last snoop transaction time
                num_of_errors_found += self.check_that_snoop_trans_are_in_cpipe_pass_time_interval(flow.snoop_responses)
            else:
                err_msg = "Val_Assert (got_idi_c2u_rsp_as_expected): The Opcode in the CSV table is unknown Opcode please fix the table or add support for the new Opcode, input Opcode: "+ opcode + ".\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

            actual_trans = flow.get_flow_progress(record_type=ccf_idi_record_info, direction="C2U", channel="RSP")

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=(num_of_errors_found == 0),
                                      parent_name="got_idi_c2u_rsp_as_expected")

        return num_of_errors_found == 0

    def got_idi_c2u_data_as_expected(self, flow, idi_c2u_data):
        num_of_errors_found = 0
        num_of_errors_found = 0

        if self.is_expected_if_valid(idi_c2u_data):
            opcode, check_op = self.get_opcode_and_operation(idi_c2u_data)

            if opcode == "snoop_response_data":
                for snoop_response in flow.snoop_responses:
                    if flow.snoop_rsp_opcode_with_data(snoop_response.snoop_rsp_opcode) or \
                            (flow.snoop_rsp_opcode_with_data(snoop_response.original_snoop_rsp_opcode) and not flow.flow_is_hom()):

                        actual_trans = flow.get_flow_progress(record_type=ccf_idi_record_info,
                                                              direction="C2U",
                                                              channel="DATA",
                                                              start_time=self.pipe_pass_start_time,
                                                              end_time=self.pipe_pass_end_time)

                        #Only if we have at list one snoop that need to give us data we will expect this kind of traffic on IDI
                        self.expected_activity_in_cpipe_pass.idi_c2u_data = True
                        if snoop_response.num_of_data_with_snoop_rsp != CCF_COH_DEFINES.num_of_data_chunk:
                            err_msg = "{} Flow: We got Snoop response that should have return {} Data chunks but we found- {} Data chunks.\n {}"\
                                .format(flow.opcode, str(CCF_COH_DEFINES.num_of_data_chunk), str(snoop_response.num_of_data_with_snoop_rsp), flow.get_flow_info_str())
                            VAL_UTDB_ERROR(time=snoop_response.time_on_idi_if, msg=err_msg)

                        self.run_transition_check(flow=flow,
                                                  actual_trans=actual_trans,
                                                  external_condition=(num_of_errors_found == 0),
                                                  parent_name="got_idi_c2u_data_as_expected")

            elif opcode in ["data", "bogus_data"]:
                actual_trans = flow.get_flow_progress(record_type=ccf_idi_record_info,
                                                      direction="C2U",
                                                      channel="DATA",
                                                      start_time=self.pipe_pass_start_time,
                                                      end_time=self.pipe_pass_end_time)
                self.expected_activity_in_cpipe_pass.idi_c2u_data = True
                actual_trans = CCF_FLOW_UTILS.get_only_data_for_write(actual_trans)
                if (len(actual_trans) == CCF_COH_DEFINES.num_of_data_chunk): #We are expecting 2 DATA chunks.
                    if check_op.lower() == "core_logic_id":
                         num_of_errors_found += self.handle_core_logic_id_op(flow, actual_trans)
                else:
                    err_msg = "{} Flow: The flow table expect- {} transactions with the type- C2U_DATA but we found- {}.\n{}"\
                        .format(flow.opcode, str(CCF_COH_DEFINES.num_of_data_chunk), str(len(actual_trans)), flow.get_flow_info_str())
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                    num_of_errors_found += 1

                if opcode == "bogus_data":
                    if any([True for data_pkt in actual_trans if data_pkt.rec_bogus == '0']):
                        err_msg = "{} Flow, TID- {} - IDI C2U data supposed to be Bogus data but the data transaction wasn't flagged as bogus data.".format(flow.opcode, flow.uri['TID'])
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                        num_of_errors_found += 1

                self.run_transition_check(flow=flow,
                                          actual_trans=actual_trans,
                                          external_condition=(num_of_errors_found == 0),
                                          parent_name="got_idi_c2u_data_as_expected")
            else:
                err_msg = "Val_Assert (got_idi_c2u_data_as_expected): IDI C2U DATA Opcode in the CSV table is unknown Opcode " \
                          "please fix the table or add support for the new Opcode, input Opcode- {}.\n{}".format(opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                num_of_errors_found += 1

        return num_of_errors_found == 0

    def got_uxi_u2c_req_as_expected(self, flow, uxi_u2c_req):
        num_of_errors_found = 0

        if self.is_expected_if_valid(uxi_u2c_req) and not self.is_nc_flow_that_should_use_sideband_access(flow):
            self.expected_activity_in_cpipe_pass.uxi_u2c_req = True
            opcode, check_op = self.get_opcode_and_operation(uxi_u2c_req)

            actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info,
                                                  direction="S2C",
                                                  channel="REQ",
                                                  start_time=flow.initial_time_stamp,
                                                  end_time=self.pipe_pass_end_time)

            if len(actual_trans) == 0:
                num_of_errors_found += 1
                err_msg = "{} Flow: We didn't found any UXI U2C REQ (opcode: {}) in the flow\n\nFlow:\n{}".format(flow.opcode, opcode,flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif len(actual_trans) > 1:
                num_of_errors_found += 1
                err_msg = "{} Flow: We are expecting to see only one UXI U2C REQ (opcode: {}) in a flow\n\nFlow:\n{}".format(flow.opcode, opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif flow.original_opcode is not None: #CBs did some opcodechange here
                if (flow.original_opcode.lower().strip() != actual_trans[0].get_rec_opcode_str().lower().strip()):
                    err_msg = "Original opcode{}, New opcode-{} Flow: " \
                              "We expected to see UXI U2C {} but we couldn't find any of them\n\nFlow:\n{}"\
                              .format(flow.original_opcode, flow.opcode, flow.original_opcode, flow.get_flow_info_str())
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif "/" in opcode:
                u2c_req_optional_opcode_list = opcode.split("/")
                if not any(True for opcode in u2c_req_optional_opcode_list if opcode.lower().strip() == actual_trans[0].get_rec_opcode_str().lower().strip()):
                    num_of_errors_found += 1
                    err_msg = "{} Flow: We expected to see UXI U2C {} but we couldn't find any of them\n\nFlow:\n{}".format(flow.opcode, opcode, flow.get_flow_info_str())
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif opcode.lower().strip() != actual_trans[0].get_rec_opcode_str().lower().strip():
                num_of_errors_found += 1
                err_msg = "{} Flow: We expected to see UXI U2C {} but we couldn't find it\n\nFlow:\n{}".format(flow.opcode, opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=((num_of_errors_found == 0) and flow.is_coherent_flow()),
                                      parent_name="got_uxi_u2c_req_as_expected")

        return num_of_errors_found == 0

    def got_uxi_u2c_rsp_as_expected(self, flow, uxi_u2c_rsp):
        num_of_errors_found = 0
        expected_num_of_rsp = 1

        fast_ipi_dont_expect_upi_trans = flow.is_ipi_interrupt() and (self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp) == 1)
        if self.is_expected_if_valid(uxi_u2c_rsp) and not fast_ipi_dont_expect_upi_trans and not self.is_nc_flow_that_should_use_sideband_access(flow):
            self.expected_activity_in_cpipe_pass.uxi_u2c_rsp = True
            opcode, check_op = self.get_opcode_and_operation(uxi_u2c_rsp)

            actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info,
                                                  direction="S2C",
                                                  channel="RSP",
                                                  start_time=self.pipe_pass_start_time,
                                                  end_time=self.pipe_pass_end_time)

            if flow.is_nc_partial_write_flow():
                expected_num_of_rsp = flow.get_num_of_data_chunk_exp_on_upi_nc() / 2 #each 2 data chunks will get on RSP

            if len(actual_trans) == 0:
                num_of_errors_found += 1
                err_msg = "{} Flow: We didn't found any UXI U2C RSP in the flow\n\nFlow:\n{}".format(flow.opcode, flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif len(actual_trans) != expected_num_of_rsp:
                num_of_errors_found += 1
                err_msg = "{} Flow: We are expecting to see {} UXI U2C RSP in the flow but we found {} \n\nFlow:\n{}".format(flow.opcode, expected_num_of_rsp, len(actual_trans), flow.get_flow_info_str())
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif ("cmpu" in opcode) or ("cmpo" in opcode) or ("fwdcnflto" in opcode) or (flow.is_non_coherent_flow() and opcode in ["ncretry"]):
                if "/" in opcode:
                    u2c_rsp_optional_opcode_list = opcode.split("/")
                    if not any(True for opcode in u2c_rsp_optional_opcode_list if opcode.lower().strip() == actual_trans[0].get_rec_opcode_str().lower().strip()):
                        num_of_errors_found += 1
                        err_msg = "{} Flow: We expected to see UXI U2C {} but we couldn't find any of them\n\nFlow:\n{}".format(flow.opcode, opcode, flow.get_flow_info_str())
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
                elif opcode.lower().strip() != actual_trans[0].get_rec_opcode_str().lower().strip():
                    num_of_errors_found += 1
                    err_msg = "{} Flow: We expected to see UXI U2C RSP {} but we couldn't find it\n\nFlow:\n{}".format(flow.opcode, opcode, flow.get_flow_info_str())
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=((num_of_errors_found == 0) and flow.is_coherent_flow()),
                                      parent_name="got_uxi_u2c_rsp_as_expected")


        return num_of_errors_found == 0

    def got_uxi_u2c_data_as_expected(self, flow, uxi_u2c_data):
        num_of_errors_found = 0

        if self.is_expected_if_valid(uxi_u2c_data) and not self.is_nc_flow_that_should_use_sideband_access(flow):
            opcode, check_op = self.get_opcode_and_operation(uxi_u2c_data)

            self.expected_activity_in_cpipe_pass.uxi_u2c_data = True

            if check_op == "direct2core":
                # in case of direct2core we can see the data on the IDI from this Cpipe pass till end of the simulation.
                self.expected_activity_in_cpipe_pass.idi_u2c_data = True
                self.expected_activity_in_cpipe_pass.direct2core_indication = True

                actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info,
                                                      direction="S2C",
                                                      channel="DATA")
            else:
                actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info,
                                                      direction="S2C",
                                                      channel="DATA",
                                                      start_time=self.pipe_pass_start_time,
                                                      end_time=self.pipe_pass_end_time)


            if opcode.lower().strip() == "data":
                if len(actual_trans) != CCF_COH_DEFINES.num_of_cfi_data_chunk:
                    num_of_errors_found += 1
                    err_msg = "{} Flow: We expected {} Data chunks on VC0_DRS but we found- {} " \
                              "The UXI.C transactions that was found are-".format(flow.opcode, str(CCF_COH_DEFINES.num_of_cfi_data_chunk), str(len(actual_trans)))
                    for trans in actual_trans:
                        err_msg += "\n\n" + trans.print_cfi_info()
                    err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            else:
                num_of_errors_found += 1
                err_msg = "Val_Assert (got_uxi_u2c_data_as_expected): User ask to find- {} in the Flow but this is an unknown option. check the checker support or your flow tables".format(str(opcode))
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=((num_of_errors_found == 0) and flow.is_coherent_flow()),
                                      parent_name="got_uxi_u2c_data_as_expected")

        return num_of_errors_found == 0

    def got_uxi_c2u_req_as_expected(self, flow, uxi_c2u_req):
        num_of_errors_found = 0
        number_of_exp_trans = 1

        if self.is_expected_if_valid(uxi_c2u_req) and not self.is_nc_flow_that_should_use_sideband_access(flow):
            self.expected_activity_in_cpipe_pass.uxi_c2u_req = True
            opcode, check_op = self.get_opcode_and_operation(uxi_c2u_req)

            actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info,
                                                  direction="C2S",
                                                  channel="REQ",
                                                  start_time=self.pipe_pass_start_time,
                                                  end_time=self.pipe_pass_end_time)

            if len(actual_trans) == 0:
                num_of_errors_found += 1
                err_msg = "{} Flow: We didn't found any UXI REQ in the flow".format(flow.opcode)
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif len(actual_trans) > number_of_exp_trans:
                num_of_errors_found += 1
                err_msg = "{} Flow: We are expecting to see only one UXI REQ in a flow".format(flow.opcode)
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif opcode.lower().strip() != actual_trans[0].get_rec_opcode_str().lower().strip():
                num_of_errors_found += 1
                err_msg = "{} Flow: The expected opcode is- {} But the actual is- {}".format(flow.opcode, opcode, actual_trans[0].get_rec_opcode_str())
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            # UXI.NC transition will be checked in nc agent.
            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=((num_of_errors_found == 0) and flow.is_coherent_flow()),
                                      parent_name="got_uxi_c2u_req_as_expected")

        return num_of_errors_found == 0

    def got_uxi_c2u_rsp_as_expected(self, flow, uxi_c2u_rsp):
        num_of_errors_found = 0

        if self.is_expected_if_valid(uxi_c2u_rsp) and not self.is_nc_flow_that_should_use_sideband_access(flow):
            self.expected_activity_in_cpipe_pass.uxi_c2u_rsp = True
            opcode, check_op = self.get_opcode_and_operation(uxi_c2u_rsp)

            actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info, direction="C2S", channel="RSP")

            if len(actual_trans) == 0:
                num_of_errors_found += 1
                err_msg = "{} Flow: We didn't found any UXI C2U RSP in the flow".format(flow.opcode)
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif len(actual_trans) > 1:
                num_of_errors_found += 1
                err_msg = "{} Flow: We are expecting to see only one UXI C2U RSP in a flow".format(flow.opcode)
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif opcode.lower().strip() != actual_trans[0].get_rec_opcode_str().lower().strip():
                num_of_errors_found += 1
                err_msg = "{} Flow: The expected opcode is- {} But the actual is- {}".format(flow.opcode, opcode, actual_trans[0].get_rec_opcode_str())
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            # UXI.NC transition will be checked in nc agent.
            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=((num_of_errors_found == 0) and flow.is_coherent_flow()),
                                      parent_name="got_uxi_c2u_rsp_as_expected")

        return num_of_errors_found == 0

    def got_uxi_c2u_data_as_expected(self, flow, uxi_c2u_data):
        num_of_errors_found = 0

        fast_ipi_dont_expect_upi_trans = flow.is_ipi_interrupt() and (self.ccf_registers.get_fast_ipi_at_specific_time(flow.initial_time_stamp) == 1)
        if self.is_expected_if_valid(uxi_c2u_data) and not fast_ipi_dont_expect_upi_trans and not self.is_nc_flow_that_should_use_sideband_access(flow):
            self.expected_activity_in_cpipe_pass.uxi_c2u_data = True
            opcode, check_op = self.get_opcode_and_operation(uxi_c2u_data)

            #In case we are sending data and right after without waiting to any event we are moving on to the next bubble.
            #In that case we don't need to see the data out on the interface till the end of the pipe pass since the pipe doesn't wait.
            if check_op == "cache2cache":
                max_time_for_data_out_on_interface = None
            else:
                max_time_for_data_out_on_interface = self.pipe_pass_end_time

            actual_trans = flow.get_flow_progress(record_type=ccf_ufi_record_info,
                                                  direction="C2S",
                                                  channel="DATA",
                                                  start_time=self.pipe_pass_start_time,
                                                  end_time=max_time_for_data_out_on_interface,
                                                  cache2cache=(check_op == "cache2cache"),
                                                  cache2ha=(check_op == "cache2ha"))

            # In a lock opcodes we have the main opcode and the msg type
            # In case that this transaction have msg type like lock we will check it also here:
            if flow.is_non_coherent_flow():
                number_of_exp_trans = 2
                if "ncmsgs." in opcode:
                    opcode_list = opcode.split(".")
                    opcode = opcode_list[0]
                    msg_type = opcode_list[1]
                    if flow.is_lock_or_unlock():
                        self.check_lock_or_unlock_ncmsgs_special_fields_flow(flow, msg_type, actual_trans)
                    elif flow.is_spcyc():
                        self.check_spcyc_ncmsgs_special_fields(flow, msg_type, actual_trans)
                    else:
                        err_msg = "Val_Assert(got_uxi_c2u_req_as_expected): We didn't expecting getting to here please check it"
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            if flow.is_nc_partial_write_flow():
                expected_num_of_data_chunk = flow.get_num_of_data_chunk_exp_on_upi_nc()
            else:
                expected_num_of_data_chunk = CCF_COH_DEFINES.num_of_cfi_data_chunk


            if len(actual_trans) == 0:
                num_of_errors_found += 1
                err_msg = "{} Flow: We didn't found any UXI WB DATA in the flow".format(flow.opcode)
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            elif len(actual_trans) != expected_num_of_data_chunk:
                num_of_errors_found += 1
                err_msg = "{} Flow: We are expecting to see {} UXI WB DATA packets in a flow but we have {}".format(flow.opcode, expected_num_of_data_chunk, len(actual_trans))
                err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            else:
                for trans in actual_trans:
                    if trans.rec_opcode.lower().strip() != opcode.lower().strip():
                        num_of_errors_found += 1
                        err_msg = "{} Flow: UXI C2U DATA - The expected opcode is- {} But the actual is- {}".format(flow.opcode, opcode, trans.rec_opcode)
                        err_msg += "\n\nFlow:\n" + flow.get_flow_info_str()
                        VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            # UXI.NC transition will be checked in nc agent.
            self.run_transition_check(flow=flow,
                                      actual_trans=actual_trans,
                                      external_condition=((num_of_errors_found == 0) and flow.is_coherent_flow()),
                                      parent_name="got_uxi_c2u_data_as_expected")

        return num_of_errors_found == 0

    def update_status_and_latest_time(self, status, exp_time, re_status, re_time):
        status &= re_status
        if re_time > exp_time:
            exp_time = re_time

        return status, exp_time

    def can_we_move_to_next_bubble(self, flow, current_bubble_row_df):
        status = True

        status &= self.got_idi_u2c_req_as_expected(flow, current_bubble_row_df.at[0, "IDI_U2C_REQ"])
        status &= self.got_idi_u2c_rsp_as_expected(flow, current_bubble_row_df.at[0, "IDI_U2C_RSP"])
        status &= self.got_idi_u2c_data_as_expected(flow, current_bubble_row_df.at[0, "IDI_U2C_DATA"])
        status &= self.got_idi_c2u_rsp_as_expected(flow, current_bubble_row_df.at[0, "IDI_C2U_RSP"])
        status &= self.got_idi_c2u_data_as_expected(flow, current_bubble_row_df.at[0, "IDI_C2U_DATA"])

        status &= self.got_uxi_c2u_req_as_expected(flow, current_bubble_row_df.at[0, "UXI_C2U_REQ"])
        status &= self.got_uxi_u2c_data_as_expected(flow, current_bubble_row_df.at[0, "UXI_U2C_DATA"])
        status &= self.got_uxi_c2u_data_as_expected(flow, current_bubble_row_df.at[0, "UXI_C2U_DATA"])
        status &= self.got_uxi_u2c_rsp_as_expected(flow, current_bubble_row_df.at[0, "UXI_U2C_RSP"])
        status &= self.got_uxi_u2c_req_as_expected(flow, current_bubble_row_df.at[0, "UXI_U2C_REQ"])
        status &= self.got_uxi_c2u_rsp_as_expected(flow, current_bubble_row_df.at[0, "UXI_C2U_RSP"])
        status &= self.is_cpipe_req_as_expected(flow, current_bubble_row_df.at[0, "CPIPE_REQ"], current_bubble_row_df.at[0, "Next Bubble"])
        return status

    def end_of_flow_checks(self, flow, flow_pipe_trace):
        #CPIPE pass check.
        #We are starting with the same pass in the pipe.
        #therefore we should be or till the last one.
        #this check is coming to make sure we didn't end our flow before the last pass the RTL did.
        #Or by any accident skip any pipe pass.
        victim_included_in_flow_pipe_pass = 0
        for pipe_pass in flow.pipe_passes_information:
            if "Victim" in pipe_pass.arbcommand_opcode and not flow.is_victim():
                victim_included_in_flow_pipe_pass += 1

        if victim_included_in_flow_pipe_pass > 1:
            err_msg = "{} Flow: The number of victim in this flow was more then 1 {} \n".format(flow.opcode, " ".join(flow.get_list_of_arbcommand_opcodes()))
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

        if len(flow.pipe_passes_information) != (len(flow_pipe_trace) + victim_included_in_flow_pipe_pass):
            err_msg = "{} Flow: The number of passes for flow {} we did in this flow, didn't much the number of passes the RTL did.\n" \
                      "RTL- {}\nFlow- {}".format(flow.opcode, flow.uri["TID"], "->".join(flow.get_list_of_arbcommand_opcodes()), "->".join(flow_pipe_trace))
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

        #cbo transition checker
        if self.si.ccf_transition_chk_en:
            cpipe_pass_item_list = []
            for item in flow.flow_progress:
                if type(item) is ccf_cbo_record_info:
                    cpipe_pass_item_list.append(item)
            self.transition_chk.transition_check(flow, cpipe_pass_item_list)


    def init_arbcommand_and_pipe_pass_time(self, flow):
        if len(flow.pipe_passes_information) > 0:
            self.reset_expected_activity_in_cpipe_pass()
            self.current_arbcommand = flow.pipe_passes_information[0].arbcommand_opcode.lower().strip()  # the first arb command will always be the opcode
            self.previous_pipe_pass_start_time = self.pipe_pass_start_time
            self.pipe_pass_start_time = flow.initial_time_stamp - 1000 #TODO: need to use clk and number of cycles
            if len(flow.pipe_passes_information) > 1:
                self.next_arbcommand = flow.pipe_passes_information[1].arbcommand_opcode.lower().strip()  # At the start we will give the next arbcommand.
                self.pipe_pass_end_time = flow.pipe_passes_information[1].arbcommand_time - 1500 #TODO: need to use clk and number of cycles
            else:
                #In case that our flow contain only one pass in the pipe.
                self.next_arbcommand = None
                self.pipe_pass_end_time = None
        else:
            err_msg = "Val_Assert (init_arbcommand_and_pipe_pass_time): We couldn't find any cpipe arbcommand in the RTL flow check your analyzer and RTL."
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def begin_of_flow_var_value_init(self, flow):
        self.init_arbcommand_and_pipe_pass_time(flow)
        self.flow_bubble_trace = ["first"]
        self.current_bubble = "first"
        self.flow_pipe_trace = [self.current_arbcommand]

        #In IDI flows we are not going over the first transaction in CSV tables.
        if flow.is_idi_flow_origin():
            self.transition_chk.transition_check(flow, [flow.flow_progress[0]]) #We are checking the first transaction mainly to make extra sure about the data we analyzed

    def update_flow_follow_information(self,flow_pipe_trace):
        if self.current_arbcommand is not flow_pipe_trace[len(flow_pipe_trace)-1]:
            flow_pipe_trace.append(self.current_arbcommand)

    def skip_flow_checkr_in_specific_cases_and_check_by_rules(self, flow: ccf_flow):
        err_msg = ""
        #If force_snoop_all_cb=1 we will be CV>0 and we will not want to skip this flow checking
        if flow.is_flusher_origin() and (flow.initial_cv_zero() and not flow.is_force_snoop_all_cb_en()) and (flow.initial_state_llc_e_or_s() or flow.initial_state_llc_i()):
            #if flow.wrote_data_to_mem() or flow.read_data_from_mem() or flow.snoop_sent() or flow.cbo_got_ufi_uxi_cmpo() or flow.cbo_got_upi_cmpu() or flow.is_data_written_to_cache():
            if len(flow.flow_progress) != 2:
                err_msg += "When we have LLCWBinv from Flusher, CV=0, LLC=E/S/I we are not expecting to see more then one read from LLC and one pass in the pipe.\n"

            for trans in flow.flow_progress:
                if type(trans) not in [ccf_cbo_record_info, ccf_llc_record_info]:
                    err_msg += "We got the follow transaction type - {} and it was not expected in Flusher flow.\n".format(str(type(trans).__name__))

            if (len(flow.snoop_requests) > 0) or (len(flow.snoop_responses) > 0):
                err_msg += "We send snoop req or receive snoop response but we didn't expect that in this flow.\n"

            if flow.wrote_data_to_mem() or flow.read_data_from_mem():
                err_msg += "We had some interaction with the memory read/write we didn't expected it in this flow.\n"

            if flow.cbo_got_ufi_uxi_cmpo() or flow.cbo_got_upi_cmpu():
                err_msg += "We didn't expect to get any UXI CMP at this flow.\n"

            if flow.is_data_written_to_cache():
                err_msg += "We didn't expect to write any data to the cache at this flow.\n"

            if err_msg != "":
                err_msg = "(skip_flow_checkr_in_specific_cases_and_check_by_rules):\n" \
                           "TID-{}, CBO_ID:{}. \n{}".format(flow.uri['TID'], flow.cbo_id_phys, err_msg)
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

            return True
        else:
            return False

    def req_sanity_check(self, flow: ccf_flow):
        if (not CCF_FLOW_UTILS.is_write_opcode(flow.opcode)) and \
           (not CCF_FLOW_UTILS.is_read_opcode(flow.opcode)) and \
           (not UXI_UTILS.is_in_coh_snp_opcodes(flow.opcode)):
            err_msg = "sanity check failed - first transaction is {} and not valid request: TID-{} ".format(flow.opcode, flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def check_flow(self, flow: ccf_flow):
        bubble_move_counter = 0
        flow_done_successfully = False
        flow_selected_row_df = None

        if self.skip_flow_checkr_in_specific_cases_and_check_by_rules(flow):
            return


        self.req_sanity_check(flow)

        flow_table_df = self.get_right_flow_from_csv_db(flow)

        if flow_table_df is not None:
            # if self.debug_prints:
            #     info_msg = "A Table was found for opcode: {}\n{}".format(flow.opcode, tabulate(flow_table_df, headers='keys', tablefmt='psql'))
            #     VAL_UTDB_MSG(time=flow.initial_time_stamp, msg=info_msg)

            VAL_UTDB_MSG(time=flow.initial_time_stamp, msg="Flow Check was started: URI[TID]: " + flow.uri["TID"] + ", Flow Opcode: "+ flow.opcode)

            self.begin_of_flow_var_value_init(flow)

            while self.current_bubble.lower() != "done":

                current_bubble_row_df = self.get_current_flow_table_row(flow, flow_table_df, self.current_bubble)

                #Save all the selected rows in single df for late flow analysis
                if flow_selected_row_df is None:
                    flow_selected_row_df = current_bubble_row_df
                else:
                    flow_selected_row_df = pd.concat([flow_selected_row_df, current_bubble_row_df])

                if len(current_bubble_row_df.index) == 0:
                    break #We didn't found any row to continue with - stopping the flow.

                if self.can_we_move_to_next_bubble(flow, current_bubble_row_df):
                    self.current_bubble = current_bubble_row_df.at[0, "Next Bubble"]

                    bubble_move_counter += 1
                    self.flow_bubble_trace.append(self.current_bubble.lower())
                    self.update_flow_follow_information(self.flow_pipe_trace)
                else:
                    flow_bubble_trace_msg = '->'.join(self.flow_bubble_trace)
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg="{} Flow: couldn't continue to the next bubble not all conditions had met. URI: {} flow_opcode: {} trace: {} ".format(flow.opcode, flow.uri["TID"], flow.opcode, flow_bubble_trace_msg))
                    break

                if bubble_move_counter > 200:
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg="{} Flow: Error counter pass 200 we probably in an infinite loop".format(flow.opcode))
                    break

            if self.current_bubble.lower() == "done":
                flow_done_successfully = True

            flow_bubble_trace_msg = '->'.join(self.flow_bubble_trace)
            flow_pipe_trace_msg = '->'.join(self.flow_pipe_trace)
            self.end_of_flow_checks(flow, self.flow_pipe_trace)
            VAL_UTDB_MSG(time=flow.initial_time_stamp, msg="Flow check is Done.\nFlow bubble trace: " + flow_bubble_trace_msg + "\nFlow cpipe passes: " + flow_pipe_trace_msg)

            if self.si.ccf_cov_en and flow_done_successfully:
                flow_selected_row_list = list(flow_selected_row_df.loc[:, 'Row Number'].values)
                self.ccf_flow_chk_cov_sample_ptr.collect_flow_coverage(flow_table_df.loc[0, 'Flow'], flow_bubble_trace_msg, flow_selected_row_list)
        else:
            err_msg = "{} Flow: We couldn't found any csv file that will describe the flow with URI {}".format(flow.opcode,flow.uri["TID"])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

