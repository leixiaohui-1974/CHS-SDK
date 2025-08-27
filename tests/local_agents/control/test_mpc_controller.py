import pytest
from swp.local_agents.control.mpc_controller import MPCController

@pytest.fixture
def mpc_setup():
    """Sets up a basic MPC controller with an ID model for testing."""
    config = {
        "target_level": 10.0,
        "q_weight": 1.0,
        "r_weight": 0.1,
        "bounds": (0.0, 1.0),
        "id_model_gain": 0.5,       # K: A control action of 1.0 causes a 0.5 unit/sec change in level
        "id_model_delay_steps": 2   # tau: The control action takes 2 steps to have an effect
    }
    # Horizon of 10 steps, dt of 1 second for simplicity
    controller = MPCController(horizon=10, dt=1.0, config=config)
    return controller

def test_mpc_returns_valid_action(mpc_setup):
    """Tests that the computed action is within the specified bounds."""
    controller = mpc_setup
    observation = {
        "water_level": 9.8,
        # No disturbance
        "disturbance_forecast": [0.0] * controller.horizon
    }

    action = controller.compute_control_action(observation, dt=1.0)

    assert 'opening' in action
    assert isinstance(action['opening'], float)
    assert controller.bounds[0] <= action['opening'] <= controller.bounds[1]

def test_mpc_reacts_to_disturbance_forecast(mpc_setup):
    """
    Tests that the controller counteracts a future disturbance.
    A positive disturbance means the water level will drop (e.g., high demand),
    so the controller should reduce its own outflow (i.e., smaller opening).
    """
    controller = mpc_setup

    # Scenario 1: No disturbance forecast
    obs_no_disturbance = {
        "water_level": 10.1, # Slightly above target
        "disturbance_forecast": [0.0] * controller.horizon
    }
    action_no_disturbance = controller.compute_control_action(obs_no_disturbance, dt=1.0)

    # Scenario 2: A large future disturbance is forecasted
    disturbance_forecast = [0.0] * controller.horizon
    disturbance_forecast[3] = 5.0 # A large demand spike is coming in 3 steps
    obs_with_disturbance = {
        "water_level": 10.1, # Same starting level
        "disturbance_forecast": disturbance_forecast
    }
    action_with_disturbance = controller.compute_control_action(obs_with_disturbance, dt=1.0)

    # Assertion: To counteract the future level drop from the disturbance,
    # the controller should choose a LARGER opening now (to pre-emptively raise the level)
    # compared to the no-disturbance case (where it wants to lower the level).
    assert action_with_disturbance['opening'] > action_no_disturbance['opening']

def test_mpc_tries_to_reach_target_level(mpc_setup):
    """
    Tests that the controller opens the gate if the level is below target and
    increases it if the level is above target, with no disturbance.
    """
    controller = mpc_setup

    # Scenario 1: Water level is below target
    obs_below_target = {
        "water_level": 9.5, # Below target
        "disturbance_forecast": [0.0] * controller.horizon
    }
    action_below = controller.compute_control_action(obs_below_target, dt=1.0)

    # Scenario 2: Water level is above target
    obs_above_target = {
        "water_level": 10.5, # Above target
        "disturbance_forecast": [0.0] * controller.horizon
    }
    action_above = controller.compute_control_action(obs_above_target, dt=1.0)

    # In our ID model, a larger opening corresponds to a larger *increase* in water level.
    # So, to raise the level from 9.5, it needs a LARGER opening than to lower the level from 10.5.
    # This might seem counter-intuitive for a gate, but it's correct for the model:
    # change_in_level = K * opening - disturbance
    # To get a positive change_in_level, we need a positive `opening`.
    assert action_below['opening'] > 0 # It should try to raise the level

    # To get a negative change_in_level (to lower the level), it needs a smaller opening.
    # Depending on the weights, it might even be 0.
    assert action_above['opening'] < action_below['opening']
