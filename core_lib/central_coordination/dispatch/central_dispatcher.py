import logging
from typing import Dict, Any, List
import numpy as np
from scipy.optimize import minimize

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.reservoir import Reservoir


class CentralDispatcherAgent(Agent):
    """
    A unified central dispatch agent that can operate in one of three modes:
    1. 'rule': Rule-based supervisory control (hysteresis).
    2. 'emergency': High-priority emergency override.
    3. 'mpc': Model Predictive Control for global optimization.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, config: Dict[str, Any]):
        super().__init__(agent_id)
        self.bus = message_bus
        self.config = config
        self.mode = self.config.get("mode")

        if not self.mode or self.mode not in ['rule', 'emergency', 'mpc']:
            raise ValueError("CentralDispatcherAgent mode must be 'rule', 'emergency', or 'mpc'.")

        logging.info(f"CentralDispatcherAgent '{self.agent_id}' initializing in '{self.mode}' mode.")

        # Common attributes
        self.command_topic = self.config.get("command_topic")

        # Mode-specific initializations
        if self.mode == 'rule':
            # Initialization for rule-based mode
            self.subscribed_topic = self.config['subscribed_topic']
            self.observation_key = self.config['observation_key']
            self.params = self.config['dispatcher_params']
            self.current_observed_value = None
            self.bus.subscribe(self.subscribed_topic, self.handle_state_message)
            logging.info(f"Monitoring '{self.observation_key}' on topic '{self.subscribed_topic}'.")

        elif self.mode == 'emergency':
            # Initialization for emergency mode
            self.reservoir: Reservoir = self.config['reservoir']
            self.emergency_flood_level = self.config['emergency_flood_level']

        elif self.mode == 'mpc':
            # Initialization for MPC mode
            self.horizon = self.config["prediction_horizon"]
            self.dt = self.config["dt"]
            self.q_weight = self.config["q_weight"]
            self.r_weight = self.config["r_weight"]
            self.state_keys = self.config["state_keys"]
            self.command_topics = self.config["command_topics"]
            self.normal_setpoints = np.array(self.config["normal_setpoints"])
            self.emergency_setpoint = self.config["emergency_setpoint"]
            self.flood_thresholds = np.array(self.config["flood_thresholds"])
            self.canal_areas = np.array(self.config["canal_surface_areas"])
            self.outflow_coeff = self.config["outflow_coefficient"]
            self.latest_states = {}
            self.latest_forecast = [0.0] * self.horizon
            for key, topic in self.config["state_subscriptions"].items():
                self.bus.subscribe(topic, lambda msg, k=key: self._handle_mpc_state_message(msg, k))
            self.bus.subscribe(self.config["forecast_subscription"], self._handle_forecast_message)


    # --- Message Handlers ---
    def handle_state_message(self, message: Message):
        """Callback for 'rule' mode to update the agent's knowledge."""
        observed_value = message.get(self.observation_key)
        if observed_value is not None:
            self.current_observed_value = observed_value

    def _handle_mpc_state_message(self, message: Message, name: str):
        """Callback for 'mpc' mode to update state."""
        self.latest_states[name] = message.get('water_level', 0)

    def _handle_forecast_message(self, message: Message):
        """Callback for 'mpc' mode to update forecast."""
        self.latest_forecast = message.get('inflow_forecast', [0.0] * self.horizon)


    def run(self, current_time: float):
        """
        Main execution logic that delegates to the appropriate mode-specific method.
        """
        if self.mode == 'rule':
            self._run_rule_based(current_time)
        elif self.mode == 'emergency':
            self._run_emergency(current_time)
        elif self.mode == 'mpc':
            self._run_mpc(current_time)

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
            logging.warning(f"    Reservoir level {current_level:.2f}m has breached emergency level {self.emergency_flood_level:.2f}m.")
            logging.warning(f"    Forcing downstream supply gate closed.")

            override_message = {'control_signal': 0.0, 'sender': self.agent_id}
            self.bus.publish(self.command_topic, override_message)

    def _run_mpc(self, current_time: float):
        """MPC-based optimization logic."""
        if len(self.latest_states) < len(self.state_keys):
            return  # Wait for all state updates

        initial_levels = np.array([self.latest_states[key] for key in self.state_keys])
        use_emergency_setpoint = any(f > 0 for f in self.latest_forecast)
        target_setpoints = self.normal_setpoints if not use_emergency_setpoint else np.array([self.emergency_setpoint] * len(self.state_keys))

        num_canals = len(self.state_keys)
        initial_guess = np.tile(target_setpoints, self.horizon)
        bounds = [(2.0, 6.0)] * len(initial_guess)

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(initial_levels, self.latest_forecast, target_setpoints),
            method='SLSQP',
            bounds=bounds
        )

        if result.success:
            optimal_setpoints_sequence = result.x.reshape((self.horizon, num_canals))
            first_optimal_setpoints = optimal_setpoints_sequence[0]
            for i, cmd_topic in enumerate(self.command_topics.values()):
                self.bus.publish(cmd_topic, {'new_setpoint': float(first_optimal_setpoints[i])})
        else:
            logging.error(f"MPC optimization failed for agent '{self.agent_id}'. Falling back to default setpoints.")
            for i, cmd_topic in enumerate(self.command_topics.values()):
                self.bus.publish(cmd_topic, {'new_setpoint': float(target_setpoints[i])})

    def _objective_function(self, setpoints_sequence: np.ndarray, initial_levels: np.ndarray, forecast: List[float], target_setpoints: np.ndarray) -> float:
        """Objective function for MPC optimization."""
        cost = 0.0
        num_canals = len(self.state_keys)
        setpoints = setpoints_sequence.reshape((self.horizon, num_canals))
        predicted_levels = np.copy(initial_levels)

        for i in range(self.horizon):
            inflow_upstream = forecast[i]
            outflow_upstream = self.outflow_coeff * (1 / (setpoints[i][0] + 1e-6))
            level_change_upstream = (inflow_upstream - outflow_upstream) * self.dt / self.canal_areas[0]

            inflow_downstream = outflow_upstream
            outflow_downstream = self.outflow_coeff * (1 / (setpoints[i][1] + 1e-6))
            level_change_downstream = (inflow_downstream - outflow_downstream) * self.dt / self.canal_areas[1]

            predicted_levels += np.array([level_change_upstream, level_change_downstream])

            cost += self.q_weight * np.sum((setpoints[i] - target_setpoints)**2)
            if i > 0:
                cost += self.r_weight * np.sum((setpoints[i] - setpoints[i-1])**2)
            for j in range(num_canals):
                if predicted_levels[j] > self.flood_thresholds[j]:
                    cost += 1e6 * (predicted_levels[j] - self.flood_thresholds[j])

        return cost
