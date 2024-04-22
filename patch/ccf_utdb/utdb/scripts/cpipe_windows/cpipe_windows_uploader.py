#!/usr/intel/bin/python3.6.3a
from systempy import *
from uvm import *
from jem_py_rt import *
from libtlmgen_py import *
from val_utdb_bint import bint
import argparse
import sys, os, re
import shutil

sys.path.append("/p/hdk/rtl/cad/x86-64_linux44/dt/utdb/22.09_shOpt64/lib")
sys.path.append("/p/hdk/rtl/cad/x86-64_linux44/dt/utdb/22.09_shOpt64/scripts/utdb/coverage")
sys.path.append("/p/hdk/rtl/cad/x86-64_linux44/dt/utdb/22.09_shOpt64/utdbpythonwrapper")
sys.path.append("/p/hdk/rtl/cad/x86-64_linux44/dt/utdb/22.09_shOpt64/table_writer")

from uploader import *
from UTDB import *

parser = argparse.ArgumentParser(description='jem python replay bins to trackers')
parser.add_argument("--logdb", "-ld", help="LOGDB output directory")
parser.add_argument("--text", "-txt", help="table tracker output filename")
parser.add_argument("--source", "-s", help="partial path to recorded bins")
args = parser.parse_args(cmd_line_args)

print("command:\n", " ".join(sys.argv))

logdb = args.logdb
text = args.text

logdb_dir_path = args.logdb.split('/')[:-1]
logdb_tmp_dir_path = [*args.logdb.split('/')[:-1], 'tmp']
logdb_name = args.logdb.split('/')[-1]
dir = os.path.join('/', *logdb_tmp_dir_path)
if not os.path.isdir(dir):
    os.mkdir(dir)
else:
    shutil.rmtree(dir)
    os.mkdir(dir)

tmp_logdb = os.path.join('/', *[*logdb_tmp_dir_path, logdb_name])


def uri2str(uri):
    temp_src = re.sub('URI_', '', uri.Source.Name().upper())
    if (uri.Instance.IsUnknown()):
        return "XXX"
    inst = uri.Instance.ToUint()
    cntr = uri.Cntr.ToUint()
    if temp_src == 'NA':
        return temp_src
    elif any([suburi in temp_src for suburi in ["COR", "IAC", "ACF", "ICE", "ATOM"]]):
        thread = 0 if uri.Thread.IsUnknown() else uri.Thread.ToUint()
        return "%s_%XT%X_%X" % (temp_src, inst, thread, cntr)
    else:
        return "%s_%03X_%X" % (temp_src, inst, cntr)


writer = Writer(tmp_logdb)
schema = table_schema()

schema.add_record_schema([
    field(name="TIME", type=FieldType.UINT, null_value='-', format="{0:<13}"),
    field(name="UNIT", null_value='-'),
    field(name='TID', null_value='-'),
    field(name='LID', null_value='-'),
    field(name='PID', null_value='-'),
    field(name='REQ', null_value='-'),
    field(name='ADDRESS', null_value='-'),
    field(name='TORID', null_value='-'),
    field(name='TOR_OCCUP', type=FieldType.UINT, null_value='-'),
    field(name='MONHIT', null_value='-'),
    field(name='MISC', null_value='-'),
    field(name='HALF', null_value='-'),
    field(name='EVENT', null_value='-')
])

writer.init(schema)

class PARAMETERS:
    SET_LSB = 6
    SET_MSB = 17
    TAG_LSB = 18
    TAG_MSB = 40
    MKTME_LSB = 41
    MKTME_MSB = 51
    CBO_NUM_TOR_ENTRY = 40
    CBO_MAX_LOGICAL_TOR_ENTRIES = 64
    CBO_NUM_TOR_IFA_ENTRY = 36
    MAX_NUM_OF_CBO = 8
    MAX_NUM_OF_HALFS = 2
    #Pipe_stages
    PIPE_U114H=0
    PIPE_U115H=1
    PIPE_U116H=2
    PIPE_U117H=3
    PIPE_U118H=4

##################################################
## TOR IFA REF model
##################################################

class TorIfaAllocationRefModel:
    AllocRefModel = dict()

    @staticmethod
    def init_ref_model():
        for cbo_id in range(0, PARAMETERS.MAX_NUM_OF_CBO):
            TorIfaAllocationRefModel.AllocRefModel[str(cbo_id)] = dict()
            for half_id in range(0, PARAMETERS.MAX_NUM_OF_HALFS):
                TorIfaAllocationRefModel.AllocRefModel[str(cbo_id)][str(half_id)] = dict()
                for tor_ifa_id in range(0,int(PARAMETERS.CBO_NUM_TOR_IFA_ENTRY/2)):
                    TorIfaAllocationRefModel.AllocRefModel[str(cbo_id)][str(half_id)][str(tor_ifa_id)] = "0"

    @staticmethod
    def update_ref_model(cbo_id, half_id, tor_ifa_id, new_value):
        TorIfaAllocationRefModel.AllocRefModel[cbo_id][half_id][tor_ifa_id] = new_value

    @staticmethod
    def is_entry_changed(cbo_id, half_id, tor_ifa_id, new_value):
        return (TorIfaAllocationRefModel.AllocRefModel[cbo_id][half_id][tor_ifa_id] != new_value)

##########################
## Victim Address per URI
##########################
class VictimAddressPerLidURI:
    VictimAddress = dict()

    @staticmethod
    def is_uri_lid_exist(uri_lid):
        return uri_lid in VictimAddressPerLidURI.VictimAddress.keys()

    @staticmethod
    def add_new_address_if_not_exist(uri_lid, address):
        if not VictimAddressPerLidURI.is_uri_lid_exist(uri_lid):
            VictimAddressPerLidURI.VictimAddress[uri_lid] = address

    @staticmethod
    def get_victim_address(uri_lid):
        if VictimAddressPerLidURI.is_uri_lid_exist(uri_lid):
            return VictimAddressPerLidURI.VictimAddress[uri_lid]
        else:
            return None

###########################################
## Addressless transaction Address per URI
###########################################
class AddressForAddresslessPerUri:
    AddresslessAddr = dict()
    AddresslessURIList = list()

    @staticmethod
    def is_addressless_opcode(opcode):
        addressless_opcodes = ["Invd", "WbInvd", "LLCWB"]
        return any([True for m_opcode in addressless_opcodes if m_opcode.lower().strip() == opcode.lower().strip()])

    @staticmethod
    def is_uri_exist(uri):
        return uri in AddressForAddresslessPerUri.AddresslessAddr.keys()

    @staticmethod
    def add_new_address_if_not_exist(uri, address):
        if not AddressForAddresslessPerUri.is_uri_exist(uri):
            AddressForAddresslessPerUri.AddresslessAddr[uri] = address

    @staticmethod
    def edit_or_add_new_address(uri, address):
        AddressForAddresslessPerUri.AddresslessAddr[uri] = address

    @staticmethod
    def get_addressless_address(uri):
        if AddressForAddresslessPerUri.is_uri_exist(uri):
            return AddressForAddresslessPerUri.AddresslessAddr[uri]
        else:
            return None

    @staticmethod
    def add_addressless_uri_to_list(uri):
        AddressForAddresslessPerUri.AddresslessURIList.append(uri)

    @staticmethod
    def is_uri_belong_to_addressless_flow(uri):
        return uri in AddressForAddresslessPerUri.AddresslessURIList

########################################################################################################
## IFA mktme per URI
## TOR IFA will not hold in the design the MKTME bits we need it to add them back only for the checkers
########################################################################################################

class IfaMktmePerURI:
    IfaMktmeBits = dict()

    @staticmethod
    def is_uri_exist(uri):
        return uri in IfaMktmePerURI.IfaMktmeBits.keys()

    @staticmethod
    def add_new_address_if_not_exist(uri, address):
        if not IfaMktmePerURI.is_uri_exist(uri):
            IfaMktmePerURI.IfaMktmeBits[uri] = address

    #TODO: we need to not override all the address but override only the mktme bits.
    @staticmethod
    def get_address_with_mktme(uri):
        if IfaMktmePerURI.is_uri_exist(uri):
            return IfaMktmePerURI.IfaMktmeBits[uri]
        else:
            return None

########################################################################################################
## Original Req opcode keeper
########################################################################################################

class OrigReqOpcodeKeeperPerURI:
    OrigReqOpcode = dict()

    @staticmethod
    def is_uri_exist(uri):
        return uri in OrigReqOpcodeKeeperPerURI.OrigReqOpcode.keys()

    @staticmethod
    def add_new_opcode_if_not_exist(uri, opcode):
        if not OrigReqOpcodeKeeperPerURI.is_uri_exist(uri):
            OrigReqOpcodeKeeperPerURI.OrigReqOpcode[uri] = opcode

    @staticmethod
    def get_orig_req_opcode(uri):
        if OrigReqOpcodeKeeperPerURI.is_uri_exist(uri):
            return OrigReqOpcodeKeeperPerURI.OrigReqOpcode[uri]
        else:
            return None

#########################
## Main uploader class
#########################

class Uploader(JemMultiPortMonitor):

    def __init__(self, name, parent=None):
        super().__init__(name, parent, all_sources_must_exist=True)
        self.write_row_to_log_list = []
        TorIfaAllocationRefModel.init_ref_model()

    def build_phase(self, phase):
        self.add_source_to_cb_mapping({
            "*half0_tlm.cpipe_windows_col.req_p*": self.half0_cpipe_windows_req_p,
            "*half1_tlm.cpipe_windows_col.req_p*": self.half1_cpipe_windows_req_p,
            "*half0_tlm.tor_ifa_windows_col.req_p*": self.half0_tor_ifa_windows_req_p,
            "*half1_tlm.tor_ifa_windows_col.req_p*": self.half1_tor_ifa_windows_req_p,
            "*cpipe_event_tlm_col.event_p*": self.cpipe_events_p,
            "*cpipe_event_tlm_col.allocation_p*": self.allocation_events_p,
            "*cpipe_event_tlm_col.vic_alloc_p*": self.victim_allocation_events_p,
            "*cpipe_col.dealloc_p*": self.deallocation_events_p,
        })


    def write_log(self, row):
        self.write_row_to_log_list.append(row.copy())

    def get_unit_str(self, unit):
        return "CPIPE_{}".format(unit)

    def extract_hex_value_from_sv_logic_type(self, sv_logic_value):
        print(sv_logic_value)
        return bint(int(str(sv_logic_value).split('h')[1].strip("}"), 16))

    def extract_opcode_from_sv_wrapper_type(self, sv_wrapper_value):
        return str(sv_wrapper_value).split("{")[0]

    def extract_address_from_sv_logic_type(self, sv_logic_value):
        return hex(int(self.extract_hex_value_from_sv_logic_type(sv_logic_value)))[2:].zfill(15)

    def get_list_of_tor_entry_with_change_in_allowsnoop_or_promotion(self, pkt):
        tor_entry_list = []
        promotion_window_entry_list = list()
        allow_snoop_entry_list = list()
        for tor_id in range(0, int(PARAMETERS.CBO_NUM_TOR_ENTRY/2)):
            if (str(pkt.AllowSnoop_valid[tor_id]) == "1") or (str(pkt.Promotion_window_valid[tor_id]) == "1"):

                #pkt.AllowSnoop[tor_id]
                if (str(pkt.AllowSnoop_valid[tor_id]) == "1"):
                    allow_snoop_entry_list.append(tor_id)

                #pkt.Promotion_window[tor_id]
                if (str(pkt.Promotion_window_valid[tor_id]) == "1"):
                    promotion_window_entry_list.append(tor_id)

        return allow_snoop_entry_list, promotion_window_entry_list

    def get_list_of_tor_ifa_entry_with_allocation_change(self, pkt, half_id):
        tor_ifa_entry_list = dict()

        for tor_ifa_id in range(0, int(PARAMETERS.CBO_NUM_TOR_IFA_ENTRY/2)):
                if (TorIfaAllocationRefModel.is_entry_changed(str(pkt.cbo_id), str(half_id), str(tor_ifa_id), str(pkt.IfaValidEntryUnnnH[tor_ifa_id]))):
                    tor_ifa_entry_list[tor_ifa_id] = str(pkt.IfaValidEntryUnnnH[tor_ifa_id])

        return tor_ifa_entry_list

    def get_list_of_tor_entry_that_doing_deallocation(self, pkt):
        tor_dealloc_entry_id_list = list()
        for tor_id in range(0, int(PARAMETERS.CBO_MAX_LOGICAL_TOR_ENTRIES)):
            if str(pkt.TOR_DeallocEntry[tor_id]) == "1":
                tor_dealloc_entry_id_list.append(tor_id)

        return tor_dealloc_entry_id_list


    ## TLM write support functions
    ###############################
    def cpipe_windows_req_p(self, pkt, half):
        line = {}
        allow_snoop_entry_list, promotion_window_entry_list = self.get_list_of_tor_entry_with_change_in_allowsnoop_or_promotion(pkt)

        tor_entry_list = allow_snoop_entry_list + promotion_window_entry_list

        for tor_id in tor_entry_list:
            line['TIME'] = get_sim_time()
            line['UNIT'] = self.get_unit_str(pkt.cbo_id)
            line['TID'] = uri2str(pkt.uri_inst[tor_id].TID)
            line['LID'] = uri2str(pkt.uri_inst[tor_id].LID)
            line['PID'] = uri2str(pkt.uri_inst[tor_id].PID)
            line['REQ'] = "-"
            line['ADDRESS'] = self.extract_address_from_sv_logic_type(pkt.Address_with_mktme[tor_id])
            line['TORID'] = str(pkt.TorID[tor_id])
            line['TOR_OCCUP'] = 0  # TODO: fix it
            line['MONHIT'] = "-"
            if tor_id in allow_snoop_entry_list:
                line['MISC'] = "AllowSnoop={}".format(pkt.AllowSnoop[tor_id])
                allow_snoop_entry_list.remove(tor_id)
            elif tor_id in promotion_window_entry_list:
                line['MISC'] = "Promotion_window={}".format(pkt.Promotion_window[tor_id])
                promotion_window_entry_list.remove(tor_id)
            line['HALF'] = str(half)
            line['EVENT'] = "-"

            self.write_log(line)

    def tor_ifa_windows_req_p(self, pkt, half):
        line = {}
        tor_entry_dict = self.get_list_of_tor_ifa_entry_with_allocation_change(pkt, half)

        for tor_id, tor_ifa_allocation in tor_entry_dict.items():
            line['TIME'] = get_sim_time()
            line['UNIT'] = self.get_unit_str(pkt.cbo_id)
            line['TID'] = uri2str(pkt.uri_inst[tor_id].TID)
            line['LID'] = uri2str(pkt.uri_inst[tor_id].LID)
            line['PID'] = uri2str(pkt.uri_inst[tor_id].PID)
            line['REQ'] = "-"
            line['ADDRESS'] = self.extract_address_from_sv_logic_type(pkt.Address[tor_id])
            line['TORID'] = str(tor_id)
            line['TOR_OCCUP'] = 0  # TODO: fix it
            line['MONHIT'] = "-"
            if tor_ifa_allocation is not None:
                line['MISC'] = "TorIfaAllocate={}".format(tor_ifa_allocation)
                if tor_ifa_allocation == "1":
                    TorIfaAllocationRefModel.update_ref_model(cbo_id=str(pkt.cbo_id), half_id=str(half), tor_ifa_id=str(tor_id), new_value="1")
                elif tor_ifa_allocation == "0":
                    TorIfaAllocationRefModel.update_ref_model(cbo_id=str(pkt.cbo_id), half_id=str(half), tor_ifa_id=str(tor_id), new_value="0")
            line['HALF'] = str(half)
            line['EVENT'] = "-"

            self.write_log(line)

            #if we did IFA allocation we are already have the full and right address
            if (AddressForAddresslessPerUri.is_uri_belong_to_addressless_flow(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']))):
                AddressForAddresslessPerUri.edit_or_add_new_address(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']), address=line['ADDRESS'])  # TODO: this is not always correct in case of addressless with initial state of LLC_I


    ###########################
    ## TLM write functions
    ###########################
    def half0_cpipe_windows_req_p(self, source, pkt):
        self.cpipe_windows_req_p(pkt=pkt, half=0)

    def half1_cpipe_windows_req_p(self, source, pkt):
        self.cpipe_windows_req_p(pkt=pkt, half=1)

    def half0_tor_ifa_windows_req_p(self, source, pkt):
        self.tor_ifa_windows_req_p(pkt=pkt, half=0)

    def half1_tor_ifa_windows_req_p(self, source, pkt):
        self.tor_ifa_windows_req_p(pkt=pkt, half=1)

    def cpipe_events_p(self, source, pkt):
        line = {}
        reject_event = ""

        line['TIME'] = get_sim_time()
        line['UNIT'] = self.get_unit_str(pkt.cbo_id)
        line['TID'] = uri2str(pkt.uri_inst[PARAMETERS.PIPE_U115H].TID)
        line['LID'] = uri2str(pkt.uri_inst[PARAMETERS.PIPE_U115H].LID)
        line['PID'] = uri2str(pkt.uri_inst[PARAMETERS.PIPE_U115H].PID)
        line['REQ'] = self.extract_opcode_from_sv_wrapper_type(pkt.RspCom[PARAMETERS.PIPE_U115H])
        line['ADDRESS'] = self.extract_address_from_sv_logic_type(pkt.pipe_address[PARAMETERS.PIPE_U115H])
        line['TORID'] = str(pkt.TorID[PARAMETERS.PIPE_U115H])
        line['TOR_OCCUP'] = 0  # TODO: fix it
        line['MONHIT'] = str(pkt.MonHit[PARAMETERS.PIPE_U115H])
        line['MISC'] = "-"
        line['HALF'] = "-" #TODO: need to add ?

        if str(pkt.Promoting[PARAMETERS.PIPE_U115H]) == '1':
            line['EVENT'] = "Promoting={}".format(str(pkt.Promoting[PARAMETERS.PIPE_U115H]))

            self.write_log(line)

        if str(pkt.EarlyRejectReasonUnnnH[PARAMETERS.PIPE_U115H].RejectDuePaMatch) == "1":
            reject_event = reject_event + "RejectDuePaMatch "
        if str(pkt.EarlyRejectReasonUnnnH[PARAMETERS.PIPE_U115H].RejectDueIRQSetMatchBlocked) == "1":
            reject_event = reject_event + "RejectDueIRQSetMatchBlocked"

        if reject_event != "":
            line['EVENT'] = reject_event
            self.write_log(line)


        #TODO: need to add rejects to this function as well

    def allocation_events_p(self, source, pkt):
        line = {}
        if str(pkt.Allocation[PARAMETERS.PIPE_U116H]) == '1':
            line['TIME'] = get_sim_time()
            line['UNIT'] = self.get_unit_str(pkt.cbo_id)
            line['TID'] = uri2str(pkt.uri_inst[PARAMETERS.PIPE_U116H].TID)
            line['LID'] = uri2str(pkt.uri_inst[PARAMETERS.PIPE_U116H].LID)
            line['PID'] = uri2str(pkt.uri_inst[PARAMETERS.PIPE_U116H].PID)
            line['REQ'] = self.extract_opcode_from_sv_wrapper_type(pkt.RspCom[PARAMETERS.PIPE_U116H])
            line['ADDRESS'] = self.extract_address_from_sv_logic_type(pkt.pipe_address[PARAMETERS.PIPE_U116H])
            line['TORID'] = str(pkt.TorID[PARAMETERS.PIPE_U116H])
            line['TOR_OCCUP'] = int(str(pkt.TOR_occupancy[PARAMETERS.PIPE_U116H]))
            line['MONHIT'] = str(pkt.MonHit[PARAMETERS.PIPE_U116H])
            line['MISC'] = "Allocation={}".format(pkt.Allocation[PARAMETERS.PIPE_U116H])
            line['HALF'] = "-" #TODO: need to add ?
            line['EVENT'] = "-"

            if(AddressForAddresslessPerUri.is_addressless_opcode(line['REQ'])):
                AddressForAddresslessPerUri.add_new_address_if_not_exist(uri="{}_{}_{}".format(line['TID'],line['LID'],line['PID']), address=line['ADDRESS']) #TODO: this is not always correct in case of addressless with initial state of LLC_I
                AddressForAddresslessPerUri.add_addressless_uri_to_list(uri="{}_{}_{}".format(line['TID'],line['LID'],line['PID']))

            OrigReqOpcodeKeeperPerURI.add_new_opcode_if_not_exist(uri="{}_{}_{}".format(line['TID'],line['LID'],line['PID']), opcode=line['REQ'])
            self.write_log(line)

    def victim_allocation_events_p(self, source, pkt):
        line = {}
        if str(pkt.allocation_U117H) == '1':
            line['TIME'] = get_sim_time()
            line['UNIT'] = self.get_unit_str(pkt.cbo_id)
            line['TID'] = uri2str(pkt.uri_inst.TID)
            line['LID'] = uri2str(pkt.uri_inst.LID)
            line['PID'] = uri2str(pkt.uri_inst.PID)
            line['REQ'] = "Victim"
            line['ADDRESS'] = "-" #TODO: need to fill it at the end. since Victim have only SET at his first pass
            line['TORID'] = str(pkt.TorID_U117H)
            line['TOR_OCCUP'] = int(str(pkt.TOR_occupancy_U115H))
            line['MONHIT'] = "-" #TODO: do we need it in victim?
            line['MISC'] = "Allocation={}".format(str(pkt.allocation_U117H))
            line['HALF'] = str(pkt.Half_U117H)
            line['EVENT'] = "-"

            OrigReqOpcodeKeeperPerURI.add_new_opcode_if_not_exist(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']), opcode=line['REQ'])

            self.write_log(line)


    def deallocation_events_p(self, source, pkt):
        line = {}
        tor_dealloc_entry_id_list = self.get_list_of_tor_entry_that_doing_deallocation(pkt)

        for tor_id in tor_dealloc_entry_id_list:
            line['TIME'] = get_sim_time()
            line['UNIT'] = self.get_unit_str(pkt.cbo_id)
            line['TID'] = uri2str(pkt.tor_uri_inst[tor_id].TID)
            line['LID'] = uri2str(pkt.tor_uri_inst[tor_id].LID)
            line['PID'] = uri2str(pkt.tor_uri_inst[tor_id].PID)
            line['REQ'] = "-" #TODO: need to take opcode from some list using URI
            line['ADDRESS'] = self.extract_address_from_sv_logic_type(pkt.dealloc_address[tor_id])
            line['TORID'] = str(tor_id)
            line['TOR_OCCUP'] = 0 #TODO: do we need it
            line['MONHIT'] = "-"
            line['MISC'] = "Deallocation=1"
            line['HALF'] = "-"  # TODO: need to add ?
            line['EVENT'] = "-"

            if "_VIC_" in line['LID']:
                VictimAddressPerLidURI.add_new_address_if_not_exist(line['LID'], line['ADDRESS'])

            IfaMktmePerURI.add_new_address_if_not_exist(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']), address=line['ADDRESS'])

            self.write_log(line)

    #############################
    ## Post replay tasks
    ############################
    def fill_missing_victim_address(self, write_row_to_log_list):
        for line in write_row_to_log_list:
            if ("_VIC_" in line['LID']) and ("-" in line['ADDRESS']):
                line['ADDRESS'] = VictimAddressPerLidURI.get_victim_address(line['LID'])
        return write_row_to_log_list

    def add_mktme_bits_to_ifa_entries(self, write_row_to_log_list):
        for line in write_row_to_log_list:
            if ("TorIfaAllocate" in line['MISC']):
                line['ADDRESS'] = IfaMktmePerURI.get_address_with_mktme(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']))
        return write_row_to_log_list

    def add_req_opcode_where_needed(self, write_row_to_log_list):
        for line in write_row_to_log_list:
            if ("-" in line['REQ']):
                line['REQ'] = OrigReqOpcodeKeeperPerURI.get_orig_req_opcode(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']))
        return write_row_to_log_list

    def edit_addressless_transaction_address(self, write_row_to_log_list):
        for line in write_row_to_log_list:
            if AddressForAddresslessPerUri.is_uri_exist(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID'])):
                line['ADDRESS'] = AddressForAddresslessPerUri.get_addressless_address(uri="{}_{}_{}".format(line['TID'], line['LID'], line['PID']))
        return write_row_to_log_list

    def pre_log_write_tasks(self, write_row_to_log_list):
        write_row_to_log_list = self.fill_missing_victim_address(write_row_to_log_list)
        write_row_to_log_list = self.add_mktme_bits_to_ifa_entries(write_row_to_log_list)
        write_row_to_log_list = self.add_req_opcode_where_needed(write_row_to_log_list)
        write_row_to_log_list = self.edit_addressless_transaction_address(write_row_to_log_list)
        return write_row_to_log_list

    #In final phase we will write all the lines we kept in the log.
    def final_phase(self, phase):
        sorted_write_row_to_log_list = sorted(self.write_row_to_log_list, key=lambda d: d['TIME'])
        sorted_write_row_to_log_list= self.pre_log_write_tasks(sorted_write_row_to_log_list)
        for row in sorted_write_row_to_log_list:
            writer.write_row(row)

        writer.close()
        writer_trace = connect(tmp_logdb)
        writer_query = from_(writer_trace)
        dump(writer_query, output=f'psv:{text}')
