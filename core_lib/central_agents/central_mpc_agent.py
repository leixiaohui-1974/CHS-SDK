import logging
from typing import Dict, Any, List
import numpy as np
from scipy.optimize import minimize

from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.core.interfaces import Agent


class CentralMPCAgent(Agent):
    """
    A dedicated agent that performs Model Predictive Control (MPC) to determine
    optimal water level setpoints for downstream PID controllers.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, **config: Dict[str, Any]):
        """
        Initializes the MPC agent.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # --- Extract MPC parameters from config ---
        self.horizon = self._config["prediction_horizon"]
        self.time_step= self._config["dt"]
        self.q_weight = self._config["q_weight"]
        self.r_weight = self._config["r_weight"]
        self.state_keys = self._config["state_keys"]
        self.command_topics = self._config["command_topics"]

        # MPC model and optimization parameters
        self.target_levels = np.array(self._config["target_water_levels"])
        self.mpc_pid_model_kp = self._config["mpc_pid_model_kp"]
        self.initial_setpoint_guess = np.array(self._config["initial_setpoint_guess"])
        self.level_setpoint_bounds = self._config["level_setpoint_bounds"]
        self.flood_thresholds = np.array(self._config["flood_thresholds"])
        self.canal_areas = np.array(self._config["canal_surface_areas"])
        self.outflow_coeff = self._config["outflow_coefficient"]

        # --- State and forecast storage ---
        self.latest_states = {}
        self.latest_forecast = [0.0] * self.horizon

        # --- Subscribe to topics ---
        for key, topic in self._config["state_subscriptions"].items():
            self.bus.subscribe(topic, lambda msg, k=key: self._handle_state_message(msg, k))
        self.bus.subscribe(self._config["forecast_subscription"], self._handle_forecast_message)

        self.logger.info(f"CentralMPCAgent '{self.agent_id}' initialized with hierarchical logic.")

    def _handle_state_message(self, message: Message, name: str):
        """Callback to update state from sensor topics."""
        self.latest_states[name] = message.get('value', 0) # Assuming sensors publish with 'value' key

    def _handle_forecast_message(self, message: Message):
        """Callback to update forecast."""
        self.latest_forecast = message.get('inflow_forecast', [0.0] * self.horizon)

    def run(self, current_time: float):
        """
        Checks for new data and runs the MPC optimization to publish water level setpoints.
        """
        if len(self.latest_states) < len(self.state_keys):
            return  # Wait for all state updates

        optimal_setpoints = self._compute_optimal_setpoints()

        # Publish the resulting water level setpoints for the local PID controllers
        for topic, setpoint in optimal_setpoints.items():
            self.bus.publish(topic, {'value': setpoint})

    def _compute_optimal_setpoints(self) -> Dict[str, float]:
        """
        Computes the optimal water level setpoints for the first time step.
        """
        initial_levels = np.array([self.latest_states[key] for key in self.state_keys])
        num_canals = len(self.state_keys)

        # The optimization variable is a sequence of water level setpoints
        initial_guess = np.tile(self.initial_setpoint_guess, self.horizon)

        # Create bounds for the optimization variables (level setpoints)
        bounds = self.level_setpoint_bounds * self.horizon

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(initial_levels, self.latest_forecast, self.target_levels),
            method='SLSQP',
            bounds=bounds
        )

        optimal_setpoints = {}
        if result.success:
            optimal_levels_sequence = result.x.reshape((self.horizon, num_canals))
            first_optimal_levels = optimal_levels_sequence[0]
            for i, cmd_topic in enumerate(self.command_topics.values()):
                optimal_setpoints[cmd_topic] = float(first_optimal_levels[i])
        else:
            self.logger.error("MPC optimization failed. Falling back to initial guess setpoints.")
            for i, cmd_topic in enumerate(self.command_topics.values()):
                optimal_setpoints[cmd_topic] = float(self.initial_setpoint_guess[i])

        return optimal_setpoints

    def _objective_function(self, level_setpoints_sequence: np.ndarray, initial_levels: np.ndarray, forecast: List[float],
                            target_levels: np.ndarray) -> float:
        """
        Objective function for MPC optimization.
        This model predicts future water levels based on the water level setpoints sent to local PIDs.
        """
        cost = 0.0
        g = 9.81  # Gravitational acceleration
        num_canals = len(self.state_keys)
        level_setpoints = level_setpoints_sequence.reshape((self.horizon, num_canals))
        predicted_levels = np.copy(initial_levels).astype(float)

        for i in range(self.horizon):
            # --- Model the behavior of the downstream PID controllers ---
            # Simplified proportional model: opening = Kp * (setpoint - current_level)
            errors = level_setpoints[i] - predicted_levels
            openings = np.clip(self.mpc_pid_model_kp * errors, 0, 1)

            # --- Simulate the physical system using the calculated openings ---
            clamped_levels = np.maximum(predicted_levels, 0)

            # Upstream canal
            inflow_upstream = forecast[i]
            outflow_upstream = self.outflow_coeff * openings[0] * np.sqrt(2 * g * clamped_levels[0])
            level_change_upstream = (inflow_upstream - outflow_upstream) * self.dt / self.canal_areas[0]

            # Downstream canal
            inflow_downstream = outflow_upstream
            outflow_downstream = self.outflow_coeff * openings[1] * np.sqrt(2 * g * clamped_levels[1])
            level_change_downstream = (inflow_downstream - outflow_downstream) * self.dt / self.canal_areas[1]

            predicted_levels += np.array([level_change_upstream, level_change_downstream])

            # --- Calculate cost for this time step ---
            # Cost for deviation from overall target water levels
            cost += self.q_weight * np.sum((predicted_levels - target_levels) ** 2)

            # Cost for changes in the issued setpoints (control action)
            if i > 0:
                cost += self.r_weight * np.sum((level_setpoints[i] - level_setpoints[i - 1]) ** 2)

            # Penalty for flooding
            for j in range(num_canals):
                if predicted_levels[j] > self.flood_thresholds[j]:
                    cost += 1e6 * (predicted_levels[j] - self.flood_thresholds[j])

        return cost
