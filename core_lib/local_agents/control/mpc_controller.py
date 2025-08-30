"""
A model predictive control (MPC) controller, enhanced for MIMO systems.
"""
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List
from collections import deque
from core_lib.core.interfaces import Controller, State

class MPCController(Controller):
    """
    A MIMO (Multiple-Input Multiple-Output) Model Predictive Controller.
    """

    def __init__(self, **kwargs):
        self.dt = kwargs.pop('dt', 10.0)
        self.horizon = kwargs.pop('horizon')
        self.model_config = kwargs.pop('model_config')
        self.objective_config = kwargs.pop('objective_config')
        self.control_config = kwargs.pop('control_config')
        self.num_actuators = self.control_config['num_actuators']

    def _objective_function(self, control_sequence: np.ndarray, current_level: float) -> float:
        cost = 0.0
        predicted_level = current_level
        controls = control_sequence.reshape((self.horizon, self.num_actuators))
        q1_sequence, q2_sequence = controls[:, 0], controls[:, 1]
        target_level = self.objective_config['target_level']
        q_weight = self.objective_config.get('q_weight', 1.0)
        r_weight = self.objective_config.get('r_weight', 0.1)
        canal_area = self.model_config['canal_area']

        for i in range(self.horizon):
            q_in, q_out = q1_sequence[i], q2_sequence[i]
            predicted_level += (q_in - q_out) * self.dt / canal_area
            cost += q_weight * ((predicted_level - target_level) ** 2)
            cost += r_weight * (q_in**2 + q_out**2)
        return cost

    def compute_control_action(self, observation: State, dt: float) -> Any:
        self.dt = dt
        current_level = observation.get("process_variable") # Changed from water_level
        if current_level is None:
            raise ValueError("Observation from LocalControlAgent must contain 'process_variable'.")

        initial_guess = np.zeros(self.horizon * self.num_actuators)
        bnds = self.control_config['bounds'] * self.horizon

        result = minimize(
            self._objective_function,
            initial_guess,
            args=(current_level,),
            method='SLSQP',
            bounds=bnds
        )

        if not result.success:
            optimal_actions = np.zeros(self.num_actuators)
        else:
            optimal_actions = result.x.reshape((self.horizon, self.num_actuators))[0, :]

        action_dict = {}
        action_topics = self.control_config['action_topics']
        for i in range(self.num_actuators):
            topic = action_topics[i]
            action_dict[topic] = {'new_setpoint': float(optimal_actions[i])}
        return action_dict
