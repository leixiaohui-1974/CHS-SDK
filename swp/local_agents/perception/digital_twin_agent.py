"""
Digital Twin Agent for state synchronization.
"""
from swp.core.interfaces import Agent, Simulatable, State

class DigitalTwinAgent(Agent):
    """
    A Perception Agent that acts as a digital twin for a physical object.

    Its primary responsibility is to maintain an internal simulation model
    and keep its state synchronized with the real physical system by processing
    incoming sensor data. It provides the most up-to-date state estimate
    to other agents (e.g., control agents).
    """

    def __init__(self, agent_id: str, simulated_object: Simulatable):
        super().__init__(agent_id)
        self.model = simulated_object
        print(f"DigitalTwinAgent '{self.agent_id}' created for model '{getattr(simulated_object, 'id', 'N/A')}'.")

    def update_state_from_sensor(self, sensor_data: State):
        """
        Updates the internal model's state based on new sensor data.

        In a real system, this would involve data fusion, filtering (e.g., Kalman filter),
        and might trigger online parameter identification.
        """
        print(f"[{self.agent_id}] Received sensor data: {sensor_data}. Updating model state.")
        self.model.set_state(sensor_data)

    def get_current_state(self) -> State:
        """
        Provides the current best estimate of the object's state.
        """
        return self.model.get_state()

    def run(self):
        """
        The main loop for the agent.

        In a real deployment, this would run continuously, listening for sensor data
        from a message bus or other data source.
        """
        print(f"DigitalTwinAgent '{self.agent_id}' is running.")
        # This is a placeholder. A real agent would have a loop here, e.g.:
        # while True:
        #   sensor_data = self.message_bus.listen()
        #   self.update_state_from_sensor(sensor_data)
        #   time.sleep(1)
        pass
