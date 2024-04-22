#!/usr/bin/env python3.6.3a
from agents.cncu_agent.checkers.cncu_base_flow_agent import CNCU_BASE_FLOW_AGENT
from agents.cncu_agent.checkers.flows.address_decode.cncu_funnyio_0x2_0x5_flow import CNCU_FUNNYIO_0x2_0x5_FLOW


class CNCU_FUNNYIO_AGENT(CNCU_BASE_FLOW_AGENT):

    def _get_related_checker_flow(self, flow):
        if CNCU_FUNNYIO_0x2_0x5_FLOW.is_new_flow(flow):
            return CNCU_FUNNYIO_0x2_0x5_FLOW(flow)
        # TODO: ranzohar - uncomment
        # elif is_funnyio:
        #     ERROR
        return None


if __name__ == "__main__":
    CNCU_FUNNYIO_AGENT.initial()
