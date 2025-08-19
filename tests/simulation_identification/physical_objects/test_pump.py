import pytest

from swp.simulation_identification.physical_objects.pump import Pump

def test_pump_on_off():
    """
    Tests the basic on/off functionality of the pump.
    """
    params = {'max_flow_rate': 10.0, 'max_head': 20.0, 'power_consumption_kw': 75.0}
    initial_state = {'status': 0, 'outflow': 0, 'power_draw_kw': 0}
    pump = Pump(name="test_pump_onoff", initial_state=initial_state, parameters=params)

    # Test turning the pump ON
    action_on = {'control_signal': 1, 'upstream_head': 5.0, 'downstream_head': 10.0}
    result_on = pump.step(action_on, dt=1.0)

    assert result_on['status'] == 1
    assert result_on['outflow'] == params['max_flow_rate']
    assert result_on['power_draw_kw'] == params['power_consumption_kw']

    # Test turning the pump OFF
    action_off = {'control_signal': 0, 'upstream_head': 5.0, 'downstream_head': 10.0}
    result_off = pump.step(action_off, dt=1.0)

    assert result_off['status'] == 0
    assert result_off['outflow'] == 0.0
    assert result_off['power_draw_kw'] == 0.0

def test_pump_max_head_exceeded():
    """
    Tests that the pump produces no flow if the required head exceeds the max head.
    """
    params = {'max_flow_rate': 10.0, 'max_head': 20.0, 'power_consumption_kw': 75.0}
    initial_state = {'status': 0}
    pump = Pump(name="test_pump_maxhead", initial_state=initial_state, parameters=params)

    # Required head (25 - 4 = 21) is greater than max_head (20)
    action = {'control_signal': 1, 'upstream_head': 4.0, 'downstream_head': 25.0}
    result = pump.step(action, dt=1.0)

    assert result['status'] == 1 # The pump is on
    assert result['outflow'] == 0.0 # But it produces no flow
    assert result['power_draw_kw'] == 0.0 # And therefore draws no power

def test_pump_invalid_control_signal():
    """
    Tests that invalid control signals are ignored.
    """
    params = {'max_flow_rate': 10.0}
    initial_state = {'status': 0} # Start with pump off
    pump = Pump(name="test_pump_invalid", initial_state=initial_state, parameters=params)

    # Send an invalid signal
    action = {'control_signal': 0.5, 'upstream_head': 5, 'downstream_head': 10}
    result = pump.step(action, dt=1.0)

    # Status should remain unchanged (off)
    assert result['status'] == 0
    assert result['outflow'] == 0.0
