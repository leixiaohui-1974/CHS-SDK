"""
A model predictive control (MPC) controller.
"""
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List
from collections import deque
from core_lib.core.interfaces import Controller, State

class MPCController(Controller):
    """
    An enhanced Model Predictive Controller that uses an Integral-Delay (ID) model
    for system prediction.
    """

    def __init__(self, **kwargs):
        """
        Initializes the MPC controller from a dictionary of arguments.
        """
        self.horizon = kwargs.pop('horizon')
        self.dt = kwargs.pop('dt', 10.0) # Default dt if not provided

        config = kwargs # The rest are config

        self.target_level = config["target_level"]
        self.q_weight = config.get("q_weight", 1.0)
        self.r_weight = config.get("r_weight", 0.1)
        self.bounds = config.get("bounds", (0, 1))
        self.K = config["id_model_gain"]
        self.tau = int(config["id_model_delay_steps"])
        self.control_history = deque([0.0] * self.tau, maxlen=self.tau)

    def _objective_function(self, control_sequence: np.ndarray,
                            current_level: float,
                            disturbance_forecast: List[float],
                            past_controls: List[float]) -> float:
        cost = 0.0
        predicted_level = current_level
        full_control_input = past_controls + list(control_sequence)
        num_steps = min(len(control_sequence), len(disturbance_forecast))

        for i in range(num_steps):
            effective_control_action = full_control_input[i]
            change_in_level = self.K * effective_control_action - disturbance_forecast[i]
            predicted_level += change_in_level * self.dt
            cost += self.q_weight * ((predicted_level - self.target_level) ** 2)
            cost += self.r_weight * (control_sequence[i] ** 2)
        return cost

    def compute_control_action(self, observation: State, dt: float) -> Any:
        self.dt = dt # Always use the dt from the harness
        current_level = observation.get("water_level")
        disturbance_forecast = observation.get("disturbance_forecast", [0.0] * self.horizon)

        if current_level is None:
            raise ValueError("Observation must contain 'water_level'.")

        if len(disturbance_forecast) < self.horizon:
            last_value = disturbance_forecast[-1] if disturbance_forecast else 0
            disturbance_forecast.extend([last_value] * (self.horizon - len(disturbance_forecast)))

        initial_guess = np.zeros(self.horizon)
        bnds = [self.bounds] * self.horizon
        past_controls_for_prediction = list(self.control_history)

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(current_level, disturbance_forecast, past_controls_for_prediction),
            method='SLSQP',
            bounds=bnds
        )

        optimal_action = result.x[0] if result.success else initial_guess[0]
        self.control_history.append(optimal_action)
        # The MPC for the canal should output a new SETPOINT for the PID
        return {'new_setpoint': float(optimal_action)}
