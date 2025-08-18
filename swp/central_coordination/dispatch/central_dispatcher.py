"""
Central Dispatcher Agent for hierarchical, high-level coordination.
"""
from swp.core.interfaces import Agent, State
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict

class CentralDispatcher(Agent):
    """
    The central coordinating agent for the entire water system.

    It operates at a higher level than local controllers. It subscribes to key
    system state information and uses a high-level strategy (e.g., rules, optimization)
    to send updated commands (like new setpoints) to the local agents.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, state_subscriptions: Dict[str, str],
                 command_topics: Dict[str, str], rules: Dict):
        """
        Initializes the CentralDispatcher.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            state_subscriptions: A dict mapping state names to topic names this agent should listen to.
                                 e.g., {'reservoir_level': 'state.reservoir.level'}
            command_topics: A dict mapping command names to the topics to publish them on.
                            e.g., {'gate1_command': 'command.gate1'}
            rules: A dictionary defining the high-level control strategy.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.command_topics = command_topics
        self.rules = rules
        self.latest_state = {}

        for state_name, topic in state_subscriptions.items():
            # Use a lambda to capture the state_name for the handler
            self.bus.subscribe(topic, lambda msg, name=state_name: self.handle_state_message(msg, name))

        print(f"CentralDispatcher '{self.agent_id}' created.")

    def handle_state_message(self, message: Message, state_name: str):
        """Stores the latest received state from a subscribed topic."""
        self.latest_state[state_name] = message
        # print(f"[{self.agent_id}] Updated state '{state_name}': {message}")

    def run(self, current_time: float):
        """
        The main execution loop for the dispatcher. At each step, it evaluates
        its rules based on the latest state and publishes new commands if necessary.

        Args:
            current_time: The current simulation time (ignored by this agent).
        """
        reservoir_level = self.latest_state.get('reservoir_level', {}).get('water_level')

        if reservoir_level is None:
            return

        flood_threshold = self.rules.get('flood_threshold', 20.0)
        normal_setpoint = self.rules.get('normal_setpoint', 15.0)
        flood_setpoint = self.rules.get('flood_setpoint', 12.0)

        target_setpoint = flood_setpoint if reservoir_level > flood_threshold else normal_setpoint

        command_message: Message = {'new_setpoint': target_setpoint}
        command_topic = self.command_topics.get('gate1_command')

        if command_topic:
            # To avoid spamming, we could add logic to only publish if the command changes
            print(f"[{self.agent_id}] Reservoir level is {reservoir_level:.2f}m. Commanding setpoint: {target_setpoint:.2f}m")
            self.bus.publish(command_topic, command_message)
