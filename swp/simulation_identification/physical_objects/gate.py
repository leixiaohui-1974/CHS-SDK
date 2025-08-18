"""
Simulation model for a Gate that can be controlled via a MessageBus.
"""
from typing import Any, Optional
from swp.core.interfaces import Simulatable, State, Parameters
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

class Gate(Simulatable):
    """
    Represents a gate, a fundamental control object in a water system.

    This version is enhanced to be a more autonomous component. It can subscribe
    to an action topic on the message bus to receive control commands, making it
    suitable for a decoupled, event-driven MAS architecture.
    """

    def __init__(self, gate_id: str, initial_state: State, params: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        self.gate_id = gate_id
        self._state = initial_state
        self._params = params
        self._action = {'target_opening': initial_state.get('opening', 0)} # Initialize with current state
        print(f"Gate '{self.gate_id}' created with initial state {self._state}.")

        if message_bus and action_topic:
            message_bus.subscribe(action_topic, self.handle_action_message)
            print(f"Gate '{self.gate_id}' subscribed to action topic '{action_topic}'.")

    def handle_action_message(self, message: Message):
        """Callback to handle incoming control action messages."""
        target_opening = message.get('control_signal')
        if target_opening is not None:
            self._action['target_opening'] = target_opening
            # print(f"[{self.gate_id}] Received new action: {self._action}")

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
        # In this event-driven version, the action is received from the message bus
        # and stored in self._action, so the 'action' parameter is ignored.
        target_opening = self._action.get('target_opening', self._state.get('opening', 0))
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
