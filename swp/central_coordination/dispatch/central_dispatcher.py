"""
Central Dispatcher Agent for hierarchical, high-level coordination.
"""
from swp.core.interfaces import Agent, State
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any

class CentralDispatcher(Agent):
    """
    The central coordinating agent for the entire water system.

    It operates at a higher level than local controllers. It subscribes to key
    system state information and uses a high-level strategy (e.g., rules, optimization)
    to send updated commands (like new setpoints) to the local agents.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 observation_topics: Dict[str, str], dispatcher_logic: Dict[str, Any]):
        """
        Initializes the CentralDispatcher.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            observation_topics: A dict mapping local names to state topics to subscribe to.
                                e.g., {'res1_level': 'state.res1.level'}
            dispatcher_logic: A dict defining the control strategy for each managed component.
                              e.g., {'res1': {'topic': 'command.res1.setpoint', 'initial_setpoint': 12.0}}
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.logic = dispatcher_logic
        self.latest_observations: Dict[str, State] = {}

        for name, topic in observation_topics.items():
            # Use a lambda to capture the state_name for the handler
            self.bus.subscribe(topic, lambda msg, name=name: self.handle_observation_message(msg, name))

        print(f"CentralDispatcher '{self.agent_id}' created.")

    def handle_observation_message(self, message: Message, name: str):
        """Stores the latest received state from a subscribed topic."""
        self.latest_observations[name] = message
        # print(f"[{self.agent_id}] Updated observation '{name}': {message}")

    def run(self, current_time: float):
        """
        The main execution loop for the dispatcher. At each step, it evaluates
        its logic for each managed entity and publishes new commands if necessary.

        Args:
            current_time: The current simulation time.
        """
        # On the first step, publish all initial setpoints
        if current_time == 0:
            for entity, logic in self.logic.items():
                command_topic = logic.get('topic')
                initial_setpoint = logic.get('initial_setpoint')
                if command_topic and initial_setpoint is not None:
                    print(f"[{self.agent_id}] Sending initial setpoint for '{entity}' to {initial_setpoint:.2f}")
                    self.bus.publish(command_topic, {'new_setpoint': initial_setpoint})

        # Example of a dynamic rule: if res1 is too high, lower res2's setpoint
        # This demonstrates system-wide coordination.
        res1_level = self.latest_observations.get('res1_level', {}).get('water_level')
        if res1_level and res1_level > 13.0:
             # This logic is arbitrary for demonstration purposes.
             res2_logic = self.logic.get('res2')
             if res2_logic:
                command_topic = res2_logic.get('topic')
                emergency_setpoint = 17.0 # lower than the initial 18.0
                print(f"[{self.agent_id}] EMERGENCY: res1 level is high ({res1_level:.2f}m)! Lowering res2 setpoint to {emergency_setpoint}m.")
                self.bus.publish(command_topic, {'new_setpoint': emergency_setpoint})
