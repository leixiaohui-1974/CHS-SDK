import unittest
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.central_coordination.perception.central_perception_agent import CentralPerceptionAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestCentralPerceptionAgent(unittest.TestCase):
    """
    Unit tests for the CentralPerceptionAgent.
    """

    def setUp(self):
        """Set up a message bus and the agent for each test."""
        self.bus = MessageBus()
        self.subscribed_topics = {
            "pump_1": "state/pump_1",
            "valve_A": "state/valve_A",
        }
        self.agent = CentralPerceptionAgent(
            agent_id="central_perception",
            message_bus=self.bus,
            subscribed_topics=self.subscribed_topics,
            global_state_topic="global_state"
        )

    def test_state_aggregation_and_publication(self):
        """
        Test that the agent correctly subscribes to topics, aggregates the
        state from incoming messages, and publishes the complete global state.
        """
        received_global_states: List[Dict[str, Any]] = []

        def global_state_callback(message: Dict[str, Any]):
            received_global_states.append(message)

        self.bus.subscribe("global_state", global_state_callback)

        # 1. Simulate a state message from the pump
        pump_state = {'flow': 100, 'pressure': 3.5}
        self.bus.publish("state/pump_1", pump_state)

        # 2. Simulate a state message from the valve
        valve_state = {'opening': 80, 'flow': 100}
        self.bus.publish("state/valve_A", valve_state)

        # At this point, the agent's internal global_state should be updated
        self.assertEqual(self.agent.global_state["pump_1"], pump_state)
        self.assertEqual(self.agent.global_state["valve_A"], valve_state)

        # 3. Run the agent to trigger publication of the global state
        self.agent.run(current_time=0.0)

        # 4. Verify that the correct global state was published
        self.assertEqual(len(received_global_states), 1)
        global_state = received_global_states[0]

        self.assertIn("pump_1", global_state)
        self.assertIn("valve_A", global_state)
        self.assertEqual(global_state["pump_1"], pump_state)
        self.assertEqual(global_state["valve_A"], valve_state)

        # 5. Simulate another update and check if the publication is correct again
        new_pump_state = {'flow': 110, 'pressure': 3.6}
        self.bus.publish("state/pump_1", new_pump_state)

        self.agent.run(current_time=1.0)

        self.assertEqual(len(received_global_states), 2)
        latest_global_state = received_global_states[1]
        self.assertEqual(latest_global_state["pump_1"], new_pump_state)
        self.assertEqual(latest_global_state["valve_A"], valve_state) # valve state should be unchanged


if __name__ == '__main__':
    unittest.main()
