import unittest
from unittest.mock import MagicMock

from core_lib.core.interfaces import Updatable, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.identification.model_updater_agent import ModelUpdaterAgent

# A mock model that implements the Updatable interface for testing purposes
class MockUpdatableModel(Updatable):
    def __init__(self):
        self.updated_params = None
        self.update_called = False

    def update_parameters(self, new_params: Parameters):
        """Mock method to record that parameters were updated."""
        self.updated_params = new_params
        self.update_called = True

    # --- Dummy methods to satisfy other potential interface requirements ---
    def get_parameters(self) -> Parameters: return {}
    def step(self, action, dt): pass
    def get_state(self): pass
    def set_state(self, state): pass
    def identify_parameters(self, data, method='offline'): pass
    @property
    def name(self): return "mock_model"


class TestModelUpdaterAgent(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        self.message_bus = MessageBus()
        self.mock_model = MockUpdatableModel()
        self.models_dict = {"my_model": self.mock_model}
        self.parameter_topic = "parameters/new"

        self.updater_agent = ModelUpdaterAgent(
            agent_id="test_updater",
            message_bus=self.message_bus,
            parameter_topic=self.parameter_topic,
            models=self.models_dict
        )

    def test_handle_new_parameters_updates_correct_model(self):
        """
        Verify that the agent correctly processes a parameter message
        and calls the update_parameters method on the target model.
        """
        # Arrange: Define the new parameters to be published
        new_parameters = {"friction_factor": 0.025, "diameter": 1.5}
        message = {
            "model_name": "my_model",
            "parameters": new_parameters
        }

        # Act: Publish the message to the topic the agent is subscribed to
        self.message_bus.publish(self.parameter_topic, message)

        # Assert: Check that the model's update method was called
        self.assertTrue(self.mock_model.update_called, "update_parameters was not called on the model.")

        # Assert: Check that the parameters were updated with the correct values
        self.assertIsNotNone(self.mock_model.updated_params)
        self.assertEqual(self.mock_model.updated_params, new_parameters)

    def test_handle_new_parameters_ignores_unknown_model(self):
        """
        Verify that the agent does not try to update a model that is not
        in its managed dictionary.
        """
        # Arrange: Define a message for a model not managed by the agent
        new_parameters = {"friction_factor": 0.03}
        message = {
            "model_name": "unknown_model",
            "parameters": new_parameters
        }

        # Act: Publish the message
        self.message_bus.publish(self.parameter_topic, message)

        # Assert: Check that the mock model's update method was NOT called
        self.assertFalse(self.mock_model.update_called, "update_parameters was called for an unknown model.")
        self.assertIsNone(self.mock_model.updated_params)

if __name__ == '__main__':
    unittest.main()
