# -*- coding: utf-8 -*-
"""
This module contains the SignalAggregatorAgent.
"""
from typing import List
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class SignalAggregatorAgent(Agent):
    """
    A generic agent that subscribes to multiple topics, aggregates their
    numeric values (by summing them), and publishes the result to a single
    output topic.

    This is useful for combining multiple inflows/outflows into a single
    net inflow for a component that can only subscribe to one topic.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus

        self.input_topics: List[str] = config['input_topics']
        self.output_topic: str = config['output_topic']
        self.last_received_values: dict[str, float] = {topic: 0.0 for topic in self.input_topics}

        if not self.input_topics or not self.output_topic:
            raise ValueError("SignalAggregatorAgent requires 'input_topics' and 'output_topic' in its config.")

        # Subscribe the same handler to all input topics
        for topic in self.input_topics:
            self.bus.subscribe(topic, lambda msg, t=topic: self.handle_signal(msg, t))
            print(f"[{self.agent_id}] Subscribed to input topic '{topic}'.")

    def handle_signal(self, message: Message, topic: str):
        """
        Callback to store the latest value from any of the input topics.
        """
        value = message.get("value", 0.0)
        if isinstance(value, (int, float)):
            self.last_received_values[topic] = value

    def run(self, current_time: float, dt: float):
        """
        In each step, sum the last known values and publish the result.
        """
        total_value = sum(self.last_received_values.values())

        # Publish the aggregated result
        self.bus.publish(self.output_topic, Message(self.agent_id, {"value": total_value}))
