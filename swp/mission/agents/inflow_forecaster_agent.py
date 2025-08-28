from swp.core.interfaces import Agent
from swp.central_coordination.collaboration.message_bus import MessageBus

class InflowForecasterAgent(Agent):
    """
    A simple helper agent that publishes a static forecast at the beginning
    of a simulation. In a real system, this would be replaced by a
    sophisticated forecasting model.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, topic: str, forecast_data: list, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic
        self.forecast_data = forecast_data

    def run(self, current_time: float):
        # Publish once at the beginning of the simulation
        if current_time == 0:
            print(f"--- InflowForecaster '{self.agent_id}' is publishing a forecast. ---")
            self.bus.publish(self.topic, {'inflow_forecast': self.forecast_data})
