# ... existing code ...
from core_lib.data_processing.cleaner import Cleaner
from core_lib.identification.rls_estimator import RLSEstimator
import pandas as pd
from scipy.interpolate import griddata

class GateControlAgent(BaseControlAgent):
    """
    A control agent for operating a gate structure based on PID control.
    This enhanced version includes capabilities for data cleaning, real-time parameter identification,
    and multi-gate flow allocation.
    """

    def __init__(self, name, message_bus, config):
        super().__init__(name, message_bus, config)
        self.physical_object_name = config['physical_object_name']
        self.pid_controller = PIDController(
            kp=config.get('kp', 1.0),
            ki=config.get('ki', 0.1),
            kd=config.get('kd', 0.05),
            setpoint=config.get('initial_setpoint', 0)
        )
        self.control_variable = config.get('control_variable', 'water_level')
        self.target_location = config.get('target_location', 'upstream')

        # --- Enhanced Features Initialization ---

        # 1. Data Cleaner
        if 'cleaner_config' in config:
            self.cleaner = Cleaner(config['cleaner_config'])
        else:
            self.cleaner = None

        # 2. Real-time Identification (RLS Estimator for Discharge Coefficient)
        if 'identification_config' in config:
            self.identifier = RLSEstimator(dim=1, forgetting_factor=config['identification_config'].get('forgetting_factor', 0.98))
            self.identified_discharge_coeff = config.get('initial_discharge_coefficient', 0.6)
            self._publish(f'agent.{self.name}.identified_discharge_coefficient', self.identified_discharge_coeff)
        else:
            self.identifier = None

        # 3. Multi-Gate Flow Allocation Strategy
        if 'allocation_table_path' in config:
            self.allocation_table = pd.read_csv(config['allocation_table_path'])
            self.number_of_gates = config.get('number_of_gates', 1)
        else:
            self.allocation_table = None

        # --- Subscription to necessary topics ---
        self.us_water_level = None
        self.ds_water_level = None
        self.gate_opening = None
        self.flow_rate = None

        self._subscribe(f'physical.{self.physical_object_name}.upstream_water_level', self._on_us_water_level)
        self._subscribe(f'physical.{self.physical_object_name}.downstream_water_level', self._on_ds_water_level)
        self._subscribe(f'physical.{self.physical_object_name}.gate_opening', self._on_gate_opening)
        self._subscribe(f'physical.{self.physical_object_name}.flow_rate', self._on_flow_rate)
        self._subscribe(f'agent.{self.name}.setpoint', self._on_setpoint_update)


    def _on_us_water_level(self, topic, data):
        if self.cleaner:
            data = self.cleaner.clean(data)
        self.us_water_level = data

    def _on_ds_water_level(self, topic, data):
        if self.cleaner:
            data = self.cleaner.clean(data)
        self.ds_water_level = data
# ... existing code ...
    def step(self, t):
        if self.us_water_level is None or self.ds_water_level is None:
            return

        # Use the appropriate water level for control
        if self.target_location == 'upstream':
            current_value = self.us_water_level
        else:
            current_value = self.ds_water_level

        if current_value is None:
            return
            
        # Update parameter identification if enabled
        if self.identifier and all([self.us_water_level, self.ds_water_level, self.gate_opening, self.flow_rate]):
             self._update_discharge_coefficient()

        # PID calculates required TOTAL flow
        required_total_flow = self.pid_controller.step(current_value, self.dt)

        # If multi-gate allocation is defined, use it. Otherwise, assume single gate control.
        if self.allocation_table is not None:
            openings = self._allocate_flow_to_gates(required_total_flow, self.us_water_level, self.ds_water_level)
            for i in range(self.number_of_gates):
                self._publish(f'control.{self.physical_object_name}.gate_{i+1}.command', openings[i])
        else:
            # Fallback to simple inverse calculation for single gate
            # (Note: This is a simplification; a proper inverse model might be needed)
            if self.us_water_level > self.ds_water_level:
                head = self.us_water_level - self.ds_water_level
                # A simplified formula Q = C * W * G * sqrt(2*g*H) => G = Q / (C * W * sqrt(2*g*H))
                # This needs gate width (W) and other params from physical object, which is not ideal for agent architecture.
                # For simplicity, we assume the PID output is gate opening directly if no allocation is used.
                # A more robust solution would be to have the PID output gate opening directly.
                # Let's adjust PID to output opening directly for the simple case.
                opening = self.pid_controller.step(current_value, self.dt)
                self._publish(f'control.{self.physical_object_name}.command', opening)


    def _update_discharge_coefficient(self):
        """
        Update the gate discharge coefficient using RLS estimator.
        This is a simplified example. A real implementation would require a more detailed physical model formulation.
        Let's assume Q = C * phi, where phi = A * sqrt(2*g*H)
        """
        import math
        gate_area = 2.0 * self.gate_opening # Assume gate width is 2m for this example
        head = self.us_water_level - self.ds_water_level
        if head <= 0 or gate_area <= 0: return

        phi = gate_area * math.sqrt(2 * 9.81 * head)
        
        # RLS: y = theta * x
        y = self.flow_rate
        x = [phi]
        
        self.identifier.update(x, y)
        self.identified_discharge_coeff = self.identifier.theta[0]
        self._publish(f'agent.{self.name}.identified_discharge_coefficient', self.identified_discharge_coeff)


    def _allocate_flow_to_gates(self, total_flow, us_level, ds_level):
        """
        Allocate total required flow among multiple gates using an allocation table.
        The table should have columns like: 'total_flow', 'head', 'gate1_opening', 'gate2_opening', ...
        """
        head = us_level - ds_level
        if head <= 0:
            return [0.0] * self.number_of_gates

        points = self.allocation_table[['total_flow', 'head']].values
        openings = []
        for i in range(self.number_of_gates):
            values = self.allocation_table[f'gate{i+1}_opening'].values
            gate_opening = griddata(points, values, (total_flow, head), method='linear', fill_value=0)
            openings.append(float(gate_opening))
            
        return openings

    def stop(self):
        print(f"Stopping {self.name}")
