"""
Simulation model for a Gate.
"""
from typing import Any
from swp.core.interfaces import Simulatable, State, Parameters

class Gate(Simulatable):
    """
    Represents a gate, a fundamental control object in a water system.

    Its state is typically its opening percentage. The control action is the
    command to change the opening. The gate's behavior (e.g., discharge)
    depends on its own state and the state of connected objects (e.g., upstream
    and downstream water levels).
    """

    def __init__(self, gate_id: str, initial_state: State, params: Parameters):
        self.gate_id = gate_id
        self._state = initial_state
        self._params = params
        print(f"Gate '{self.gate_id}' created with initial state {self._state}.")

    def step(self, action: Any, dt: float) -> State:
        """
        Simulates the gate's change over a single time step.

        The action is typically a target opening. This model would simulate
        the gate motor moving towards that target.

        Args:
            action: The control action, e.g., {'target_opening': 0.8}.
            dt: The time step duration in seconds.

        Returns:
            The updated state of the gate.
        """
        # Placeholder logic: gate moves towards target opening at a max rate
        target_opening = action.get('target_opening', self._state.get('opening', 0))
        current_opening = self._state.get('opening', 0)
        max_rate = self._params.get('max_rate_of_change', 0.05) # 5% per second

        if target_opening > current_opening:
            new_opening = min(current_opening + max_rate * dt, target_opening)
        else:
            new_opening = max(current_opening - max_rate * dt, target_opening)

        self._state['opening'] = new_opening
        # print(f"Gate '{self.gate_id}' step: opening -> {self._state['opening']:.2f}")
        return self._state

    def get_state(self) -> State:
        """Returns the current state of the gate."""
        return self._state

    def set_state(self, state: State):
        """Sets the state of the gate."""
        self._state = state

    def get_parameters(self) -> Parameters:
        """Returns the model parameters of the gate."""
        return self._params

    def calculate_discharge(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the flow through the gate based on water levels.
        This is a core function but not part of the Simulatable interface.
        It's called by the system simulation harness.

        Args:
            upstream_level: Water level upstream of the gate.
            downstream_level: Water level downstream of the gate.

        Returns:
            The discharge (flow rate, m^3/s).
        """
        # Placeholder logic: simplified gate discharge formula
        opening = self._state.get('opening', 0)
        head_diff = upstream_level - downstream_level
        if head_diff < 0:
            return 0 # No reverse flow in this simple model

        discharge_coeff = self._params.get('discharge_coefficient', 0.6)
        width = self._params.get('width', 10) # meters
        # Q = C * A * sqrt(2*g*h)
        # A = opening * width
        g = 9.81
        discharge = discharge_coeff * (opening * width) * (2 * g * head_diff)**0.5
        return discharge
