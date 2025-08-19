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
    system state information and forecasts, and uses a high-level strategy
    to send updated commands (like new setpoints) to the local agents.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus,
                 state_subscriptions: Dict[str, str],
                 command_topics: Dict[str, str],
                 forecast_subscriptions: Dict[str, str] = None,
                 rules: Any = None):
        """
        Initializes the CentralDispatcher.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus.
            state_subscriptions: A dict mapping local names to state topics to subscribe to.
            command_topics: A dict mapping local command names to command topics.
            forecast_subscriptions: A dict mapping local names to forecast topics.
            rules: A set of rules or a function that defines the dispatch logic.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.command_topics = command_topics
        self.rules = rules or {}
        self.latest_states: Dict[str, State] = {}
        self.forecasts: Dict[str, Dict] = {}
        self.active_setpoint_name = "normal"

        if state_subscriptions:
            for name, topic in state_subscriptions.items():
                self.bus.subscribe(topic, lambda msg, name=name: self.handle_state_message(msg, name))

        if forecast_subscriptions:
            for name, topic in forecast_subscriptions.items():
                self.bus.subscribe(topic, lambda msg, name=name: self.handle_forecast_message(msg, name))

        print(f"CentralDispatcher '{self.agent_id}' created.")

    def handle_state_message(self, message: Message, name: str):
        """Stores the latest received state from a subscribed topic."""
        self.latest_states[name] = message

    def handle_forecast_message(self, message: Message, name: str):
        """Stores the latest received forecast from a subscribed topic."""
        self.forecasts[name] = message
        print(f"  [{self.agent_id}] Received forecast '{name}': {message}")

    def run(self, current_time: float):
        """
        Evaluates the system state against a set of rules and activates a
        corresponding control profile. This version supports multiple reservoirs.
        """
        flood_alert_count = 0
        drought_alert_count = 0

        # Rule evaluation for each managed reservoir
        for name, state in self.latest_states.items():
            # Assumes state messages contain level, max_volume, etc.
            # And that the rule keys match the state names (e.g., 'res1').
            level = state.get('water_level')
            max_level = self.rules.get(f"{name}_max_level", float('inf'))

            if level is None:
                continue

            if level > self.rules.get(f"{name}_flood_threshold", max_level):
                flood_alert_count += 1
            elif level < self.rules.get(f"{name}_drought_threshold", 0):
                drought_alert_count += 1

        # Determine the system-wide control profile
        new_setpoint_name = "normal"
        if flood_alert_count > 0:
            new_setpoint_name = "system_flood"
        elif drought_alert_count > 0:
            new_setpoint_name = "system_drought"

        # --- Publish Commands ---
        # Only publish if the overall setpoint profile has changed
        if new_setpoint_name != self.active_setpoint_name:
            self.active_setpoint_name = new_setpoint_name
            print(f"  [{current_time}s] [{self.agent_id}] System state change. Activating '{self.active_setpoint_name}' profile.")

            # Send a new setpoint command for each managed entity
            for command_name, topic in self.command_topics.items():
                # e.g., command_name 'res1_control' -> entity_name 'res1'
                entity_name = command_name.replace('_control', '')

                # Rule key is like 'res1_system_flood_setpoint'
                rule_key = f"{entity_name}_{self.active_setpoint_name}_setpoint"

                if rule_key in self.rules:
                    setpoint = self.rules[rule_key]
                    print(f"  [{self.agent_id}] -> Sending new setpoint for '{entity_name}': {setpoint}")
                    # The message could contain a target level for an MPC controller
                    # or a direct value for a simpler controller.
                    self.bus.publish(topic, {'new_setpoint': setpoint})
