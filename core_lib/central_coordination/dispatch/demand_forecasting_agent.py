"""
Central agent for demand forecasting.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List, Dict

class DemandForecastingAgent(Agent):
    """
    A central agent responsible for forecasting water demand for the system.

    This agent can use historical data, weather forecasts, and other external
    factors to predict future water needs, providing crucial input for
    the central dispatch and MPC agents.

    The current implementation uses a simple averaging model for demonstration.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, historical_data_topics: List[str], forecast_topic: str):
        """
        Initializes the DemandForecastingAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            historical_data_topics: Topics to subscribe to for historical usage data.
            forecast_topic: The topic to publish demand forecasts to.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.historical_data_topics = historical_data_topics
        self.forecast_topic = forecast_topic
        self.historical_data: Dict[str, List] = {topic: [] for topic in historical_data_topics}

        for topic in self.historical_data_topics:
            self.bus.subscribe(topic, self.handle_data)

        print(f"DemandForecastingAgent '{self.agent_id}' initialized. Subscribed to {len(self.historical_data_topics)} data topics.")

    def handle_data(self, message: Message, topic: str):
        """Callback to collect historical data."""
        if 'demand' in message:
            self.historical_data[topic].append(message['demand'])

    def run(self, current_time: float):
        """
        The main execution logic. Periodically generates and publishes a new forecast.
        """
        # For example, run the forecast every 24 hours (86400 seconds)
        if int(current_time) > 0 and int(current_time) % 86400 == 0:
            self.generate_forecast(current_time)

    def generate_forecast(self, current_time: float):
        """
        Generates a demand forecast based on the collected historical data.

        This is a simple averaging model. A real implementation would use
        a more sophisticated forecasting model (e.g., ARIMA, LSTM).
        """
        print(f"[{self.agent_id} at {current_time}] Generating new demand forecast...")

        all_demands = []
        for topic in self.historical_data_topics:
            all_demands.extend(self.historical_data[topic])

        if not all_demands:
            # No historical data, use a default forecast
            forecast_demands = [10.0] * 24 # Default forecast for 24 hours
        else:
            # Simple average of all historical demands
            avg_demand = sum(all_demands) / len(all_demands)
            forecast_demands = [avg_demand] * 24 # Forecast the average for the next 24 hours

        forecast = {"start_time": current_time, "horizon": 24, "demands": forecast_demands}

        self.bus.publish(self.forecast_topic, forecast)
        print(f"[{self.agent_id}] Published new forecast to '{self.forecast_topic}': {forecast_demands}")
