"""
Simulation model for a Pump.
"""
from swp.core.interfaces import Simulatable, State, Parameters
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Pump(Simulatable):
    """
    Represents a controllable pump in a water system.
    When 'on', it provides a certain flow rate, provided the head difference
    is within its operational limits.
    It can be controlled via the message bus.
    """

    def __init__(self, pump_id: str, initial_state: State, params: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        """
        Args:
            pump_id: Unique identifier for the pump.
            initial_state: e.g., {'status': 0} (0 for off, 1 for on)
            params: e.g., {'max_flow_rate': 10, 'max_head': 20, 'power_consumption_kw': 50}
            message_bus: The message bus for agent-based control.
            action_topic: The topic to listen on for control signals.
        """
        self.pump_id = pump_id
        self._state = initial_state
        self._params = params
        self._state['flow_rate'] = 0.0  # Initial flow rate in m^3/s
        self._state['power_draw_kw'] = 0.0 # Initial power draw

        self.bus = message_bus
        self.action_topic = action_topic
        self.target_status = self._state.get('status', 0) # 0 for off, 1 for on

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Pump '{self.pump_id}' subscribed to action topic '{self.action_topic}'.")

        print(f"Pump '{self.pump_id}' created with initial state {self._state}.")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the flow provided by the pump.
        If the pump is 'on', it delivers its max_flow_rate, unless the required
        head lift exceeds the max_head.
        """
        if self._state.get('status', 0) == 0:
            return 0.0 # Pump is off

        max_head = self._params.get('max_head', 20)
        required_head = downstream_level - upstream_level

        # If the required head lift is greater than what the pump can provide, flow is zero.
        # A more complex model could have a pump curve here.
        if required_head > max_head:
            return 0.0

        return self._params.get('max_flow_rate', 10.0)

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        new_target = message.get('control_signal')
        if new_target in [0, 1]:
            self.target_status = new_target

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the pump's state over a single time step.

        Args:
            action: A dictionary containing:
                    - 'control_signal': (Optional) The target status (0 for off, 1 for on).
                    - 'upstream_level': The water level at the pump's intake.
                    - 'downstream_level': The water level at the pump's outlet.
            dt: The time step duration in seconds.
        """
        # Update target status from direct control signal if present
        control_signal = action.get('control_signal')
        if control_signal in [0, 1]:
            self.target_status = control_signal

        # Update the state instantly
        self._state['status'] = self.target_status

        # Calculate and update the flow rate
        upstream_level = action.get('upstream_level', 0)
        downstream_level = action.get('downstream_level', 0)
        flow = self._calculate_flow(upstream_level, downstream_level)
        self._state['flow_rate'] = flow
        self._state['outflow'] = flow  # Ensure compatibility with the harness
        self._state['discharge'] = flow # Ensure compatibility with the harness

        # Update power draw
        if flow > 0:
             self._state['power_draw_kw'] = self._params.get('power_consumption_kw', 50.0)
        else:
            self._state['power_draw_kw'] = 0.0

        return self._state

    def get_state(self) -> State:
        return self._state

    def set_state(self, state: State):
        self._state = state

    def get_parameters(self) -> Parameters:
        return self._params

    def get_flow(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the prospective flow for a given time step, used by the harness.
        This is a stateless calculation based on provided levels and current pump status.
        """
        # This is a bit tricky for a pump, as its flow is not a passive result of head_diff.
        # The harness expects to get a prospective flow. We assume the pump is either on or off
        # and check if the head is viable.
        if self._state.get('status', 0) == 0:
            return 0.0

        max_head = self._params.get('max_head', 20)
        required_head = downstream_level - upstream_level

        if required_head > max_head:
            return 0.0

        return self._params.get('max_flow_rate', 10.0)
