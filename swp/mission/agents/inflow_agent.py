from swp.core.interfaces import Agent
from swp.central_coordination.collaboration.message_bus import MessageBus

class InflowAgent(Agent):
    """
    A simple helper agent that provides a constant inflow to a topic,
    simulating a steady source of water.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, inflow_topic: str, inflow_rate: float, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.inflow_topic = inflow_topic
        self.inflow_rate = inflow_rate

    def run(self, current_time: float):
        # Publish inflow at every step
        self.bus.publish(self.inflow_topic, {'inflow_rate': self.inflow_rate})
