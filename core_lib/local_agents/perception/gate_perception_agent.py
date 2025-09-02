from core_lib.core.interfaces import Agent
from core_lib.identification.rls_estimator import RLSEstimator

class GatePerceptionAgent(Agent):
    """
    A dedicated perception agent for a single gate structure.
    Its responsibilities include:
    1. Subscribing to raw sensor data from the physical gate.
    2. Cleaning and filtering the sensor data.
    3. Performing real-time identification of physical parameters (e.g., discharge coefficient).
    4. Publishing the cleaned, high-fidelity state information to the message bus.
    """
    def __init__(self, agent_id, message_bus, physical_object_name, 
                 identification_config=None, cleaner_config=None, 
                 initial_discharge_coefficient=0.6, **kwargs):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.physical_object_name = physical_object_name
        
        # --- Feature Initialization ---

        # 1. Data Cleaner (simplified - no external cleaner class needed)
        self.cleaner = None

        # 2. Real-time Identification (RLS Estimator for Discharge Coefficient)
        if identification_config:
            self.identifier = RLSEstimator(num_params=1, lambda_=identification_config.get('forgetting_factor', 0.98))
            self.identified_discharge_coeff = initial_discharge_coefficient
            self._publish(f'agent.{self.agent_id}.identified_discharge_coefficient', self.identified_discharge_coeff)
        else:
            self.identifier = None
        
        # Internal state for raw data
        self.raw_us_water_level = None
        self.raw_ds_water_level = None
        self.raw_gate_opening = None
        self.raw_flow_rate = None

        # Subscribe to raw physical data
        self._subscribe(f'physical.{self.physical_object_name}.upstream_water_level', self._on_raw_us_water_level)
        self._subscribe(f'physical.{self.physical_object_name}.downstream_water_level', self._on_raw_ds_water_level)
        self._subscribe(f'physical.{self.physical_object_name}.gate_opening', self._on_raw_gate_opening)
        self._subscribe(f'physical.{self.physical_object_name}.flow_rate', self._on_raw_flow_rate)

    def _publish(self, topic: str, data):
        """Publish data to a topic via the message bus."""
        self.message_bus.publish(topic, data)

    def _subscribe(self, topic: str, callback):
        """Subscribe to a topic via the message bus."""
        self.message_bus.subscribe(topic, callback)

    # --- Raw Data Callbacks ---
    def _on_raw_us_water_level(self, topic, data): self.raw_us_water_level = data
    def _on_raw_ds_water_level(self, topic, data): self.raw_ds_water_level = data
    def _on_raw_gate_opening(self, topic, data): self.raw_gate_opening = data
    def _on_raw_flow_rate(self, topic, data): self.raw_flow_rate = data

    def step(self, t):
        # 1. Clean data
        cleaned_us_level = self.cleaner.clean(self.raw_us_water_level) if self.cleaner and self.raw_us_water_level is not None else self.raw_us_water_level
        cleaned_ds_level = self.cleaner.clean(self.raw_ds_water_level) if self.cleaner and self.raw_ds_water_level is not None else self.raw_ds_water_level
        cleaned_opening = self.cleaner.clean(self.raw_gate_opening) if self.cleaner and self.raw_gate_opening is not None else self.raw_gate_opening
        cleaned_flow = self.cleaner.clean(self.raw_flow_rate) if self.cleaner and self.raw_flow_rate is not None else self.raw_flow_rate

        # 2. Publish cleaned data
        if cleaned_us_level is not None: self._publish(f'agent.{self.agent_id}.upstream_water_level', cleaned_us_level)
        if cleaned_ds_level is not None: self._publish(f'agent.{self.agent_id}.downstream_water_level', cleaned_ds_level)
        if cleaned_opening is not None: self._publish(f'agent.{self.agent_id}.gate_opening', cleaned_opening)
        if cleaned_flow is not None: self._publish(f'agent.{self.agent_id}.flow_rate', cleaned_flow)

        # 3. Update parameter identification if enabled
        if self.identifier and all([cleaned_us_level, cleaned_ds_level, cleaned_opening, cleaned_flow]):
             self._update_discharge_coefficient(cleaned_us_level, cleaned_ds_level, cleaned_opening, cleaned_flow)

    def _update_discharge_coefficient(self, us_level, ds_level, opening, flow):
        """
        Updates the gate discharge coefficient using the RLS estimator.
        Q = C * phi, where phi = A * sqrt(2*g*H)
        """
        import math
        # Parameters like gate width should ideally come from a config or physical object properties
        gate_width = 2.0 
        gate_area = gate_width * opening
        head = us_level - ds_level
        
        if head <= 0 or gate_area <= 0: return

        phi = gate_area * math.sqrt(2 * 9.81 * head)
        
        if phi > 0:
            y = flow
            x = [phi]
            self.identifier.update(x, y)
            self.identified_discharge_coeff = self.identifier.theta[0]
            self._publish(f'agent.{self.agent_id}.identified_discharge_coefficient', self.identified_discharge_coeff)

    def run(self, current_time: float):
        """
        The main execution loop for the agent.
        For this perception agent, the primary logic is in the step method
        which is called by the simulation framework.
        """
        # This agent is primarily event-driven through step() calls
        pass

    def stop(self):
        print(f"Stopping {self.agent_id}")

