from swp.core.interfaces import Agent
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List, Optional

class HydropowerControlAgent(Agent):
    """
    A local control agent responsible for managing a group of hydropower turbines
    to meet a collective power generation target.

    It listens for high-level power targets and grid capacity limits, and
    translates them into specific outflow commands for each turbine.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 turbine_action_topics: List[str],
                 power_target_topic: str = "target/power/total",
                 grid_limit_topic: str = "grid/power/limit",
                 head_m: float = 10.0, # Assumed constant head in meters
                 turbine_efficiency: float = 0.9):
        super().__init__(agent_id)
        self.bus = message_bus
        self.turbine_action_topics = turbine_action_topics
        self.num_turbines = len(turbine_action_topics)

        self.power_target_topic = power_target_topic
        self.grid_limit_topic = grid_limit_topic

        # Assumed physical constants for power calculation
        self.head = head_m
        self.efficiency = turbine_efficiency
        self.rho = 1000  # Water density
        self.g = 9.81    # Gravity

        # Internal state
        self.total_power_target_mw = 10.0 # Default target in MW
        self.grid_power_limit_mw = float('inf') # Default limit in MW

        # Subscribe to topics
        self.bus.subscribe(self.power_target_topic, self.handle_power_target)
        self.bus.subscribe(self.grid_limit_topic, self.handle_grid_limit)

    def handle_power_target(self, message: Message):
        """Callback to update the total power target."""
        if 'target_mw' in message:
            self.total_power_target_mw = message['target_mw']
            print(f"[{self.agent_id}] Received new power target: {self.total_power_target_mw:.2f} MW")

    def handle_grid_limit(self, message: Message):
        """Callback to update the grid power limit."""
        if 'limit_mw' in message:
            self.grid_power_limit_mw = message['limit_mw']
            print(f"[{self.agent_id}] Received new grid limit: {self.grid_power_limit_mw:.2f} MW")

    def run(self, current_time: float):
        """
        The agent's main logic loop, executed at each simulation step.
        """
        # Determine the effective power target, respecting the grid limit
        effective_power_target_mw = min(self.total_power_target_mw, self.grid_power_limit_mw)

        # For simplicity, distribute the target equally among all turbines
        # A more advanced agent would use an economic dispatch table (see Example 5.3)
        power_per_turbine_mw = effective_power_target_mw / self.num_turbines
        power_per_turbine_w = power_per_turbine_mw * 1e6 # Convert MW to W

        # Convert power target to required outflow using the hydropower equation
        # P = η * ρ * g * Q * H  =>  Q = P / (η * ρ * g * H)
        denominator = self.efficiency * self.rho * self.g * self.head
        if denominator < 1e-3:
            outflow_per_turbine = 0.0
        else:
            outflow_per_turbine = power_per_turbine_w / denominator

        # Publish the same outflow command to each turbine
        for topic in self.turbine_action_topics:
            action_message = {
                'target_outflow': outflow_per_turbine,
                'sender': self.agent_id
            }
            self.bus.publish(topic, action_message)
