import pytest

from swp.simulation_identification.physical_objects.river_channel import RiverChannel

def test_river_channel_linear_reservoir_model():
    """
    Tests the basic logic of the linear reservoir model where outflow = k * volume.
    """
    # 1. Setup
    params = {'k': 0.0001} # Storage coefficient
    initial_volume = 5e5
    initial_state = {'volume': initial_volume, 'outflow': 0}
    channel = RiverChannel(name="test_channel", initial_state=initial_state, parameters=params)

    inflow = 100.0  # m^3/s
    dt = 60.0       # 1 minute

    channel.set_inflow(inflow)

    # 2. Manual Calculation for Expected Result
    # Outflow is calculated based on the volume *before* the step's mass balance
    expected_outflow = params['k'] * initial_volume
    expected_delta_volume = (inflow - expected_outflow) * dt
    expected_new_volume = initial_volume + expected_delta_volume

    # 3. Execution
    result_state = channel.step(action=None, dt=dt)

    # 4. Assertion
    assert result_state['outflow'] == pytest.approx(expected_outflow)
    assert result_state['volume'] == pytest.approx(expected_new_volume)

def test_river_channel_reaches_equilibrium():
    """
    Tests that the channel reaches equilibrium (inflow = outflow) over time.
    """
    params = {'k': 0.0002}
    initial_state = {'volume': 0}
    channel = RiverChannel(name="test_channel_equil", initial_state=initial_state, parameters=params)

    constant_inflow = 100.0
    channel.set_inflow(constant_inflow)
    dt = 600 # 10 minute timesteps

    # Run for many steps to approach equilibrium
    for _ in range(1000):
        state = channel.step(action=None, dt=dt)

    # At equilibrium, inflow should equal outflow
    # Outflow = k * V  => V_eq = Inflow / k
    # So, Inflow = k * V_eq = Outflow_eq
    assert state['outflow'] == pytest.approx(constant_inflow, rel=1e-3)
    assert state['volume'] == pytest.approx(constant_inflow / params['k'], rel=1e-3)
