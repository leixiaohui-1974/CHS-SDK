# -*- coding: utf-8 -*-

"""
A simplified Central Dispatcher Agent for the Yin Chuo Ji Liao project.
"""
from swp.core.interfaces import Agent
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict

class CentralDispatcherAgent(Agent):
    """
    A rule-based supervisory agent that demonstrates hierarchical control.

    It monitors the state of a key system component (e.g., a terminal reservoir)
    and adjusts the setpoint of a local controller to meet a high-level objective.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 observation_topic: str,
                 observation_key: str,
                 command_topic: str,
                 config: Dict):
        """
        Initializes the CentralDispatcherAgent.

        Args:
            agent_id: The unique ID of this agent.
            message_bus: The system's message bus.
            observation_topic: The state topic to monitor.
            observation_key: The key of the variable to monitor in the state message.
            command_topic: The topic to publish setpoint adjustment commands to.
            config: A dictionary containing control parameters, e.g.,
                    {'low_level': 212.0, 'high_level': 213.0,
                     'low_setpoint': 349.8, 'high_setpoint': 349.2}
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.observation_topic = observation_topic
        self.observation_key = observation_key
        self.command_topic = command_topic
        self.config = config
        self.current_mode = None # e.g., 'normal', 'filling', 'reducing'

        self.bus.subscribe(self.observation_topic, self.handle_observation)
        print(f"CentralDispatcherAgent '{self.agent_id}' created. Subscribed to '{observation_topic}'.")

    def handle_observation(self, message: Message):
        """
        Callback executed when new state information is received.
        """
        level = message.get(self.observation_key)
        if level is None:
            return

        new_mode = self.current_mode
        if level < self.config['low_level']:
            new_mode = 'filling'
        elif level > self.config['high_level']:
            new_mode = 'reducing'
        else:
            # Could add a 'normal' mode or just let it be
            pass

        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.publish_new_setpoint()

    def publish_new_setpoint(self):
        """
        Publishes a new setpoint command based on the current operating mode.
        """
        new_setpoint = None
        if self.current_mode == 'filling':
            new_setpoint = self.config['low_setpoint'] # Raise upstream level to send more water
        elif self.current_mode == 'reducing':
            new_setpoint = self.config['high_setpoint'] # Lower upstream level to send less

        if new_setpoint is not None:
            command_message = {'new_setpoint': new_setpoint}
            self.bus.publish(self.command_topic, command_message)
            print(f"CentralDispatcher '{self.agent_id}' changed mode to '{self.current_mode}' and sent new setpoint: {new_setpoint}")

    def run(self, current_time: float):
        """
        This agent is event-driven, so the run loop is a no-op.
        """
        pass
