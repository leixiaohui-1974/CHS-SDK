"""
Simulation model for a Valve.
"""
import math
from swp.core.interfaces import Simulatable, State, Parameters
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Valve(Simulatable):
    """
    Represents a controllable valve in a water system.
    Its flow rate is calculated based on the head difference across it.
    The valve's opening percentage (0-100) adjusts its discharge capacity.
    It can be controlled directly via its `step` method or via messages on a message bus.
    """

    def __init__(self, valve_id: str, initial_state: State, params: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        """
        Args:
            valve_id: Unique identifier for the valve.
            initial_state: e.g., {'opening': 100} (percentage)
            params: e.g., {'diameter': 0.5, 'discharge_coefficient': 0.8}
            message_bus: The message bus for agent-based control.
            action_topic: The topic to listen on for control signals.
        """
        self.valve_id = valve_id
        self._state = initial_state
        self._params = params
        self._state['flow_rate'] = 0  # Initial flow rate in m^3/s

        self.bus = message_bus
        self.action_topic = action_topic
        self.target_opening = self._state.get('opening', 100.0) # The desired opening percentage

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Valve '{self.valve_id}' subscribed to action topic '{self.action_topic}'.")

        print(f"Valve '{self.valve_id}' created with initial state {self._state}.")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the flow through the valve using a modified orifice equation.
        Q = C_d * A * sqrt(2 * g * delta_h)
        where A is the area of the pipe, and C_d is the effective discharge
        coefficient, which is a function of the valve opening.
        """
        C_d_max = self._params.get('discharge_coefficient', 0.8)
        diameter = self._params.get('diameter', 0.5)
        g = 9.81  # acceleration due to gravity

        opening_percent = self._state.get('opening', 0)

        # Simple linear mapping of opening percentage to effective discharge coefficient
        effective_C_d = C_d_max * (opening_percent / 100.0)

        area = math.pi * (diameter / 2)**2
        head_diff = upstream_level - downstream_level

        if head_diff <= 0:
            return 0  # No flow or reverse flow (not modeled)

        flow = effective_C_d * area * (2 * g * head_diff)**0.5
        return flow

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        new_target = message.get('control_signal')
        if isinstance(new_target, (int, float)):
            # Clamp target opening between 0 and 100
            self.target_opening = max(0.0, min(100.0, new_target))

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the valve's state over a single time step.

        Args:
            action: A dictionary containing:
                    - 'control_signal': (Optional) The target opening percentage (0-100).
                    - 'upstream_level': The water level of the component directly upstream.
                    - 'downstream_level': The water level of the component directly downstream.
            dt: The time step duration in seconds (currently unused as change is instant).
        """
        # Update target opening from direct control signal if present
        control_signal = action.get('control_signal')
        if control_signal is not None:
             if isinstance(control_signal, (int, float)):
                self.target_opening = max(0.0, min(100.0, control_signal))

        # Update the state instantly
        self._state['opening'] = self.target_opening

        # Calculate and update the flow rate based on the new state and hydraulic conditions
        inflow = action.get('inflow', 0)
        opening_percent = self._state.get('opening', 0)

        if inflow > 0:
            # In a pump-driven system, pass the inflow through if the valve is open.
            if opening_percent > 0:
                flow = inflow
            else:
                flow = 0 # Valve is closed, blocks flow.
        else:
            # In a gravity-fed system, calculate flow based on head difference.
            upstream_level = action.get('upstream_level', 0)
            downstream_level = action.get('downstream_level', 0)
            flow = self._calculate_flow(upstream_level, downstream_level)

        self._state['flow_rate'] = flow
        self._state['outflow'] = flow  # Ensure compatibility with the harness
        self._state['discharge'] = flow # Ensure compatibility with the harness

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
        This is a stateless calculation based on provided levels and current valve opening.
        """
        return self._calculate_flow(upstream_level, downstream_level)
