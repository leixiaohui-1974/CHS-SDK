"""
Central agent for anomaly detection.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List, Dict, Any

class CentralAnomalyDetectionAgent(Agent):
    """
    A central agent responsible for detecting system-wide anomalies.

    This agent subscribes to state topics from various perception agents,
    analyzes the combined data for inconsistencies or unexpected patterns,
    and publishes alerts if an anomaly is detected.

    Current implementation includes a rule to detect if a pump is active
    but producing no outflow.
    """
    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 topics_to_monitor: List[str],
                 alert_topic: str,
                 outflow_threshold: float = 0.01):
        """
        Initializes the CentralAnomalyDetectionAgent.

        Args:
            agent_id: The unique ID of the agent.
            message_bus: The system's message bus.
            topics_to_monitor: A list of topics to subscribe to for data.
            alert_topic: The topic to publish anomaly alerts to.
            outflow_threshold: The outflow value below which a running pump is considered anomalous.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topics_to_monitor = topics_to_monitor
        self.alert_topic = alert_topic
        self.outflow_threshold = outflow_threshold
        self.latest_data: Dict[str, Message] = {}
        self.active_alerts: Dict[str, Message] = {}

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
        self.detect_anomalies(current_time)

    def detect_anomalies(self, current_time: float):
        """
        Analyzes the current snapshot of data to find anomalies.
        This version checks for pumps that are on but have no flow.
        """
        for topic, data in self.latest_data.items():
            # Rule: Detect if a pump is active but has no significant outflow.
            # This identifies a potential pump failure or blockage.
            if 'pump' in topic and isinstance(data, dict) and 'status' in data and 'outflow' in data:
                pump_id = topic
                alert_key = f"{pump_id}_no_flow"

                is_on = data['status'] == 1
                no_flow = data['outflow'] < self.outflow_threshold

                # If the anomaly condition is met
                if is_on and no_flow:
                    if alert_key not in self.active_alerts:
                        alert_message = {
                            "timestamp": current_time,
                            "anomaly_type": "PUMP_NO_FLOW",
                            "source_topic": topic,
                            "details": f"Pump is active but outflow is {data['outflow']:.4f}, which is below the threshold of {self.outflow_threshold:.4f}."
                        }
                        self.bus.publish(self.alert_topic, alert_message)
                        self.active_alerts[alert_key] = alert_message
                        print(f"[{self.agent_id} at {current_time:.2f}] New Anomaly Detected: {alert_message['details']}")
                else:
                    # If the anomaly condition is no longer met, clear the alert
                    if alert_key in self.active_alerts:
                        del self.active_alerts[alert_key]
                        print(f"[{self.agent_id} at {current_time:.2f}] Anomaly Cleared: Pump at '{topic}' is now operating normally.")
