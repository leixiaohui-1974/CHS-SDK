"""
Simulation model for a Valve.
"""
import math
import numpy as np
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters, Identifiable
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class Valve(PhysicalObjectInterface, Identifiable):
    """
    Represents a controllable valve in a water system.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self._params.setdefault('discharge_coefficient', 0.6)
        self._params.setdefault('diameter', 0.5)
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_opening = self._state.get('opening', 100.0)

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Valve '{self.name}' subscribed to action topic '{self.action_topic}'.")

        print(f"Valve '{self.name}' created with initial state {self._state}.")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """
        Calculates the flow through the valve using a modified orifice equation.
        """
        C_d = self._params['discharge_coefficient']
        diameter = self._params['diameter']
        g = 9.81

        opening_percent = self._state.get('opening', 0)
        # The discharge coefficient is now the parameter to be identified.
        # It's scaled by the opening.
        effective_C_d = C_d * (opening_percent / 100.0)

        area = math.pi * (diameter / 2)**2
        head_diff = upstream_level - downstream_level

        if head_diff <= 0:
            return 0

        flow = effective_C_d * area * (2 * g * head_diff)**0.5
        return flow

    def identify_parameters(self, data: Dict[str, np.ndarray]):
        """
        Identifies the `discharge_coefficient` parameter.

        Args:
            data: A dictionary containing historical data, expecting:
                  - 'openings': Valve opening percentages.
                  - 'upstream_levels': Upstream water levels.
                  - 'downstream_levels': Downstream water levels.
                  - 'observed_flows': Corresponding observed valve flows.
        """
        print(f"[{self.name}] Starting parameter identification for 'discharge_coefficient'.")
        # Extract data from the dictionary
        openings = data.get('openings')
        up_levels = data.get('upstream_levels')
        down_levels = data.get('downstream_levels')
        obs_flows = data.get('observed_flows')

        if any(d is None for d in [openings, up_levels, down_levels, obs_flows]):
            print(f"[{self.name}] ERROR: Missing data for identification.")
            return

        # Valve equation: flow = C_d * (opening/100) * A * sqrt(2*g*H)
        # So, C_d = flow / [(opening/100) * A * sqrt(2*g*H)]
        # We can calculate an estimated C_d for each data point and average them.

        g = 9.81
        area = math.pi * (self._params['diameter'] / 2)**2

        # Vectorized calculation to find C_d for each time step
        head_diff = up_levels - down_levels
        # Avoid division by zero or sqrt of negative
        valid_indices = (head_diff > 0) & (openings > 0)

        if not np.any(valid_indices):
            print(f"[{self.name}] No valid data points for identification (head difference and opening must be positive).")
            return

        denominator = (openings[valid_indices] / 100.0) * area * np.sqrt(2 * g * head_diff[valid_indices])

        # Avoid division by zero in the denominator
        valid_denominator = denominator > 1e-6

        estimated_coeffs = obs_flows[valid_indices][valid_denominator] / denominator[valid_denominator]

        # A simple approach is to take the mean of all calculated coefficients
        if len(estimated_coeffs) > 0:
            new_coeff = np.mean(estimated_coeffs)
            self._params['discharge_coefficient'] = new_coeff
            print(f"[{self.name}] Identification complete. New discharge_coefficient: {new_coeff:.4f}")
        else:
            print(f"[{self.name}] Identification skipped, no valid data points resulted in a valid coefficient.")


    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        new_target = message.get('control_signal')
        if isinstance(new_target, (int, float)):
            self.target_opening = max(0.0, min(100.0, new_target))

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Updates the valve's state over a single time step.
        """
        control_signal = action.get('control_signal')
        if control_signal is not None:
             if isinstance(control_signal, (int, float)):
                self.target_opening = max(0.0, min(100.0, control_signal))

        self._state['opening'] = self.target_opening

        opening_percent = self._state.get('opening', 0)

        if self._inflow > 0:
            if opening_percent > 0:
                outflow = self._inflow
            else:
                outflow = 0
        else:
            upstream_level = action.get('upstream_head', 0)
            downstream_level = action.get('downstream_head', 0)
            outflow = self._calculate_flow(upstream_level, downstream_level)

        self._state['outflow'] = outflow

        return self.get_state()


class ValveStation(PhysicalObjectInterface):
    """
    Represents a valve station, which is a collection of individual valves.
    It aggregates the flow of all valves within it. The control of individual
    valves is handled by an external agent.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters, valves: list[Valve]):
        super().__init__(name, initial_state, parameters)
        self.valves = valves
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('valve_count', len(self.valves))
        print(f"ValveStation '{self.name}' created with {len(self.valves)} valves.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Steps each valve in the station and aggregates their states.
        The `action` dict (containing upstream/downstream heads) is passed to each valve.
        """
        total_outflow = 0.0

        for valve in self.valves:
            # Individual valve control signals are received via their own message bus subscriptions.
            valve_state = valve.step(action, dt)
            total_outflow += valve_state.get('outflow', 0)

        self._state['total_outflow'] = total_outflow

        return self._state

    @property
    def is_stateful(self) -> bool:
        return False
