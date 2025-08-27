"""
An agent that simulates water use from a component, acting as an outflow disturbance.
"""
from swp.core.interfaces import Agent
from swp.simulation_identification.physical_objects.canal import Canal

class WaterUseAgent(Agent):
    """
    A custom agent to simulate water being taken from a canal at a diversion point.
    This acts as a controllable outflow disturbance on a physical component.
    """
    def __init__(self, agent_id: str, canal_to_affect: Canal, start_time: float,
                 duration: float, diversion_rate: float, dt: float):
        super().__init__(agent_id)
        self.canal_to_affect = canal_to_affect
        self.start_time = start_time
        self.end_time = start_time + duration
        self.diversion_rate = diversion_rate  # m^3/s
        self.dt = dt

    def run(self, current_time: float):
        """
        If within the time window, remove water from the canal's volume.
        This is the main entry point called by the simulation harness.
        """
        if self.start_time <= current_time < self.end_time:
            # Directly manipulate the state of the physical object.
            # This is a simplification; in a real system, this might be a message
            # that the canal object itself would handle.
            volume_to_remove = self.diversion_rate * self.dt
            current_volume = self.canal_to_affect.get_state()['volume']
            new_volume = max(0, current_volume - volume_to_remove)
            self.canal_to_affect.set_state({'volume': new_volume})
