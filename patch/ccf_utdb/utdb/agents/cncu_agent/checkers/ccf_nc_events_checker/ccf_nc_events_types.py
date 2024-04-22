from agents.cncu_agent.common.cncu_defines import SB


class COLORS:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    LIGHT_PURPLE = '\033[94m'
    PURPLE = '\033[95m'
    END = '\033[0m'


class EVENT_CHANNEL:  # Needs to be ordered from the channel which treated lowest to the fastest
    SB_CRWR = 1
    SB_MSG = 2
    WIRE = 3


class INFO:
    def __init__(self, flow_name, start_time, end_time, src_pid, dest_pid, opcode, info="None"):
        self.start_time = start_time
        self.end_time = end_time
        self.flow_name = flow_name
        self.src_pid = src_pid
        self.dest_pid = dest_pid
        self.opcode = opcode
        self.info = info
        self._set_channel()

    def is_incoming_event(self):
        return self.dest_pid == SB.EPS.ncevents

    def get_time(self):
        return self.end_time

    def _set_channel(self):
        if self.opcode == SB.OPCODES.cr_wr:
            self.channel = EVENT_CHANNEL.SB_CRWR
        elif self.opcode in [SB.OPCODES.pcu_ncu_msg, SB.OPCODES.ncu_pcu_msg, SB.OPCODES.ncu_ncu_msg,
                             SB.OPCODES.mclk_event, SB.OPCODES.fclk_event]:
            self.channel = EVENT_CHANNEL.SB_MSG
        else:
            self.channel = EVENT_CHANNEL.WIRE

    def print(self, color=False):
        if self.is_incoming_event():
            print((COLORS.YELLOW if color else "") + self.to_string())
        else:
            print((COLORS.LIGHT_PURPLE if color else "") + self.to_string())

    def to_string(self):
        return (("Incoming" if self.is_incoming_event() else "Reported") + \
                " Event - {0:<12} - {1:<12} - {2:<20} - from {3:<4} to {4:<4} - {5}").format(
            self.flow_name, str(self.get_time()) + " - " + str(self.end_time), self.opcode, hex(self.src_pid[7:0]),
            hex(self.dest_pid[7:0]),
            self.info
        )

    def __str__(self):
        return self.to_string()


class EVENT_INFO(INFO):
    def __init__(self, flow_name, start_time, end_time, src_pid, dest_pid, opcode, events):
        super().__init__(start_time=start_time, end_time=end_time, info=", ".join(events),
                         src_pid=src_pid, dest_pid=dest_pid, flow_name=flow_name, opcode=opcode)
        self.events = events

    def is_reporting_event(self):
        return self.dest_pid in SB.EPS.sncu


class CRASHLOG_INFO(INFO):
    def __init__(self, start_time, end_time, src_pid, dest_pid, opcode,
                 valid: int, ccf_id: int, module_id: int, events: list):
        super().__init__(start_time=start_time, end_time=end_time,
                         src_pid=src_pid, dest_pid=dest_pid, flow_name="Crashlog", opcode=opcode)
        self.valid = valid
        self.ccf_id = ccf_id
        self.module_id = module_id
        self.events = events
        self.__set_info(valid, ccf_id, module_id, events)

    def __set_info(self, valid, ccf_id, module_id, events):
        self.info = "VALID = {0}, CCF_ID = {1}, MODULE_ID = {2}, EVENTS = {3}".format(
            valid, ccf_id, module_id, ", ".join(events))


class EXPECTED_ITEM:
    def __init__(self, info: INFO, counter):
        self.info = info
        self.counter = counter
        self.may_reported = False

    def get_time(self):
        return self.info.get_time()

    def get_channel(self):
        return self.info.channel

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "(" + str(self.get_time()) + ", " + str(self.counter) + ", " + str(self.may_reported) + ")"
