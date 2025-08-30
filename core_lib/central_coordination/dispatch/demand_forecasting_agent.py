"""
Central agent for demand forecasting.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List, Dict

class DemandForecastingAgent(Agent):
    """
    A central agent responsible for forecasting water demand for the system.

    This agent subscribes to historical water usage data and uses a simple
    moving average model to predict future demand. The forecast is then

    published for use by other decision-making agents like a central dispatcher.
    """
    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 historical_data_topic: str,
                 forecast_topic: str,
                 forecast_interval_seconds: int = 86400,
                 window_size: int = 24,
                 forecast_horizon: int = 12,
                 max_history: int = 1000):
        """
        Initializes the DemandForecastingAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            historical_data_topic: Topic to subscribe to for aggregate historical usage data.
            forecast_topic: The topic to publish demand forecasts to.
            forecast_interval_seconds: How often (in simulation seconds) to generate a new forecast.
            window_size: The number of historical data points to use for the moving average.
            forecast_horizon: The number of future steps to include in the forecast.
            max_history: The maximum number of historical data points to store.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.historical_data_topic = historical_data_topic
        self.forecast_topic = forecast_topic
        self.forecast_interval = forecast_interval_seconds
        self.window_size = window_size
        self.forecast_horizon = forecast_horizon
        self.max_history = max_history
        self.demand_history: List[float] = []

        self.bus.subscribe(self.historical_data_topic, self.handle_data)

        print(f"DemandForecastingAgent '{self.agent_id}' initialized. Subscribed to '{self.historical_data_topic}'.")

    def handle_data(self, message: Message, topic: str):
        """
        Callback to collect historical data. Assumes message has a 'demand' key.
        """
        demand = message.get('demand')
        if isinstance(demand, (int, float)):
            self.demand_history.append(demand)
            # Keep history from growing indefinitely
            if len(self.demand_history) > self.max_history:
                self.demand_history.pop(0)

    def run(self, current_time: float):
        """
        The main execution logic. Periodically generates and publishes a new forecast.
        """
        if int(current_time) > 0 and int(current_time) % self.forecast_interval == 0:
            self.generate_forecast(current_time)

    def generate_forecast(self, current_time: float):
        """
        Generates a demand forecast using a simple moving average of the historical data.
        """
        if len(self.demand_history) < self.window_size:
            print(f"[{self.agent_id} at {current_time:.2f}] Not enough data to forecast (have {len(self.demand_history)}, need {self.window_size}).")
            return

        # Calculate the moving average of the last N data points
        last_n_demands = self.demand_history[-self.window_size:]
        predicted_demand = sum(last_n_demands) / len(last_n_demands)

        # Create a simple forecast by projecting this value over the horizon
        forecast_values = [predicted_demand] * self.forecast_horizon

        forecast_message = {
            "start_time": current_time,
            "horizon_steps": self.forecast_horizon,
            "demands": forecast_values,
            "model_type": "MovingAverage",
            "details": f"Moving average over last {self.window_size} data points."
        }

        self.bus.publish(self.forecast_topic, forecast_message)
        print(f"[{self.agent_id} at {current_time:.2f}] Published new forecast to '{self.forecast_topic}'.")
