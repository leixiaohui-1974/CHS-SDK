import pytest
import numpy as np
from unittest.mock import MagicMock

from swp.simulation_identification.identification.identification_agent import ParameterIdentificationAgent
from swp.central_coordination.collaboration.message_bus import MessageBus

@pytest.fixture
def agent_setup():
    """Sets up a mock model, bus, and the identification agent."""

    # Create a mock object that respects the Identifiable interface
    mock_model = MagicMock()
    mock_model.identify_parameters.return_value = {'param': 1.0}

    bus = MessageBus()
    config = {
        "identification_interval": 5,
        "identification_data_map": {
            "rainfall": "data/rainfall",
            "observed_runoff": "data/runoff"
        }
    }

    agent = ParameterIdentificationAgent(
        agent_id="test_id_agent",
        target_model=mock_model,
        message_bus=bus,
        config=config
    )

    return bus, agent, mock_model, config

def test_agent_collects_data(agent_setup):
    """Tests that the agent correctly subscribes and collects data."""
    bus, agent, _, config = agent_setup

    bus.publish("data/rainfall", {'value': 0.1})
    bus.publish("data/runoff", {'value': 10})
    bus.publish("data/rainfall", {'value': 0.2})
    bus.publish("data/runoff", {'value': 20})

    assert len(agent.data_history['rainfall']) == 2
    assert len(agent.data_history['observed_runoff']) == 2
    assert agent.new_data_count == 2
    assert agent.data_history['rainfall'] == [0.1, 0.2]

def test_agent_triggers_identification_at_interval(agent_setup):
    """Tests that the agent calls identify_parameters on the model when the interval is reached."""
    bus, agent, mock_model, config = agent_setup

    # Publish enough data to trigger identification
    for i in range(config["identification_interval"]):
        bus.publish("data/rainfall", {'value': 0.1 * i})
        bus.publish("data/runoff", {'value': 10 * i})

    # The agent should trigger on the next run call
    agent.run(current_time=100)

    # Assert that the model's method was called exactly once
    mock_model.identify_parameters.assert_called_once()

    # Assert that the data passed to the method is correct
    args, _ = mock_model.identify_parameters.call_args
    passed_data = args[0]
    assert 'rainfall' in passed_data
    assert 'observed_runoff' in passed_data
    assert isinstance(passed_data['rainfall'], np.ndarray)
    assert len(passed_data['rainfall']) == config["identification_interval"]

def test_agent_resets_history_after_identification(agent_setup):
    """Tests that the agent's internal history is cleared after identification."""
    bus, agent, _, config = agent_setup

    # Publish data and trigger identification
    for i in range(config["identification_interval"]):
        bus.publish("data/rainfall", {'value': 0.1})
        bus.publish("data/runoff", {'value': 10})

    agent.run(current_time=100)

    # Assert that history and counters are reset
    assert agent.new_data_count == 0
    assert len(agent.data_history['rainfall']) == 0
    assert len(agent.data_history['observed_runoff']) == 0
