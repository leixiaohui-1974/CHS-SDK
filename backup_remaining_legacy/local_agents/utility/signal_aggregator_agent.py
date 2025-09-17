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
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus

        # Config should be a list of dicts: [{'topic': 't1', 'key': 'k1'}, {'topic': 't2', 'key': 'k2'}]
        self.input_configs: List[Dict[str, str]] = kwargs['input_configs']
        self.output_topic: str = kwargs['output_topic']
        self.last_received_values: dict[str, float] = {conf['topic']: 0.0 for conf in self.input_configs}

        if not self.input_configs or not self.output_topic:
            raise ValueError("SignalAggregatorAgent requires 'input_configs' and 'output_topic'.")

        # Subscribe to all input topics
        for config in self.input_configs:
            topic = config['topic']
            key = config['key']
            self.bus.subscribe(topic, lambda msg, t=topic, k=key: self.handle_signal(msg, t, k))
            print(f"[{self.agent_id}] Subscribed to input topic '{topic}' to read key '{key}'.")

    def handle_signal(self, message: Message, topic: str, key: str):
        """
        Callback to store the latest value and immediately publish the new sum.
        """
        value = message.get(key)
        if isinstance(value, (int, float)):
            self.last_received_values[topic] = value
            self.publish_aggregation()

    def publish_aggregation(self):
        """Sums the last known values and publishes the result."""
        total_value = sum(self.last_received_values.values())
        # The Reservoir component expects the key to be "inflow_rate"
        self.bus.publish(self.output_topic, {"inflow_rate": total_value})

    def run(self, current_time: float):
        """
        The agent's behavior is purely reactive. On the first step, it publishes
        the initial sum of zero.
        """
        if current_time == 0:
            self.publish_aggregation()
