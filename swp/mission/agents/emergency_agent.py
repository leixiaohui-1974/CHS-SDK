# -*- coding: utf-8 -*-

"""
Emergency Management Agent for the Yin Chuo Ji Liao project.
"""
from swp.core.interfaces import Agent
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import List

class EmergencyAgent(Agent):
    """
    An agent responsible for detecting and responding to emergencies, such as
    pipe bursts.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 pressure_topics: List[str],
                 emergency_threshold: float,
                 action_topic: str):
        """
        Initializes the EmergencyAgent.

        Args:
            agent_id: The unique ID of this agent.
            message_bus: The system's message bus for communication.
            pressure_topics: A list of pressure state topics to monitor.
            emergency_threshold: The pressure value below which an emergency is declared.
            action_topic: The topic to publish the emergency shutdown command to.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.pressure_topics = pressure_topics
        self.emergency_threshold = emergency_threshold
        self.action_topic = action_topic
        self.emergency_declared = False

        # Subscribe to all specified pressure topics
        for topic in self.pressure_topics:
            self.bus.subscribe(topic, self.handle_pressure_update)
            print(f"EmergencyAgent '{self.agent_id}' subscribed to pressure topic '{topic}'.")

    def handle_pressure_update(self, message: Message):
        """
        Callback executed when a new pressure reading is received.
        """
        if self.emergency_declared:
            return # Already in an emergency state, do nothing more.

        pressure = message.get('pressure')
        if pressure is None:
            return

        if pressure < self.emergency_threshold:
            print(f"!!! EMERGENCY DECLARED by {self.agent_id} !!!")
            print(f"    Pressure dropped to {pressure:.2f}, which is below the threshold of {self.emergency_threshold:.2f}.")
            self.emergency_declared = True
            self.trigger_emergency_action()

    def trigger_emergency_action(self):
        """
        Publishes an emergency action to the message bus, such as closing a gate.
        """
        # Command to close the gate completely.
        action_message: Message = {'control_signal': 0.0, 'agent_id': self.agent_id}
        self.bus.publish(self.action_topic, action_message)
        print(f"    Emergency action sent: Closing intake via topic '{self.action_topic}'.")

    def run(self, current_time: float):
        """
        The main execution loop for the agent. For this event-driven agent,
        this method is a no-op as logic is triggered by message callbacks.
        """
        pass
