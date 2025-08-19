import pytest

from swp.simulation_identification.physical_objects.lake import Lake

def test_lake_mass_balance():
    """
    Tests the basic mass balance (inflow - outflow - evaporation) of the lake.
    """
    # 1. Setup
    params = {
        'surface_area': 1e6,
        'max_volume': 50e6,
        'evaporation_rate_m_per_s': 1e-8 # 10nm/s
    }
    initial_volume = 40e6
    initial_state = {'volume': initial_volume, 'water_level': 40.0, 'outflow': 0}
    lake = Lake(name="test_lake_balance", initial_state=initial_state, parameters=params)

    inflow = 200.0   # m^3/s
    outflow = 150.0  # m^3/s
    dt = 3600        # 1 hour

    lake.set_inflow(inflow)
    action = {'outflow': outflow}

    # 2. Manual Calculation for Expected Result
    evaporation_volume_per_second = params['evaporation_rate_m_per_s'] * params['surface_area']
    net_flow_per_second = inflow - outflow - evaporation_volume_per_second
    delta_volume = net_flow_per_second * dt
    expected_new_volume = initial_volume + delta_volume
    expected_new_water_level = expected_new_volume / params['surface_area']

    # 3. Execution
    result_state = lake.step(action, dt)

    # 4. Assertion
    assert result_state['volume'] == pytest.approx(expected_new_volume)
    assert result_state['water_level'] == pytest.approx(expected_new_water_level)
    assert result_state['outflow'] == outflow # Should be set to the requested outflow

def test_lake_max_volume_constraint():
    """
    Tests that the lake's volume does not exceed its max_volume.
    """
    params = {
        'surface_area': 1e6,
        'max_volume': 50e6,
        'evaporation_rate_m_per_s': 0 # Ignore evaporation for this test
    }
    # Start the lake almost full
    initial_volume = 49.99e6
    initial_state = {'volume': initial_volume}
    lake = Lake(name="test_lake_max", initial_state=initial_state, parameters=params)

    # High inflow, low outflow, should cause it to fill up
    inflow = 500.0
    outflow = 10.0
    dt = 3600

    lake.set_inflow(inflow)
    action = {'outflow': outflow}

    # Execute
    result_state = lake.step(action, dt)

    # Assert that the volume is capped at max_volume and not higher
    assert result_state['volume'] == pytest.approx(params['max_volume'])

def test_lake_min_volume_constraint():
    """
    Tests that the lake's volume does not go below zero.
    """
    params = {'surface_area': 1e6, 'max_volume': 50e6, 'evaporation_rate_m_per_s': 0}
    # Start with very little water
    initial_volume = 1000
    initial_state = {'volume': initial_volume}
    lake = Lake(name="test_lake_min", initial_state=initial_state, parameters=params)

    # No inflow, high outflow demand
    inflow = 0.0
    outflow = 500.0 # This would make the volume negative if not for the constraint
    dt = 60

    lake.set_inflow(inflow)
    action = {'outflow': outflow}

    # Execute
    result_state = lake.step(action, dt)

    # Assert that the volume is capped at 0
    assert result_state['volume'] == pytest.approx(0.0)
    # The actual outflow should also be limited by what's available
    assert result_state['outflow'] <= initial_volume / dt
