from agents.ccf_agent.ccf_coherency_agent.ccf_clos_chk import ccf_clos_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.cncu_agent.utils.cncu_utils import CNCU_UTILS
from agents.ccf_common_base.ccf_common_base import ccf_idi_record_info, ccf_cfi_record_info, \
    ccf_cbo_record_info
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.ccf_utils import CCF_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_registers import ccf_registers
from agents.ccf_common_base.pre_calc_agent import pre_calc_agent
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent
from val_utdb_report import VAL_UTDB_ERROR
from val_utdb_bint import bint
from agents.ccf_common_base.hash_calc_agent import hash_calc_agent
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from agents.ccf_common_base.uxi_utils import UXI_UTILS


class SANTA_golden_models(ccf_coherency_base_chk):
    RdIFA_golden_model = dict()
    WRq_golden_model = dict()
    HTID_golden_model = dict()
    EOP_golden_model = dict()

    cfi_inv_opcodes_without_data = ["InvItoE", "InvXtoI", "InvItoM"]
    cfi_req_opcodes_with_data = ["RdInv", "RdInvOwn", "RdCode", "RdData", "RdDataMig", "RdCur"]
    #The assumption is that all those opcodes will be maped only to RfIFA
    RdIFA_opcodes = cfi_inv_opcodes_without_data + cfi_req_opcodes_with_data + ["E_CmpO", "M_CmpO", "SI_CmpO", "Data_E", "Data_M", "Data_SI", "MemData"]

    @staticmethod
    def print_error(class_name="SANTA_golden_models", source="SANTA_golden_models", time=None, msg=""):
        VAL_UTDB_ERROR(class_name=class_name, source=source, time=time, msg=msg)

    @staticmethod
    def is_belong_to_RdIFA(rtid: bint):
        return rtid[9] == 1 #This is True only for LNL-M will change at PTL

    @staticmethod
    def is_exist_in_RdIFA(flow_key):
        return flow_key in SANTA_golden_models.RdIFA_golden_model.keys() # and (SANTA_golden_models.RdIFA_golden_model[flow_key]["COUNTER"] > 0)

    @staticmethod
    def is_exist_in_WRq(flow_key):
        return flow_key in SANTA_golden_models.WRq_golden_model.keys() # and (SANTA_golden_models.WRq_golden_model[flow_key]["COUNTER"] > 0)

    @staticmethod
    def is_rtid_already_exist_in_RdIFA(flow_key, bint_rtid):
        if flow_key in SANTA_golden_models.RdIFA_golden_model.keys():
            return SANTA_golden_models.RdIFA_golden_model[flow_key]['RTID'] == bint_rtid
        else:
            return False

    @staticmethod
    def is_rtid_already_exist_in_WRq(flow_key, bint_rtid):
        if flow_key in SANTA_golden_models.WRq_golden_model.keys():
            return SANTA_golden_models.WRq_golden_model[flow_key]['RTID'] == bint_rtid
        else:
            return False

    @staticmethod
    def is_exist_in_HTID(flow_key):
        return flow_key in SANTA_golden_models.HTID_golden_model.keys()

    @staticmethod
    def check_if_RTID_already_active_in_RdIFA(flow_key, santa_id, time, bint_rtid):
        rtid_exist = False
        for flow_key_iter in list(SANTA_golden_models.RdIFA_golden_model.keys()):
            if (SANTA_golden_models.RdIFA_golden_model[flow_key_iter]['RTID'] == bint_rtid) and (SANTA_golden_models.RdIFA_golden_model[flow_key_iter]['SANTA_ID'] == santa_id):
                if (SANTA_golden_models.RdIFA_golden_model[flow_key_iter]['START_TIME'] < time) and (SANTA_golden_models.RdIFA_golden_model[flow_key_iter]['END_TIME'] > time):
                    err_msg = "(check_if_RTID_already_active_in_RdIFA): We tried to allocate the same RTID as an existing active transaction RTID. RTID: {}, active URI:{}, new allocated URI: {}".format(hex(bint_rtid)[2:], flow_key_iter, flow_key)
                    SANTA_golden_models.print_error(time=time, msg=err_msg)
                    rtid_exist = True

            #IF our new allocated transaction is being sent after the current end time transaction we can remove the old record
            #if (SANTA_golden_models.RdIFA_golden_model[flow_key_iter]['END_TIME'] is not None) and (SANTA_golden_models.RdIFA_golden_model[flow_key_iter]['END_TIME'] < time):
            #    del SANTA_golden_models.RdIFA_golden_model[flow_key_iter]

        return rtid_exist

    @staticmethod
    def get_number_of_expected_return_pkts(flow, opcode, time_for_error):
        #cfi_inv_opcodes_without_data = ["InvItoE", "InvXtoI", "InvItoM"]
        #cfi_req_opcodes_with_data = ["RdInv", "RdInvOwn", "RdCode", "RdData", "RdDataMig", "RdCur"]
        if (opcode in UXI_UTILS.uxi_coh_snp_opcodes):
            if flow.wrote_data_to_mem():
                return 3
            else:
                return 2
        else:
            if opcode in SANTA_golden_models.cfi_inv_opcodes_without_data:
                return 2
            elif opcode in SANTA_golden_models.cfi_req_opcodes_with_data:
                return 4
            else:
                err_msg = "Val_Assert (get_number_of_expected_return_pkts): the opcode {} is unknown fix the checker".format(opcode)
                SANTA_golden_models.print_error(time=time_for_error, msg=err_msg)

    @staticmethod
    def add_entry_to_RdIFA_and_check(time, flow: ccf_flow, actual_pkt, bint_rtid):
        SANTA_golden_models.check_if_RTID_already_active_in_RdIFA(flow.flow_key, actual_pkt.rec_unit, time, bint_rtid)

        SANTA_golden_models.RdIFA_golden_model[flow.flow_key] = dict()
        SANTA_golden_models.RdIFA_golden_model[flow.flow_key]['URI'] = {'TID': actual_pkt.rec_tid,
                                                                        'LID': actual_pkt.rec_lid,
                                                                        'PID': actual_pkt.rec_pid}
        SANTA_golden_models.RdIFA_golden_model[flow.flow_key]['SANTA_ID'] = actual_pkt.rec_unit
        SANTA_golden_models.RdIFA_golden_model[flow.flow_key]['RTID'] = bint_rtid
        SANTA_golden_models.RdIFA_golden_model[flow.flow_key]['COUNTER'] = SANTA_golden_models.get_number_of_expected_return_pkts(flow=flow,
                                                                                                                                  opcode=actual_pkt.rec_opcode,
                                                                                                                                  time_for_error=time)
        SANTA_golden_models.RdIFA_golden_model[flow.flow_key]['START_TIME'] = time
        SANTA_golden_models.RdIFA_golden_model[flow.flow_key]['END_TIME'] = None
        SANTA_golden_models.check_RTID_from_RdIFA(time, flow.flow_key, bint_rtid)

    @staticmethod
    def add_entry_to_WRq_and_check(time, flow, actual_pkt, bint_rtid):
        SANTA_golden_models.WRq_golden_model[flow.flow_key] = dict()
        SANTA_golden_models.WRq_golden_model[flow.flow_key]['URI'] = {'TID': actual_pkt.rec_tid,
                                                                      'LID': actual_pkt.rec_lid,
                                                                      'PID': actual_pkt.rec_pid}
        SANTA_golden_models.WRq_golden_model[flow.flow_key]['SANTA_ID'] = flow.santa_id
        SANTA_golden_models.WRq_golden_model[flow.flow_key]['RTID'] = bint_rtid
        SANTA_golden_models.WRq_golden_model[flow.flow_key]['COUNTER'] = 3  # For two pumps of the write and the cmpU
        SANTA_golden_models.WRq_golden_model[flow.flow_key]['START_TIME'] = time
        SANTA_golden_models.WRq_golden_model[flow.flow_key]['END_TIME'] = None
        SANTA_golden_models.check_RTID_from_WRq(time, flow.flow_key, bint_rtid)

    @staticmethod
    def add_entry_to_HTID_golden_and_check(time, flow, opcode, htid):
        SANTA_golden_models.HTID_golden_model[flow.flow_key] = dict()
        SANTA_golden_models.HTID_golden_model[flow.flow_key]['HTID'] = htid
        SANTA_golden_models.HTID_golden_model[flow.flow_key]['COUNTER'] = SANTA_golden_models.get_number_of_expected_return_pkts(flow=flow,
                                                                                                                                 opcode=opcode,
                                                                                                                                 time_for_error=time)
        SANTA_golden_models.HTID_golden_model[flow.flow_key]['START_TIME'] = time
        SANTA_golden_models.HTID_golden_model[flow.flow_key]['END_TIME'] = None

    @staticmethod
    def get_RTID_for_flow_key(flow_key, txn_opcode, time_for_error):
        if SANTA_golden_models.is_exist_in_RdIFA(flow_key) and (txn_opcode in SANTA_golden_models.RdIFA_opcodes):
            return hex(SANTA_golden_models.RdIFA_golden_model[flow_key]['RTID'])[2:]
        elif SANTA_golden_models.is_exist_in_WRq(flow_key):
            return hex(SANTA_golden_models.WRq_golden_model[flow_key]['RTID'])[2:]
        else:
            err_msg = "(get_RTID_for_flow_key): User ask for RTID value from golden model but we didn't found any please check it. (TID:{})".format(flow_key)
            SANTA_golden_models.print_error(time=time_for_error, msg=err_msg)
            return None

    @staticmethod
    def get_HTID_for_flow_key(flow_key, time_for_error):
        if SANTA_golden_models.is_exist_in_HTID(flow_key):
            return hex(SANTA_golden_models.HTID_golden_model[flow_key]['HTID'])[2:]
        else:
            err_msg = "(get_HTID_for_flow_key): User ask for HTID value from golden model but we didn't found any please check it. (TID:{})".format(flow_key)
            SANTA_golden_models.print_error(time=time_for_error, msg=err_msg)
            return None

    @staticmethod
    def dec_RdIFA_counter(flow_key, time):
        SANTA_golden_models.RdIFA_golden_model[flow_key]['COUNTER'] = SANTA_golden_models.RdIFA_golden_model[flow_key]['COUNTER'] - 1
        if (SANTA_golden_models.RdIFA_golden_model[flow_key]['COUNTER'] < 0):
            err_msg = "(dec_RdIFA_counter): RdIFA counter for Key:{} is < 0 that does not make sense.".format(flow_key)
            SANTA_golden_models.print_error(time=time, msg=err_msg)

        if (SANTA_golden_models.RdIFA_golden_model[flow_key]['END_TIME'] is None) or (time > SANTA_golden_models.RdIFA_golden_model[flow_key]['END_TIME']):
            SANTA_golden_models.RdIFA_golden_model[flow_key]['END_TIME'] = time
            #del SANTA_golden_models.RdIFA_golden_model[tid]

    @staticmethod
    def dec_WRq_counter(flow_key, time):
        SANTA_golden_models.WRq_golden_model[flow_key]['COUNTER'] = SANTA_golden_models.WRq_golden_model[flow_key]['COUNTER'] - 1
        if (SANTA_golden_models.WRq_golden_model[flow_key]['COUNTER'] < 0):
            err_msg = "(dec_WRq_counter): WRq counter for Key:{} is < 0 that does not make sense.".format(flow_key)
            SANTA_golden_models.print_error(time=time, msg=err_msg)

        if (SANTA_golden_models.WRq_golden_model[flow_key]['END_TIME'] is None) or (time > SANTA_golden_models.WRq_golden_model[flow_key]['END_TIME']):
            SANTA_golden_models.WRq_golden_model[flow_key]['END_TIME'] = time
            #del SANTA_golden_models.WRq_golden_model[tid]

    @staticmethod
    def dec_HTID_counter(flow_key, time):
        SANTA_golden_models.HTID_golden_model[flow_key]['COUNTER'] = SANTA_golden_models.HTID_golden_model[flow_key]['COUNTER'] - 1
        if (SANTA_golden_models.HTID_golden_model[flow_key]['COUNTER'] < 0):
            err_msg = "(dec_HTID_counter): HTID counter for Key:{} is < 0 that does not make sense.".format(flow_key)
            SANTA_golden_models.print_error(time=time, msg=err_msg)

        if (SANTA_golden_models.HTID_golden_model[flow_key]['END_TIME'] is None) or (time > SANTA_golden_models.HTID_golden_model[flow_key]['END_TIME']):
            SANTA_golden_models.HTID_golden_model[flow_key]['END_TIME'] = time
            #del SANTA_golden_models.HTID_golden_model[tid]

    @staticmethod
    def check_RTID_from_RdIFA(time, flow_key, rtid):
        if rtid[9] != 1:
            err_msg = "(check_RTID_from_RdIFA): For UPI Read requests we are expecting to see " \
                      "RTID[9] == 1 but the value is 0 (TID:{})".format(flow_key)
            SANTA_golden_models.print_error(time=time, msg=err_msg)
        if rtid[8] != 0:
            err_msg = "(check_RTID_from_RdIFA): RTID[8] is reserved bit so it should be 0 but the actual value is 1. (TID:{})".format(flow_key)
            SANTA_golden_models.print_error(time=time, msg=err_msg)

    @staticmethod
    def check_RTID_from_WRq(time, flow_key, rtid):
        if rtid[9] != 0:
            err_msg = "(check_RTID_from_WRq): For UPI Write requests we are expecting to see " \
                      "RTID[9] == 0 but the value is 0 (TID:{})".format(flow_key)
            SANTA_golden_models.print_error(time=time, msg=err_msg)
        #if rtid[8] != 0:
        #    err_msg = "(check_RTID_from_RdIFA): RTID[8] is reserved bit so it should be 0 but the actual value is 1. (TID:{})".format(flow_key)
        #    SANTA_golden_models.print_error(time=time, msg=err_msg)

    @staticmethod
    def check_that_we_dont_have_alloc_in_multipale_queues(bint_rtid, flow_key, time_for_error):
        if SANTA_golden_models.is_belong_to_RdIFA(bint_rtid):
            if SANTA_golden_models.is_rtid_already_exist_in_WRq(flow_key, bint_rtid):
                err_msg = "(check_rtid): RTID belong to RdIFA but we found it in WRq (TID:{})".format(flow_key)
                SANTA_golden_models.print_error(time=time_for_error, msg=err_msg)
        elif not SANTA_golden_models.is_belong_to_RdIFA(bint_rtid):
            if SANTA_golden_models.is_rtid_already_exist_in_RdIFA(flow_key, bint_rtid):
                err_msg = "(check_rtid): RTID belong to WRq but we found it in RdIFA (TID:{})".format(flow_key)
                SANTA_golden_models.print_error(time=time_for_error, msg=err_msg)

    #EOP
    #####
    @staticmethod
    def is_exist_in_EOP_golden(flow_key):
        return flow_key in SANTA_golden_models.EOP_golden_model.keys()

    @staticmethod
    def get_EOP_by_flow_key(flow_key):
        return SANTA_golden_models.EOP_golden_model[flow_key]

    @staticmethod
    def add_entry_to_EOP_golden(flow_key, eop_value):
        SANTA_golden_models.EOP_golden_model[flow_key] = eop_value

    @staticmethod
    def delete_entry_in_EOP_golden_if_exist(flow_key):
        if SANTA_golden_models.is_exist_in_EOP_golden(flow_key):
            del SANTA_golden_models.EOP_golden_model[flow_key]


############################
# Transition packets
############################
class IDI_TRANSACTION(ccf_idi_record_info):
    def __init__(self):
        super().__init__()
        self.pre_calc = pre_calc_agent.get_pointer()

    def populate_common_not_relevant_fields(self):
        self.rec_time = "DoNotCheck"
        self.rec_tid = "DoNotCheck"
        self.rec_lid = "DoNotCheck"
        self.rec_pid = "DoNotCheck"
        self.rec_lpid = "DoNotCheck"
        self.checked_by_transition_checker = "DoNotCheck"

    def set_all_fields_as_DoNotCheck(self):
        self.populate_common_not_relevant_fields()
        self.rec_unit = "DoNotCheck"
        self.rec_opcode = "DoNotCheck"
        self.address = "DoNotCheck"
        self.address_parity = "DoNotCheck"
        self.rec_idi_interface = "DoNotCheck"
        self.cqid = "DoNotCheck"
        self.uqid = "DoNotCheck"
        self.lpid = "DoNotCheck"
        self.clos = "DoNotCheck"
        self.rec_selfsnoop = "DoNotCheck"
        self.rec_cache_near = "DoNotCheck"
        self.rec_logic_id = "DoNotCheck"
        self.rec_physical_id = "DoNotCheck"
        self.rec_go_type = "DoNotCheck"
        self.rec_bogus = "DoNotCheck"
        self.rec_pre = "DoNotCheck"
        self.hash = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.non_temporal = "DoNotCheck"

    
    def get_exp_unit(self, flow: ccf_flow):
        is_atom = CCF_UTILS.is_atom_module_by_physical_id(flow.requestor_physical_id)
        cor_emu_unit_string = "AT_IDI_" if is_atom else "IA_IDI_"
        return cor_emu_unit_string + str(flow.requestor_physical_id)

    def get_idi_opcode(self, flow: ccf_flow):
        if flow.original_opcode is not None:
            return flow.original_opcode
        else:
            return flow.opcode

    def get_address_align(self, address, align_address_lsb_bit):
        cl_align_address = bint(int(address, 16))
        cl_align_address[(align_address_lsb_bit - 1):0] = 0
        cl_align_address = hex(cl_align_address)[2:]
        return cl_align_address

    def get_address_and_return_cl_align_address(self, address):
        return self.get_address_align(address, CCF_COH_DEFINES.set_lsb)

    def get_address(self, flow: ccf_flow):
        return flow.address.lstrip("0") or "0"

    def address_parity_calc(self, flow: ccf_flow):
        return "DoNotCheck" #Address Parity is not supported in LNL-M.

    def data_parity_calc(self, flow: ccf_flow):
        return "DoNotCheck"  # Address Parity is not supported in LNL-M.

    def get_cqid(self, flow: ccf_flow):
        if flow.is_idi_flow_origin():
            return flow.flow_progress[0].cqid
        else:
            return None

    def get_uqid(self, flow):
        return flow.get_exp_uqid()

    def get_lpid(self, flow: ccf_flow):
        return str(flow.lpid)

    def get_clos(self, flow: ccf_flow):
        return flow.clos

    def get_selfsnoop(self, flow: ccf_flow):
        return flow.selfsnoop

    def get_cache_near(self, flow: ccf_flow):
        return flow.cache_near

    def get_logic_id(self, flow: ccf_flow):
        return flow.requestor_logic_id

    def get_phy_id(self, flow: ccf_flow):
        return flow.requestor_physical_id

class IDI_C2U_REQ_pkt(IDI_TRANSACTION):
    def __init__(self, unit=None, opcode=None, address=None, cqid=None, lpid=None, clos=None,
                 selfsnoop=None, cache_near=None, logic_id=None, phy_id=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = unit
        self.rec_opcode = opcode
        self.address = address
        self.rec_idi_interface = "C2U REQ"
        self.cqid = cqid
        self.uqid = "DoNotCheck"
        self.lpid = lpid
        self.clos = clos
        self.rec_selfsnoop = selfsnoop
        self.rec_cache_near = cache_near
        self.rec_logic_id = logic_id
        self.rec_physical_id = phy_id
        self.rec_go_type = "DoNotCheck"
        self.rec_bogus = "DoNotCheck"
        self.rec_pre = "DoNotCheck"
        self.hash = "DoNotCheck"  # We currently don't checking Hash field
        self.data = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.non_temporal = "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.rec_opcode = self.get_idi_opcode(flow)
        self.address = self.get_address(flow)
        self.cqid = self.get_cqid(flow)
        self.lpid = self.get_lpid(flow)
        self.clos = self.get_clos(flow)
        self.rec_selfsnoop = self.get_selfsnoop(flow)
        self.rec_cache_near = self.get_cache_near(flow)
        self.rec_logic_id = self.get_logic_id(flow)
        self.rec_physical_id = self.get_phy_id(flow)

class IDI_C2U_RSP_pkt(IDI_TRANSACTION):
    def __init__(self, uqid=None):
        super().__init__()
        self.set_all_fields_as_DoNotCheck()

        #override only follow fields
        self.rec_idi_interface = "C2U RSP"
        self.uqid = uqid

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        if flow.opcode in ["INTPHY", "INTLOG", "LOCK", "SPLITLOCK", "UNLOCK"]:
            self.uqid = "DoNotCheck"
        else:
            self.uqid = self.get_uqid(flow)


class IDI_C2U_DATA_pkt(IDI_TRANSACTION):
    def __init__(self, uqid=None):
        super().__init__()
        self.set_all_fields_as_DoNotCheck()

        # override only follow fields
        self.rec_idi_interface = "C2U DATA"
        self.uqid = uqid

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.uqid = self.get_uqid(flow)
        self.data_parity = self.data_parity_calc(flow)

class IDI_U2C_REQ_pkt(IDI_TRANSACTION):
    def __init__(self, uqid=None, address=None):
        super().__init__()
        self.set_all_fields_as_DoNotCheck()

        # override only follow fields
        self.rec_idi_interface = "U2C REQ"
        self.address = address
        self.uqid = uqid

    def get_address(self, flow: ccf_flow):
        if flow.is_llc_special_opcode():
            real_address = ccf_addressless_db.get_pointer().get_real_address_by_uri(flow.uri['TID'])
            if real_address == "0": #corner case where real address is 0
                return "0"
            else:
                return real_address
        else:
            return self.get_address_and_return_cl_align_address(flow.address)

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.address = self.get_address(flow)
        self.uqid = self.get_uqid(flow)
        self.address_parity = self.address_parity_calc(flow)

    def fix_exp_according_to_current_snoop_opcode(self, flow: ccf_flow, act_trans):
        self.rec_opcode = act_trans.rec_opcode
        if self.is_selfsnpinv():
            self.lpid = self.get_lpid(flow)
        else:
            self.lpid = "DoNotCheck"
        if self.rec_opcode in ["INTPHY", "INTLOG", "STARTREQ", "STOPREQ"]:
            self.address = "DoNotCheck"
            self.uqid = "DoNotCheck"



class IDI_U2C_RSP_pkt(IDI_TRANSACTION):
    def __init__(self, opcode=None, cqid=None, pre=None, uqid=None, lpid=None, logic_id=None, phy_id=None):
        super().__init__()
        self.set_all_fields_as_DoNotCheck()

        # override only follow fields
        self.rec_logic_id = logic_id
        self.rec_physical_id = phy_id
        self.rec_opcode = opcode
        self.rec_pre = pre
        self.rec_idi_interface = "U2C RSP"
        self.cqid = cqid
        self.uqid = uqid
        self.lpid = lpid
        self.dbp_params = 'DoNotCheck' #kmoses1: dbp params will be checked in dedicated checker


    def get_uqid(self, flow):
        if self.rec_opcode is None:
            return None
        elif "WRITEPULL" in self.rec_opcode:
            return flow.get_exp_uqid()
        else:
            return "DoNotCheck"

    def get_lpid(self, flow: ccf_flow):
        if self.rec_opcode is None:
            return None
        elif "EXTCMP" in self.rec_opcode:
            return str(flow.lpid)
        else:
            return "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_pre = self.pre_calc.get_rspPRE(flow, collect_cov=True)
        self.cqid = self.get_cqid(flow)
        self.uqid = self.get_uqid(flow)
        self.lpid = self.get_lpid(flow)
        self.rec_logic_id = self.get_logic_id(flow)
        self.rec_physical_id = self.get_phy_id(flow)


class IDI_U2C_DATA_pkt(IDI_TRANSACTION):
    def __init__(self, opcode=None, cqid=None, pre=None):
        super().__init__()
        self.set_all_fields_as_DoNotCheck()

        # override only follow fields
        self.rec_pre = pre
        self.rec_idi_interface = "U2C DATA"
        self.cqid = cqid

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_pre = self.pre_calc.get_dataPRE(flow, collect_cov=True)
        self.cqid = self.get_cqid(flow)
        self.data_parity = self.data_parity_calc(flow)


class CFI_TRANSACTION(ccf_cfi_record_info):
    def __init__(self):
        super().__init__()
        self.hash_calc_agent = hash_calc_agent.get_pointer()
        self.clos_chk = ccf_clos_chk.get_pointer()


    def populate_common_not_relevant_fields(self):
        self.rec_time = "DoNotCheck"
        self.rec_tid = "DoNotCheck"
        self.rec_lid = "DoNotCheck"
        self.rec_pid = "DoNotCheck"
        self.checked_by_transition_checker = "DoNotCheck"

    ################################
    # Expected Fields - functions
    ################################
    def get_flow_address(self, flow: ccf_flow):
        if flow.is_llc_special_opcode():
            return ccf_addressless_db.get_pointer().get_real_address_by_uri(flow.uri['TID'])
        else:
            return flow.address

    def get_hash_id_str(self, address):
        return str(self.hash_calc_agent.get_hash(address))

    def get_exp_unit(self, flow: ccf_flow):
        if type(self) in [UPI_C_DATA_SA_D_pkt, UPI_C_DATA_PW_pkt, UPI_C_RSP_SR_U_pkt]: #The assumption here for UPI_C_RSP_SR_U_pkt is that CmpU will always go back only for WR
            return CCF_UTILS.get_santa_name(flow.cbo_half_id)
        else:
            return CCF_UTILS.get_santa_name(self.get_hash_id_str(flow.address))

    def get_exp_destID(self, flow, interface, time_for_error_prints):
        if CCF_UTILS.is_cfi_u2c_dir(interface):
            if type(self) in [UPI_C_RSP_SR_U_pkt]: #The assumption here is that CmpU will always go back only for WR
                santa_id = int(flow.cbo_half_id)
            else:
                santa_id = self.hash_calc_agent.get_hash(flow.address)
            return CCF_UTILS.get_santa_rsp_id_name(santa_id)
        elif CCF_UTILS.is_cfi_c2u_dir(interface):
            hbo_id = self.hash_calc_agent.get_hash(self.get_flow_address(flow))
            return CCF_UTILS.get_hbo_dest_id_name(hbo_id)
        else:
            err_msg = "We didn't expect this direction check your log, interface: {}".format(interface)
            VAL_UTDB_ERROR(time=time_for_error_prints, msg=err_msg)

    def get_exp_rspID(self, flow, interface, time_for_error_prints):
        if CCF_UTILS.is_cfi_u2c_dir(interface):
            return None  # I don't see a use for it if we will have use we should fail since we return None.
        elif CCF_UTILS.is_cfi_c2u_dir(interface):
            if type(self) in [UPI_C_DATA_SA_D_pkt, UPI_C_DATA_PW_pkt]:
                return CCF_UTILS.get_santa_rsp_id_name(int(flow.cbo_half_id))
            else:
                santa_id = self.hash_calc_agent.get_hash(flow.address)
                return CCF_UTILS.get_santa_rsp_id_name(santa_id)
        else:
            err_msg = "We didn't expect this direction check your log, interface: {}".format(interface)
            VAL_UTDB_ERROR(time=time_for_error_prints, msg=err_msg)

    def get_exp_core_id(self, flow: ccf_flow):
        if flow.is_snoop_opcode():
            santa_id = 1 if (CCF_UTILS.get_santa_name(1) == flow.flow_progress[0].rec_unit) else 0
            return CCF_UTILS.get_sbo_id(santa_id)
        elif flow.is_victim():
            parent_requestor_logic_id = ccf_dbs.ccf_flows[flow.uri['TID']].requestor_logic_id
            return str(parent_requestor_logic_id)
        elif flow.is_flusher_origin():
            return "DoNotCheck" # Coreid[1:0] = flushed_id[1:0] - Since we have many flushers (16 in each cbo), then we have aliasing on coreid, so it becomes almost random number.
        else:
            return str(flow.requestor_logic_id)

    def get_exp_RTID(self, flow: ccf_flow):
        return SANTA_golden_models.get_RTID_for_flow_key(flow.flow_key, self.rec_opcode, flow.initial_time_stamp)

    def get_exp_HTID(self, flow: ccf_flow):
        return SANTA_golden_models.get_HTID_for_flow_key(flow.flow_key, flow.initial_time_stamp)

    def address_parity_calc(self, address):
        return "DoNotCheck" #Address parity is not part of LNL-M.

    def get_exp_rsp_pcls(self, flow):
        return "DoNotCheck" #This is a field that pushed by VC and PRE transition checker comapre it with the PRE on idi.

    def get_exp_data_pcls(self, flow: ccf_flow):
        # This field is generated by VC but we are using this flow indication for PRE calculation,
        # therefore there is benefit to check our that our indication is correct
        return flow.cfi_upi_data_pcls

    def get_exp_tc(self, flow):
        return str(self.clos_chk.get_exp_traffic_class(flow))

    def get_exp_cachefar(self, flow):
        return "0" #Should be always 0 at LNL-M

    def get_exp_is_wb(self, flow: ccf_flow):
        if flow.is_core_clean() or flow.is_core_modified() or flow.is_llc_clean() or flow.is_llc_modified():
            return "1"
        else:
            return "0"

    def get_exp_dbp_params(self, flow):
        return "DoNotCheck" # We don't need to calculate dbp_parmas here since we have dedicative checker for it

    def get_exp_dbpinfo(self, flow):
        return "DoNotCheck" # We don't need to calculate dbpinfo here since we have dedicative checker for it

    def get_exp_rctrl(self, flow, pkt_type, vc_id, interface, time_for_error_prints):
        direction = interface.split("_")[0]
        channel = interface.split("_")[1]

        if direction == CCF_UTILS.get_cfi_u2c_dir_str():
            return "DoNotCheck"
        elif direction == CCF_UTILS.get_cfi_c2u_dir_str():
            if not flow.is_coherent_flow():
                is_interrupt = CNCU_UTILS.is_interrupt_for_rctrl(bint(int(flow.address, 16)), flow.opcode)
                bint_rctrl = CNCU_UTILS.get_nc_flow_rctrl(ccf_ral_agent.get_pointer(), time_for_error_prints, pkt_type, is_interrupt=is_interrupt)
                return str(bint_rctrl)
            if channel == "REQ":
                return "1"
            elif channel == "DATA":
                return "0"
            elif channel == "RSP" and (pkt_type in ["SR-U", "SR-H"]):
                return "0"
            else:
                err_msg = "We didn't find any condition fit to: channel: {}, vc_id: {}".format(channel,vc_id)
                VAL_UTDB_ERROR(time=time_for_error_prints, msg=err_msg)
        else:
            err_msg = "We didn't expect this direction check your log, direction: {}".format(direction)
            VAL_UTDB_ERROR(time=time_for_error_prints, msg=err_msg)

    def get_address_align(self, address, align_address_lsb_bit):
        cl_align_address = bint(int(address, 16))
        cl_align_address[(align_address_lsb_bit - 1):0] = 0
        cl_align_address = hex(cl_align_address)[2:]
        return cl_align_address

    def get_address_and_return_cl_align_address(self, address):
        return self.get_address_align(address, CCF_COH_DEFINES.set_lsb)

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        VAL_UTDB_ERROR(time=0, msg="User need to implement this function, please check your code.")


"""
SA Packet on CFI REQ channel 
"""
class UPI_C_REQ_SA_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None,opcode=None, address=None, address_parity=None, rctrl=None, dst_id=None,
                               rsp_id=None, rtid=None, traffic_class=None, core_id=None, trace_pkt=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_REQ_0".format(CCF_UTILS.get_cfi_c2u_dir_str())
        self.msg_class = "REQ"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = address_parity
        self.protocol_id = "UPI.C"
        self.pkt_type = "SA"
        self.vc_id = "UPI_REQ"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = rsp_id
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = traffic_class
        self.core_id = core_id
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = "DoNotCheck"
        self.length = "DoNotCheck"

    def get_expected_address(self, flow: ccf_flow):
        CL_align_opcode = ["CLFLUSH", "CLFLUSHOPT", "LLCWB", "LLCWBINV", "CLWB"]
        #CL_align_opcode = []
        # We will use CL align address in two cases:
        # 1. IDI opcodes: CLFLUSH, CLFLUSHOPT, CLWB, LLCWB, LLCWBINV will always go out at CFI as CL align
        #   - was done like this to make sure we don't have Critical Chunk bug in those opcodes
        # 2. If we forces critical chunk zero that mean address[5] == 0
        if (flow.opcode in CL_align_opcode) or (ccf_registers.get_pointer().force_critical_chunk_zero[flow.cbo_id_phys] == 1):
            return self.get_address_align(flow.address, 6)
        else:
            return self.get_address_align(flow.address, 5)

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.address = self.get_expected_address(flow=flow)
        self.address_parity = self.address_parity_calc(flow.address)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.rsp_id = self.get_exp_rspID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.traffic_class = self.get_exp_tc(flow)
        self.core_id = self.get_exp_core_id(flow=flow)

"""
CFI SA Packet on CFI DATA channel.
"""
class UPI_C_DATA_SA_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None,opcode=None, address=None, rctrl=None,
                                dst_id=None, rsp_id=None, rtid=None, traffic_class=None, core_id=None, trace_pkt=None, eop=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_DATA_0".format(CCF_UTILS.get_cfi_c2u_dir_str())
        self.msg_class = "WB"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SA"
        self.vc_id = "UPI_WB"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = rsp_id
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = traffic_class
        self.core_id = core_id
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = eop
        self.length = "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.address = self.get_address_and_return_cl_align_address(flow.address)
        self.address_parity = self.address_parity_calc(flow.address)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.rsp_id = self.get_exp_rspID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.traffic_class = str(self.clos_chk.get_exp_traffic_class(flow))
        self.core_id = self.get_exp_core_id(flow)


"""
CFI SA-S Packet on CFI REQ channel.
"""
class UPI_C_REQ_SA_S_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, address=None, rctrl=None,
                                      dst_id=None, rsp_id=None, rtid=None, htid=None, trace_pkt=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_REQ_0".format(CCF_UTILS.get_cfi_u2c_dir_str())
        self.msg_class = "SNP"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SA-S"
        self.vc_id = "UPI_SNP"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = rsp_id
        self.rtid = "DoNotCheck" # rtid is part of snoop pkt but CCF don't use it and not return it with any of the snoop response pkts
        self.htid = htid
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = "DoNotCheck"
        self.length = "DoNotCheck"


    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = "DoNotCheck" #In our env we will random the SANTA the snoop will be sent to. therefore the isn't any real reason to check it.
        self.address = self.get_address_and_return_cl_align_address(flow.address)
        self.address_parity = self.address_parity_calc(flow.address)
        self.rctrl = "DoNotCheck" #CCF doesn't use RCTRL inside CCF it's don't care
        self.dst_id = "DoNotCheck" #In our env we will random the SANTA the snoop will be sent to. therefore the isn't any real reason to check it.
        self.rsp_id = "DoNotCheck" #There is no support for C2C data FWD therefore CCF not use it
        self.htid = self.get_exp_HTID(flow=flow)


"""
CFI SA-SL Packet on CFI REQ channel.
"""
class UPI_C_REQ_SA_SL_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, address=None, rctrl=None, dst_id=None, htid=None, trace_pkt=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_REQ_0".format(CCF_UTILS.get_cfi_u2c_dir_str())
        self.msg_class = "SNP"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SA-SL"
        self.vc_id = "UPI_SNP"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = "DoNotCheck"
        self.htid = htid
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = "DoNotCheck"
        self.length = "DoNotCheck"


    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = "DoNotCheck" #In our env we will random the SANTA the snoop will be sent to. therefore the isn't any real reason to check it.
        self.address = self.get_address_and_return_cl_align_address(flow.address)
        self.address_parity = self.address_parity_calc(flow.address)
        self.rctrl = "DoNotCheck" #CCF doesn't use RCTRL inside CCF it's don't care
        self.dst_id = "DoNotCheck" #In our env we will random the SANTA the snoop will be sent to. therefore the isn't any real reason to check it.
        self.htid = self.get_exp_HTID(flow=flow)


"""
CFI SR-H Packet on CFI RSP channel.
"""
class UPI_C_RSP_SR_H_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, address=None, rctrl=None, dst_id=None, htid=None, trace_pkt=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_RSP_0".format(CCF_UTILS.get_cfi_c2u_dir_str())
        self.msg_class = "RSP"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SR-H"
        self.vc_id = "VC0_NDR"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = "DoNotCheck"
        self.htid = htid
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = "DoNotCheck"
        self.length = "DoNotCheck"


    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.address = self.get_address_and_return_cl_align_address(flow.address)
        self.address_parity = self.address_parity_calc(flow.address)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.htid = self.get_exp_HTID(flow=flow)


"""
CFI SR-HD Packet on CFI DATA channel.
"""
class UPI_C_DATA_SR_HD_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, address=None, rctrl=None, dst_id=None, htid=None, par=None,
                 pcls=None, trace_pkt=None, eop=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_DATA_0".format(CCF_UTILS.get_cfi_c2u_dir_str())
        self.msg_class = "RSP"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = par
        self.protocol_id = "UPI.C"
        self.pkt_type = "SR-HD"
        self.vc_id = "VC0_DRS"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = "DoNotCheck"
        self.htid = htid
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = pcls
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = eop
        self.length = "DoNotCheck"


    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.address = self.get_address_and_return_cl_align_address(flow.address)
        self.address_parity = self.address_parity_calc(flow.address)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.htid = self.get_exp_HTID(flow=flow)
        self.pcls = self.get_exp_data_pcls(flow=flow)


"""
CFI SR-U Packet on CFI RSP channel.
"""
class UPI_C_RSP_SR_U_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, rctrl=None, dst_id=None, rtid=None, pcls=None, trace_pkt=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_RSP_0".format(CCF_UTILS.get_cfi_u2c_dir_str())
        self.msg_class = "RSP"
        self.rec_opcode = opcode
        self.address = "DoNotCheck"
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SR-U"
        self.vc_id = "VC0_NDR"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = pcls
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = "DoNotCheck"
        self.length = "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.pcls = self.get_exp_rsp_pcls(flow=flow)


"""
CFI SR-O Packet on CFI RSP channel.
"""
class UPI_C_RSP_SR_O_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, rctrl=None, dst_id=None, rtid=None, pcls=None,
                 dbp_params=None, trace_pkt=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_RSP_0".format(CCF_UTILS.get_cfi_u2c_dir_str())
        self.msg_class = "RSP"
        self.rec_opcode = opcode
        self.address = "DoNotCheck"
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SR-O"
        self.vc_id = "VC0_NDR"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = pcls
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = dbp_params
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = "DoNotCheck"
        self.length = "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.pcls = self.get_exp_rsp_pcls(flow=flow)
        self.dbp_params = self.get_exp_dbp_params(flow=flow)


"""
CFI SR-CD Packet on CFI DATA channel.
"""
class UPI_C_DATA_SR_CD_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, rctrl=None, dst_id=None, rtid=None, pcls=None, trace_pkt=None, eop=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_DATA_0".format(CCF_UTILS.get_cfi_u2c_dir_str())
        self.msg_class = "RSP"
        self.rec_opcode = opcode
        self.address = "DoNotCheck"
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SR-CD"
        self.vc_id = "VC0_DRS"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = pcls
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = eop
        self.length = "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface,
                                          time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.pcls = self.get_exp_data_pcls(flow=flow)


"""
CFI SA-D Packet on CFI DATA channel.
"""
class UPI_C_DATA_SA_D_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, address=None, rctrl=None, dst_id=None, rsp_id=None, rtid=None,
                 traffic_class=None, cachefar=None, dbpinfo=None, pcls=None, core_id=None, is_wb=None, trace_pkt=None, eop=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_DATA_0".format(CCF_UTILS.get_cfi_c2u_dir_str())
        self.msg_class = "WB"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "SA-D"
        self.vc_id = "UPI_WB"
        self.rctrl = rctrl
        self.dst_id = dst_id
        self.rsp_id = rsp_id
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = pcls
        self.dbpinfo = dbpinfo
        self.dbp_params = "DoNotCheck"
        self.cachefar = cachefar
        self.traffic_class = traffic_class
        self.core_id = core_id
        self.is_wb = is_wb
        self.trace_pkt = trace_pkt
        self.eop = eop
        self.length = "DoNotCheck"

    def get_exp_tc(self, flow):
        return "0" #since SA_D are WBs and TC will be 0 for WBs

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow)
        self.address = self.get_address_and_return_cl_align_address(self.get_flow_address(flow)) #We are using get_flow_address_function since this pkt can be origin from LLC special opcodes
        self.rctrl = self.get_exp_rctrl(flow=flow, pkt_type=self.pkt_type, vc_id=self.vc_id,
                                        interface=self.interface, time_for_error_prints=flow.initial_time_stamp)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface,
                                          time_for_error_prints=flow.initial_time_stamp)
        self.rsp_id = self.get_exp_rspID(flow=flow, interface=self.interface,
                                         time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.traffic_class = self.get_exp_tc(flow=flow)
        self.cachefar = self.get_exp_cachefar(flow=flow)
        self.dbpinfo = self.get_exp_dbpinfo(flow=flow)
        self.pcls = self.get_exp_data_pcls(flow=flow)
        self.core_id = self.get_exp_core_id(flow=flow)
        self.is_wb = self.get_exp_is_wb(flow=flow)


"""
CFI SA-D Packet on CFI DATA channel.
"""
class UPI_C_DATA_PW_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, address=None, dst_id=None, rsp_id=None, rtid=None,
                 traffic_class=None, core_id=None, trace_pkt=None, eop=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_DATA_0".format(CCF_UTILS.get_cfi_c2u_dir_str())
        self.msg_class = "WB"
        self.rec_opcode = opcode
        self.address = address
        self.address_parity = "DoNotCheck"
        self.protocol_id = "UPI.C"
        self.pkt_type = "PW"
        self.vc_id = "UPI_WB"
        self.rctrl = "DoNotCheck"
        self.dst_id = dst_id
        self.rsp_id = rsp_id
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = traffic_class
        self.core_id = core_id
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = eop
        self.length = "DoNotCheck"

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.address = self.get_address_and_return_cl_align_address(flow.address)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface,
                                          time_for_error_prints=flow.initial_time_stamp)
        self.rsp_id = self.get_exp_rspID(flow=flow, interface=self.interface,
                                         time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)
        self.traffic_class = self.get_exp_tc(flow=flow)
        self.core_id = self.get_exp_core_id(flow=flow)


"""
CFI SA-D Packet on CFI DATA channel.
"""
class CXM_DATA_int_64B_DRS_pkt(CFI_TRANSACTION):
    def __init__(self, rec_unit=None, opcode=None, dst_id=None, rtid=None, trace_pkt=None, eop=None):
        super().__init__()
        self.populate_common_not_relevant_fields()
        self.rec_unit = rec_unit
        self.interface = "{}_DATA_0".format(CCF_UTILS.get_cfi_u2c_dir_str())
        self.msg_class = "DoNotCheck"
        self.rec_opcode = opcode
        self.address = "DoNotCheck"
        self.address_parity = "DoNotCheck"
        self.protocol_id = "CXM"
        self.pkt_type = "DRS"
        self.vc_id = "VC0_DRS"
        self.rctrl = "DoNotCheck"
        self.dst_id = dst_id
        self.rsp_id = "DoNotCheck"
        self.rtid = rtid
        self.htid = "DoNotCheck"
        self.chunk = "DoNotCheck"
        self.data = "DoNotCheck"
        self.data_parity = "DoNotCheck"
        self.paramA = "DoNotCheck"
        self.msg_type = "DoNotCheck"
        self.pcls = "DoNotCheck"
        self.dbpinfo = "DoNotCheck"
        self.dbp_params = "DoNotCheck"
        self.cachefar = "DoNotCheck"
        self.traffic_class = "DoNotCheck"
        self.core_id = "DoNotCheck"
        self.is_wb = "DoNotCheck"
        self.trace_pkt = trace_pkt
        self.eop = eop
        self.length = "DoNotCheck" #The length is given by external IP depend if this is 64B or 32B pkt

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        self.rec_unit = self.get_exp_unit(flow=flow)
        self.dst_id = self.get_exp_destID(flow=flow, interface=self.interface,
                                          time_for_error_prints=flow.initial_time_stamp)
        self.rtid = self.get_exp_RTID(flow=flow)


class CBO_CPIPE_RECORD(ccf_cbo_record_info):
    def __init__(self):
        super().__init__()
        self.give_DoNotCheck_as_initial_value()

    def give_DoNotCheck_as_initial_value(self):
        for attr, exp_value in vars(self).items():
            setattr(self, attr, "DoNotCheck")

    def get_cqid(self, flow: ccf_flow):
        if flow.is_idi_flow_origin():
            return str(int(flow.flow_progress[0].cqid, 16))
        else:
            return None

    def get_htid_in_snoop_flow(self, flow: ccf_flow):
        if flow.is_cfi_flow_origin():
            return flow.flow_progress[0].htid
        else:
            return None

    def set_exp_data_according_to_flow(self, flow: ccf_flow):
        if flow.is_idi_flow_origin():
            self.sqid = self.get_cqid(flow)
            self.cache_near = flow.get_effective_cache_near_value()
        elif flow.is_cfi_flow_origin():
            # In case of conflict we see that in the second lookup we are not updating the selfsnoop - since selfsnoop is not use for snoop opcode we will ignore it when we have conflict.
            #If in another project it will effect also in snoop opcode we will need to fix this here.
            if flow.had_conflict:
                self.selfsnp = "DoNotCheck"
            # In case of CB enable situation of always_selfsnoop we will see in cpipe selfsnoop=1 even if this is snoop from UPI
            elif flow.is_always_selfsnoop():
                self.selfsnp = "1"
            else:
                self.selfsnp = "0"
            self.htid = self.get_htid_in_snoop_flow(flow)


class transition_chk(ccf_coherency_base_chk):
    def __init__(self):
        super().__init__()
        self.ccf_ral_agent = ccf_ral_agent.get_pointer()
        self.UPI_C_REQ_SA_pkt_opcode_list = ["RdCur", "RdCode", "RdData", "RdDataMig", "RdInvOwn", "InvXtoI", "InvItoE", "RdInv", "InvItoM"]
        self.UPI_C_DATA_SA_pkt_opcode_list = ["ReqFwdCnflt"]
        self.UPI_C_REQ_SA_S_pkt_opcode_list = ["SnpCur", "SnpCode", "SnpData", "SnpDataMig", "SnpInvOwn", "SnpDataMig"]
        self.UPI_C_REQ_SA_SL_pkt_opcode_list = ["SnpLCur", "SnpLCode", "SnpLData", "SnpLFlush", "SnpLInv", "SnpLDrop", "SnpInvMig", "SnpLDataMig"]
        self.UPI_C_RSP_SR_H_pkt_opcode_list = ["RspI", "RspS", "RspE", "RspFwd", "RspFwdI-C", "RspFwdS", "RspFwdI-D"]
        self.UPI_C_DATA_SR_HD_pkt_opcode_list = ["RspFwdIWb", "RspFwdSWb", "RspIWb", "RspSWb", "RspCurData"]
        self.UPI_C_RSP_SR_U_pkt_opcode_list = ["CmpU"]
        self.UPI_C_RSP_SR_O_pkt_opcode_list = ["M_CmpO", "E_CmpO", "SI_CmpO", "FwdCnfltO"]
        self.UPI_C_DATA_SR_CD_pkt_opcode_list = ["Data_M", "Data_E", "Data_SI"]
        self.UPI_C_DATA_SA_D_pkt_opcode_list = ["WbMtoI", "WbMtoS", "WbMtoE", "WbMtoIPush", "WbEtoI"]
        self.UPI_C_DATA_PW_pkt_opcode_list = ["WbMtoIPtl", "WbMtoEPtl", "NonSnpWrPtl"]
        self.CXM_DATA_int_64B_DRS_pkt_opcode_list = ["MemData"]

    def with_the_same_uri_fields(self, uri_dict, actual_pkt):
        return ((uri_dict['TID'] == actual_pkt.rec_tid) and (uri_dict['LID'] == actual_pkt.rec_lid) and (uri_dict['PID'] == actual_pkt.rec_pid))

    def should_allocate_RdIFA_entry(self, vc_id, flow_key, actual_pkt):
        is_second_rtid_flow = False
        if SANTA_golden_models.is_exist_in_RdIFA(flow_key=flow_key):
            is_not_same_uri = not self.with_the_same_uri_fields(SANTA_golden_models.RdIFA_golden_model[flow_key]["URI"], actual_pkt)

            # This is a checking for one of the checker assumptions if this will not be true anymore we will need to review the checker again.
            if (SANTA_golden_models.RdIFA_golden_model[flow_key]["COUNTER"] != 0) and (SANTA_golden_models.RdIFA_golden_model[flow_key]["URI"]['TID'] != actual_pkt.rec_tid):
                err_msg = "(RdIFA_golden_model): A situation that in the same flow two RTID are running at the same time and not one by one is not expected. (URI-{}).".format(actual_pkt.rec_tid)
                VAL_UTDB_ERROR(time=actual_pkt.rec_time, msg=err_msg)

            is_second_rtid_flow = (SANTA_golden_models.RdIFA_golden_model[flow_key]["COUNTER"] == 0) and is_not_same_uri

        return (vc_id == "UPI_REQ") and (not SANTA_golden_models.is_exist_in_RdIFA(flow_key=flow_key) or is_second_rtid_flow)

    def should_allocate_WRq_entry(self, vc_id, flow_key, actual_pkt):
        is_second_rtid_flow = False

        if SANTA_golden_models.is_exist_in_WRq(flow_key=flow_key):
            is_not_same_uri = not self.with_the_same_uri_fields(SANTA_golden_models.WRq_golden_model[flow_key]["URI"], actual_pkt)

            #This is a checking for one of the checker assumptions if this will not be true anymore we will need to review the checker again.
            if (SANTA_golden_models.WRq_golden_model[flow_key]["COUNTER"] != 0) and (SANTA_golden_models.WRq_golden_model[flow_key]["URI"]['TID'] != actual_pkt.rec_tid):
                err_msg = "(should_allocate_WRq_entry): A situation that in the same flow two RTID are running at the same time and not one by one is not expected. (URI-{}).".format(actual_pkt.rec_tid)
                VAL_UTDB_ERROR(time=actual_pkt.rec_time, msg=err_msg)

            is_second_rtid_flow = (SANTA_golden_models.WRq_golden_model[flow_key]["COUNTER"] == 0) and is_not_same_uri # We have diffrent URI set and the previous RTID flow already ended.

        return (vc_id == "UPI_WB") and (not SANTA_golden_models.is_exist_in_WRq(flow_key=flow_key) or is_second_rtid_flow)

    def alloc_RTID_and_HTID_in_golden_model_if_first_time_use(self, flow, exp_pkt, actual_pkt):
        if exp_pkt.rtid is None:  # None mean we expect some value there but we didn't populate yet
            if actual_pkt.rtid is None:
                err_msg = "(alloc_RTID_and_HTID_in_golden_model_if_first_time_use): RTID of the actual trans is None," \
                          "this wasn't expected please check your code/RTL(URI-{}).".format(actual_pkt.rec_tid)
                VAL_UTDB_ERROR(time=actual_pkt.rec_time, msg=err_msg)
            else:
                bint_rtid = bint(int(actual_pkt.rtid, 16))

                if self.should_allocate_RdIFA_entry(vc_id=exp_pkt.vc_id, flow_key=flow.flow_key, actual_pkt=actual_pkt):
                    SANTA_golden_models.add_entry_to_RdIFA_and_check(time=actual_pkt.rec_time,
                                                                     flow=flow,
                                                                     actual_pkt=actual_pkt,
                                                                     bint_rtid=bint_rtid)

                elif self.should_allocate_WRq_entry(vc_id=exp_pkt.vc_id, flow_key=flow.flow_key, actual_pkt=actual_pkt):
                    SANTA_golden_models.add_entry_to_WRq_and_check(time=actual_pkt.rec_time,
                                                                   flow=flow,
                                                                   actual_pkt=actual_pkt,
                                                                   bint_rtid=bint_rtid)

                elif not (SANTA_golden_models.is_exist_in_RdIFA(flow_key=flow.flow_key) or
                          SANTA_golden_models.is_exist_in_WRq(flow_key=flow.flow_key)):
                    err_msg = "Val_Assert (alloc_RTID_and_HTID_in_golden_model_if_first_time_use): " \
                              "We don't have any RTID record of this TID-{} and we didn't allocated it also now.".format(actual_pkt.rec_tid)
                    VAL_UTDB_ERROR(time=actual_pkt.rec_time, msg=err_msg)


                SANTA_golden_models.check_that_we_dont_have_alloc_in_multipale_queues(bint_rtid=bint_rtid,
                                                                                      flow_key=flow.flow_key,
                                                                                      time_for_error=actual_pkt.rec_time)

        if exp_pkt.htid is None:  # None mean we expect some value there but we didn't populate yet
            if actual_pkt.htid is None:
                err_msg = "(alloc_RTID_and_HTID_in_golden_model_if_first_time_use): HTID of the actual trans is None," \
                          "this wasn't expected please check your code/RTL(URI-{}).".format(actual_pkt.rec_tid)
                VAL_UTDB_ERROR(time=actual_pkt.rec_time, msg=err_msg)
            else:
                bint_htid = bint(int(actual_pkt.htid, 16))

                if (exp_pkt.vc_id == "UPI_SNP") and (actual_pkt.rec_opcode in UXI_UTILS.uxi_coh_snp_opcodes) and not SANTA_golden_models.is_exist_in_HTID(flow.flow_key):
                    SANTA_golden_models.add_entry_to_HTID_golden_and_check(time=actual_pkt.rec_time,
                                                                           flow=flow,
                                                                           opcode=actual_pkt.rec_opcode,
                                                                           htid=bint_htid)

                elif not SANTA_golden_models.is_exist_in_HTID(flow.flow_key):
                    err_msg = "Val_Assert (alloc_RTID_and_HTID_in_golden_model_if_first_time_use): " \
                              "you didn't allocated the HTID, something went wrong if you got here. TID- {}".format(actual_pkt.rec_tid)
                    VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def dec_RTID_and_HTID_counters(self, flow_key, act_pkt, exp_pkt):
        if exp_pkt.rtid != "DoNotCheck":
            if SANTA_golden_models.is_exist_in_RdIFA(flow_key=flow_key) and (act_pkt.rec_opcode in SANTA_golden_models.RdIFA_opcodes):
                SANTA_golden_models.dec_RdIFA_counter(flow_key=flow_key, time=act_pkt.rec_time)
            elif SANTA_golden_models.is_exist_in_WRq(flow_key=flow_key):
                SANTA_golden_models.dec_WRq_counter(flow_key=flow_key, time=act_pkt.rec_time)
            else:
                err_msg = "(dec_RTID_and_HTID_counters): You shouldn't get here, " \
                        "since you should have this TID - {} flow_key - {} store in RdIFA/WRq golden model".format(act_pkt.rec_tid, flow_key)
                VAL_UTDB_ERROR(time=act_pkt.rec_time, msg=err_msg)

        if exp_pkt.htid != "DoNotCheck":
            if SANTA_golden_models.is_exist_in_HTID(flow_key=flow_key):
                SANTA_golden_models.dec_HTID_counter(flow_key=flow_key, time=act_pkt.rec_time)
            else:
                err_msg = "(dec_RTID_and_HTID_counters): You shouldn't get here, " \
                        "since you should have this TID - {} store in HTID golden model".format(act_pkt.rec_tid)
                VAL_UTDB_ERROR(time=act_pkt.rec_time, msg=err_msg)

    def get_exp_pkt_class(self, pkt):
        if type(pkt) is ccf_idi_record_info:
            if pkt.rec_idi_interface == "C2U REQ":
                return IDI_C2U_REQ_pkt()
            elif pkt.rec_idi_interface == "C2U RSP":
                return IDI_C2U_RSP_pkt()
            elif pkt.rec_idi_interface == "C2U DATA":
                return IDI_C2U_DATA_pkt()
            elif pkt.rec_idi_interface == "U2C REQ":
                return IDI_U2C_REQ_pkt()
            elif pkt.rec_idi_interface == "U2C RSP":
                return IDI_U2C_RSP_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_idi_interface == "U2C DATA":
                return IDI_U2C_DATA_pkt()
            else:
                VAL_UTDB_ERROR(time=0, msg="(transition - get_exp_pkt_class):We didn't found any match to any known IDI pkt type.")

        elif type(pkt) is ccf_cfi_record_info:
            if pkt.rec_opcode in self.UPI_C_REQ_SA_pkt_opcode_list:
                return UPI_C_REQ_SA_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_DATA_SA_pkt_opcode_list:
                return UPI_C_DATA_SA_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_REQ_SA_S_pkt_opcode_list:
                return UPI_C_REQ_SA_S_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_REQ_SA_SL_pkt_opcode_list:
                return UPI_C_REQ_SA_SL_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_RSP_SR_H_pkt_opcode_list:
                return UPI_C_RSP_SR_H_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_DATA_SR_HD_pkt_opcode_list:
                return UPI_C_DATA_SR_HD_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_RSP_SR_U_pkt_opcode_list:
                return UPI_C_RSP_SR_U_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_RSP_SR_O_pkt_opcode_list:
                return UPI_C_RSP_SR_O_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_DATA_SR_CD_pkt_opcode_list:
                return UPI_C_DATA_SR_CD_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_DATA_SA_D_pkt_opcode_list:
                return UPI_C_DATA_SA_D_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.UPI_C_DATA_PW_pkt_opcode_list:
                return UPI_C_DATA_PW_pkt(opcode=pkt.rec_opcode)
            elif pkt.rec_opcode in self.CXM_DATA_int_64B_DRS_pkt_opcode_list:
                return CXM_DATA_int_64B_DRS_pkt(opcode=pkt.rec_opcode)
            else:
                VAL_UTDB_ERROR(time=0, msg="(transition - get_exp_pkt_class):We didn't expect this pkt opcode-{}, please check your code.".format(pkt.rec_opcode))
        elif type(pkt) == ccf_cbo_record_info:
            return CBO_CPIPE_RECORD()
        else:
            VAL_UTDB_ERROR(time=0, msg="(transition - get_exp_pkt_class): We didn't expect this pkt type, please check your code.")

    def trace_pkt_force_apply(self, actual_pkt: ccf_cfi_record_info):
        block_name = "santa{}_regs".format(actual_pkt.get_santa_id())
        direction = "TX" if actual_pkt.is_c2u_dir() else "RX"
        cfi_interface = actual_pkt.get_cfi_interface()
        return (self.ccf_ral_agent.read_reg_field(block_name, "CFI_{}_{}_DCD_CFG".format(direction,cfi_interface), "FORCE_TRACE", actual_pkt.rec_time) == 1)

    def do_expected_fixes_for_trace_pkt(self, flow: ccf_flow, actual_pkt):
        if self.trace_pkt_force_apply(actual_pkt) and actual_pkt.is_cfi_c2u_dir():
            return "1"
        elif self.si.dfd_en == 0:
            return "DoNotCheck"#If dfd_en register value is 0 we are not going to check trace_pkt
        elif self.si.cdtf_en == 1 :
            return "DoNotCheck" #when CDTF is enabled, overide is randomized - it is checked in dedicated checker
        elif actual_pkt.is_cfi_u2c_dir():
            return "DoNotCheck" #Need to fix with the right condition for CXM and fix U2C UPI/CXM BFM behavior - we don't want to invest time in it now - fix in PTL
        elif (actual_pkt.chunk == "0" and actual_pkt.is_upi_rd_data()) or (
                actual_pkt.eop == "0" and (actual_pkt.is_upi_snp_rsp_wb() or actual_pkt.is_upi_wb() or actual_pkt.is_upi_c_reqfwdcnflt())):
            return "0"
        else:
            exp_trace_pkt = None
            for trans in flow.flow_progress:
                if type(trans) is ccf_cfi_record_info:
                    if (exp_trace_pkt is None) or \
                            ((trans.rec_time <= actual_pkt.rec_time) and ((exp_trace_pkt == "0") and (trans.trace_pkt == "1"))):
                        exp_trace_pkt = trans.trace_pkt
            return exp_trace_pkt

    def do_expected_fixes_for_eop(self, flow_key, actual_pkt):
        if SANTA_golden_models.is_exist_in_EOP_golden(flow_key):
            exp_eop = SANTA_golden_models.get_EOP_by_flow_key(flow_key)
            SANTA_golden_models.delete_entry_in_EOP_golden_if_exist(flow_key)
            return exp_eop
        else:
            SANTA_golden_models.add_entry_to_EOP_golden(flow_key, "1")
            return "0" #This is the first Data pump

    def do_expecetd_fixes_per_actual_trans(self, flow: ccf_flow, exp_pkt, actual_pkt):
        if type(exp_pkt) == IDI_U2C_REQ_pkt:
            exp_pkt.fix_exp_according_to_current_snoop_opcode(flow, actual_pkt)

        if (type(actual_pkt) is ccf_cfi_record_info):
            exp_pkt.trace_pkt = self.do_expected_fixes_for_trace_pkt(flow=flow, actual_pkt=actual_pkt)
            if "DATA" in actual_pkt.interface:
                exp_pkt.eop = self.do_expected_fixes_for_eop(flow_key=flow.flow_key, actual_pkt=actual_pkt)

        return exp_pkt

    def compare_trans(self, actual_trans, exp_trans):
        objects_ptr_names = ["hash_calc_agent", "clos_chk", "pre_calc"]
        err_msg = ""
        for attr, exp_value in vars(exp_trans).items():
            if (exp_value is not "DoNotCheck") and (attr not in objects_ptr_names) and getattr(actual_trans, attr) != exp_value:
                err_msg += "Mismatch at field: {}, Actual: {} Expected: {}\n".format(attr, getattr(actual_trans, attr), exp_value)
        return err_msg

    def transition_check(self, flow, trans_list):
        is_trans_cfi_type = (type(trans_list[0]) == ccf_cfi_record_info)

        exp_pkt = self.get_exp_pkt_class(trans_list[0])
        if is_trans_cfi_type:
            self.alloc_RTID_and_HTID_in_golden_model_if_first_time_use(flow=flow, exp_pkt=exp_pkt, actual_pkt=trans_list[0])
        exp_pkt.set_exp_data_according_to_flow(flow)

        for actual_pkt in trans_list:
            if is_trans_cfi_type:
                self.dec_RTID_and_HTID_counters(flow.flow_key, actual_pkt, exp_pkt)

            exp_pkt = self.do_expecetd_fixes_per_actual_trans(flow, exp_pkt, actual_pkt)

            err_msg = self.compare_trans(actual_trans=actual_pkt, exp_trans=exp_pkt)

            if err_msg != "":
                full_err_msg = "(transition_check): Transition checker fail\n" \
                               "\nURI - {}" \
                               "\nTransaction exp type - {}\n" \
                               "{}".format(actual_pkt.rec_tid, exp_pkt.__class__.__name__, err_msg)
                VAL_UTDB_ERROR(time=actual_pkt.rec_time, msg=full_err_msg)

            actual_pkt.checked_by_transition_checker = True
