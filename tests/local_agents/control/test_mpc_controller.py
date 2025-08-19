import pytest
from swp.local_agents.control.mpc_controller import MPCController

@pytest.fixture
def mpc_setup():
    """Sets up a basic MPC controller for testing."""
    config = {
        "target_level": 10.0,  # Target water level of 10m
        "q_weight": 1.0,       # Weight for level deviation
        "r_weight": 0.5,       # Weight for control action cost
        "bounds": (0.0, 1.0),  # Control action is between 0 and 1
        "max_outflow": 150.0   # Max possible outflow at opening=1.0
    }
    # Horizon of 5 steps, dt of 3600 seconds (1 hour)
    controller = MPCController(horizon=5, dt=3600, config=config)
    return controller

def test_mpc_returns_valid_action(mpc_setup):
    """Tests that the computed action is within the specified bounds."""
    controller = mpc_setup
    observation = {
        "water_level": 9.8,
        "surface_area": 1e6,
        "inflow_forecast": [50, 55, 60, 58, 52] # Steady inflow
    }

    action = controller.compute_control_action(observation, dt=3600)

    assert 'opening' in action
    assert isinstance(action['opening'], float)
    assert 0.0 <= action['opening'] <= 1.0

def test_mpc_reacts_to_high_inflow_forecast(mpc_setup):
    """
    Tests that the controller increases outflow when a high inflow is forecasted,
    even if the current level is below target.
    """
    controller = mpc_setup

    # Scenario 1: Low, stable forecast
    obs_low_inflow = {
        "water_level": 9.9,
        "surface_area": 1e6,
        "inflow_forecast": [10, 10, 10, 10, 10]
    }
    action_low = controller.compute_control_action(obs_low_inflow, dt=3600)

    # Scenario 2: High inflow forecast (a flood is coming)
    obs_high_inflow = {
        "water_level": 9.9, # Same starting level
        "surface_area": 1e6,
        "inflow_forecast": [100, 120, 150, 130, 110]
    }
    action_high = controller.compute_control_action(obs_high_inflow, dt=3600)

    # Assertion: The action for the high inflow scenario should be significantly
    # larger (i.e., more gate opening) than for the low inflow one.
    assert action_high['opening'] > action_low['opening']

def test_mpc_reduces_outflow_when_level_is_low(mpc_setup):
    """
    Tests that the controller closes the gate if the level is low and
    inflow is not significant.
    """
    controller = mpc_setup

    # Scenario: Water level is well below target, and inflow is low
    observation = {
        "water_level": 8.5, # Far below target
        "surface_area": 1e6,
        "inflow_forecast": [10, 10, 10, 10, 10]
    }
    action = controller.compute_control_action(observation, dt=3600)

    # Assertion: The controller should try to conserve water, so the opening
    # should be very small (close to the lower bound of 0).
    assert action['opening'] == pytest.approx(0.0, abs=1e-2)
