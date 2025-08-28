from swp.core.interfaces import Agent
from swp.central_coordination.collaboration.message_bus import MessageBus

class GridCommunicationAgent(Agent):
    """
    A simple agent that simulates interaction with an external power grid.

    It mimics the grid sending a new, lower power generation limit at a
    pre-defined time in the simulation to test the response of the control system.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 grid_limit_topic: str = "grid/power/limit",
                 rejection_time_s: float = 150.0,
                 new_limit_mw: float = 5.0):
        super().__init__(agent_id)
        self.bus = message_bus
        self.grid_limit_topic = grid_limit_topic
        self.rejection_time_s = rejection_time_s
        self.new_limit_mw = new_limit_mw
        self._rejection_sent = False

    def run(self, current_time: float):
        """
        The agent's main logic loop. Publishes a grid limit if the time is right.
        """
        if not self._rejection_sent and current_time >= self.rejection_time_s:
            print(f"[{self.agent_id}] Grid event triggered at t={current_time:.1f}s. Sending new power limit.")

            limit_message = {
                'limit_mw': self.new_limit_mw,
                'reason': 'Grid congestion',
                'sender': self.agent_id
            }
            self.bus.publish(self.grid_limit_topic, limit_message)
            self._rejection_sent = True
