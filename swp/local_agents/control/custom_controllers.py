from swp.core.interfaces import Controller
from typing import Dict, Any

class HydropowerController(Controller):
    """
    A custom controller to manage a hydropower station with a turbine and a bypass gate.
    It receives a target total outflow from the Central Dispatcher and decides how
    to allocate it between the turbine and the gate.
    """
    def __init__(self, turbine_max_flow: float, setpoint: float = 0.0, **kwargs):
        self.setpoint = setpoint
        self.turbine_max_flow = turbine_max_flow

    def compute_control_action(self, observation: Dict[str, Any], dt: float) -> Dict[str, Any]:
        target_total_outflow = self.setpoint
        inflow_to_station = observation.get('outflow', 0)
        turbine_flow = min(inflow_to_station, self.turbine_max_flow)
        gate_flow = max(0, target_total_outflow - turbine_flow)
        return {"turbine_target_outflow": turbine_flow, "gate_target_outflow": gate_flow}

    def update_setpoint(self, message: Dict[str, Any]):
        self.setpoint = message.get('new_setpoint', self.setpoint)
        print(f"  [HydropowerController] Received new command. Total outflow setpoint: {self.setpoint} m^3/s")

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
