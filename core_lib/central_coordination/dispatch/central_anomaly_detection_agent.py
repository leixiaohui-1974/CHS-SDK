"""
Central agent for anomaly detection.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List

class CentralAnomalyDetectionAgent(Agent):
    """
    A central agent responsible for detecting system-wide anomalies.

    This agent subscribes to state topics from various perception agents,
    analyzes the combined data for inconsistencies or unexpected patterns,
    and publishes alerts if an anomaly is detected.

    The current implementation uses a simple rule-based approach for demonstration.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, topics_to_monitor: List[str], alert_topic: str):
        """
        Initializes the CentralAnomalyDetectionAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            topics_to_monitor: A list of topics to subscribe to for data.
            alert_topic: The topic to publish anomaly alerts to.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topics_to_monitor = topics_to_monitor
        self.alert_topic = alert_topic
        self.latest_data = {}

        for topic in self.topics_to_monitor:
            self.bus.subscribe(topic, self.handle_message)

        print(f"CentralAnomalyDetectionAgent '{self.agent_id}' initialized. Monitoring {len(self.topics_to_monitor)} topics.")

    def handle_message(self, message: Message, topic: str):
        """Callback to store the latest message from a monitored topic."""
        self.latest_data[topic] = message

    def run(self, current_time: float):
        """
        The main execution logic, called at each time step.
        Analyzes the collected data to detect anomalies.
        """
        self.run_time = current_time
        self.detect_anomalies()

    def detect_anomalies(self):
        """
        Analyzes the current snapshot of data to find anomalies.

        This is a simple rule-based example. A real implementation would use
        more sophisticated methods.
        """
        # Example rule: if reservoir 'res1' level > 95 and gate 'g1' is closed (opening < 0.01)
        res1_topic = 'res1.state'
        g1_topic = 'g1.state'

        anomaly_detected = False
        description = ""

        if res1_topic in self.latest_data and g1_topic in self.latest_data:
            res1_data = self.latest_data[res1_topic]
            g1_data = self.latest_data[g1_topic]

            reservoir_level = res1_data.get('level', 0)
            gate_opening = g1_data.get('opening', 0)

            if reservoir_level > 95.0 and gate_opening < 0.01:
                anomaly_detected = True
                description = f"High water level ({reservoir_level}m) in reservoir 'res1' while upstream gate 'g1' is closed."

        if anomaly_detected:
            alert_message = {"timestamp": self.run_time, "anomaly": description}
            self.bus.publish(self.alert_topic, alert_message)
            print(f"[{self.agent_id} at {self.run_time}] ANOMALY DETECTED: {description}")
