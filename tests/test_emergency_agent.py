import unittest
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.local_agents.supervisory.emergency_agent import EmergencyAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestEmergencyAgent(unittest.TestCase):
    """
    Unit tests for the EmergencyAgent.
    """

    def setUp(self):
        """Set up a message bus and the agent for each test."""
        self.bus = MessageBus()
        self.monitored_topics = ["state/pipe_1", "state/pipe_2"]
        self.action_topic = "emergency/command"
        self.pressure_threshold = 1.5 # Bar

        self.agent = EmergencyAgent(
            agent_id="emergency_monitor",
            message_bus=self.bus,
            subscribed_topics=self.monitored_topics,
            pressure_threshold=self.pressure_threshold,
            action_topic=self.action_topic
        )

    def test_no_action_on_normal_pressure(self):
        """
        Test that the agent does not declare an emergency when pressure is normal.
        """
        received_actions: List[Dict[str, Any]] = []
        def action_callback(message: Dict[str, Any]):
            received_actions.append(message)

        self.bus.subscribe(self.action_topic, action_callback)

        # Simulate a normal pressure reading
        normal_state = {'pressure': 2.0, 'flow': 50}
        self.bus.publish("state/pipe_1", normal_state)

        # Verify no emergency action was taken
        self.assertEqual(len(received_actions), 0)
        self.assertFalse(self.agent.emergency_declared)

    def test_emergency_declaration_on_low_pressure(self):
        """
        Test that the agent declares an emergency and publishes a command
        when pressure drops below the threshold.
        """
        received_actions: List[Dict[str, Any]] = []
        def action_callback(message: Dict[str, Any]):
            received_actions.append(message)

        self.bus.subscribe(self.action_topic, action_callback)

        # Simulate a low pressure reading
        low_pressure_state = {'pressure': 1.2, 'flow': 45}
        self.bus.publish("state/pipe_2", low_pressure_state)

        # Verify an emergency action was taken
        self.assertEqual(len(received_actions), 1)
        self.assertTrue(self.agent.emergency_declared)

        # Check the content of the emergency message
        emergency_message = received_actions[0]
        self.assertEqual(emergency_message['command'], 'EMERGENCY_SHUTDOWN')
        self.assertEqual(emergency_message['new_setpoint'], 0.0)

    def test_only_one_emergency_declaration(self):
        """
        Test that the agent only declares an emergency once, even if multiple
        low-pressure events occur.
        """
        received_actions: List[Dict[str, Any]] = []
        def action_callback(message: Dict[str, Any]):
            received_actions.append(message)

        self.bus.subscribe(self.action_topic, action_callback)

        # First low pressure event
        low_pressure_1 = {'pressure': 1.1}
        self.bus.publish("state/pipe_1", low_pressure_1)

        # Second low pressure event
        low_pressure_2 = {'pressure': 0.9}
        self.bus.publish("state/pipe_2", low_pressure_2)

        # Verify only one emergency action was taken
        self.assertEqual(len(received_actions), 1)
        self.assertTrue(self.agent.emergency_declared)


if __name__ == '__main__':
    unittest.main()
