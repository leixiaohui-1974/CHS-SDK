import pytest
import math

from swp.simulation_identification.physical_objects.valve import Valve

def test_valve_flow_at_various_openings():
    """
    Tests that the valve's outflow correctly scales with its opening percentage.
    """
    params = {'diameter': 0.5, 'discharge_coefficient': 0.8}
    valve = Valve(name="test_valve", initial_state={'opening': 50.0}, parameters=params)

    action = {'upstream_head': 10.0, 'downstream_head': 5.0}
    head_diff = action['upstream_head'] - action['downstream_head']
    area = math.pi * (params['diameter'] / 2)**2
    g = 9.81

    # Test at 50% opening
    valve.step({'control_signal': 50.0, **action}, dt=1.0)
    effective_C_d_50 = params['discharge_coefficient'] * (50.0 / 100.0)
    expected_flow_50 = effective_C_d_50 * area * (2 * g * head_diff)**0.5
    assert valve.get_state()['outflow'] == pytest.approx(expected_flow_50)
    assert valve.get_state()['opening'] == 50.0

    # Test at 100% opening
    valve.step({'control_signal': 100.0, **action}, dt=1.0)
    effective_C_d_100 = params['discharge_coefficient'] * (100.0 / 100.0)
    expected_flow_100 = effective_C_d_100 * area * (2 * g * head_diff)**0.5
    assert valve.get_state()['outflow'] == pytest.approx(expected_flow_100)
    assert valve.get_state()['opening'] == 100.0

def test_valve_forced_flow():
    """
    Tests that the valve passes through a forced inflow when open.
    """
    valve = Valve(name="test_valve", initial_state={'opening': 100.0}, parameters={})
    forced_inflow = 7.5
    valve.set_inflow(forced_inflow)

    # Action is ignored when inflow is set, but provided for completeness
    action = {'upstream_head': 10.0, 'downstream_head': 5.0}
    state = valve.step(action, dt=1.0)

    assert state['outflow'] == pytest.approx(forced_inflow)

def test_valve_fully_closed():
    """
    Tests that there is no flow when the valve is fully closed (0% opening).
    """
    valve = Valve(name="test_valve", initial_state={'opening': 0.0}, parameters={'diameter': 0.5})

    # Test gravity flow when closed
    action = {'control_signal': 0.0, 'upstream_head': 10.0, 'downstream_head': 5.0}
    state_gravity = valve.step(action, dt=1.0)
    assert state_gravity['outflow'] == 0.0

    # Test forced flow when closed
    valve.set_inflow(10.0)
    state_forced = valve.step(action, dt=1.0)
    assert state_forced['outflow'] == 0.0

def test_valve_control_signal_clamps():
    """
    Tests that control signals for opening are clamped to the [0, 100] range.
    """
    valve = Valve(name="test_valve", initial_state={'opening': 50.0}, parameters={})
    action = {'upstream_head': 10.0, 'downstream_head': 5.0} # Flow doesn't matter here

    # Test clamping for value > 100
    state_over = valve.step({'control_signal': 150.0, **action}, dt=1.0)
    assert state_over['opening'] == 100.0

    # Test clamping for value < 0
    state_under = valve.step({'control_signal': -50.0, **action}, dt=1.0)
    assert state_under['opening'] == 0.0
