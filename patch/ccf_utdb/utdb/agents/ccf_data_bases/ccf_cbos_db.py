from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


#TODO mlugassi - should be removed after adding deallocation time to ccf_flow recoreds
class ccf_cbos_db(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.all_recs = (self.DB.all.TIME > 0)
        self.tor_dealloc = (self.DB.all.MISC.contains("TOR deallocated"))

    def get_dealloc_times(self):
        all_recs = self.all_recs & self.tor_dealloc
        all_recs_flow = self.DB.flow(all_recs['+'])
        dealloc_recs = self.DB.execute(all_recs_flow)
        dealloc_times = dict()
        for events in dealloc_recs:
            for ev in events.EVENTS:
                dealloc_times[ev.LID] = ev.TIME
        return dealloc_times


