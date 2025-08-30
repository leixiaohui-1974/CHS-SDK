"""
Simulation model for a Lake.
"""
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from typing import Dict, Any, List

class Lake(PhysicalObjectInterface):
    """
    Represents a lake, which is functionally similar to a reservoir.
    Its state is determined by the balance of inflows, outflows, and evaporation.
    The relationship between volume and water level is defined by a storage curve.

    State Variables:
        - volume (float): The current volume of water in the lake (m^3).
        - water_level (float): The current water level (m), interpolated from the storage curve.
        - outflow (float): The outflow from the lake for the current step (m^3/s).

    Parameters:
        - storage_curve (list): A list of [volume, level] pairs defining the lake's geometry.
        - evaporation_rate_m_per_s (float): The rate of evaporation in meters per second.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0.0)
        self.evaporation_rate_m_per_s = self._params.get('evaporation_rate_m_per_s', 0)

        if 'storage_curve' not in self._params:
            raise ValueError("Lake parameters must include a 'storage_curve'.")

        self._validate_and_prepare_storage_curve()

        # Set initial water level from initial volume
        if 'volume' in self._state:
            self._state['water_level'] = self._get_level_from_volume(self._state['volume'])

        print(f"Lake '{self.name}' created with initial state {self._state}.")

    def _validate_and_prepare_storage_curve(self):
        """Validates the storage curve and prepares it for interpolation."""
        curve = self._params['storage_curve']
        if not isinstance(curve, list) or len(curve) < 2 or not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in curve):
            raise ValueError("'storage_curve' must be a list of [volume, level] pairs.")

        self.storage_curve_np = np.array(sorted(curve, key=lambda p: p[0]))
        self._volumes = self.storage_curve_np[:, 0]
        self._levels = self.storage_curve_np[:, 1]

        if not np.all(np.diff(self._volumes) > 0):
            raise ValueError("Volumes in 'storage_curve' must be strictly increasing.")

    def _get_level_from_volume(self, volume: float) -> float:
        """Interpolates water level from volume using the storage curve."""
        return np.interp(volume, self._volumes, self._levels)

    def _get_volume_from_level(self, level: float) -> float:
        """Interpolates volume from water level using the storage curve."""
        return np.interp(level, self._levels, self._volumes)

    def _get_surface_area_from_volume(self, volume: float) -> float:
        """Estimates surface area by finding the slope of the storage curve at the current volume."""
        # Find the two volume points surrounding the current volume
        idx = np.searchsorted(self._volumes, volume, side='right')
        if idx == 0 or idx >= len(self._volumes):
            # If at the edges, use the slope of the nearest segment
            idx = max(1, min(idx, len(self._volumes) - 1))

        v1, v2 = self._volumes[idx-1], self._volumes[idx]
        l1, l2 = self._levels[idx-1], self._levels[idx]

        # dV/dL = area. So area = (v2-v1) / (l2-l1)
        if l2 - l1 > 1e-6: # Avoid division by zero for flat segments
            return (v2 - v1) / (l2 - l1)
        else:
            # Fallback for flat curves: use previous segment or a default small area
            if idx > 1:
                v0, l0 = self._volumes[idx-2], self._levels[idx-2]
                if l1 - l0 > 1e-6:
                    return (v1 - v0) / (l1 - l0)
            return 1.0 # Return a small positive area to avoid errors

    def set_parameters(self, parameters: Parameters):
        """Override to re-validate the storage curve when parameters are updated."""
        super().set_parameters(parameters)
        if 'storage_curve' in parameters:
            self._validate_and_prepare_storage_curve()

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """Advances the lake simulation for one time step."""
        inflow = self._inflow
        current_volume = self._state['volume']

        # Evaporation depends on the current surface area, which is not constant
        surface_area = self._get_surface_area_from_volume(current_volume)
        evaporation_volume_per_second = self.evaporation_rate_m_per_s * surface_area

        outflow = action.get('outflow', 0)
        max_possible_outflow = current_volume / dt if dt > 0 else 0
        outflow = min(outflow, max_possible_outflow)

        delta_volume = (inflow - outflow - evaporation_volume_per_second) * dt
        new_volume = max(0, current_volume + delta_volume)

        self._state['volume'] = new_volume
        self._state['water_level'] = self._get_level_from_volume(new_volume)
        self._state['outflow'] = outflow

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        return True

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """Identifies the storage curve parameters using historical data."""
        if not all(k in data for k in ['inflows', 'outflows', 'levels']):
            raise ValueError("Identification data must contain 'inflows', 'outflows', and 'levels'.")

        inflows = data['inflows']
        outflows = data['outflows']
        observed_levels = data['levels']
        dt = 3600  # Assume hourly data for now

        def _simulation_error(level_params: np.ndarray) -> float:
            candidate_curve = np.column_stack((self._volumes, level_params))
            candidate_curve = candidate_curve[candidate_curve[:, 0].argsort()]
            candidate_volumes = candidate_curve[:, 0]
            candidate_levels = candidate_curve[:, 1]

            simulated_volumes = np.zeros_like(inflows)
            initial_volume = np.interp(observed_levels[0], candidate_levels, candidate_volumes)
            simulated_volumes[0] = initial_volume

            for i in range(1, len(inflows)):
                # Evaporation is ignored in this offline identification for simplicity,
                # assuming it's a minor component compared to inflows/outflows or handled in preprocessing.
                delta_v = (inflows[i-1] - outflows[i-1]) * dt
                simulated_volumes[i] = simulated_volumes[i-1] + delta_v

            simulated_levels = np.interp(simulated_volumes, candidate_volumes, candidate_levels)
            rmse = np.sqrt(np.mean((simulated_levels - observed_levels)**2))
            return rmse

        initial_guess = self._levels
        bounds = [(initial_guess[i-1] if i > 0 else -np.inf,
                   initial_guess[i+1] if i < len(initial_guess)-1 else np.inf)
                  for i in range(len(initial_guess))]

        result = minimize(_simulation_error, initial_guess, method='L-BFGS-B', bounds=bounds)

        if result.success:
            new_levels = result.x
            new_storage_curve = np.column_stack((self._volumes, new_levels)).tolist()
            print(f"Parameter identification successful for '{self.name}'.")
            return {'storage_curve': new_storage_curve}
        else:
            print(f"Warning: Parameter identification failed for '{self.name}': {result.message}")
            return {'storage_curve': self._params['storage_curve']}
