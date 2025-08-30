import unittest
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.perception.reservoir_perception_agent import ReservoirPerceptionAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestReservoirPerceptionAgent(unittest.TestCase):
    """
    Unit tests for the ReservoirPerceptionAgent.
    """

    def setUp(self):
        """Set up a new reservoir, message bus, and agent for each test."""
        self.bus = MessageBus()
        self.initial_state = {'water_level': 10.0, 'volume': 10000.0}
        self.parameters = {'surface_area': 1000.0}
        self.reservoir = Reservoir(
            name="test_reservoir",
            initial_state=self.initial_state,
            parameters=self.parameters
        )
        self.agent = ReservoirPerceptionAgent(
            agent_id="test_perception_agent",
            reservoir_model=self.reservoir,
            message_bus=self.bus,
            state_topic="perception/reservoir/state"
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.agent_id, "test_perception_agent")
        self.assertEqual(self.agent.model, self.reservoir)
        self.assertEqual(self.agent.bus, self.bus)
        self.assertEqual(self.agent.state_topic, "perception/reservoir/state")

    def test_perception_and_publication(self):
        """Test that the agent perceives the reservoir's state and publishes it."""
        # A list to store messages received from the bus
        received_messages: List[Dict[str, Any]] = []

        # A callback to append messages to our list
        def message_callback(message: Dict[str, Any]):
            received_messages.append(message)

        # Subscribe our callback to the agent's state topic
        self.bus.subscribe("perception/reservoir/state", message_callback)

        # Run the agent's logic for one step
        self.agent.run(current_time=0.0)

        # Check that one message was received
        self.assertEqual(len(received_messages), 1)

        # Check that the received message contains the correct state
        message = received_messages[0]
        self.assertIn('water_level', message)
        self.assertIn('volume', message)
        self.assertAlmostEqual(message['water_level'], self.initial_state['water_level'])
        self.assertAlmostEqual(message['volume'], self.initial_state['volume'])

if __name__ == '__main__':
    unittest.main()
