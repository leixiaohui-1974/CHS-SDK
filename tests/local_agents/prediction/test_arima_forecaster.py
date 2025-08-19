import pytest
import numpy as np
from swp.local_agents.prediction.arima_forecaster import ARIMAForecaster
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

@pytest.fixture
def arima_setup():
    """Sets up a MessageBus and a basic ARIMAForecaster agent for testing."""
    bus = MessageBus()
    config = {
        "observation_topic": "data/inflow",
        "observation_key": "value",
        "forecast_topic": "forecast/inflow",
        "history_size": 50,
        "arima_order": (1, 0, 0),  # Use a simple AR(1) model for testing
        "forecast_steps": 5,
        "refit_interval": 10
    }
    agent = ARIMAForecaster(agent_id="arima_test_agent", message_bus=bus, config=config)
    return bus, agent, config

def test_arima_forecaster_collects_history(arima_setup):
    """Tests that the agent correctly collects data from the message bus."""
    bus, agent, config = arima_setup

    # Publish some messages
    for i in range(5):
        bus.publish(config["observation_topic"], {config["observation_key"]: i})

    assert len(agent.history) == 5
    assert agent.new_obs_since_fit == 5
    assert list(agent.history) == [0.0, 1.0, 2.0, 3.0, 4.0]

def test_arima_forecaster_fits_and_forecasts(arima_setup):
    """
    Tests the end-to-end process of fitting a model and publishing a forecast.
    """
    bus, agent, config = arima_setup

    # Use a simple, predictable time series
    # A sine wave is good because it's not just a straight line
    time_series = np.sin(np.linspace(0, 4 * np.pi, config["history_size"])) * 10 + 50

    # 1. Populate the agent's history
    for value in time_series:
        agent.handle_observation_message({config["observation_key"]: value})

    assert len(agent.history) == config["history_size"]

    # 2. Set up a listener to capture the forecast
    received_forecasts = []
    def forecast_listener(message: Message):
        received_forecasts.append(message)

    bus.subscribe(config["forecast_topic"], forecast_listener)

    # 3. Run the agent
    # With the history populated and new_obs_since_fit > refit_interval,
    # a single run should trigger both fitting and forecasting.
    agent.run(current_time=1)

    # 4. Assert the results
    assert len(received_forecasts) == 1, "A forecast message should have been published"

    forecast_message = received_forecasts[0]
    assert "values" in forecast_message
    assert "forecast_steps" in forecast_message
    assert len(forecast_message["values"]) == config["forecast_steps"]
    assert forecast_message["forecast_steps"] == config["forecast_steps"]

def test_arima_forecaster_does_not_forecast_with_insufficient_data(arima_setup):
    """Tests that no forecast is made if the history is too short."""
    bus, agent, config = arima_setup

    # Populate with only a few data points (less than refit_interval)
    for i in range(config["refit_interval"] - 1):
        bus.publish(config["observation_topic"], {config["observation_key"]: i})

    # Set up a listener
    received_forecasts = []
    bus.subscribe(config["forecast_topic"], lambda msg: received_forecasts.append(msg))

    # Run the agent
    agent.run(current_time=0)

    # Assert that no model was fitted and no forecast was published
    assert agent.model_fit is None
    assert len(received_forecasts) == 0
