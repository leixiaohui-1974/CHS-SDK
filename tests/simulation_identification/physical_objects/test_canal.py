import pytest
import math

from swp.simulation_identification.physical_objects.canal import Canal

def test_canal_manning_flow():
    """
    Tests the Canal model's outflow calculation using Manning's equation.
    """
    # 1. Setup
    params = {
        'bottom_width': 20.0,
        'length': 5000.0,
        'slope': 0.0001,
        'side_slope_z': 2.0,
        'manning_n': 0.025
    }
    # Start with a known volume
    initial_volume = 5e5
    initial_state = {'volume': initial_volume, 'water_level': 0, 'outflow': 0}

    canal = Canal(name="test_canal", initial_state=initial_state, parameters=params)

    inflow = 100.0  # m^3/s
    dt = 60.0      # 1 minute time step
    canal.set_inflow(inflow)

    # 2. Manual Calculation for Expected Result
    # First, calculate the initial water level from the initial volume
    a = params['side_slope_z']
    b = params['bottom_width']
    c = -initial_volume / params['length']
    # y = (-b + sqrt(b^2 - 4ac)) / 2a
    initial_water_level = (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)

    # Now, calculate hydraulic properties based on this water level
    area = (params['bottom_width'] + params['side_slope_z'] * initial_water_level) * initial_water_level
    wetted_perimeter = params['bottom_width'] + 2 * initial_water_level * math.sqrt(1 + params['side_slope_z']**2)
    hydraulic_radius = area / wetted_perimeter

    # Finally, calculate expected outflow using Manning's equation
    expected_outflow = (1 / params['manning_n']) * area * (hydraulic_radius**(2/3)) * (params['slope']**0.5)

    # And the expected new volume
    expected_delta_volume = (inflow - expected_outflow) * dt
    expected_new_volume = initial_volume + expected_delta_volume

    # 3. Execution
    result_state = canal.step(action=None, dt=dt)

    # 4. Assertion
    assert result_state['outflow'] == pytest.approx(expected_outflow)
    assert result_state['water_level'] == pytest.approx(initial_water_level) # water level is calculated before volume update
    assert result_state['volume'] == pytest.approx(expected_new_volume)

def test_canal_no_inflow_drains():
    """
    Tests that the canal drains over time if there is no inflow.
    """
    params = {
        'bottom_width': 20.0,
        'length': 5000.0,
        'slope': 0.0001,
        'side_slope_z': 2.0,
        'manning_n': 0.025
    }
    initial_volume = 5e5
    initial_state = {'volume': initial_volume, 'water_level': 0, 'outflow': 0}
    canal = Canal(name="test_canal_drain", initial_state=initial_state, parameters=params)

    # No inflow
    canal.set_inflow(0.0)

    # Run for one step
    result_state = canal.step(action=None, dt=60.0)

    # Assert that some outflow occurred and volume decreased
    assert result_state['outflow'] > 0
    assert result_state['volume'] < initial_volume
