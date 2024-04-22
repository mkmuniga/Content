from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_common_base import memory_data_entry, tmp_data_time_struct, ccf_cfi_record_info, \
    ccf_ufi_record_info
from agents.ccf_agent.ccf_base_agent.ccf_base_agent import ccf_base_agent
from agents.ccf_data_bases.ccf_addressless_db import ccf_addressless_db
from val_utdb_base_components import EOT
from val_utdb_report import VAL_UTDB_ERROR

#This class is intened for collecting data from U2C_DATA/ C2U_DATA/ U2C_RSP and C2U_RSP. partially also C2U_REQ for getting len and self_snoop indications

class ccf_address_db_agent(ccf_base_agent):
    def __init__(self):
        self.configure()
        self.special_address_db = ccf_addressless_db.get_pointer()
        self.tmp_idi_data = {}
        self.tmp_cfi_data = {}
        self.tmp_ufi_data = {}

    def run(self):
        for uri in self.ccf_flows.keys():
            flow = self.ccf_flows[uri]
            if (flow.opcode not in CCF_FLOW_UTILS.idi_addressless_opcodes) or (flow.flow_hit_mmio_lt() and "PORT" in flow.opcode):
                for idx in range(len(flow.flow_progress)):
                    self.update_address_data_db(flow, idx)

    def update_address_data_db(self, flow, idx):
        if flow.flow_progress[idx].is_record_belong_to_interface("IDI"):
            self.handle_idi_item(flow, idx)
        elif flow.flow_progress[idx].is_record_belong_to_interface("LLC"):
            self.handle_llc_item(flow.flow_progress[idx])
        elif flow.flow_progress[idx].is_record_belong_to_interface("CFI"):
            self.handle_cfi_item(flow, idx)
        elif flow.flow_progress[idx].is_record_belong_to_interface("UFI"):
            self.handle_ufi_item(flow, idx)

    def handle_idi_item(self, flow, idx):
        ignore_c2u_data = (not flow.flow_is_hom()) and flow.flow_progress[idx].is_c2u_data_if() and flow.final_snp_rsp == "RspIFwdMO" and ("CCF_SNP" in flow.flow_progress[idx].rec_lid)
        ignore_c2u_rsp = (not flow.flow_is_hom()) and flow.flow_progress[idx].is_c2u_rsp_if() and flow.final_snp_rsp == "RspIFwdMO"
        
        if (flow.flow_progress[idx].is_u2c_data_if() or (flow.flow_progress[idx].is_c2u_data_if() and not ignore_c2u_data)) and flow.sad_results != "CRABABORT":
            self.create_one_idi_data_packet(flow.flow_progress[idx])
            if self.is_idi_data_entry_ready_for_update(flow.flow_progress[idx]):
                self.update_idi_item(flow, idx)
        elif (flow.flow_progress[idx].is_u2c_rsp_if() and flow.flow_progress[idx].is_go()) or (flow.flow_progress[idx].is_c2u_rsp_if() and not ignore_c2u_rsp):
            self.update_idi_state(flow, idx)



    def update_idi_item(self, flow, idx):
        entry = memory_data_entry()
        entry.tid = flow.flow_progress[idx].rec_tid
        entry.data = self.tmp_idi_data[flow.flow_progress[idx].rec_tid].data
        entry.byteen = self.tmp_idi_data[flow.flow_progress[idx].rec_tid].byteen
        entry.cache_type = "MLC_" + str(flow.flow_progress[idx].rec_logic_id)
        entry.access_type = self.get_idi_access_type(flow.flow_progress[idx])
        entry.time = self.tmp_idi_data[flow.flow_progress[idx].rec_tid].time
        #in special addresses in IDI, should "fix" the address to be aligned with LLC and CFI
        if flow.opcode in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes_on_idi:
            address = CCF_FLOW_UTILS.get_idi_aligned_address(self.special_address_db.get_real_address_by_uri(flow.uri["TID"]))
        else:
            address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[idx].address)
        self.update_mem_db(address, entry)
        self.tmp_idi_data.pop(flow.flow_progress[idx].rec_tid)

    def update_idi_state(self, flow, idx):
        if not flow.is_cfi_NcMsgS_flow_origin():
            entry = memory_data_entry()
            entry.tid = flow.flow_progress[idx].rec_tid
            entry.cache_type = "MLC_" + str(flow.flow_progress[idx].rec_logic_id)
            entry.access_type = self.get_idi_access_type(flow.flow_progress[idx])
            entry.state = self.get_state(flow.flow_progress[idx])
            entry.time = int(flow.flow_progress[idx].rec_time)
            if flow.opcode in CCF_FLOW_UTILS.c2u_special_addresses_req_opcodes_on_idi and ("CBB_SNP" not in flow.flow_progress[idx].rec_lid) and entry.state != "I":#no meaning to l2c_tag when llc_I
                address = CCF_FLOW_UTILS.get_idi_aligned_address(self.special_address_db.get_real_address_by_uri(flow.uri["TID"]))
            else:
                address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[idx].address)
            self.update_mem_db(address, entry)

    def get_state(self, idi_item):
        if idi_item.is_c2u_rsp_if() and (not idi_item.is_c2u_lock_or_unlock_rsp()):
            return self.extract_state_options_from_rsps(idi_item)
        elif idi_item.is_u2c_rsp_if() and idi_item.is_go():
            return self.extract_state_options_from_go(idi_item.rec_go_type)

    def extract_state_options_from_rsps(self, idi_item):
        if idi_item.rec_opcode == "RspSFwdMO":
            return "M->S"
        elif idi_item.rec_opcode == "RspIFwdMO":
            return "M->I"
        elif idi_item.rec_opcode == "RspIFwdFE":
            return "E->I"
        elif idi_item.rec_opcode == "RspSFwdFE":
            return "E->S"
        elif idi_item.rec_opcode == "RspEFFwdMO":
            return "M->E"
        elif idi_item.rec_opcode in ["RspIHitI", "RspFlushed"]:
            return "I->I"
        elif idi_item.rec_opcode == "RspIHitFSE":
            return "F/S/E->I"
        elif idi_item.rec_opcode == "RspSHitFSE":
            return "F/S/E->S"
        elif idi_item.rec_opcode == "RspSI":
            return "S/I"
        elif idi_item.rec_opcode in ["RspVFwdV", "RspVHitV", "RspNack"]:
            return "same_as_before"
        else:
            VAL_UTDB_ERROR(time=idi_item.rec_time, msg="didn't found a case for opcode " + idi_item.rec_opcode + " for URI: " + idi_item.rec_lid)

    def extract_state_options_from_go(self, go_type):
        if "GO_I" in go_type:
            return "I"
        elif "GO_S" in go_type:
            return "S/I"
        elif "GO_F" in go_type:
            return "F/S/I"
        elif "GO_E" in go_type:
            return "E/M/I"
        elif "GO_M" in go_type:
            return "M"

    def get_idi_access_type(self, idi_item):
        if idi_item.is_c2u_data_if():
            if "SNP" in idi_item.rec_lid:
                return "C2U_DATA_RSP"
            elif idi_item.rec_bogus == "1":
                return "C2U_BOGUS_DATA"
            else:
                return "C2U_DATA"
        elif idi_item.is_u2c_data_if():
            return "U2C_DATA"
        elif (idi_item.is_u2c_rsp_if() and "GO" in idi_item.rec_opcode):
            return "GO_STATE_UPDATE"
        elif idi_item.is_c2u_rsp_if():
            return "STATE_RSP_UPDATE"


    def create_one_idi_data_packet(self, idi_item):
        if idi_item.rec_tid in self.tmp_idi_data.keys() and self.tmp_idi_data[idi_item.rec_tid] is not None:
            if idi_item.chunk == CCF_COH_DEFINES.data_chunk_0:
                self.tmp_idi_data[idi_item.rec_tid].data = self.tmp_idi_data[idi_item.rec_tid].data.replace(" ", "") + idi_item.data.replace(" ", "")
                if idi_item.is_c2u_data_if():
                    self.tmp_idi_data[idi_item.rec_tid].byteen = self.tmp_idi_data[idi_item.rec_tid].byteen + idi_item.rec_byteen
            elif idi_item.chunk == CCF_COH_DEFINES.data_chunk_1:
                self.tmp_idi_data[idi_item.rec_tid].data = idi_item.data.replace(" ", "") + self.tmp_idi_data[idi_item.rec_tid].data.replace(" ", "")
                if idi_item.is_c2u_data_if():
                    self.tmp_idi_data[idi_item.rec_tid].byteen = idi_item.rec_byteen + self.tmp_idi_data[idi_item.rec_tid].byteen
        else:
            self.tmp_idi_data[idi_item.rec_tid] = tmp_data_time_struct()
            self.tmp_idi_data[idi_item.rec_tid].data = idi_item.data
            self.tmp_idi_data[idi_item.rec_tid].time = int(idi_item.rec_time)
            if idi_item.is_c2u_data_if():
                self.tmp_idi_data[idi_item.rec_tid].byteen = idi_item.rec_byteen


    def is_idi_data_entry_ready_for_update(self, idi_item):
        if idi_item.rec_tid in self.tmp_idi_data:
            uri = idi_item.rec_tid
        else:
            VAL_UTDB_ERROR(time=idi_item.rec_time, msg="can't get here. " + idi_item.rec_tid + " is not in tmp_idi_data")

        return self.tmp_idi_data[uri].data is not None and len(self.tmp_idi_data[uri].data) == 128

    def update_mem_db(self, addr, entry):
        if (addr not in self.mem_db.keys()):
            self.mem_db[addr] = [entry]
        else:
            self.mem_db[addr].append(entry)

    def handle_ufi_item(self, flow, idx):
        if flow.flow_progress[idx].is_ufi_data_access():
            self.create_one_uxi_data_packet(flow.flow_progress[idx], self.tmp_ufi_data)
            if self.is_uxi_data_packet_ready(flow.flow_progress[idx].rec_lid, self.tmp_ufi_data):
                mem_entry = memory_data_entry()
                mem_entry.tid = flow.flow_progress[idx].rec_tid
                mem_entry.time = int(self.tmp_ufi_data[flow.flow_progress[idx].rec_lid].time)
                mem_entry.data = self.tmp_ufi_data[flow.flow_progress[idx].rec_lid].data
                mem_entry.cache_type = "MEM"
                mem_entry.access_type = self.get_uxi_access_type(flow.flow_progress[idx])
                if ("deadbeef" in flow.flow_progress[idx].address) or (flow.sad_results != "HOM"):
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[0].address)
                else:
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[idx].address)
                self.update_mem_db(address, mem_entry)
                self.tmp_ufi_data.pop(flow.flow_progress[idx].rec_lid)

    def handle_cfi_item(self, flow, idx):
        if flow.flow_progress[idx].is_cfi_data_access():
            self.create_one_uxi_data_packet(flow.flow_progress[idx], self.tmp_cfi_data)
            if self.is_uxi_data_packet_ready(flow.flow_progress[idx].rec_lid, self.tmp_cfi_data):
                mem_entry = memory_data_entry()
                mem_entry.tid = flow.flow_progress[idx].rec_tid
                mem_entry.time = int(self.tmp_cfi_data[flow.flow_progress[idx].rec_lid].time)
                mem_entry.data = self.tmp_cfi_data[flow.flow_progress[idx].rec_lid].data
                mem_entry.cache_type = "MEM"
                mem_entry.access_type = self.get_uxi_access_type(flow.flow_progress[idx])
                if ("deadbeef" in flow.flow_progress[idx].address) or (flow.sad_results != "HOM"):
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[0].address)
                else:
                    address = CCF_FLOW_UTILS.get_idi_aligned_address(flow.flow_progress[idx].address)
                self.update_mem_db(address, mem_entry)
                self.tmp_cfi_data.pop(flow.flow_progress[idx].rec_lid)

    #Dict type is a mutable type and therefore can be edit by reference
    def create_one_uxi_data_packet(self, uxi_item, tmp_data_dict):
        if uxi_item.rec_lid in tmp_data_dict.keys() and tmp_data_dict[uxi_item.rec_lid].data is not None:
            if uxi_item.chunk == "0":
                tmp_data_dict[uxi_item.rec_lid].data = tmp_data_dict[uxi_item.rec_lid].data.replace(" ", "") + uxi_item.data.replace(" ", "")
            else:
                tmp_data_dict[uxi_item.rec_lid].data = uxi_item.data.replace(" ", "") + tmp_data_dict[uxi_item.rec_lid].data.replace(" ", "")
        else:
            tmp_data_dict[uxi_item.rec_lid] = tmp_data_time_struct()
            tmp_data_dict[uxi_item.rec_lid].data = uxi_item.data
            tmp_data_dict[uxi_item.rec_lid].time = uxi_item.rec_time

    def is_uxi_data_packet_ready(self, uri, tmp_data_dict):
        return (tmp_data_dict[uri].data is not None) and (len(tmp_data_dict[uri].data) == 128)

    def get_uxi_access_type(self, uxi_item):
        if ((type(uxi_item) is ccf_cfi_record_info) and uxi_item.is_cfi_write_data()) or ((type(uxi_item) is ccf_ufi_record_info) and uxi_item.is_ufi_write_data()):
            return "WRITE_TO_MEM"
        elif ((type(uxi_item) is ccf_cfi_record_info) and uxi_item.is_cfi_read_data()) or ((type(uxi_item) is ccf_ufi_record_info) and uxi_item.is_ufi_read_data()):
            return "READ_FROM_MEM"

    def handle_llc_item(self, llc_item):
        if llc_item.is_wr_data_uop():
            mem_entry = memory_data_entry()
            mem_entry.tid = llc_item.rec_tid
            mem_entry.cache_type = "LLC"
            mem_entry.access_type = self.get_llc_access_type(llc_item)
            mem_entry.data = llc_item.rec_data.replace(" ","")
            mem_entry.state = self.get_updated_state(llc_item)
            mem_entry.time = int(llc_item.rec_time)
            address = llc_item.get_llc_aligned_address()
            self.update_mem_db(address, mem_entry)

    def get_llc_access_type(self, item):
        if item.is_wr_data_uop():
            return "WRITE_TO_LLC"
        elif item.is_rd_data_uop():
            return "READ_FROM_LLC"

    def get_updated_state(self, llc_item):
        s = None
        if llc_item.is_late_wr_state():
            s = llc_item.rec_new_state.split("LLC_")[1][0]
        elif "-" not in (llc_item.rec_state):
            s = llc_item.rec_state.split("LLC_")[1][0]
        return s



