from val_utdb_base_components import val_utdb_component, EOT
from val_utdb_report import VAL_UTDB_ERROR

from agents.ccf_queries.ccf_power_qry import ccf_power_qry

class ccf_power_state_agent:
    __power_db: ccf_power_qry.power_rec = list()
    test_power_flow_db = list()

    @staticmethod
    def run_db_builder(qry: ccf_power_qry):
        for rec in qry.get_power_records():
            for record in rec.EVENTS:
                ccf_power_state_agent.__power_db.append(qry.power_rec(record))

    @staticmethod
    def get_last_power_on_timing():
        last_power_on_time = 0
        for rec in ccf_power_state_agent.__power_db:
            if (rec.time > last_power_on_time) and (rec.cstate == "Warm_Rest_Exit"):
                last_power_on_time = rec.time
        return last_power_on_time

    @staticmethod
    def get_all_power_on_timing():
        power_on = {}
        for rec in ccf_power_state_agent.__power_db:
            if (rec.cstate == "Warm_Rest_Exit" or rec.cstate == "Cold_Reset_Exit"):
                power_on[rec.time] = rec.cstate
        return power_on

    @staticmethod
    def get_all_power_off_timing():
        power_off = []
        for rec in ccf_power_state_agent.__power_db:
            if (rec.cstate == "Warm_Reset_Entry" or rec.cstate == "Cold_Reset_Entry"):
                power_off.append(rec.time)
        return power_off

    @staticmethod
    def get_all_c6_exit_timing():
        c6_exit = []
        for rec in ccf_power_state_agent.__power_db:
            if (rec.cstate == "C6_Exit"):
                c6_exit.append(rec.time)
        return c6_exit

    @staticmethod
    def get_all_c6_entry_timing():
        c6_entry = []
        for rec in ccf_power_state_agent.__power_db:
            if (rec.cstate == "C6_Entry"):
                c6_entry.append(rec.time)
        return c6_entry

    @staticmethod
    def get_all_c6_times_between_times(all_c6_times, start_time, end_time):
        c6_times = []
        for j in range(len(all_c6_times)):
            if (all_c6_times[j] > start_time) and (all_c6_times[j] <= end_time):
                c6_times.append(all_c6_times[j])
        return c6_times

    def get_all_monitor_copy_times(start_time, end_time):
        copy_monitor = []
        for rec in ccf_power_state_agent.__power_db:
            if (rec.copy_monitor_fsm == "MONCOPY_HBO_WRITE_ENTRIES"):
                if (rec.time > start_time) and (rec.time < end_time):
                    copy_monitor.append(rec.time)
        return list(copy_monitor)

    @staticmethod
    def initialize_test_power_flow_db():
        temp_dict = dict()
        power_on = ccf_power_state_agent.get_all_power_on_timing()
        power_off = ccf_power_state_agent.get_all_power_off_timing()
        c6_times = ccf_power_state_agent.get_all_c6_entry_timing()

        #check that values make sense
        if len(power_on.keys()) != (len(power_off) + 1):
            VAL_UTDB_ERROR(time=EOT, msg="power off times is " + str(len(power_off)) + " while power on is " + str(len(power_on)))

        temp_dict["START_TEST"] = 0

        power_on_times = list(power_on)

        for i in range(len(power_off)):
            temp_dict["END_TEST"] = power_off[i]

            temp_dict["C6_TIME_IN_RANGE"] = ccf_power_state_agent.get_all_c6_times_between_times(all_c6_times=c6_times,
                                                                                                 start_time=temp_dict["START_TEST"],
                                                                                                 end_time=temp_dict["END_TEST"])
            temp_dict["COLD_RESET"] = (power_on[power_on_times[i]] == "Cold_Reset_Exit")
            ccf_power_state_agent.test_power_flow_db.append(temp_dict.copy())

            #Next power section
            temp_dict["START_TEST"] = power_on_times[i + 1]

        temp_dict["END_TEST"] = 20000000000  # 20000000000 as eot indication
        temp_dict["C6_TIME_IN_RANGE"] = ccf_power_state_agent.get_all_c6_times_between_times(all_c6_times=c6_times,
                                                                                             start_time=temp_dict["START_TEST"],
                                                                                             end_time=temp_dict["END_TEST"])


        temp_dict["COLD_RESET"] = (power_on[power_on_times[-1]] == "Cold_Reset_Exit")
        ccf_power_state_agent.test_power_flow_db.append(temp_dict.copy())


