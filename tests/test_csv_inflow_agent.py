import unittest
import sys
from pathlib import Path
from unittest.mock import Mock
from typing import Any, Dict, List
import os

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.data_access.csv_inflow_agent import CsvInflowAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestCsvInflowAgent(unittest.TestCase):
    """
    Unit tests for the CsvInflowAgent.
    """

    def setUp(self):
        """Set up a message bus, a mock component, and the agent for each test."""
        self.bus = MessageBus()
        self.mock_component = Mock()
        self.mock_component.name = "target_reservoir"

        # Path to the dummy CSV file
        self.csv_path = Path(__file__).parent / "test_inflow.csv"

        self.agent = CsvInflowAgent(
            agent_id="test_csv_agent",
            message_bus=self.bus,
            target_component=self.mock_component,
            csv_file_path=str(self.csv_path),
            time_column="time",
            data_column="inflow"
        )

    def test_data_publication_at_exact_times(self):
        """
        Test that the agent publishes the correct data when the simulation time
        exactly matches a timestamp in the CSV.
        """
        received_messages: List[Dict[str, Any]] = []
        def message_callback(message: Dict[str, Any]):
            received_messages.append(message)

        self.bus.subscribe("inflow/target_reservoir", message_callback)

        # Run at time t=2
        self.agent.run(current_time=2.0)
        self.assertEqual(len(received_messages), 1)
        self.assertAlmostEqual(received_messages[0]['inflow_rate'], 15.0)

        # Run at time t=10
        self.agent.run(current_time=10.0)
        self.assertEqual(len(received_messages), 2)
        self.assertAlmostEqual(received_messages[1]['inflow_rate'], 18.0)

    def test_data_publication_at_intermediate_times(self):
        """
        Test that the agent publishes the last known value when the simulation
        time is between timestamps in the CSV.
        """
        received_messages: List[Dict[str, Any]] = []
        def message_callback(message: Dict[str, Any]):
            received_messages.append(message)

        self.bus.subscribe("inflow/target_reservoir", message_callback)

        # Run at time t=3 (should get data from t=2)
        self.agent.run(current_time=3.0)
        self.assertEqual(len(received_messages), 1)
        self.assertAlmostEqual(received_messages[0]['inflow_rate'], 15.0)

        # Run at time t=7 (should get data from t=5)
        self.agent.run(current_time=7.0)
        self.assertEqual(len(received_messages), 2)
        self.assertAlmostEqual(received_messages[1]['inflow_rate'], 20.0)

    def test_no_publication_before_first_timestamp(self):
        """
        Test that the agent does not publish any data before the first
        timestamp in the CSV.
        """
        received_messages: List[Dict[str, Any]] = []
        def message_callback(message: Dict[str, Any]):
            received_messages.append(message)

        self.bus.subscribe("inflow/target_reservoir", message_callback)

        # Run at time t=-1
        self.agent.run(current_time=-1.0)
        self.assertEqual(len(received_messages), 0)

if __name__ == '__main__':
    unittest.main()
