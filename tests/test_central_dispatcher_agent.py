import unittest
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

# A mock Reservoir class for testing the emergency mode
class MockReservoir:
    def __init__(self, initial_level=10.0):
        self._level = initial_level

    def get_state(self):
        return {'water_level': self._level}

    def set_level(self, level):
        self._level = level


class TestCentralDispatcherAgent(unittest.TestCase):
    """
    Unit tests for the consolidated CentralDispatcherAgent.
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

    def test_emergency_mode_no_action(self):
        """Test emergency mode: Does NOT act when level is normal."""
        command_topic = "command/gate_1"
        mock_reservoir = MockReservoir(initial_level=95)

        config = {
            "mode": "emergency",
            "reservoir": mock_reservoir,
            "emergency_flood_level": 100.0,
            "command_topic": command_topic
        }
        agent = CentralDispatcherAgent("emergency_dispatcher", self.bus, config)

        self.bus.subscribe(command_topic, lambda msg: self._message_callback(msg, command_topic))

        agent.run(current_time=0)

        self.assertNotIn(command_topic, self.received_messages)

    def test_emergency_mode_triggers_override(self):
        """Test emergency mode: Issues an override when level is critical."""
        command_topic = "command/gate_1"
        mock_reservoir = MockReservoir(initial_level=105)

        config = {
            "mode": "emergency",
            "reservoir": mock_reservoir,
            "emergency_flood_level": 100.0,
            "command_topic": command_topic
        }
        agent = CentralDispatcherAgent("emergency_dispatcher", self.bus, config)

        self.bus.subscribe(command_topic, lambda msg: self._message_callback(msg, command_topic))

        agent.run(current_time=0)

        self.assertIn(command_topic, self.received_messages)
        self.assertEqual(len(self.received_messages[command_topic]), 1)
        self.assertEqual(self.received_messages[command_topic][0]['control_signal'], 0.0)

    def test_rule_mode_issues_high_setpoint(self):
        """Test rule mode: Issues high setpoint when level is low."""
        command_topic = "command/pid_1"
        state_topic = "state/reservoir_2"

        config = {
            "mode": "rule",
            "subscribed_topic": state_topic,
            "observation_key": "water_level",
            "command_topic": command_topic,
            "dispatcher_params": {
                "low_level": 10,
                "high_level": 20,
                "low_setpoint": 12,
                "high_setpoint": 18
            }
        }
        agent = CentralDispatcherAgent("rule_dispatcher", self.bus, config)

        self.bus.subscribe(command_topic, lambda msg: self._message_callback(msg, command_topic))

        # Publish a low water level
        self.bus.publish(state_topic, {"water_level": 5})
        agent.run(current_time=0)

        self.assertIn(command_topic, self.received_messages)
        self.assertEqual(self.received_messages[command_topic][0]['new_setpoint'], 18)

    def test_rule_mode_issues_low_setpoint(self):
        """Test rule mode: Issues low setpoint when level is high."""
        command_topic = "command/pid_1"
        state_topic = "state/reservoir_2"

        config = {
            "mode": "rule",
            "subscribed_topic": state_topic,
            "observation_key": "water_level",
            "command_topic": command_topic,
            "dispatcher_params": {
                "low_level": 10,
                "high_level": 20,
                "low_setpoint": 12,
                "high_setpoint": 18
            }
        }
        agent = CentralDispatcherAgent("rule_dispatcher", self.bus, config)

        self.bus.subscribe(command_topic, lambda msg: self._message_callback(msg, command_topic))

        # Publish a high water level
        self.bus.publish(state_topic, {"water_level": 25})
        agent.run(current_time=0)

        self.assertIn(command_topic, self.received_messages)
        self.assertEqual(self.received_messages[command_topic][0]['new_setpoint'], 12)

    def test_mpc_mode_runs_without_error(self):
        """Test MPC mode: Runs optimization and publishes a command."""
        cmd_topic_1 = "command/mpc_sp_1"
        cmd_topic_2 = "command/mpc_sp_2"
        state_topic_1 = "state/level_1"
        state_topic_2 = "state/level_2"
        forecast_topic = "forecast/inflow"

        config = {
            "mode": "mpc",
            "prediction_horizon": 5,
            "dt": 3600,
            "q_weight": 1.0,
            "r_weight": 0.5,
            "state_keys": ["level_1", "level_2"],
            "command_topics": {"cmd1": cmd_topic_1, "cmd2": cmd_topic_2},
            "normal_setpoints": [4.0, 4.0],
            "emergency_setpoint": 3.0,
            "flood_thresholds": [6.0, 6.0],
            "canal_surface_areas": [10000, 10000],
            "outflow_coefficient": 500,
            "state_subscriptions": {"level_1": state_topic_1, "level_2": state_topic_2},
            "forecast_subscription": forecast_topic
        }
        agent = CentralDispatcherAgent("mpc_dispatcher", self.bus, config)

        self.bus.subscribe(cmd_topic_1, lambda msg: self._message_callback(msg, cmd_topic_1))
        self.bus.subscribe(cmd_topic_2, lambda msg: self._message_callback(msg, cmd_topic_2))

        # Publish initial state and forecast
        self.bus.publish(state_topic_1, {"water_level": 4.1})
        self.bus.publish(state_topic_2, {"water_level": 4.2})
        self.bus.publish(forecast_topic, {"inflow_forecast": [0.5, 0.6, 0.7, 0.5, 0.4]})

        agent.run(current_time=0)

        # Check that a command was published on both topics
        self.assertIn(cmd_topic_1, self.received_messages)
        self.assertIn(cmd_topic_2, self.received_messages)
        self.assertEqual(len(self.received_messages[cmd_topic_1]), 1)
        self.assertIn('new_setpoint', self.received_messages[cmd_topic_1][0])


if __name__ == '__main__':
    unittest.main()
