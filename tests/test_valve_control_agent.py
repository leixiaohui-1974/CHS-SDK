import unittest
from unittest.mock import Mock
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.local_agents.control.valve_control_agent import ValveControlAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestValveControlAgent(unittest.TestCase):
    """
    Unit tests for the ValveControlAgent.
    """

    def setUp(self):
        """Set up a mock controller, message bus, and agent for each test."""
        self.bus = MessageBus()
        self.mock_controller = Mock()
        self.mock_controller.compute_control_action.return_value = 0.75  # 75% open

        self.agent = ValveControlAgent(
            agent_id="test_valve_control_agent",
            controller=self.mock_controller,
            message_bus=self.bus,
            observation_topic="perception/valve/state",
            observation_key="outflow",
            action_topic="action/valve/command",
            dt=1.0,
            command_topic="command/valve/setpoint"
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.agent_id, "test_valve_control_agent")
        # A more robust test would be to check if the bus has subscriptions
        # for the topics, but without a public interface to subscribers,
        # we trust the agent's constructor.

    def test_control_logic_flow(self):
        """
        Test the full flow: setpoint command -> observation -> controller -> action.
        """
        # A list to store received action messages
        received_actions: List[Dict[str, Any]] = []

        def action_callback(message: Dict[str, Any]):
            received_actions.append(message)

        # Subscribe to the action topic to capture the agent's output
        self.bus.subscribe("action/valve/command", action_callback)

        # Make the mock controller behave as if it only has 'set_setpoint'
        del self.mock_controller.update_setpoint

        # 1. Simulate receiving a new setpoint command
        setpoint_command = {'new_setpoint': 150.0}
        self.bus.publish("command/valve/setpoint", setpoint_command)

        # Verify the controller's setpoint was updated
        self.mock_controller.set_setpoint.assert_called_with(150.0)

        # 2. Simulate receiving a new observation from a perception agent
        observation_message = {'outflow': 145.0, 'pressure': 2.1}
        self.bus.publish("perception/valve/state", observation_message)

        # 3. Verify the controller was called with the correct process variable
        expected_observation_for_controller = {'process_variable': 145.0}
        self.mock_controller.compute_control_action.assert_called_with(
            expected_observation_for_controller, self.agent.dt
        )

        # 4. Verify that the correct action was published
        self.assertEqual(len(received_actions), 1)
        action_message = received_actions[0]
        self.assertEqual(action_message['control_signal'], 0.75)
        self.assertEqual(action_message['agent_id'], self.agent.agent_id)

if __name__ == '__main__':
    unittest.main()
