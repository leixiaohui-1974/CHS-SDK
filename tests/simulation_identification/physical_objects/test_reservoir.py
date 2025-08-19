import pytest

from swp.simulation_identification.physical_objects.reservoir import Reservoir

def test_reservoir_mass_balance():
    """
    Tests the basic mass balance (inflow - outflow) of the reservoir.
    """
    # 1. Setup
    params = {'surface_area': 1.5e6}
    initial_volume = 25e6
    initial_state = {'volume': initial_volume, 'water_level': initial_volume / params['surface_area']}
    reservoir = Reservoir(name="test_res_balance", initial_state=initial_state, parameters=params)

    inflow = 500.0   # m^3/s
    outflow = 350.0  # m^3/s
    dt = 3600        # 1 hour

    reservoir.set_inflow(inflow)
    action = {'outflow': outflow}

    # 2. Manual Calculation for Expected Result
    net_flow_per_second = inflow - outflow
    delta_volume = net_flow_per_second * dt
    expected_new_volume = initial_volume + delta_volume
    expected_new_water_level = expected_new_volume / params['surface_area']

    # 3. Execution
    result_state = reservoir.step(action, dt)

    # 4. Assertion
    assert result_state['volume'] == pytest.approx(expected_new_volume)
    assert result_state['water_level'] == pytest.approx(expected_new_water_level)

def test_reservoir_volume_can_go_negative():
    """
    Tests that the reservoir's volume can become negative, as there is no
    explicit constraint in the model. This is a characteristic of this
    simplified model.
    """
    params = {'surface_area': 1.5e6}
    initial_state = {'volume': 1000}
    reservoir = Reservoir(name="test_res_neg", initial_state=initial_state, parameters=params)

    # No inflow, high outflow demand
    inflow = 0.0
    outflow = 50.0
    dt = 60 # 1 minute

    reservoir.set_inflow(inflow)
    action = {'outflow': outflow}

    # Execute
    result_state = reservoir.step(action, dt)

    # Assert that the volume has become negative
    expected_volume = 1000 + (0 - 50) * 60
    assert result_state['volume'] == pytest.approx(expected_volume)
    assert result_state['volume'] < 0
