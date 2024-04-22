from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_common_base import memory_data_entry
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_data_bases.ccf_dbs import ccf_dbs
from agents.ccf_common_base.ccf_common_base_class import ccf_base_chk
from val_utdb_report import VAL_UTDB_ERROR, EOT, VAL_UTDB_MSG
from collections import OrderedDict
from val_utdb_bint import bint

class ccf_dump_chk(ccf_base_chk):
    def __init__(self):
        super().__init__()
        self.llc_db = {}
        self.ingored_addr_l = []


    def run(self):

        #First run on db is to clean it from problematic addresses
        for address in self.mem_db.keys():
            #add ignore
            self.check_and_add_to_ignore_list(address)

        self.sort_mem_db()
        for address in self.mem_db.keys():
            if address in self.dump_db and self.address_is_valid_for_dump_chk(address):
                self.check_address(address)
            else:
                VAL_UTDB_MSG(time=EOT, msg="Address = " + address + " is not in dump_db or was ignored")
        VAL_UTDB_MSG(time=EOT, msg="checking dump ---> done")

    def sort_mem_db(self):
        for addr in self.mem_db.keys():
            self.mem_db[addr].sort(key=memory_data_entry.get_time)

        ccf_dbs.sort_mem_db()
        ccf_dbs.sort_dump_db()
        self.llc_db = OrderedDict(sorted(self.llc_db.items()))

    def check_and_add_to_ignore_list(self,address):
        for mem_access in self.mem_db[address]:
            #NC Access with MKTME bits -check the flows the accessed this address
            if ("WRITE_TO_MEM" in mem_access.access_type or "READ_FROM_MEM" in mem_access.access_type) and mem_access.tid is not None:
                ccf_flow = self.ccf_flows[mem_access.tid]
                if not ccf_flow.flow_is_hom() and ccf_flow.flow_accessed_mktme():
                    address_without_mktme = hex(bint(int(address, 16))[CCF_COH_DEFINES.tag_msb:0])
                    address_without_mktme_aligned = CCF_FLOW_UTILS.get_idi_aligned_address(address_without_mktme)
                    if address not in self.ingored_addr_l:
                        self.ingored_addr_l.append(address)
                        VAL_UTDB_MSG(time=EOT,msg="Address " + address + ' has been added to ignored list in dump checker')
                    if address_without_mktme_aligned not in self.ingored_addr_l:
                        self.ingored_addr_l.append(address_without_mktme_aligned)
                        VAL_UTDB_MSG(time=EOT, msg="Address " + str(address_without_mktme_aligned) +  ' has been added to ignored list in dump checker')
            #Bug in RTL where RspIFwdM is changed to RspI but the modified data is forwared to requesting core - should be xied in PTL
            #HSD link: https://hsdes.intel.com/resource/13010148049
            if "C2U_DATA_RSP" in mem_access.access_type and mem_access.tid is not None:
                ccf_flow = self.ccf_flows[mem_access.tid]
                if ccf_flow.original_snoop_rsp_m() and not ccf_flow.snoop_rsp_m():
                    VAL_UTDB_MSG(time=EOT, msg="Address " + str(address) + ' has been added to ignored list in dump checker due to FwdM to RspI/S issue')
                    if address not in self.ingored_addr_l:
                        self.ingored_addr_l.append(address)

            #Port Out or Port In - may collide with other addresses in the LLC even though they are addressless transactions becaseu these are MMIO_LT address
            #In CCF there is no way to compare the data
            if ("WRITE_TO_MEM" in mem_access.access_type or "READ_FROM_MEM") and mem_access.tid is not None:
                ccf_flow = self.ccf_flows[mem_access.tid]
                if ccf_flow.is_portout() or ccf_flow.is_portin():
                    VAL_UTDB_MSG(time=EOT, msg="Address " + str(address) + ' has been added to ignored to list a C2U_PORT_OUT send to an exsiting address in LLC')
                    if address not in self.ingored_addr_l:
                        self.ingored_addr_l.append(address)

    def address_is_valid_for_dump_chk(self,address):
        return address not in self.ingored_addr_l

    def is_mlc_state_non_I(self, mlc):
        for key in mlc.keys():
            if mlc[key].state != "I":
                return 1
        return 0

    def is_mlc_state(self, mlc, desired):
        for key in mlc.keys():
            if mlc[key].state == desired:
                return 1
        return 0

    def is_special_abort_case(self, llc_dump_data, mem_dump_data):
        if llc_dump_data == "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" \
                and \
                mem_dump_data == "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000":
            return 1
        return 0


    def get_ref_mem_data(self, address):
        #Start from the last access to this address and move backwards
        for i in range(-1, -1 * (len(self.mem_db[address])) - 1, -1):

            entry = self.mem_db[address][i]

            no_bogus = "BOGUS" not in entry.access_type
            #In case of GO sent to core we have to check that it was not GO_I to recevie valid data with no bogus
            if entry.access_type == "GO_STATE_UPDATE":
                if entry.tid is not None:
                    ccf_flow = self.ccf_flows[entry.tid]

                if not ccf_flow.cbo_sent_go_i() and no_bogus:
                    for j in range(-1, -1 * (len(self.mem_db[address])) - 1, -1):
                        data_entry = self.mem_db[address][j]
                        no_bogus_on_data_entry = "BOGUS" not in data_entry.access_type
                        if data_entry.tid == ccf_flow.uri["TID"] and data_entry.data is not None and len(data_entry.data) == 128 and no_bogus_on_data_entry:
                            return data_entry


            #Otherwise check data is valid with no bogus - This will include all other access for example write to mem write to llc c2u data and preload
            elif entry.access_type not in ["U2C_DATA", "READ_FROM_MEM"] and entry.data is not None and len(entry.data) == 128 and no_bogus:
                    return entry

    def get_llc_ref(self, address, llc_dump):
        for addr in self.llc_db.keys():
            dist = CCF_FLOW_UTILS.get_distance(address, addr)
            if dist in [0,1] and self.llc_db[addr].slice == int(llc_dump.cache_type.split("LLC_")[1])\
                and self.llc_db[addr].half == int(llc_dump.half) and self.llc_db[addr].set == llc_dump.set\
                    and int(self.llc_db[addr].way) == int(llc_dump.way):
                return self.llc_db[addr]
        VAL_UTDB_ERROR(time=EOT, msg="Rule_0: address = " + address + " wasn't found in llc_ref_db")

    def check_llc_dump_vs_mlc_dump(self, address, llc_dump, mlc_dump, mem_dump):
        if llc_dump.map == str(CCF_COH_DEFINES.SNOOP_FILTER):
            # MLC can be empty if state != M
            if llc_dump.state == "M":
                if not mlc_dump.keys():
                    VAL_UTDB_ERROR(time=llc_dump.time, msg="Rule_1: llc.map = SF and llc.state = M but MLC is empty. address = " + address)
                if llc_dump.cv == "0".zfill(CCF_COH_DEFINES.num_physical_cv_bits):
                    VAL_UTDB_ERROR(time=llc_dump.time, msg="Rule_2: llc.map = SF and llc.state = M but llc.cv is empty. address = " + address)
        else:
            if llc_dump.state == "E" and (not self.is_mlc_state(mlc_dump, "M")):
                # the additional condition of mlc.state != M is due to ItoM flow:
                # llc state changed from M to E, so its data is different from MEM, but we don't lose the data
                # because the modified data is in the core.
                self.compare_llc_dump_and_mem_dump(llc_dump, mem_dump, address)

        if not mlc_dump.keys():
            for idx in mlc_dump.keys():
                if llc_dump.cv[(self.si.num_of_cbo*CCF_COH_DEFINES.num_of_ccf_clusters - 1) - int(idx)] != '1':
                    VAL_UTDB_ERROR(time=llc_dump.time,
                                   msg="Rule_3: CV mismatch between LLC and MLC for address = " + address)

    def compare_llc_dump_and_mem_dump(self, llc_dump, mem_dump, address):
        if self.si.is_nem_test == 0:
            if (llc_dump.data != mem_dump.data) and (not self.is_special_abort_case(llc_dump.data, mem_dump.data)):
                assert_error = 0
                if self.si.ccf_preload_data_correctable_errs == 0:
                    assert_error = 1
                else:
                    dist_data = CCF_FLOW_UTILS.get_distance(llc_dump.data, mem_dump.data)
                    assert_error = dist_data > 1

                if assert_error:
                    VAL_UTDB_ERROR(time=EOT, msg="Rule_4: data_mismatch for address = " + address + "\n"
                                   + "LLC_DMP: = " + llc_dump.data + "\n"
                                   + "MEM_DMP: = " + mem_dump.data)

    def compare_llc_dump_and_ref_mem(self, llc_dump, ref_mem, address):
        if (llc_dump.data != ref_mem.data):
            assert_error = 0
            if self.si.ccf_preload_data_correctable_errs == 0:
                assert_error = 1
            else:
                dist_data = CCF_FLOW_UTILS.get_distance(ref_mem.data, llc_dump.data)
                assert_error = dist_data > 1

            if assert_error:
                VAL_UTDB_ERROR(time=llc_dump.time,
                               msg="Rule_5: data_mismatch for address = " + address + "\n"
                                   + "LLC_DMP: = " + llc_dump.data + "\n"
                                   + "EXPECTD: = " + ref_mem.data)

    def compare_llc_dump_and_llc_ref(self, llc_dump, llc_ref, address):
        if (llc_ref.data != llc_dump.data):
            assert_error = 0
            if self.si.ccf_preload_data_correctable_errs == 0:
                assert_error = 1
            else:
                dist_data = CCF_FLOW_UTILS.get_distance(llc_ref.data, llc_dump.data)
                assert_error = dist_data > 1

            if assert_error:
                VAL_UTDB_ERROR(time=llc_dump.time,
                               msg="Rule_6: data_mismatch for address = " + address + "\n"
                                   + "LLC_REF: = " + llc_ref.data + "\n"
                                   + "LLC_DMP: = " + llc_dump.data)

    def compare_mlc_dump_and_ref_mem(self, mlc_dump, idx, ref_mem, address):
        if ref_mem != None and ref_mem.data != mlc_dump[idx].data:#in case that there is only state change in ref_mem but the data is preloaded
            VAL_UTDB_ERROR(time=mlc_dump[idx].time,
                           msg="Rule_7: data_mismatch for address = " + address + " in MLC = " + idx + "\n"
                               + "MLC_DMP: = " + mlc_dump[idx].data + "\n"
                               + "EXPECTD: = " + ref_mem.data)

    def check_llc_dump_vs_llc_ref_fields(self, address, llc_dump, llc_ref):
        if llc_ref.time >= llc_dump.time:
            VAL_UTDB_ERROR(time=llc_dump.time,
                           msg="Rule_8: Time of llc_ref can't be after dump_db entry. address = " + address + " llc_ref_time = " + str(
                               llc_ref.time))

        if llc_ref.cv.zfill(CCF_COH_DEFINES.num_physical_cv_bits) != llc_dump.cv:
            VAL_UTDB_ERROR(time=llc_dump.time,
                           msg="Rule_9: cv_mismatch between llc_dump and llc_ref reference. address = " + address + " llc_ref_time = " + str(
                               llc_ref.time))

        if int(llc_ref.map) != int(llc_dump.map):
            VAL_UTDB_ERROR(time=llc_dump.time,
                           msg="Rule_10: map_mismatch between llc_dump and llc_ref reference. address = " + address + " llc_ref_time = " + str(
                               llc_ref.time))

        if llc_ref.state != llc_dump.state:
            VAL_UTDB_ERROR(time=llc_dump.time,
                           msg="Rule_11: state_mismatch between llc_dump and llc_ref reference. address = " + address + " llc_ref_time = " + str(
                               llc_ref.time))

        if int(llc_ref.map) != CCF_COH_DEFINES.SNOOP_FILTER:
            self.compare_llc_dump_and_llc_ref(llc_dump, llc_ref, address)


    def check_address(self, address):
        llc_dump = None
        mlc_dump = {}
        mem_dump = None
        ref_mem = self.get_ref_mem_data(address)

        for rec in self.dump_db[address]:
            if "MLC" in rec.cache_type:
                idx = rec.cache_type.split("MLC_")[1]
                mlc_dump[idx] = rec
            elif "LLC" in rec.cache_type:
                llc_dump = rec
            elif "MEM" in rec.cache_type:
                mem_dump = rec


        if llc_dump != None:
            self.check_llc_dump_vs_mlc_dump(address, llc_dump, mlc_dump, mem_dump)

            llc_ref = self.get_llc_ref(address, llc_dump)

            if ("I" not in llc_ref.state):
                self.check_llc_dump_vs_llc_ref_fields(address, llc_dump, llc_ref)

                if llc_ref.state == "E" and not self.is_mlc_state(mlc_dump, "M"):
                    if int(llc_ref.map) != CCF_COH_DEFINES.SNOOP_FILTER:
                        self.compare_llc_dump_and_mem_dump(llc_dump, mem_dump, address)
                        self.compare_llc_dump_and_ref_mem(llc_dump, ref_mem, address)


                    for idx in mlc_dump.keys():
                        if self.is_mlc_state(mlc_dump, "S"):
                            self.compare_mlc_dump_and_ref_mem(mlc_dump, idx, ref_mem, address)

                if llc_ref.state == "S":
                    if int(llc_ref.map) != CCF_COH_DEFINES.SNOOP_FILTER:
                        self.compare_llc_dump_and_mem_dump(llc_dump, mem_dump, address)
                        self.compare_llc_dump_and_ref_mem(llc_dump, ref_mem, address)

                    for idx in mlc_dump.keys():
                        if self.is_mlc_state(mlc_dump, "S"):
                            self.compare_mlc_dump_and_ref_mem(mlc_dump, idx, ref_mem, address)

                    if self.is_mlc_state(mlc_dump, "E") or self.is_mlc_state(mlc_dump, "M"):
                        VAL_UTDB_ERROR(time=EOT, msg="Rule_12: MLC state can't be E or M while LLC state is E. address = " + address)

                if llc_ref.state == "M":
                    if int(llc_ref.map) != CCF_COH_DEFINES.SNOOP_FILTER:
                        #LLC will match the REF only if MLC is not M state
                        # if ref_mem is MLC in M, it might has more updated data than LLC, so in that case don't compare
                        if not self.is_mlc_state(mlc_dump, "M"):
                            self.compare_llc_dump_and_ref_mem(llc_dump, ref_mem, address)

                    for idx in mlc_dump.keys():
                        if self.is_mlc_state(mlc_dump, "E") or self.is_mlc_state(mlc_dump, "S"):
                            self.compare_mlc_dump_and_ref_mem(mlc_dump, idx, ref_mem, address)

        else:
            #currently we can't compare dump_db to ref_mem (address_db) because address_db might be updated from IDI-Bridge VC model, and there is no point to check it
            # if ref_mem != None:
            #     if "-" in ref_mem.data:#in case we don't have the full line
            #         for idx in range(128):
            #             if ref_mem.data[idx] != "-" and ref_mem.data[idx] != mem_dump.data[idx]:
            #                     VAL_UTDB_ERROR(time=EOT, msg="dump_chk_failure: data_mismatch between mem and ref reference for address = " + address + " in index = " + idx)
            #     elif mem_dump.data != ref_mem.data:
            #         VAL_UTDB_ERROR(time=EOT, msg="dump_chk_failure: data_mismatch between mem and data_chk reference for address = " + address)
            # else:
            #     VAL_UTDB_MSG(time=EOT, msg="Address = " + address + " is not in address_db and also not in llc_db probably because IDI BRIDGE sent it back to MEM")

            if self.is_mlc_state_non_I(mlc_dump):
                VAL_UTDB_ERROR(time=EOT, msg="Rule_13: LLC is Invalid while MLC is not Invalid. address = " + address)








