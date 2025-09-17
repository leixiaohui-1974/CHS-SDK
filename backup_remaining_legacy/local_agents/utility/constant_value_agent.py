# -*- coding: utf-8 -*-
"""
This module defines an agent that publishes a constant value to a topic.
"""
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class ConstantValueAgent(Agent):
    """
    A simple agent that continuously publishes a constant value to a topic.
    This is useful for providing constant inputs to other components.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        """
        Initializes the ConstantValueAgent.

        Args:
            agent_id (str): The unique identifier for the agent.
            message_bus (MessageBus): The message bus for communication.
            **kwargs: Agent-specific configuration containing:
                - topic (str): The topic to publish the value to.
                - value (any): The constant value to publish.
                - key (str, optional): The key for the value in the message dictionary. Defaults to 'value'.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        if 'topic' not in kwargs or 'value' not in kwargs:
            raise ValueError(f"[{agent_id}]'topic' and 'value' must be provided in the agent configuration.")
        self.topic = kwargs['topic']
        self.value = kwargs['value']
        self.key = kwargs.get('key', 'value')

    def run(self, current_time: float):
        """
        Publish the constant value at each time step.
        """
        message = {'sender_id': self.agent_id, self.key: self.value}
        self.bus.publish(self.topic, message)
