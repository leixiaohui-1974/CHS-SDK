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
        The main execution loop for the dispatcher. At each step, it evaluates
        its rules based on the latest states and forecasts, then publishes new
        commands if necessary.
        """
        # --- Proactive Control Logic ---
        # This logic decides which setpoint profile is active.
        new_setpoint_name = "normal" # Default to normal operations

        # Check for an inflow forecast that might trigger a proactive change
        inflow_forecast = self.forecasts.get("inflow_forecast")
        if inflow_forecast and inflow_forecast.get("trend") == "increasing":
            new_setpoint_name = "proactive_flood"

        # --- Reactive Control Logic (can override proactive) ---
        # This logic checks current state for immediate danger
        if 'flood_threshold' in self.rules:
            reservoir_level = self.latest_states.get('reservoir_level', {}).get('water_level')
            if reservoir_level is not None and reservoir_level > self.rules['flood_threshold']:
                new_setpoint_name = "reactive_flood"

        # --- Publish Commands ---
        # Only publish if the overall setpoint profile has changed
        if new_setpoint_name != self.active_setpoint_name:
            self.active_setpoint_name = new_setpoint_name
            print(f"  [{self.agent_id}] Event detected. Switching to '{self.active_setpoint_name}' control profile.")

            # Iterate through all command topics and send the appropriate setpoint
            # based on the active profile.
            for command_name, topic in self.command_topics.items():
                # Assumes rule key is like 'gate1_proactive_flood_setpoint'
                entity_name = command_name.replace('_command', '')
                rule_key = f"{entity_name}_{self.active_setpoint_name}_setpoint"

                if rule_key in self.rules:
                    setpoint = self.rules[rule_key]
                    print(f"  [{self.agent_id}] Sending new setpoint for '{entity_name}' to {setpoint:.2f}")
                    self.bus.publish(topic, {'new_setpoint': setpoint})
