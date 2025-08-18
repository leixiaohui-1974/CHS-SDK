"""
Simulation model for a Reservoir.
"""
from swp.core.interfaces import Simulatable, Identifiable, State, Parameters
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional, List

class Reservoir(Simulatable, Identifiable):
    """
    Represents a reservoir, a fundamental controlled object in a water system.

    Its state typically includes water level or storage volume. It is influenced
    by inflows (from rivers, rainfall) and outflows (through gates, pumps, evaporation).

    This version is message-aware and can subscribe to disturbance topics.
    """

    def __init__(self, reservoir_id: str, initial_state: State, params: Parameters,
                 message_bus: Optional[MessageBus] = None,
                 disturbance_topics: Optional[List[str]] = None):
        self.reservoir_id = reservoir_id
        self._state = initial_state
        self._params = params
        self.disturbance_inflow = 0.0 # Additional inflow from disturbances

        if message_bus and disturbance_topics:
            for topic in disturbance_topics:
                message_bus.subscribe(topic, self.handle_disturbance_message)

        print(f"Reservoir '{self.reservoir_id}' created with initial state {self._state}.")

    def handle_disturbance_message(self, message: Message):
        """Callback to handle incoming disturbance messages (e.g., rainfall)."""
        inflow_rate = message.get('inflow_rate', 0)
        self.disturbance_inflow += inflow_rate
        # print(f"[{self.reservoir_id}] Received disturbance inflow: {inflow_rate}")

    def step(self, action: Any, dt: float) -> State:
        """
        Simulates the reservoir's change over a single time step.
        """
        # Get base flows from the action dictionary (e.g., from harness)
        base_inflow = action.get('inflow', 0)
        base_outflow = action.get('outflow', 0)

        # Add the inflow received from disturbance messages
        total_inflow = base_inflow + self.disturbance_inflow

        # Reset the disturbance inflow for the next step
        self.disturbance_inflow = 0.0

        current_volume = self._state.get('volume', 0)
        surface_area = self._params.get('surface_area', 1e6) # m^2

        new_volume = current_volume + (total_inflow - base_outflow) * dt
        self._state['volume'] = new_volume
        self._state['water_level'] = new_volume / surface_area # Simplified relationship

        return self._state

    def get_state(self) -> State:
        """Returns the current state of the reservoir."""
        return self._state

    def set_state(self, state: State):
        """Sets the state of the reservoir."""
        self._state = state

    def get_parameters(self) -> Parameters:
        """Returns the model parameters of the reservoir."""
        return self._params

    def identify_parameters(self, data: Any, method: str = 'offline') -> Parameters:
        """
        Identifies reservoir parameters. Placeholder implementation.
        """
        print(f"Identifying parameters for Reservoir '{self.reservoir_id}' using {method} method.")
        return self._params
