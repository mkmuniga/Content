from agents.cncu_agent.checkers.cncu_base_flow_agent import CNCU_BASE_FLOW_AGENT
from agents.cncu_agent.checkers.flows.address_decode.cncu_cfg_flow import CNCU_CFG_FLOW


class CNCU_DOWNSTREAM_MMIO_AGENT(CNCU_BASE_FLOW_AGENT):

    def _get_related_checker_flow(self, flow):
        if CNCU_CFG_FLOW.is_new_flow(flow):
            return CNCU_CFG_FLOW(flow)
        # TODO: ranzohar - uncomment
        # elif is cfg:
        #     ERROR
        return None


if __name__ == "__main__":
    CNCU_DOWNSTREAM_MMIO_AGENT.initial()
