"""
A Model Predictive Control (MPC) controller.
"""
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List
from swp.core.interfaces import Controller, State

class MPCController(Controller):
    """
    A simple Model Predictive Controller for a single-state system like a reservoir.

    This controller uses a simplified internal model to predict future states
    and optimizes a sequence of control actions to minimize a cost function.
    """

    def __init__(self, horizon: int, dt: float, config: Dict[str, Any]):
        """
        Initializes the MPCController.

        Args:
            horizon: The number of time steps to look ahead (prediction horizon).
            dt: The simulation time step in seconds.
            config: A dictionary with MPC parameters:
                - target_level: The desired water level for the reservoir.
                - q_weight: The weight for deviations from the target level (cost).
                - r_weight: The weight for control action changes (cost).
                - bounds: A tuple (min, max) for the control action (e.g., gate opening).
        """
        self.horizon = horizon
        self.dt = dt
        self.target_level = config["target_level"]
        self.q_weight = config.get("q_weight", 1.0)
        self.r_weight = config.get("r_weight", 0.1)
        self.bounds = config.get("bounds", (0, 1))

    def _objective_function(self, control_sequence: np.ndarray,
                            current_level: float, surface_area: float,
                            inflow_forecast: List[float]) -> float:
        """
        The function to be minimized. Calculates the total cost for a given
        control sequence.
        """
        cost = 0.0
        predicted_level = current_level

        # Ensure control_sequence and inflow_forecast have the same length (horizon)
        num_steps = min(len(control_sequence), len(inflow_forecast))

        for i in range(num_steps):
            # Simplified model: Outflow is proportional to control action (e.g., gate opening)
            # This is a major simplification. A real MPC would use a more accurate model.
            # Let's assume the control action is a normalized outflow rate.
            outflow = control_sequence[i] * 100 # Example scaling factor

            # Simplified water balance
            delta_volume = (inflow_forecast[i] - outflow) * self.dt
            predicted_level += delta_volume / surface_area

            # Cost calculation
            # 1. Cost for deviating from the target level
            cost += self.q_weight * ((predicted_level - self.target_level) ** 2)

            # 2. Cost for control action magnitude/change (simplified to magnitude here)
            cost += self.r_weight * (control_sequence[i] ** 2)

        return cost

    def compute_control_action(self, observation: State, dt: float) -> Any:
        """
        Computes the optimal control action using MPC.
        """
        # Extract necessary info from observation
        current_level = observation.get("water_level")
        surface_area = observation.get("surface_area")
        inflow_forecast = observation.get("inflow_forecast") # Expected to be a list

        if current_level is None or surface_area is None or inflow_forecast is None:
            raise ValueError("Observation must contain 'water_level', 'surface_area', and 'inflow_forecast'.")

        # Ensure forecast matches horizon length
        if len(inflow_forecast) < self.horizon:
            # Pad forecast with the last value if it's too short
            last_value = inflow_forecast[-1] if inflow_forecast else 0
            inflow_forecast.extend([last_value] * (self.horizon - len(inflow_forecast)))

        # Initial guess for the control sequence (e.g., all zeros)
        initial_guess = np.zeros(self.horizon)

        # Bounds for each control action in the sequence
        bnds = [self.bounds] * self.horizon

        # Run the optimization
        result = minimize(
            self._objective_function,
            initial_guess,
            args=(current_level, surface_area, inflow_forecast),
            method='SLSQP', # A method that supports bounds
            bounds=bnds
        )

        # The optimal control sequence is in result.x
        # MPC policy: apply only the first action of the sequence
        optimal_action = result.x[0] if result.success else initial_guess[0]

        # Return the action in the format expected by the actuator (e.g., a Gate)
        return {'opening': float(optimal_action)}
