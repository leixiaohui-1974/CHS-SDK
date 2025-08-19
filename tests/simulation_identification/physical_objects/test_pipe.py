import pytest
import math

from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.core.interfaces import State, Parameters

def test_pipe_gravity_flow():
    """
    Tests the Pipe model's flow calculation under normal gravity flow conditions.
    """
    # 1. Setup
    params_dict = {
        'length': 100.0,
        'diameter': 0.5,
        'friction_factor': 0.02
    }
    initial_state = {'outflow': 0.0, 'head_loss': 0.0}
    parameters = params_dict

    pipe = Pipe(name="test_pipe", initial_state=initial_state, parameters=parameters)

    action = {
        'upstream_head': 10.0,
        'downstream_head': 8.0
    }
    dt = 1.0

    # 2. Manual Calculation for Expected Result
    g = 9.81
    head_difference = action['upstream_head'] - action['downstream_head']
    area = (math.pi / 4) * (params_dict['diameter'] ** 2)
    flow_coefficient = area * math.sqrt(2 * g * params_dict['diameter'] / (params_dict['friction_factor'] * params_dict['length']))
    expected_outflow = flow_coefficient * math.sqrt(head_difference)

    # 3. Execution
    result_state = pipe.step(action, dt)

    # 4. Assertion
    assert result_state['outflow'] == pytest.approx(expected_outflow)
    assert result_state['head_loss'] == pytest.approx(head_difference)

def test_pipe_forced_flow():
    """
    Tests the Pipe model's behavior when inflow is forced (e.g., by a pump).
    """
    # 1. Setup
    params_dict = {
        'length': 100.0,
        'diameter': 0.5,
        'friction_factor': 0.02
    }
    initial_state = {'outflow': 0.0, 'head_loss': 0.0}
    parameters = params_dict

    pipe = Pipe(name="test_pipe_forced", initial_state=initial_state, parameters=parameters)

    # In forced flow, the action dictionary for heads is ignored
    action = {
        'upstream_head': 10.0,
        'downstream_head': 8.0
    }
    forced_inflow = 5.0 # m^3/s
    dt = 1.0

    # The harness would call this before step()
    pipe.set_inflow(forced_inflow)

    # 2. Manual Calculation for Expected Result
    g = 9.81
    area = (math.pi / 4) * (params_dict['diameter'] ** 2)
    flow_coefficient = area * math.sqrt(2 * g * params_dict['diameter'] / (params_dict['friction_factor'] * params_dict['length']))
    expected_head_loss = (forced_inflow / flow_coefficient)**2

    # 3. Execution
    result_state = pipe.step(action, dt)

    # 4. Assertion
    # Outflow should equal the forced inflow
    assert result_state['outflow'] == pytest.approx(forced_inflow)
    # Head loss should be calculated based on the forced flow
    assert result_state['head_loss'] == pytest.approx(expected_head_loss)

def test_pipe_no_flow():
    """
    Tests that there is no flow when the head difference is zero or negative.
    """
    # 1. Setup
    pipe = Pipe(
        name="test_pipe_no_flow",
        initial_state={'outflow': 0.0, 'head_loss': 0.0},
        parameters={'length': 100.0, 'diameter': 0.5, 'friction_factor': 0.02}
    )

    # 2. Test with zero head difference
    action_zero_head = {'upstream_head': 10.0, 'downstream_head': 10.0}
    result_zero_head = pipe.step(action_zero_head, 1.0)
    assert result_zero_head['outflow'] == 0.0
    assert result_zero_head['head_loss'] == 0.0

    # 3. Test with negative head difference
    action_neg_head = {'upstream_head': 9.0, 'downstream_head': 10.0}
    result_neg_head = pipe.step(action_neg_head, 1.0)
    assert result_neg_head['outflow'] == 0.0
    assert result_neg_head['head_loss'] == 0.0
