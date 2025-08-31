"""
An agent that logs all messages from a specific topic for later analysis.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional, Any

class TopicLoggerAgent(Agent):
    """
    Subscribes to a given topic and stores the last received message.
    It exposes this stored value via a `get_state` method, allowing its
    data to be captured in the main simulation history log.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        """
        Initializes the TopicLoggerAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The system's message bus.
            **kwargs: Must contain 'topic_to_log' (str).
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = kwargs.get('topic_to_log')
        if not self.topic:
            raise ValueError(f"[{agent_id}] TopicLoggerAgent requires 'topic_to_log' in its configuration.")

        self.last_message = {"value": 0.0} # Default state
        self.bus.subscribe(self.topic, self.handle_message)
        print(f"[{self.agent_id}] Initialized. Subscribed to log topic '{self.topic}'.")

    def handle_message(self, message: Message):
        """Stores the payload of the last received message."""
        self.last_message = message

    def get_state(self) -> dict[str, Any]:
        """
        Makes the agent stateful so its data is recorded by the harness.
        Returns the last message payload it received.
        """
        return self.last_message

    def run(self, current_time: float):
        """This agent is purely reactive, so the run method does nothing."""
        pass
