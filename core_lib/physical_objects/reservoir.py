"""
Simulation model for a Reservoir.
"""
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional, List

class Reservoir(PhysicalObjectInterface):
    """
    Represents a reservoir, a fundamental object in a water system.
    Its state is determined by the balance of inflows and outflows.
    It can receive physical inflow from upstream components and data-driven
    inflow (e.g., rainfall, observed data) from the message bus.
    The relationship between volume and water level is defined by a storage curve.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, inflow_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0) # Ensure outflow is in the state

        if 'storage_curve' not in self._params:
            raise ValueError("Reservoir parameters must include a 'storage_curve'.")

        self._validate_and_prepare_storage_curve()

        self.bus = message_bus
        # Get inflow topic from direct argument or from the parameters dictionary for flexibility
        self.inflow_topic = inflow_topic or self._params.get('inflow_topic')
        self.data_inflow = 0.0

        if self.bus and self.inflow_topic:
            self.bus.subscribe(self.inflow_topic, self.handle_inflow_message)
            print(f"Reservoir '{self.name}' subscribed to data inflow topic '{self.inflow_topic}'.")

        print(f"Reservoir '{self.name}' created with initial state {self._state}.")

    def _validate_and_prepare_storage_curve(self):
        """Validates the storage curve and prepares it for interpolation."""
        curve = self._params['storage_curve']
        if not isinstance(curve, list) or len(curve) < 2 or not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in curve):
            raise ValueError("'storage_curve' must be a list of [volume, level] pairs.")

        # Ensure it's a numpy array and sorted by volume for interpolation
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

    def set_parameters(self, parameters: Parameters):
        """Override to re-validate the storage curve when parameters are updated."""
        super().set_parameters(parameters)
        if 'storage_curve' in parameters:
            self._validate_and_prepare_storage_curve()

    def handle_inflow_message(self, message: Message):
        """Callback to handle incoming data-driven inflow messages."""
        inflow_value = message.get('control_signal') or message.get('inflow_rate')
        if isinstance(inflow_value, (int, float)):
            self.data_inflow += inflow_value

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """Simulates the reservoir's change over a single time step."""
        physical_inflow = self._inflow
        total_inflow = physical_inflow + self.data_inflow
        outflow = action.get('outflow', 0)

        current_volume = self._state.get('volume', 0)

        delta_volume = (total_inflow - outflow) * dt
        new_volume = max(0, current_volume + delta_volume)

        self._state['volume'] = new_volume
        self._state['water_level'] = self._get_level_from_volume(new_volume)
        self._state['outflow'] = outflow
        self._state['inflow'] = total_inflow # Add inflow to state for perception

        # Reset the data-driven inflow for the next step
        self.data_inflow = 0.0

        return self._state

    @property
    def is_stateful(self) -> bool:
        return True

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """
        Identifies the storage curve parameters using historical data.

        Args:
            data: A dictionary containing numpy arrays for:
                  - 'inflows': Time series of total inflow to the reservoir.
                  - 'outflows': Time series of total outflow from the reservoir.
                  - 'levels': Time series of observed water levels.
            method: The identification method (currently only 'offline' is supported).

        Returns:
            A dictionary containing the newly identified 'storage_curve'.
        """
        if not all(k in data for k in ['inflows', 'outflows', 'levels']):
            raise ValueError("Identification data must contain 'inflows', 'outflows', and 'levels'.")

        inflows = data['inflows']
        outflows = data['outflows']
        observed_levels = data['levels']

        # Assume dt is constant, derived from the number of data points over a period (e.g., 1 day)
        # This should ideally be provided in the data. For now, we assume steps are per hour.
        dt = 3600 # seconds

        def _simulation_error(level_params: np.ndarray) -> float:
            """Objective function for the optimizer."""
            # Create a candidate storage curve using the optimizer's current parameters
            candidate_curve = np.column_stack((self._volumes, level_params))

            # Sort by volume just in case, though we only optimize levels
            candidate_curve = candidate_curve[candidate_curve[:, 0].argsort()]
            candidate_volumes = candidate_curve[:, 0]
            candidate_levels = candidate_curve[:, 1]

            # Simulate water balance
            simulated_volumes = np.zeros_like(inflows)
            initial_volume = np.interp(observed_levels[0], candidate_levels, candidate_volumes)
            simulated_volumes[0] = initial_volume

            for i in range(1, len(inflows)):
                delta_v = (inflows[i-1] - outflows[i-1]) * dt
                simulated_volumes[i] = simulated_volumes[i-1] + delta_v

            # Convert simulated volumes to levels using the candidate curve
            simulated_levels = np.interp(simulated_volumes, candidate_volumes, candidate_levels)

            # Calculate RMSE
            rmse = np.sqrt(np.mean((simulated_levels - observed_levels)**2))
            return rmse

        # We optimize the 'level' part of the curve, keeping the 'volume' points fixed.
        initial_guess = self._levels

        # Define bounds to prevent levels from becoming non-monotonic
        bounds = [(initial_guess[i-1] if i > 0 else -np.inf,
                   initial_guess[i+1] if i < len(initial_guess)-1 else np.inf)
                  for i in range(len(initial_guess))]

        result = minimize(
            _simulation_error,
            initial_guess,
            method='L-BFGS-B', # A good quasi-Newton method that handles bounds
            bounds=bounds
        )

        if result.success:
            new_levels = result.x
            new_storage_curve = np.column_stack((self._volumes, new_levels)).tolist()
            print(f"Parameter identification successful for '{self.name}'.")
            return {'storage_curve': new_storage_curve}
        else:
            print(f"Warning: Parameter identification failed for '{self.name}': {result.message}")
            return {'storage_curve': self._params['storage_curve']} # Return original
