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
                 state_subscriptions: Dict[str, str], command_topics: Dict[str, str],
                 rules: Any):
        """
        Initializes the CentralDispatcher.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            state_subscriptions: A dict mapping local names to state topics to subscribe to.
                                 e.g., {'reservoir_level': 'state.reservoir.level'}
            command_topics: A dict mapping local command names to command topics.
                            e.g., {'gate1_command': 'command.gate1.setpoint'}
            rules: A set of rules or a function that defines the dispatch logic.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.command_topics = command_topics
        self.rules = rules
        self.latest_states: Dict[str, State] = {}
        self.has_run_initial = False

        for name, topic in state_subscriptions.items():
            # Use a lambda to capture the state_name for the handler
            self.bus.subscribe(topic, lambda msg, name=name: self.handle_state_message(msg, name))

        print(f"CentralDispatcher '{self.agent_id}' created.")

    def handle_state_message(self, message: Message, name: str):
        """Stores the latest received state from a subscribed topic."""
        self.latest_states[name] = message
        # print(f"[{self.agent_id}] Updated state '{name}': {message}")

    def run(self, current_time: float):
        """
        The main execution loop for the dispatcher. At each step, it evaluates
        its rules and publishes new commands if necessary.

        Args:
            current_time: The current simulation time.
        """
        # This is a generic, data-driven rule evaluator.
        # It can be extended with more sophisticated logic.

        # On the first run, send all initial setpoints
        if not self.has_run_initial:
            for command_name, topic in self.command_topics.items():
                # Assumes rule key is like 'res1_normal_setpoint' for command 'res1_command'
                entity_name = command_name.replace('_command', '')
                rule_key = f"{entity_name}_normal_setpoint"
                if rule_key in self.rules:
                    setpoint = self.rules[rule_key]
                    print(f"[{self.agent_id}] Sending initial setpoint for '{entity_name}' to {setpoint:.2f}")
                    self.bus.publish(topic, {'new_setpoint': setpoint})
            self.has_run_initial = True


        # --- Example-specific rule logic ---
        # This section can be replaced by a more generic rule engine.

        # Logic for the hierarchical control example
        if 'flood_threshold' in self.rules:
            reservoir_level = self.latest_states.get('reservoir_level', {}).get('water_level')
            if reservoir_level is not None and reservoir_level > self.rules['flood_threshold']:
                print(f"[{self.agent_id}] FLOOD ALERT: Reservoir level ({reservoir_level:.2f}m) is above threshold! "
                      f"Sending new setpoint: {self.rules['flood_setpoint']:.2f}m")
                self.bus.publish(self.command_topics['gate1_command'], {'new_setpoint': self.rules['flood_setpoint']})
