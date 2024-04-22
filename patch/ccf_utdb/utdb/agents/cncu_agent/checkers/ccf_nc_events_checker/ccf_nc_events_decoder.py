from agents.cncu_agent.common.cncu_defines import EVENTS_TYPES, SB
from agents.cncu_agent.common.cncu_types import SB_TRANSACTION


def get_events_bits_nums(tran: SB_TRANSACTION):
    bits_nums = list()

    for i, data_byte in enumerate(tran.data):
        for j in range(8):
            if data_byte[j] == 1:
                bits_nums.append((i * 8) + j)
    return bits_nums


class EVENTS_DECODER:

    def __init__(self):
        self._broadcast_event_decoder = dict()
        self._core_event_decoder = dict()
        self._mclk_decoder = dict()
        self._fclk_decoder = dict()

        self._build_broadcast_event_decoder()
        self._build_core_event_decoder()
        self._build_mclk_decoder()
        self._build_fclk_decoder()

    def _build_broadcast_event_decoder(self):
        self._broadcast_event_decoder[EVENTS_TYPES.msmi] = 2
        self._broadcast_event_decoder[EVENTS_TYPES.csmi] = 3
        self._broadcast_event_decoder[EVENTS_TYPES.llbbrk] = 8
        self._broadcast_event_decoder[EVENTS_TYPES.lterr] = 9
        self._broadcast_event_decoder[EVENTS_TYPES.cmci] = 1
        self._broadcast_event_decoder[EVENTS_TYPES.psmi] = 10
        self._broadcast_event_decoder[EVENTS_TYPES.pcusmi] = 7
        self._broadcast_event_decoder[EVENTS_TYPES.unctrap] = 13
        self._broadcast_event_decoder[EVENTS_TYPES.mcerr] = 0
        self._broadcast_event_decoder[EVENTS_TYPES.rmca] = 11
        self._broadcast_event_decoder[EVENTS_TYPES.rmsmi] = 12

        for ev_type in EVENTS_TYPES.get_events_types():
            if ev_type in self._broadcast_event_decoder.keys():
                self._broadcast_event_decoder[self._broadcast_event_decoder[ev_type]] = ev_type

    def _build_core_event_decoder(self):
        self._core_event_decoder[EVENTS_TYPES.msmi] = 2
        self._core_event_decoder[EVENTS_TYPES.csmi] = 3
        self._core_event_decoder[EVENTS_TYPES.llbbrk] = 4
        self._core_event_decoder[EVENTS_TYPES.umcf] = 0
        self._core_event_decoder[EVENTS_TYPES.ierr] = 1
        self._core_event_decoder[EVENTS_TYPES.rmca] = 6
        self._core_event_decoder[EVENTS_TYPES.rmsmi] = 7

        for ev_type in EVENTS_TYPES.get_events_types():
            if ev_type in self._core_event_decoder.keys():
                self._core_event_decoder[self._core_event_decoder[ev_type]] = ev_type

    def _build_mclk_decoder(self):
        self._mclk_decoder[EVENTS_TYPES.msmi] = 27
        self._mclk_decoder[EVENTS_TYPES.csmi] = 26
        self._mclk_decoder[EVENTS_TYPES.llbbrk] = 29
        self._mclk_decoder[EVENTS_TYPES.lterr] = 28
        self._mclk_decoder[EVENTS_TYPES.cmci] = 31
        self._mclk_decoder[EVENTS_TYPES.umcf] = 30
        self._mclk_decoder[EVENTS_TYPES.ierr] = 25
        self._mclk_decoder[EVENTS_TYPES.rmca] = 21
        self._mclk_decoder[EVENTS_TYPES.rmsmi] = 24

        for ev_type in EVENTS_TYPES.get_events_types():
            if ev_type in self._mclk_decoder.keys():
                self._mclk_decoder[self._mclk_decoder[ev_type]] = ev_type

    def _build_fclk_decoder(self):
        self._fclk_decoder[EVENTS_TYPES.msmi] = 55
        self._fclk_decoder[EVENTS_TYPES.csmi] = 54
        self._fclk_decoder[EVENTS_TYPES.llbbrk] = 50
        self._fclk_decoder[EVENTS_TYPES.lterr] = 59
        self._fclk_decoder[EVENTS_TYPES.cmci] = 61
        self._fclk_decoder[EVENTS_TYPES.psmi] = 57
        self._fclk_decoder[EVENTS_TYPES.pcusmi] = 58
        self._fclk_decoder[EVENTS_TYPES.unctrap] = 51
        self._fclk_decoder[EVENTS_TYPES.umcnf] = 53
        self._fclk_decoder[EVENTS_TYPES.umcf] = 60
        self._fclk_decoder[EVENTS_TYPES.ierr] = 63
        self._fclk_decoder[EVENTS_TYPES.exterr] = 62
        self._fclk_decoder[EVENTS_TYPES.rmsmi] = 49
        self._fclk_decoder[EVENTS_TYPES.rmca] = 48

        for ev_type in EVENTS_TYPES.get_events_types():
            if ev_type in self._fclk_decoder.keys():
                self._fclk_decoder[self._fclk_decoder[ev_type]] = ev_type

    def decode(self, events_msg: SB_TRANSACTION):
        events = list()
        event_bits = get_events_bits_nums(events_msg)
        if events_msg.opcode == SB.OPCODES.mclk_event:
            for i in event_bits:
                if i > 9:
                    events.append(self._mclk_decoder[i])

        elif events_msg.opcode == SB.OPCODES.fclk_event:
            for i in event_bits:
                events.append(self._fclk_decoder[i])

        elif events_msg.opcode == SB.OPCODES.cr_wr and events_msg.addr == 0x48 and events_msg.dest_pid == SB.EPS.ncevents:
            for i in event_bits:
                events.append(self._core_event_decoder[i])
        elif events_msg.opcode == SB.OPCODES.cr_wr and events_msg.addr == 0x48 and events_msg.dest_pid in SB.EPS.internal_cores:
            for i in event_bits:
                events.append(self._broadcast_event_decoder[i])
        elif events_msg.opcode == SB.OPCODES.cr_wr and events_msg.addr == 0x5070 and events_msg.data[0][0] == 1:
            events.append(EVENTS_TYPES.unctrap)

        return set(sorted(events))
