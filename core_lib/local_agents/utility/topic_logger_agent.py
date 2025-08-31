# -*- coding: utf-8 -*-
"""
A simple agent for logging data from a message bus topic.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List

class TopicLoggerAgent(Agent):
    """
    Subscribes to a specific topic and stores the last received message as its state.
    This allows the SimulationHarness to capture and log any data published
    on the message bus.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, topic_to_log: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic_to_log
        self._state: State = {}  # The state will hold the content of the last message

        self.bus.subscribe(self.topic, self.handle_message)
        print(f"[{self.agent_id}] Initialized. Subscribed to log topic '{self.topic}'.")

    def handle_message(self, message: Message):
        """Stores the received message."""
        self._state = message

    def run(self, current_time: float):
        """The agent's behavior is purely reactive, so this method does nothing."""
        pass

    def get_state(self) -> State:
        """Returns the last message that was received."""
        return self._state
