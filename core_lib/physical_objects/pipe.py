"""
Simulation model for a Pipe.
"""
import math
from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters

class Pipe(PhysicalObjectInterface):
    """
    Represents a pipe, which transports water between two points.
    This model can use either the Darcy-Weisbach or Manning's equation
    to calculate flow, based on the 'calculation_method' parameter.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self._state.setdefault('head_loss', 0)

        self.method = self._params.get('calculation_method', 'darcy_weisbach')
        if self.method not in ['darcy_weisbach', 'manning']:
            raise ValueError(f"Unknown calculation_method: {self.method}")

        print(f"Pipe '{self.name}' created using '{self.method}' method.")

    def _calculate_flow_darcy_weisbach(self, head_difference: float, f: Optional[float] = None) -> float:
        """Calculates flow using the Darcy-Weisbach equation."""
        if head_difference <= 0:
            return 0

        g = 9.81
        friction_factor = f if f is not None else self._params['friction_factor']
        length = self._params['length']
        diameter = self._params['diameter']
        area = (math.pi / 4) * (diameter ** 2)

        # Q = A * sqrt(2 * g * h_L * D / (f * L))
        if friction_factor * length == 0: return 0
        flow = area * math.sqrt(2 * g * head_difference * diameter / (friction_factor * length))
        return flow

    def _calculate_flow_manning(self, head_difference: float, n: Optional[float] = None) -> float:
        """Calculates flow using the Manning's equation for a full circular pipe."""
        if head_difference <= 0:
            return 0

        manning_n = n if n is not None else self._params['manning_n']
        if manning_n == 0: return float('inf')

        length = self._params['length']
        if length == 0: return float('inf')

        diameter = self._params['diameter']

        area = (math.pi / 4) * (diameter ** 2)
        hydraulic_radius = diameter / 4 # For a full circular pipe
        slope = head_difference / length

        # Q = (1.0/n) * A * R_h^(2/3) * S^(1/2) --- SI units
        flow = (1.0 / manning_n) * area * (hydraulic_radius ** (2/3)) * math.sqrt(slope)
        return flow

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """Calculates the flow through the pipe for one time step."""
        upstream_head = action.get('upstream_head', 0)
        downstream_head = action.get('downstream_head', 0)
        head_difference = upstream_head - downstream_head

        if self.method == 'darcy_weisbach':
            outflow = self._calculate_flow_darcy_weisbach(head_difference)
        else: # manning
            outflow = self._calculate_flow_manning(head_difference)

        self._state['head_loss'] = head_difference if head_difference > 0 else 0
        self._state['outflow'] = outflow
        return self.get_state()

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """Identifies the pipe's hydraulic parameter (friction factor or Manning's n)."""
        required_keys = ['upstream_levels', 'downstream_levels', 'observed_flows']
        if not all(k in data for k in required_keys):
            raise ValueError(f"Identification data must contain {required_keys}.")

        up_levels = data['upstream_levels']
        down_levels = data['downstream_levels']
        obs_flows = data['observed_flows']
        head_diffs = up_levels - down_levels

        if self.method == 'manning':
            param_key = 'manning_n'
            calc_func = self._calculate_flow_manning
            initial_guess = self._params.get(param_key, 0.013)
            bounds = [(0.001, 0.1)] # Physical bounds for Manning's n
        else: # darcy_weisbach
            param_key = 'friction_factor'
            calc_func = self._calculate_flow_darcy_weisbach
            initial_guess = self._params.get(param_key, 0.02)
            bounds = [(0.001, 0.5)] # Physical bounds for f

        def _simulation_error(param_to_id: np.ndarray) -> float:
            """Objective function for the optimizer."""
            param = param_to_id[0]
            simulated_flows = np.array([calc_func(h, param) for h in head_diffs])
            rmse = np.sqrt(np.mean((simulated_flows - obs_flows)**2))
            return rmse

        result = minimize(
            _simulation_error,
            np.array([initial_guess]),
            method='L-BFGS-B', # This method supports bounds
            bounds=bounds
        )

        if result.success:
            new_param_val = result.x[0]
            print(f"Parameter identification successful for '{self.name}'. New {param_key} = {new_param_val:.6f}")
            return {param_key: new_param_val}
        else:
            print(f"Warning: Parameter identification failed for '{self.name}': {result.message}")
            return {}
