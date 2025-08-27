import pytest

from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine

def test_power_generation():
    """
    Tests the basic power generation calculation under normal conditions.
    """
    params = {'efficiency': 0.85, 'max_flow_rate': 150.0}
    # The new __init__ is compatible with the old call for non-agent use
    turbine = WaterTurbine(name="test_turbine", initial_state={}, parameters=params)

    # Set inflow and action for the step
    inflow = 100.0
    turbine.set_inflow(inflow)
    action = {'upstream_head': 100.0, 'downstream_head': 80.0}

    # FIX: Manually set the target outflow to simulate an agent's command
    turbine.target_outflow = 120.0 # Agent wants 120, but only 100 is available

    # Manual calculation
    head = action['upstream_head'] - action['downstream_head']
    # P = η * ρ * g * Q * H
    expected_power = params['efficiency'] * 1000 * 9.81 * inflow * head

    # Execute step
    state = turbine.step(action, dt=1.0)

    assert state['outflow'] == pytest.approx(inflow) # Outflow should be limited by inflow
    assert state['power'] == pytest.approx(expected_power)

def test_outflow_limited_by_max_flow_rate():
    """
    Tests that the outflow is capped at the turbine's max_flow_rate.
    """
    max_flow = 150.0
    params = {'efficiency': 0.85, 'max_flow_rate': max_flow}
    turbine = WaterTurbine(name="test_turbine", initial_state={}, parameters=params)

    # Inflow is higher than the max flow rate
    inflow = 200.0
    turbine.set_inflow(inflow)
    action = {'upstream_head': 100.0, 'downstream_head': 80.0}

    # FIX: Agent wants more than is possible
    turbine.target_outflow = 300.0

    # Execute step
    state = turbine.step(action, dt=1.0)

    # Outflow should be capped at max_flow_rate
    assert state['outflow'] == pytest.approx(max_flow)

    # Power should be calculated using the capped outflow
    head = action['upstream_head'] - action['downstream_head']
    expected_power = params['efficiency'] * 1000 * 9.81 * max_flow * head
    assert state['power'] == pytest.approx(expected_power)

def test_outflow_limited_by_target_outflow():
    """
    Tests that the outflow is capped by the agent's target outflow.
    """
    params = {'efficiency': 0.85, 'max_flow_rate': 150.0}
    turbine = WaterTurbine(name="test_turbine", initial_state={}, parameters=params)

    inflow = 200.0
    turbine.set_inflow(inflow)
    action = {'upstream_head': 100.0, 'downstream_head': 80.0}

    # FIX: Agent wants less than the available inflow
    target_flow = 80.0
    turbine.target_outflow = target_flow

    state = turbine.step(action, dt=1.0)

    assert state['outflow'] == pytest.approx(target_flow)

def test_no_power_with_no_head():
    """
    Tests that no power is generated if the head difference is zero or negative.
    """
    params = {'efficiency': 0.85, 'max_flow_rate': 150.0}
    turbine = WaterTurbine(name="test_turbine", initial_state={}, parameters=params)
    turbine.set_inflow(100.0)
    turbine.target_outflow = 100.0 # Agent wants flow

    # Test with zero head
    action_zero_head = {'upstream_head': 80.0, 'downstream_head': 80.0}
    state_zero_head = turbine.step(action_zero_head, dt=1.0)
    assert state_zero_head['power'] == 0.0

    # Test with negative head
    action_neg_head = {'upstream_head': 79.0, 'downstream_head': 80.0}
    state_neg_head = turbine.step(action_neg_head, dt=1.0)
    assert state_neg_head['power'] == 0.0

def test_no_power_with_no_flow():
    """
    Tests that no power is generated if there is no flow, even with a head difference.
    """
    params = {'efficiency': 0.85, 'max_flow_rate': 150.0}
    turbine = WaterTurbine(name="test_turbine", initial_state={}, parameters=params)

    # Set inflow to zero
    turbine.set_inflow(0.0)
    turbine.target_outflow = 100.0 # Agent wants flow, but none is available
    action = {'upstream_head': 100.0, 'downstream_head': 80.0}

    # Execute step
    state = turbine.step(action, dt=1.0)

    assert state['outflow'] == 0.0
    assert state['power'] == 0.0
