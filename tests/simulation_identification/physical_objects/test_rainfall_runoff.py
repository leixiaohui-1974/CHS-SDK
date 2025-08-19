import pytest

from swp.simulation_identification.physical_objects.rainfall_runoff import RainfallRunoff
from swp.central_coordination.collaboration.message_bus import MessageBus

def test_rainfall_runoff_calculation():
    """
    Tests the basic runoff calculation: Runoff = Coeff * Intensity * Area
    """
    # 1. Setup
    # Using simple, clear numbers for easy verification
    params = {
        'catchment_area': 1000,  # m^2
        'runoff_coefficient': 0.5   # dimensionless
    }
    rainfall_intensity = 0.01  # m/s (equivalent to 36 mm/hr)
    dt = 60  # seconds

    # The component requires a message bus to receive rainfall data
    bus = MessageBus()
    rainfall_topic = "weather/rainfall"

    runoff_model = RainfallRunoff(
        name="test_runoff_calc",
        parameters=params,
        message_bus=bus,
        rainfall_topic=rainfall_topic
    )

    # 2. Manual Calculation for Expected Result
    expected_outflow = params['runoff_coefficient'] * rainfall_intensity * params['catchment_area']
    # Expected: 0.5 * 0.01 * 1000 = 5.0 m^3/s

    # 3. Execution
    # Simulate a message being published with the rainfall data
    bus.publish(rainfall_topic, {'rainfall_intensity': rainfall_intensity})

    # The 'action' for this component is currently unused, so pass an empty dict
    action = {}
    result_state = runoff_model.step(action, dt)

    # 4. Assertion
    assert 'outflow' in result_state
    assert result_state['outflow'] == pytest.approx(expected_outflow)

def test_rainfall_runoff_no_rainfall_message():
    """
    Tests that if no rainfall message is received, the outflow is zero.
    """
    # 1. Setup
    params = {'catchment_area': 1000, 'runoff_coefficient': 0.5}
    dt = 60
    bus = MessageBus()
    rainfall_topic = "weather/rainfall"

    runoff_model = RainfallRunoff(
        name="test_runoff_no_rain",
        parameters=params,
        message_bus=bus,
        rainfall_topic=rainfall_topic
    )

    # 2. Execution - Do NOT publish a message
    action = {}
    result_state = runoff_model.step(action, dt)

    # 3. Assertion
    assert result_state['outflow'] == pytest.approx(0.0)

def test_rainfall_runoff_resets_intensity():
    """
    Tests that rainfall intensity is reset to zero after a step, so that
    a single rainfall message doesn't persist forever.
    """
    # 1. Setup
    params = {'catchment_area': 1000, 'runoff_coefficient': 0.5}
    rainfall_intensity = 0.01
    dt = 60
    bus = MessageBus()
    rainfall_topic = "weather/rainfall"

    runoff_model = RainfallRunoff(
        name="test_runoff_reset",
        parameters=params,
        message_bus=bus,
        rainfall_topic=rainfall_topic
    )
    action = {}

    # 2. Execution - First step with rain
    bus.publish(rainfall_topic, {'rainfall_intensity': rainfall_intensity})
    first_step_state = runoff_model.step(action, dt)
    assert first_step_state['outflow'] > 0

    # 3. Execution - Second step with no new message
    second_step_state = runoff_model.step(action, dt)

    # 4. Assertion - Outflow should be zero in the second step
    assert second_step_state['outflow'] == pytest.approx(0.0)
