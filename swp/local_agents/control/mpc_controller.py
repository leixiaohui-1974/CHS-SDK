"""
A Model Predictive Control (MPC) controller.
"""
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List
from collections import deque
from swp.core.interfaces import Controller, State

class MPCController(Controller):
    """
    A Model Predictive Controller enhanced to use an Integral-Delay (ID) model
    for system predictions, as described in the design document for a "现地MPC".
    """

    def __init__(self, horizon: int, dt: float, config: Dict[str, Any]):
        """
        Initializes the MPCController.

        Args:
            horizon: The number of time steps to look ahead (prediction horizon).
            dt: The simulation time step in seconds.
            config: A dictionary with MPC parameters:
                - target_level: The desired water level.
                - q_weight: Weight for deviations from the target level.
                - r_weight: Weight for control action magnitude/change.
                - bounds: A tuple (min, max) for the control action.
                - id_model_gain (K): The gain of the Integral-Delay model.
                - id_model_delay_steps (tau): The time delay in discrete steps.
        """
        self.horizon = horizon
        self.dt = dt
        self.target_level = config["target_level"]
        self.q_weight = config.get("q_weight", 1.0)
        self.r_weight = config.get("r_weight", 0.1)
        self.bounds = config.get("bounds", (0, 1))

        # ID Model parameters
        self.K = config["id_model_gain"]
        self.tau = int(config["id_model_delay_steps"]) # Delay in number of steps

        # Store a history of control actions to handle the delay
        self.control_history = deque([0.0] * self.tau, maxlen=self.tau)

    def _objective_function(self, control_sequence: np.ndarray,
                            current_level: float,
                            disturbance_forecast: List[float],
                            past_controls: List[float]) -> float:
        """
        The function to be minimized. Calculates the total cost for a given
        control sequence using the ID model.
        """
        cost = 0.0
        predicted_level = current_level

        # The full control sequence available for prediction includes
        # historical actions and the new candidate sequence.
        full_control_input = past_controls + list(control_sequence)

        num_steps = min(len(control_sequence), len(disturbance_forecast))

        for i in range(num_steps):
            # The control action that affects the current step 'i' was
            # taken 'tau' steps ago.
            # Index is i + tau (for past_controls) - tau = i
            effective_control_action = full_control_input[i]

            # ID Model: Change in level is proportional to the delayed control action,
            # minus any external disturbances (e.g., forecasted outflow/demand).
            change_in_level = self.K * effective_control_action - disturbance_forecast[i]

            predicted_level += change_in_level * self.dt

            # Cost calculation
            # 1. Cost for deviating from the target level
            cost += self.q_weight * ((predicted_level - self.target_level) ** 2)

            # 2. Cost for control action magnitude
            cost += self.r_weight * (control_sequence[i] ** 2)

        return cost

    def compute_control_action(self, observation: State, dt: float) -> Any:
        """
        Computes the optimal control action using MPC with the ID model.
        """
        current_level = observation.get("water_level")
        # The 'disturbance_forecast' can be net inflow (inflow - base_outflow) or similar
        disturbance_forecast = observation.get("disturbance_forecast", [0.0] * self.horizon)

        if current_level is None:
            raise ValueError("Observation must contain 'water_level'.")

        # Ensure forecast matches horizon length
        if len(disturbance_forecast) < self.horizon:
            last_value = disturbance_forecast[-1] if disturbance_forecast else 0
            disturbance_forecast.extend([last_value] * (self.horizon - len(disturbance_forecast)))

        initial_guess = np.zeros(self.horizon)
        bnds = [self.bounds] * self.horizon

        # Pass the history of controls needed to simulate the delay
        past_controls_for_prediction = list(self.control_history)

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(current_level, disturbance_forecast, past_controls_for_prediction),
            method='SLSQP',
            bounds=bnds
        )

        optimal_action = result.x[0] if result.success else initial_guess[0]

        # Update control history with the chosen action
        self.control_history.append(optimal_action)

        return {'opening': float(optimal_action)}
