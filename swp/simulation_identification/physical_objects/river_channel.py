"""
Simulation model for a River Channel.
"""
from typing import Dict, Any
from swp.core.interfaces import Simulatable, State, Parameters

class RiverChannel(Simulatable):
    """
    Represents a segment of a river.

    This model simulates the flow of water through a river reach. Its state
    can include variables like water level at different points, or simply the
    total volume of water in the reach.

    For this implementation, we use a simplified "linear reservoir" model, where
    the outflow is proportional to the storage (volume) in the channel.
    """

    def __init__(self, channel_id: str, initial_state: State, params: Parameters):
        self.channel_id = channel_id
        self._state = initial_state
        self._params = params # e.g., {'k': 0.0001, 'length': 5000}
        print(f"RiverChannel '{self.channel_id}' created with initial state {self._state}.")

    def step(self, action: Any, dt: float) -> State:
        """
        Simulates the river channel's change over a single time step.

        Args:
            action: A dictionary of flows. For a river channel, the key 'inflow'
                    represents the total aggregated inflow from all upstream sources
                    as calculated by the simulation harness.
            dt: The time step duration in seconds.

        Returns:
            The updated state of the river channel.
        """
        inflow = action.get('inflow', 0)
        current_volume = self._state.get('volume', 0)

        # Outflow is proportional to storage (k * V)
        k = self._params.get('k', 0.0001) # Storage coefficient
        outflow = k * current_volume

        # Water balance equation
        delta_volume = (inflow - outflow) * dt
        new_volume = current_volume + delta_volume
        self._state['volume'] = new_volume

        # Update other state variables (e.g., water level) if needed
        # This is a simplification
        self._state['outflow'] = outflow
        # print(f"RiverChannel '{self.channel_id}' step: volume -> {self._state['volume']:.2f} m^3, outflow -> {outflow:.2f} m^3/s")
        return self._state

    def get_state(self) -> State:
        """Returns the current state of the river channel."""
        return self._state

    def set_state(self, state: State):
        """Sets the state of the river channel."""
        self._state = state

    def get_parameters(self) -> Parameters:
        """Returns the model parameters of the river channel."""
        return self._params
