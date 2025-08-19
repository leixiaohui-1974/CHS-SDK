import pytest
import numpy as np
from swp.local_agents.prediction.lstm_forecaster import LSTMFlowForecaster
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

@pytest.fixture
def lstm_setup():
    """Sets up a MessageBus and a basic LSTMFlowForecaster agent for testing."""
    bus = MessageBus()
    config = {
        "observation_topic": "data/inflow",
        "observation_key": "value",
        "forecast_topic": "forecast/inflow",
        "history_size": 100,
        "refit_interval": 40, # Should be > input_window + output_window
        "input_window_size": 30,
        "output_window_size": 5,
        "epochs": 1, # Use only 1 epoch for fast testing
        "learning_rate": 0.01
    }
    agent = LSTMFlowForecaster(agent_id="lstm_test_agent", message_bus=bus, config=config)
    return bus, agent, config

def test_lstm_agent_runs_without_crashing(lstm_setup):
    """
    A simple smoke test to ensure the agent's fit and forecast methods
    can be executed without runtime errors.
    """
    bus, agent, config = lstm_setup

    # Use a simple sine wave as data
    time_series = np.sin(np.linspace(0, 8 * np.pi, config["history_size"]))

    # 1. Populate history
    for value in time_series:
        agent.handle_observation_message({'value': value})

    # 2. Set up listener
    received_forecasts = []
    bus.subscribe(config["forecast_topic"], lambda msg: received_forecasts.append(msg))

    # 3. Run the agent
    # This should trigger both fitting and forecasting
    try:
        agent.run(current_time=100)
    except Exception as e:
        pytest.fail(f"Agent run method failed with an exception: {e}")

    # 4. Assert that a forecast was published
    assert len(received_forecasts) == 1, "A forecast message should have been published"

    forecast_message = received_forecasts[0]
    assert "values" in forecast_message
    assert "forecast_steps" in forecast_message
    assert len(forecast_message["values"]) == config["output_window_size"]
    assert forecast_message["forecast_steps"] == config["output_window_size"]
