"""
Simulation model for a Gate.
"""
from swp.core.interfaces import Simulatable, State, Parameters
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Gate(Simulatable):
    """
    Represents a controllable gate in a water system.
    Its discharge is calculated based on the upstream water level provided by the harness.
    It can be controlled directly via its `step` method or via messages on a message bus.
    """

    def __init__(self, gate_id: str, initial_state: State, params: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        self.gate_id = gate_id
        self._state = initial_state  # e.g., {'opening': 0.5}
        self._params = params  # e.g., {'max_rate_of_change': 0.1, 'discharge_coefficient': 0.6, 'width': 10}
        self._state['discharge'] = 0  # Initial discharge
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_opening = self._state.get('opening', 0) # The desired opening

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Gate '{self.gate_id}' subscribed to action topic '{self.action_topic}'.")

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

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        new_target = message.get('control_signal')
        if new_target is not None:
            self.target_opening = new_target
            # print(f"Gate '{self.gate_id}' received new target opening: {self.target_opening}")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the gate's state over a single time step.
        The new harness provides the `upstream_level` needed for discharge calculation.

        Args:
            action: A dictionary containing:
                    - 'control_signal': (Optional) The target opening for the gate (for direct control).
                    - 'upstream_level': The water level of the component directly upstream.
            dt: The time step duration in seconds.
        """
        # Determine the target opening. Use signal from direct control if present,
        # otherwise use the target set by the message bus.
        control_signal = action.get('control_signal')
        if control_signal is not None:
            self.target_opening = control_signal

        # Update gate opening towards the target opening, respecting rate of change
        max_roc = self._params.get('max_rate_of_change', 0.05)
        current_opening = self._state.get('opening', 0)

        if self.target_opening > current_opening:
            new_opening = min(current_opening + max_roc * dt, self.target_opening)
        else:
            new_opening = max(current_opening - max_roc * dt, self.target_opening)

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
