import pytest
import math

from swp.simulation_identification.physical_objects.gate import Gate

def test_gate_orifice_flow():
    """
    Tests the Gate model's outflow calculation using the orifice equation.
    """
    # 1. Setup
    params = {
        'discharge_coefficient': 0.6,
        'width': 10.0,
        'max_opening': 1.0,
        'max_rate_of_change': 1.0  # Set high to not interfere with this test
    }
    # Gate is 50% open
    initial_state = {'opening': 0.5, 'outflow': 0}
    gate = Gate(name="test_gate_flow", initial_state=initial_state, parameters=params)

    action = {
        'control_signal': 0.5, # Maintain 50% opening
        'upstream_head': 12.0,
        'downstream_head': 10.0
    }
    dt = 1.0

    # 2. Manual Calculation for Expected Result
    g = 9.81
    head_diff = action['upstream_head'] - action['downstream_head']
    area = initial_state['opening'] * params['width']
    expected_outflow = params['discharge_coefficient'] * area * math.sqrt(2 * g * head_diff)

    # 3. Execution
    result_state = gate.step(action, dt)

    # 4. Assertion
    assert result_state['outflow'] == pytest.approx(expected_outflow)
    assert result_state['opening'] == initial_state['opening'] # Should not change

def test_gate_rate_of_change():
    """
    Tests that the gate opening respects the 'max_rate_of_change' parameter.
    """
    params = {
        'discharge_coefficient': 0.6,
        'width': 10.0,
        'max_opening': 1.0,
        'max_rate_of_change': 0.1 # Can only change opening by 0.1 per second
    }
    initial_state = {'opening': 0.2, 'outflow': 0} # Start at 20%
    gate = Gate(name="test_gate_roc", initial_state=initial_state, parameters=params)

    # Command the gate to open to 100%
    action = {
        'control_signal': 1.0,
        'upstream_head': 12.0,
        'downstream_head': 10.0
    }
    dt = 1.0

    # Expected opening after one step is initial + rate*dt
    expected_opening = initial_state['opening'] + params['max_rate_of_change'] * dt

    # Execute and assert
    result_state = gate.step(action, dt)
    assert result_state['opening'] == pytest.approx(expected_opening)

    # Execute for another 2 seconds (total 3s)
    gate.step(action, dt)
    result_state = gate.step(action, dt)
    expected_opening_3s = initial_state['opening'] + 3 * params['max_rate_of_change'] * dt
    assert result_state['opening'] == pytest.approx(expected_opening_3s)

def test_gate_fully_opens_and_stops():
    """
    Tests that the gate stops opening once it reaches the target opening.
    """
    params = {'max_rate_of_change': 0.1}
    initial_state = {'opening': 0.8} # Start at 80%
    gate = Gate(name="test_gate_stop", initial_state=initial_state, parameters=params)

    # Command to open to 95%
    action = {'control_signal': 0.95, 'upstream_head': 10, 'downstream_head': 8}
    dt = 1.0

    # First step: should open to 0.9
    result1 = gate.step(action, dt)
    assert result1['opening'] == pytest.approx(0.9)

    # Second step: should open to 0.95 and stop there
    result2 = gate.step(action, dt)
    assert result2['opening'] == pytest.approx(0.95)

    # Third step: should remain at 0.95
    result3 = gate.step(action, dt)
    assert result3['opening'] == pytest.approx(0.95)
