# -*- coding: utf-8 -*-
"""
A simple agent for logging data from a message bus topic.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List

class TopicLoggerAgent(Agent):
    """
    Subscribes to a specific topic and stores all received messages with timestamps.
    This allows the SimulationHarness to capture and log any data published
    on the message bus.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, topic_to_log: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic_to_log
        self._state: State = {}  # The state will hold the content of the last message
        self.message_history: List[dict] = []  # Store all messages with timestamps
        self.current_time = 0.0

        self.bus.subscribe(self.topic, self.handle_message)
        print(f"[{self.agent_id}] Initialized. Subscribed to log topic '{self.topic}'.")

    def handle_message(self, message: Message):
        """Stores the received message and adds it to history."""
        self._state = message
        # Add message to history with current simulation time
        self.message_history.append({
            'time': self.current_time,
            'message': dict(message) if message else {}
        })

    def run(self, current_time: float):
        """Update the current time for timestamping messages."""
        self.current_time = current_time

    def get_state(self) -> State:
        """Returns the last message that was received."""
        return self._state
    
    def get_message_history(self) -> List[dict]:
        """Returns the complete message history."""
        return self.message_history
