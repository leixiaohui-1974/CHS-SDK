from core_lib.core.interfaces import Controller, State
from core_lib.local_agents.control.pid_controller import PIDController
from typing import Dict, Any
import numpy as np

class HydropowerController(Controller):
    """
    A custom controller to manage a hydropower station with multiple turbines.
    It receives a power target and grid limit from a high-level agent and decides
    the flow for each turbine.
    """
    def __init__(self, head_m: float, num_turbines: int = 6, **kwargs):
        self.head = head_m
        self.num_turbines = num_turbines
        self.power_target_mw = 0
        self.grid_limit_mw = float('inf')

    def compute_control_action(self, observation: Dict[str, Any], dt: float) -> Dict[str, Any]:
        # Update head from the latest observation from the reservoir if available
        self.head = observation.get('water_level', self.head)

        # Determine the effective power target, respecting the grid limit
        effective_target = min(self.power_target_mw, self.grid_limit_mw)

        # Simple distribution logic: divide target equally among turbines
        target_per_turbine = effective_target / self.num_turbines

        # This is a highly simplified physical model to convert power to flow.
        # A real controller would use a pre-computed lookup table.
        # Power (W) = eff * rho * g * Q * H
        eff, rho, g = 0.9, 1000, 9.81
        required_flow_per_turbine = (target_per_turbine * 1e6) / (eff * rho * g * self.head) if self.head > 0 else 0

        # The LocalControlAgent will dispatch these actions to the correct topics
        actions = {}
        for i in range(self.num_turbines):
            # The key here does not matter as the LocalControlAgent uses a list of topics
            actions[f'turbine_{i+1}'] = {'outflow': required_flow_per_turbine}
        return actions

    def update_setpoint(self, message: Dict[str, Any]):
        """
        Receives a command message from a high-level agent to update targets.
        """
        if 'target_mw' in message:
            self.power_target_mw = message.get('target_mw', self.power_target_mw)
            print(f"[{self.__class__.__name__}] New power target: {self.power_target_mw:.2f} MW")
        if 'limit_mw' in message:
            self.grid_limit_mw = message.get('limit_mw', self.grid_limit_mw)
            print(f"[{self.__class__.__name__}] New grid limit: {self.grid_limit_mw:.2f} MW")


class DirectGateController(Controller):
    """
    A simple controller that directly sets the gate opening based on its setpoint.
    """
    def __init__(self, setpoint=1.0, **kwargs):
        self.setpoint = setpoint

    def compute_control_action(self, obs, dt):
        return {'opening': self.setpoint}

    def update_setpoint(self, msg):
        self.setpoint = msg.get('new_setpoint', self.setpoint)


class JointPIDController(Controller):
    """
    A controller that uses a single PID to compute a net flow demand and then
    splits this demand into two separate control actions (e.g., for a pump and a valve).
    """
    def __init__(self, pid_params: dict, actuator_limits: dict, messaging_params: dict, **kwargs):
        """
        Initializes the JointPIDController.

        Args:
            pid_params: Dictionary with PID configuration (Kp, Ki, Kd, setpoint, etc.).
            actuator_limits: Dictionary with max values for the actuators (e.g., max_inflow).
            messaging_params: Dictionary with topic names for the output signals.
        """
        self.pid_controller = PIDController(
            Kp=pid_params['Kp'], Ki=pid_params['Ki'], Kd=pid_params['Kd'],
            setpoint=pid_params['setpoint'],
            min_output=pid_params.get('min_output', -1e6),
            max_output=pid_params.get('max_output', 1e6)
        )

        self.max_inflow = actuator_limits['max_inflow']
        self.max_outflow = actuator_limits['max_outflow']

        self.pump_topic = messaging_params['pump_command_topic']
        self.valve_topic = messaging_params['valve_command_topic']
        print(f"JointPIDController created. Pump topic: '{self.pump_topic}', Valve topic: '{self.valve_topic}'.")

    def compute_control_action(self, observation: State, dt: float) -> Dict[str, float]:
        """
        Computes the net flow demand and splits it into pump and valve actions.

        Args:
            observation: The current state, must contain the key 'process_variable'.
            dt: The time step duration in seconds.

        Returns:
            A dictionary where keys are topic names and values are the control signals.
        """
        net_flow_demand = self.pid_controller.compute_control_action(observation, dt)

        pump_inflow = 0.0
        valve_outflow = 0.0

        if net_flow_demand > 0:
            pump_inflow = net_flow_demand
        else:
            valve_outflow = -net_flow_demand

        # Clamp to actuator limits
        pump_inflow = max(0, min(pump_inflow, self.max_inflow))
        valve_outflow = max(0, min(valve_outflow, self.max_outflow))

        # Return a dictionary mapping topic names to the computed signals
        return {
            self.pump_topic: pump_inflow,
            self.valve_topic: valve_outflow
        }

    def update_setpoint(self, message: Dict[str, Any]):
        """
        Updates the internal PID controller's setpoint.
        """
        if 'new_setpoint' in message and hasattr(self.pid_controller, 'set_setpoint'):
            self.pid_controller.set_setpoint(message['new_setpoint'])
