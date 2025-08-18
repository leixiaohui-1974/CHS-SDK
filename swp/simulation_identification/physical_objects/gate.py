"""
Simulation model for a Gate.
"""
from swp.core.interfaces import Simulatable, State, Parameters
from typing import Dict, Any

class Gate(Simulatable):
    """
    Represents a controllable gate in a water system.
    Its discharge is calculated based on the upstream water level provided by the harness.
    """

    def __init__(self, gate_id: str, initial_state: State, params: Parameters):
        self.gate_id = gate_id
        self._state = initial_state  # e.g., {'opening': 0.5}
        self._params = params  # e.g., {'max_rate_of_change': 0.1, 'discharge_coefficient': 0.6, 'width': 10}
        self._state['discharge'] = 0  # Initial discharge
        print(f"Gate '{self.gate_id}' created with initial state {self._state}.")

    def _calculate_discharge(self, upstream_level: float, downstream_level: float = 0) -> float:
        """
        Calculates the discharge through the gate using the orifice equation.
        Q = C * A * sqrt(2 * g * h)
        where A is the area of the opening (opening * width)
        and h is the head difference (upstream_level - downstream_level).
        """
        C = self._params.get('discharge_coefficient', 0.6)
        width = self._params.get('width', 10)
        g = 9.81  # acceleration due to gravity

        opening = self._state.get('opening', 0)
        area = opening * width

        head = upstream_level - downstream_level
        if head <= 0:
            return 0 # No flow or reverse flow

        discharge = C * area * (2 * g * head)**0.5
        return discharge

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the gate's state over a single time step.
        The new harness provides the `upstream_level` needed for discharge calculation.

        Args:
            action: A dictionary containing:
                    - 'control_signal': (Optional) The target opening for the gate.
                    - 'upstream_level': The water level of the component directly upstream.
            dt: The time step duration in seconds.
        """
        # Update gate opening based on control signal from controller or agent
        control_signal = action.get('control_signal')
        if control_signal is not None:
            max_roc = self._params.get('max_rate_of_change', 0.05)
            current_opening = self._state.get('opening', 0)

            target_opening = control_signal

            if target_opening > current_opening:
                new_opening = min(current_opening + max_roc * dt, target_opening)
            else:
                new_opening = max(current_opening - max_roc * dt, target_opening)

            max_opening = self._params.get('max_opening', 1.0)
            self._state['opening'] = max(0.0, min(new_opening, max_opening))

        # Calculate and update the discharge based on the new state and upstream level
        upstream_level = action.get('upstream_level', 0)
        self._state['discharge'] = self._calculate_discharge(upstream_level)

        return self._state

    def get_state(self) -> State:
        return self._state

    def set_state(self, state: State):
        self._state = state

    def get_parameters(self) -> Parameters:
        return self._params
