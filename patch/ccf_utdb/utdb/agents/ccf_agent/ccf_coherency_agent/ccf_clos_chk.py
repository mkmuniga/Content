from val_utdb_bint import bint

from agents.ccf_agent.ccf_coherency_agent.ccf_coherency_base_chk import ccf_coherency_base_chk
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_cov import clos_coverage
from agents.ccf_agent.ccf_coherency_agent.ccf_flow_utils import CCF_FLOW_UTILS
from agents.ccf_common_base.ccf_common_base import ccf_cfi_record_info, ccf_llc_record_info
from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from agents.ccf_common_base.ccf_flow_type import ccf_flow
from agents.ccf_common_base.ccf_registers import ccf_registers
from val_utdb_report import VAL_UTDB_ERROR, VAL_UTDB_MSG

class ccf_clos_chk(ccf_coherency_base_chk):

    def __init__(self):
        self.ccf_registers = ccf_registers.get_pointer()
        self.exluded_opcodes_from_clos_check = ["PORT_OUT", "PORT_IN", "INTPRIUP", "STOPREQ", "INTA", "EOI", "INTPHY", "INTLOG", "CLRMONITOR", "NOP", "LOCK", "UNLOCK", "SPLITLOCK", "ENQUEUE", "SPCYC"]
        if self.si.ccf_cov_en:
            self.clos_cov = clos_coverage.get_pointer()

    def should_check_flow(self, flow: ccf_flow):
        #do_not_chack_flow = flow.is_portout() or flow.is_portin() or flow.is_nop()

        return super().should_check_flow(flow) and flow.opcode not in self.exluded_opcodes_from_clos_check \
               and not flow.is_u2c_cfi_uxi_nc_interrupt() and not flow.is_u2c_ufi_uxi_nc_req_opcode() \
               and not flow.is_u2c_cfi_uxi_nc_req_opcode() \
               and not flow.is_u2c_dpt_req()

    def get_clostagways_value(self, cbo_phy_id, clos, way, time):
        return bint(self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("ingress_" + str(cbo_phy_id), "ia_cos_ways[{}]".format(clos), "clostagways", time))[way]

    def get_closways_value(self, cbo_phy_id, clos, way, time):
        return bint(self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("ingress_" + str(cbo_phy_id), "ia_cos_ways[{}]".format(clos), "closways", time))[way]

    def get_uncore_demand_req_memory_priority_0_value(self, cbo_id_phys, clos, time):
        return self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(cbo_id_phys), "uncore_demand_req_memory_priority_0", "clos{}_demand_priority".format(clos), time)

    def get_uncore_prefetch_req_memory_priority_0_value(self, cbo_id_phys, clos, time):
        return self.ccf_registers.ccf_ral_agent_ptr.read_reg_field("cbregs_all" + str(cbo_id_phys), "uncore_prefetch_req_memory_priority_0", "clos{}_pref_priority".format(clos), time)

    def get_clos_bit_location_for_tag_way(self, tag_way):
        if tag_way > (CCF_COH_DEFINES.clos_reg_tag_way_size - 1):
            return (tag_way - CCF_COH_DEFINES.clos_reg_tag_way_size)
        else:
            return tag_way

    def get_map(self, data_map):
        if data_map == "SF_ENTRY":
            return data_map
        else:
            return data_map.split("_")[1]

    def check_expected_final_data_way_as_expeced(self, flow, exp_data_way):
        if flow.final_map != exp_data_way:
            err_msg = "(get_allocated_data_way): Data way expected: {} but actual is: {}.(TID-{})" \
                .format(exp_data_way, flow.final_map, flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)

    def is_tag_way_come_from_victim(self, flow: ccf_flow):
        return flow.get_victim_tag_way() == flow.final_tag_way

    def is_data_way_come_from_victim(self, flow: ccf_flow):
        return flow.get_flow_victim_map() == flow.final_map.split("_")[-1]

    def is_tag_way_clos_exception(self, flow: ccf_flow):
        #According to HAS if we did Victim for both TAG way and Data way and the Data way fit to CLOS policy,
        #But TAG way is not fitting we can use this TAG array if we are using the victim Dway even if this is violates the TAG CLOS.
        return self.is_tag_way_come_from_victim(flow) and self.is_data_way_come_from_victim(flow)

    def get_allocated_data_way(self, flow: ccf_flow):
        #Case 1: Flow allocated DATA way without Victim
        if flow.allocated_data_way is not None and flow.get_flow_victim_map() is None:
            return self.get_map(flow.allocated_data_way)

        #Case 2: Flow allocate DATA way using Victim so we will use it's DATA way.
        #In this case we can use the Victim Dway or any other Dway that we allocated individually
        elif (flow.allocated_data_way is not None) and (flow.get_flow_victim_map() is not None):
            return self.get_map(flow.allocated_data_way)

        #Case3: We didn't allocated Data way but we are using the Victim Data way
        elif (flow.allocated_data_way is None) and (flow.get_flow_victim_map() is not None):
            self.check_expected_final_data_way_as_expeced(flow, flow.get_flow_victim_map())
            return self.get_map(flow.get_flow_victim_map())
        else:
            err_msg = "Val_Assert (get_allocated_data_way): Please check your assumptions you shouldn't got here. (TID-{})".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)
            return None



    def check_allocated_tag_way_according_to_clos_policy(self, flow: ccf_flow):
        if flow.allocated_tag_way is None:
            err_msg = "(check_allocated_tag_way_according_to_clos_policy): We are supposed to see TAG way allocation but we didn't found any.(TID-{})".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)
            return

        clos_tag_bit_loc = self.get_clos_bit_location_for_tag_way(int(flow.allocated_tag_way))
        clos = flow.get_clos_value()

        clos_policy = self.get_clostagways_value(cbo_phy_id=flow.cbo_id_phys, clos=clos, way=clos_tag_bit_loc, time=flow.first_accept_time) #self.ccf_registers.ia_cos_ways__clostagways[flow.cbo_id_phys][clos][clos_tag_bit_loc]

        if clos_policy == 0 and not self.is_tag_way_clos_exception(flow):
            err_msg = "(check_allocated_tag_way_according_to_clos_policy): Our CLOS policy for CBO_ID:{}, CLOS:{}, TAG_WAY:{} is zero " \
                      "but it seems that we still try to allocate this TAG way for the current CLOS. (TID-{})"\
                      .format(str(flow.cbo_id_phys), str(clos), flow.allocated_tag_way, flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)
        else:
            if self.si.ccf_cov_en:
                self.clos_cov.collect_llc_clos_cov(flow, collect="TAG_WAY")

    def check_allocated_data_way_according_to_clos_policy(self, flow: ccf_flow):
        data_way = self.get_allocated_data_way(flow)
        if data_way is None:
            err_msg = "(check_allocated_data_way_according_to_clos_policy): We are supposed to see DATA way allocation but we didn't found any.(TID-{})".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)
            return

        if(data_way != "SF_ENTRY"):
            clos = flow.get_clos_value()
            clos_policy = self.get_closways_value(cbo_phy_id=flow.cbo_id_phys, clos=clos, way=int(data_way), time=flow.first_accept_time) #self.ccf_registers.ia_cos_ways__closways[flow.cbo_id_phys][clos][int(data_way)]

            if clos_policy == 0:
                err_msg = "(check_allocated_data_way_according_to_clos_policy): our CLOS policy for CBO_ID:{}, CLOS:{}, DATA_WAY:{} is zero " \
                          "but it seems that we still try to allocate this DATA way for the current CLOS.(TID-{})"\
                          .format(str(flow.cbo_id_phys), str(clos), data_way, flow.uri['TID'])
                VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)
            else:
                if self.si.ccf_cov_en:
                    self.clos_cov.collect_llc_clos_cov(flow, collect="DATA_WAY")



    def check_promoted_trans_clos_policy(self, flow: ccf_flow):
        # If flow was promoted the CLOS check was already checked once we are checking the prefetch.
        # We only want to see that the allocated TAG and DATA are the same like we expected.
        # the allocated TAG and data are coming from the prefetch and we will compare them to the final map and tag.
        # Remember: that we will not use Data way in case the demand is not CN=1 or we got M_CmpO
        if (flow.is_cache_near() or flow.cbo_got_ufi_uxi_cmpo_m()) and (flow.final_map != flow.allocated_data_way):
            err_msg = "(Promoted - CLOS check): We didn't expect see that promoted transaction will not use the same map as prefetch. " \
                      "prefetch_map - {}, demand map - {}. (TID- {})".format(flow.allocated_data_way, flow.final_map,
                                                                             flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)

        if (int(flow.final_tag_way) != int(flow.allocated_tag_way)):
            # the allocated TAG and data are coming from the prefetch and we will compare them to the final map and tag
            err_msg = "(Promoted - CLOS check): We didn't expect see that promoted transaction will not use the same TAG as prefetch. " \
                      "prefetch_tag_way - {}, demand tag_way - {}. (TID- {})".format(flow.allocated_tag_way,
                                                                                     flow.final_tag_way,
                                                                                     flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.first_accept_time, msg=err_msg)

    def check_idi_and_snoop_tran_clos_policy(self, flow: ccf_flow):
        tag_allocation = flow.initial_state_llc_i() and not flow.final_state_llc_i()
        data_way_allocation = (not flow.initial_map_dway() and flow.final_map_dway()) or \
                              (flow.initial_map_dway() and flow.final_map_dway() and (flow.initial_map != flow.final_map))
        no_allocation_was_done = not (tag_allocation or data_way_allocation)

        # case 1: Miss that ended with record in LLC - our assumption is that RTL will always allocate TAG Way and DATA way at first pass
        #HAS Rule: We know that if we are doing allocation to tag and data using victim flow or silent evict flow we need that only data way CLOS policy will be right.
        # If we don't have available data way we will allocate map=SF.
        if tag_allocation:
            if (flow.is_alloc_tag_and_victim_map_data() or flow.is_flow_with_silent_evict()) and not flow.final_map_sf():
                self.check_allocated_data_way_according_to_clos_policy(flow)
            else:
                self.check_allocated_tag_way_according_to_clos_policy(flow)
                self.check_allocated_data_way_according_to_clos_policy(flow)
        # Case 2: Hit but we have only Tag way and we are allocating Data way
        # Case 3: We have TAG way and we have Data way but Data way changed - is that legal case ?
        elif data_way_allocation and not tag_allocation:
            self.check_allocated_data_way_according_to_clos_policy(flow)
        # Case 4: No allocation was done.
        elif no_allocation_was_done:
            pass
        else:
            err_msg = "Val_Assert (check_idi_and_snoop_tran_clos_policy): Why did you got here? (TID-{})".format(flow.uri['TID'])
            VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)

    def llc_clos_check(self, flow: ccf_flow):
        if flow.clos_en: #If Clos disable all ways are valid not need to check.
            if flow.is_flow_promoted():
                self.check_promoted_trans_clos_policy(flow)

            elif flow.is_idi_flow_origin() or flow.is_snoop_opcode():
                self.check_idi_and_snoop_tran_clos_policy(flow)

            elif flow.is_victim() or flow.is_flusher_origin():
                pass #In victim flow we are not checking LLC CLOS

            else:
                err_msg = "Val_Assert (CLOS checker): We didn't done any check on this flow. why? (TID-{}, LID-{})".format(flow.uri['TID'], flow.uri['LID'])
                VAL_UTDB_ERROR(time=flow.initial_time_stamp, msg=err_msg)


    def get_exp_traffic_class(self, flow: ccf_flow):
        clos = flow.get_clos_value()
        if flow.is_llcpref():
            return self.get_uncore_prefetch_req_memory_priority_0_value(cbo_id_phys=flow.cbo_id_phys, clos=clos, time=flow.first_accept_time) #self.ccf_registers.uncore_prefetch_req_memory_priority_0[flow.cbo_id_phys][clos]

        elif flow.opcode in CCF_FLOW_UTILS.DEMAND_READs_for_cxm_priority:
            return self.get_uncore_demand_req_memory_priority_0_value(cbo_id_phys=flow.cbo_id_phys, clos=clos, time=flow.first_accept_time) #self.ccf_registers.uncore_demand_req_memory_priority_0[flow.cbo_id_phys][clos]

        elif flow.opcode in CCF_FLOW_UTILS.MLC_PREF_for_cxm_priority:
            if self.ccf_registers.clos_to_tc_mlc_pref_is_demand[flow.cbo_id_phys] == 1:
                return self.get_uncore_demand_req_memory_priority_0_value(cbo_id_phys=flow.cbo_id_phys, clos=clos, time=flow.first_accept_time) #self.ccf_registers.uncore_demand_req_memory_priority_0[flow.cbo_id_phys][clos]
            else:
                return self.get_uncore_prefetch_req_memory_priority_0_value(cbo_id_phys=flow.cbo_id_phys, clos=clos, time=flow.first_accept_time) #self.ccf_registers.uncore_prefetch_req_memory_priority_0[flow.cbo_id_phys][clos]

        else:
            return 0 # default TC should be 0

    def check_flow(self, flow: ccf_flow):
        self.llc_clos_check(flow)

