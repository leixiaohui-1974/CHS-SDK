import unittest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.central_coordination.dispatch.central_anomaly_detection_agent import CentralAnomalyDetectionAgent
from core_lib.central_coordination.dispatch.demand_forecasting_agent import DemandForecastingAgent

class MockMessageBus:
    def __init__(self):
        self.subscriptions = {}
        self.published_messages = []

    def subscribe(self, topic, callback):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)

    def publish(self, topic, message):
        self.published_messages.append({'topic': topic, 'message': message})
        if topic in self.subscriptions:
            for callback in self.subscriptions[topic]:
                callback(message, topic)

class TestCentralAnomalyDetectionAgent(unittest.TestCase):
    def setUp(self):
        self.bus = MockMessageBus()
        self.agent = CentralAnomalyDetectionAgent(
            agent_id='anomaly_detector_1',
            message_bus=self.bus,
            topics_to_monitor=['res1.state', 'g1.state'],
            alert_topic='alerts.anomaly'
        )

    def test_no_anomaly(self):
        # Simulate normal conditions
        self.bus.publish('res1.state', {'level': 80.0})
        self.bus.publish('g1.state', {'opening': 0.5})

        self.agent.run(current_time=100)

        # No alert should be published
        self.assertEqual(len(self.bus.published_messages), 2) # The two state messages

    def test_anomaly_detected(self):
        # Simulate anomaly condition: high water level and closed gate
        self.bus.publish('res1.state', {'level': 98.0})
        self.bus.publish('g1.state', {'opening': 0.0})

        self.agent.run(current_time=200)

        # An alert should be published
        self.assertEqual(len(self.bus.published_messages), 3)
        alert = self.bus.published_messages[-1]
        self.assertEqual(alert['topic'], 'alerts.anomaly')
        self.assertIn('High water level', alert['message']['anomaly'])

class TestDemandForecastingAgent(unittest.TestCase):
    def setUp(self):
        self.bus = MockMessageBus()
        self.agent = DemandForecastingAgent(
            agent_id='demand_forecaster_1',
            message_bus=self.bus,
            historical_data_topics=['city.demand', 'industry.demand'],
            forecast_topic='forecast.demand'
        )

    def test_no_historical_data(self):
        # Run the agent at a time that triggers the forecast
        self.agent.run(current_time=86400)

        # A default forecast should be published
        self.assertEqual(len(self.bus.published_messages), 1)
        forecast_msg = self.bus.published_messages[0]
        self.assertEqual(forecast_msg['topic'], 'forecast.demand')
        self.assertEqual(forecast_msg['message']['demands'], [10.0] * 24)

    def test_with_historical_data(self):
        # Simulate receiving historical data
        self.bus.publish('city.demand', {'demand': 15.0})
        self.bus.publish('city.demand', {'demand': 25.0})
        self.bus.publish('industry.demand', {'demand': 30.0})

        # Run the agent to trigger the forecast
        self.agent.run(current_time=86400)

        # The forecast should be the average of the historical data ( (15+25+30)/3 = 23.333 )
        self.assertEqual(len(self.bus.published_messages), 4) # 3 data messages + 1 forecast
        forecast_msg = self.bus.published_messages[-1]
        self.assertEqual(forecast_msg['topic'], 'forecast.demand')
        self.assertAlmostEqual(forecast_msg['message']['demands'][0], 23.333, places=3)
        self.assertEqual(len(forecast_msg['message']['demands']), 24)


if __name__ == '__main__':
    unittest.main()
