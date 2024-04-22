#!/usr/bin/env python3.6.3

#################################################################################################
# ccf_coherency_qry.py 
#
# Owner:              asaffeld
# Creation Date:      11.2020
#
# ###############################################
#
# Description:
#   This file contain all ccf_coherency queries and flow definitions
#################################################################################################
from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry
from agents.ccf_common_base.coh_global import COH_GLOBAL
from val_utdb_base_components import EOT
from val_utdb_report import VAL_UTDB_ERROR


class ccf_coherency_qry(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.uri_tid = (self.DB.all.TID == '@tid')
        self.uri_lid = (self.DB.all.LID == '@lid')
        self.uri_pid = (self.DB.all.PID == '@pid')


        self.only_cbo_trk = (self.DB.all.SELECTOR == "cbo")
        self.only_ring_trk = (self.DB.all.SELECTOR == "ring")
        self.only_llc_trk = (self.DB.all.SELECTOR == "llc")
        self.only_cfi_trk = (self.DB.all.SELECTOR == "cfi")
        self.only_cfi_unit_is_santa = (self.DB.all.UNIT.contains("SANTA"))

        self.only_conflict_lookup_line = (self.DB.all.MISC.contains("Conflict LookUp"))
        self.FwdCnfltO = (self.DB.all.OPCODE == "FwdCnfltO")
        self.cbo_ReqFwdCnflt = (self.DB.all.MSG == "C2S_BL_UPI_ReqFwdCnflt")
        self.ReqFwdCnflt = (self.DB.all.OPCODE == "ReqFwdCnflt")


    def flow_by_tid(self):
        #uri_e = self.uri_tid & self.uri_lid & self.uri_pid
        uri_e = self.uri_tid
        uri_flows = self.DB.flow(uri_e['+'])
        return self.DB.execute(uri_flows)

    def conflict_indication(self, cbo_id):
        cbo_id_e = (self.DB.all.UNIT == "CPIPE_{}".format(cbo_id))
        FwdCnfltO_e = self.FwdCnfltO & self.only_cbo_trk & self.only_conflict_lookup_line & cbo_id_e
        ReqFwdCnflt_e = self.cbo_ReqFwdCnflt & self.only_cbo_trk & cbo_id_e
        flow = (self.DB.flow(FwdCnfltO_e|ReqFwdCnflt_e))
        conflict_flows = (self.DB.flow(flow['+']))
        return self.DB.execute(conflict_flows)

    def filter_all_ReqFwdCnflt(self):
        ReqFwdCnflt_e = self.ReqFwdCnflt & self.only_cfi_trk & self.only_cfi_unit_is_santa
        flow = (self.DB.flow(ReqFwdCnflt_e))
        ReqFwdCnflt_trns = (self.DB.flow(flow['+']))
        return self.DB.execute(ReqFwdCnflt_trns)

    def vulnerable_data_flow(self, llc_id):
        not_reject_e = (self.DB.all.REJECTED == 0)
        drd_e = (self.DB.all.ARBCMD.contains("DRd", True))
        llc_id_e = (self.DB.all.UNIT == "LLC_{}".format(llc_id))
        vulnerable_e = self.only_llc_trk & llc_id_e & drd_e & not_reject_e
        flow = (self.DB.flow(vulnerable_e))
        vulnerable_flow = (self.DB.flow(flow['+']))
        return self.DB.execute(vulnerable_flow)

    def promoted_flow_uri_list(self, cbo_id):
        cbo_id_e = (self.DB.all.UNIT == "CPIPE_{}".format(cbo_id))
        flow_promoted_e = (self.DB.all.MISC.contains("Prefetch Promoting", True))
        drd_e = (self.DB.all.OPCODE.contains("DRd", True))
        promoted_drd_e = self.only_cbo_trk & cbo_id_e & drd_e & flow_promoted_e
        flow = (self.DB.flow(promoted_drd_e))
        promoted_drd_flow = (self.DB.flow(flow['+']))
        promoted_drd_flow_results = self.DB.execute(promoted_drd_flow)
        list_of_flow_keys = []
        for promoted_drd in promoted_drd_flow_results:
            for record in promoted_drd.EVENTS:
                if record.TIME > COH_GLOBAL.global_vars["START_OF_TEST"] and record.TIME < COH_GLOBAL.global_vars["END_OF_TEST"]:
                    list_of_flow_keys.append(record.TID)
        return list_of_flow_keys

    def llc_record_for_promoted_drd(self, tid):
        not_reject_e = (self.DB.all.REJECTED == 0)
        user_tid_e = (self.DB.all.TID == tid)
        promoted_drd_cmp_e = (self.DB.all.ARBCMD.contains("E_CmpO", True))
        promoted_drd_llc_write_e = self.only_llc_trk & not_reject_e & promoted_drd_cmp_e & user_tid_e
        flow = (self.DB.flow(promoted_drd_llc_write_e))
        llc_promoted_write_flow = (self.DB.flow(flow['+']))
        llc_promoted_write_flow_records = self.DB.execute(llc_promoted_write_flow)
        list_of_record = []
        for llc_promoted_write in llc_promoted_write_flow_records:
            for record in llc_promoted_write.EVENTS:
                if (record.TIME > COH_GLOBAL.global_vars["START_OF_TEST"]) and (record.TIME < COH_GLOBAL.global_vars["END_OF_TEST"]):
                    list_of_record.append(record)
        return list_of_record


    def read_vulnerable_dway(self, llc_id):
        not_reject_e = (self.DB.all.REJECTED == 0)
        llc_id_e = (self.DB.all.UNIT == "LLC_{}".format(llc_id))
        rd_pfvl_e = (self.DB.all.PFVL_RD == "1")
        read_vulnerable_dway_e = self.only_llc_trk & llc_id_e & rd_pfvl_e & not_reject_e
        flow = (self.DB.flow(read_vulnerable_dway_e))
        read_vulnerable_dway_flow = (self.DB.flow(flow['+']))
        return self.DB.execute(read_vulnerable_dway_flow)

    def get_tor_dealloc_time(self, tid_uri):
        uri_e = (self.DB.all.TID == tid_uri)
        dealloc_e = (self.DB.all.MISC.contains("TOR deallocated", True))
        get_tor_deallc_e = self.only_cbo_trk & dealloc_e & uri_e
        event = (self.DB.flow(get_tor_deallc_e))
        dealloc_event = (self.DB.flow(event['+']))
        dealloc_event_result = self.DB.execute(dealloc_event)
        if len(dealloc_event_result) > 1:
            VAL_UTDB_ERROR(time=EOT, msg="(get_tor_dealloc_time):We got more then one deallocation event that was not expected(URI-{})".format(tid_uri))
            return None
        else:
            for dealloc_event_result_e in dealloc_event_result:
                for record in dealloc_event_result_e.EVENTS:
                    return record.TIME



    class ccf_coherency_rec(ccf_base_qry.ccf_base_rec):
        # define utdb rec wrapper here
        pass


