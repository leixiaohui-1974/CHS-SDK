"""
Simulation model for a Valve.
"""
import math
import numpy as np
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters, Identifiable
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.config.parameter_manager import get_parameter_manager
from core_lib.config.constants import PhysicalConstants, MathematicalConstants, HydraulicConstants
from typing import Dict, Any, Optional

class Valve(PhysicalObjectInterface, Identifiable):
    """
    Represents a controllable valve in a water system.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        
        # 获取参数管理器
        self.param_manager = get_parameter_manager()
        
        # 物理常量定义（从常量类获取）
        self.GRAVITY_ACCELERATION = PhysicalConstants.GRAVITY_ACCELERATION
        self.PI = MathematicalConstants.PI
        self.PERCENT_CONVERSION = self.param_manager.get_unit_conversion('DECIMAL_TO_PERCENT')
        self.DIAMETER_FACTOR = HydraulicConstants.DIAMETER_FACTOR
        self.SQRT_FACTOR = HydraulicConstants.SQRT_FACTOR
        self.POWER_EXPONENT = HydraulicConstants.POWER_EXPONENT
        
        # 默认参数值（从参数管理器获取）
        self.DEFAULT_DISCHARGE_COEFFICIENT = self.param_manager.get_parameter('valve_parameters', 'default_discharge_coefficient', 0.6)
        self.DEFAULT_DIAMETER = self.param_manager.get_parameter('physical_objects', 'default_diameter', 0.5)
        self.DEFAULT_OPENING = HydraulicConstants.MIN_OPENING
        self.DEFAULT_OUTFLOW = self.param_manager.get_parameter('physical_objects', 'default_outflow', 0.0)
        self.DEFAULT_FULL_OPENING = HydraulicConstants.FULL_OPENING_PERCENT
        
        # 验证关键参数
        if 'discharge_coefficient' not in self._params:
            print(f"警告: 阀门 '{self.name}' 建议配置 'discharge_coefficient' 参数")
        if 'diameter' not in self._params:
            print(f"警告: 阀门 '{self.name}' 建议配置 'diameter' 参数")
            
        self._state.setdefault('outflow', self.DEFAULT_OUTFLOW)
        self._params.setdefault('discharge_coefficient', self.DEFAULT_DISCHARGE_COEFFICIENT)
        self._params.setdefault('diameter', self.DEFAULT_DIAMETER)
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_opening = self._state.get('opening', self.DEFAULT_FULL_OPENING)

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

        opening_percent = self._state.get('opening', self.DEFAULT_OPENING)
        # The discharge coefficient is now the parameter to be identified.
        # It's scaled by the opening.
        effective_C_d = C_d * (opening_percent / self.PERCENT_CONVERSION)

        area = self.PI * (diameter / self.DIAMETER_FACTOR)**self.DIAMETER_FACTOR
        head_diff = upstream_level - downstream_level

        if head_diff <= 0:
            return self.DEFAULT_OUTFLOW

        flow = effective_C_d * area * (self.SQRT_FACTOR * self.GRAVITY_ACCELERATION * head_diff)**self.POWER_EXPONENT
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

        area = self.PI * (self._params['diameter'] / self.DIAMETER_FACTOR)**self.DIAMETER_FACTOR

        # Vectorized calculation to find C_d for each time step
        head_diff = up_levels - down_levels
        # Avoid division by zero or sqrt of negative
        valid_indices = (head_diff > 0) & (openings > 0)

        if not np.any(valid_indices):
            print(f"[{self.name}] No valid data points for identification (head difference and opening must be positive).")
            return

        denominator = (openings[valid_indices] / 100.0) * area * np.sqrt(2 * self.GRAVITY_ACCELERATION * head_diff[valid_indices])

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
        print(f"[{self.name}] Received action message: {message}")
        if isinstance(new_target, (int, float)):
            min_opening = HydraulicConstants.MIN_OPENING * self.PERCENT_CONVERSION
            max_opening = HydraulicConstants.MAX_OPENING * self.PERCENT_CONVERSION
            self.target_opening = max(min_opening, min(max_opening, new_target))
            print(f"[{self.name}] Updated target_opening to: {self.target_opening}")

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        Updates the valve's state over a single time step.
        """
        control_signal = action.get('control_signal')
        if control_signal is not None:
             if isinstance(control_signal, (int, float)):
                min_opening = HydraulicConstants.MIN_OPENING * self.PERCENT_CONVERSION
                max_opening = HydraulicConstants.MAX_OPENING * self.PERCENT_CONVERSION
                self.target_opening = max(min_opening, min(max_opening, control_signal))

        self._state['opening'] = self.target_opening
        print(f"[{self.name}] Step: target_opening={self.target_opening}, _state['opening']={self._state['opening']}")

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

    def get_state(self) -> Dict[str, float]:
        """Returns the current state of the valve, including key parameters for logging."""
        # This overrides the base implementation to include parameters in the history log.
        state = self._state.copy()
        state['discharge_coefficient'] = self._params.get('discharge_coefficient')
        return state


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

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        Steps each valve in the station and aggregates their states.
        The `action` dict (containing upstream/downstream heads) is passed to each valve.
        """
        total_outflow = 0.0

        for valve in self.valves:
            # Individual valve control signals are received via their own message bus subscriptions.
            valve_state = valve.step(action, time_step)
            total_outflow += valve_state.get('outflow', 0)

        self._state['total_outflow'] = total_outflow

        return self._state

    @property
    def is_stateful(self) -> bool:
        return False
