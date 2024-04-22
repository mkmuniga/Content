from agents.ccf_common_base.ccf_common_base_class import ccf_base_qry


class ccf_prefetch_wcil_dpt_at_same_time_db(ccf_base_qry):

    def queries(self):
        # define utdb queires here
        self.all_recs = (self.DB.all.TIME > 0)

    def get_prefetch_wcil_dpt_at_same_time_times(self):
        all_recs_flow = self.DB.flow(self.all_recs['+'])
        all_recs = self.DB.execute(all_recs_flow)
        prefetch_wcil_dpt_at_same_time_list = list()
        for events in all_recs:
            for ev in events.EVENTS:
                prefetch_wcil_dpt_at_same_time_list.append(ev.TIME)
        return prefetch_wcil_dpt_at_same_time_list


