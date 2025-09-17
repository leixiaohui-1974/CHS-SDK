import logging
from typing import Dict, Any

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.reservoir import Reservoir


class CentralDispatcherAgent(Agent):
    """
    A central dispatch agent that can operate in one of two modes:
    1. 'rule': Rule-based supervisory control (hysteresis).
    2. 'emergency': High-priority emergency override.

    The 'mpc' mode has been deprecated and moved to the dedicated CentralMPCAgent.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, **config: Dict[str, Any]):
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = config
        self.mode = self._config.get("mode")

        if not self.mode or self.mode not in ['rule', 'emergency']:
            raise ValueError("CentralDispatcherAgent mode must be 'rule' or 'emergency'. "
                             "'mpc' mode is now handled by CentralMPCAgent.")

        logging.info(f"CentralDispatcherAgent '{self.agent_id}' initializing in '{self.mode}' mode.")

        # Common attributes
        self.command_topic = self._config.get("command_topic")

        # Mode-specific initializations
        if self.mode == 'rule':
            # Initialization for rule-based mode
            self.subscribed_topic = self._config['subscribed_topic']
            self.observation_key = self._config['observation_key']
            self.params = self._config['dispatcher_params']
            self.current_observed_value = None
            self.bus.subscribe(self.subscribed_topic, self.handle_state_message)
            logging.info(f"Monitoring '{self.observation_key}' on topic '{self.subscribed_topic}'.")

        elif self.mode == 'emergency':
            # Initialization for emergency mode
            self.reservoir: Reservoir = self._config['reservoir']
            self.emergency_flood_level = self._config['emergency_flood_level']

    # --- Message Handlers ---
    def handle_state_message(self, message: Message):
        """Callback for 'rule' mode to update the agent's knowledge."""
        observed_value = message.get(self.observation_key)
        if observed_value is not None:
            self.current_observed_value = observed_value

    def run(self, current_time: float):
        """
        Main execution logic that delegates to the appropriate mode-specific method.
        """
        if self.mode == 'rule':
            self._run_rule_based(current_time)
        elif self.mode == 'emergency':
            self._run_emergency(current_time)

    # --- Mode-Specific Logic ---
    def _run_rule_based(self, current_time: float):
        """Rule-based (hysteresis) control logic."""
        if self.current_observed_value is None:
            return

        low_level = self.params['low_level']
        high_level = self.params['high_level']
        new_setpoint = None

        if self.current_observed_value < low_level:
            new_setpoint = self.params['high_setpoint']
        elif self.current_observed_value > high_level:
            new_setpoint = self.params['low_setpoint']

        if new_setpoint is not None:
            logging.info(f"Dispatcher '{self.agent_id}' issuing new setpoint: {new_setpoint}")
            command_message: Message = {'new_setpoint': new_setpoint}
            self.bus.publish(self.command_topic, command_message)

    def _run_emergency(self, current_time: float):
        """Emergency override logic."""
        current_level = self.reservoir.get_state().get('water_level', 0)

        if current_level > self.emergency_flood_level:
            logging.warning(f"!!! [{self.agent_id}] EMERGENCY OVERRIDE !!!")
            logging.warning(
                f"    Reservoir level {current_level:.2f}m has breached emergency level {self.emergency_flood_level:.2f}m.")
            logging.warning(f"    Forcing downstream supply gate closed.")

            override_message = {'control_signal': 0.0, 'sender': self.agent_id}
            self.bus.publish(self.command_topic, override_message)
