# -*- coding: utf-8 -*-
"""
This module defines custom agents for the parameter identification scenario.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class ConstantValueAgent(Agent):
    """
    A simple agent that continuously publishes a constant value to a topic.
    This is useful for providing constant inputs (like a downstream level of 0)
    to other agents that require all inputs to come from topics.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = config['topic']
        self.value = config['value']
        self.key = config.get('key', 'value')

    def run(self, current_time: float, dt: float):
        """Publish the constant value at each time step."""
        message = Message(self.agent_id, {self.key: self.value})
        self.bus.publish(self.topic, message)
