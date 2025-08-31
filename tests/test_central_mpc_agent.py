import unittest
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.central_agents.central_mpc_agent import CentralMPCAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestCentralMPCAgent(unittest.TestCase):
    """
    Unit tests for the CentralMPCAgent.
    """

    def setUp(self):
        """Set up a new message bus for each test."""
        self.bus = MessageBus()
        self.received_messages: Dict[str, List[Dict[str, Any]]] = {}

    def _message_callback(self, message: Dict[str, Any], topic: str):
        """A generic callback to store messages received on a topic."""
        if topic not in self.received_messages:
            self.received_messages[topic] = []
        self.received_messages[topic].append(message)

    def test_mpc_agent_runs_and_publishes_level_setpoints(self):
        """Test that the CentralMPCAgent runs and publishes water level setpoints."""
        cmd_topic_1 = "command/mpc_sp_1"
        cmd_topic_2 = "command/mpc_sp_2"
        state_topic_1 = "state/level_1"
        state_topic_2 = "state/level_2"
        forecast_topic = "forecast/inflow"

        # Configuration matching the new hierarchical logic
        config = {
            "prediction_horizon": 10,
            "dt": 60,
            "q_weight": 1.0,
            "r_weight": 0.1,
            "state_keys": ["level_1", "level_2"],
            "command_topics": {"cmd1": cmd_topic_1, "cmd2": cmd_topic_2},
            "target_water_levels": [5.0, 5.0],
            "mpc_pid_model_kp": 0.5,
            "initial_setpoint_guess": [5.0, 5.0],
            "level_setpoint_bounds": [[4.0, 6.0], [4.0, 6.0]],
            "flood_thresholds": [5.8, 5.8],
            "canal_surface_areas": [1500.0, 1500.0],
            "outflow_coefficient": 0.1,
            "state_subscriptions": {"level_1": state_topic_1, "level_2": state_topic_2},
            "forecast_subscription": forecast_topic
        }

        agent = CentralMPCAgent(agent_id="mpc_agent_1", message_bus=self.bus, **config)

        self.bus.subscribe(cmd_topic_1, lambda msg: self._message_callback(msg, cmd_topic_1))
        self.bus.subscribe(cmd_topic_2, lambda msg: self._message_callback(msg, cmd_topic_2))

        # Publish initial state from sensors (using 'value' key)
        self.bus.publish(state_topic_1, {"value": 4.8})
        self.bus.publish(state_topic_2, {"value": 4.9})
        self.bus.publish(forecast_topic, {"inflow_forecast": [10.0] * 10})

        agent.run(current_time=0)

        self.assertIn(cmd_topic_1, self.received_messages)
        self.assertIn(cmd_topic_2, self.received_messages)
        self.assertEqual(len(self.received_messages[cmd_topic_1]), 1)
        # Check for the correct message key 'value'
        self.assertIn('value', self.received_messages[cmd_topic_1][0])
        # Check that the output is a float (a water level)
        self.assertIsInstance(self.received_messages[cmd_topic_1][0]['value'], float)
        # Check if the value is within the expected bounds
        self.assertGreaterEqual(self.received_messages[cmd_topic_1][0]['value'], 4.0)
        self.assertLessEqual(self.received_messages[cmd_topic_1][0]['value'], 6.0)

if __name__ == '__main__':
    unittest.main()
