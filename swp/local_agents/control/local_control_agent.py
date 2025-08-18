"""
A Local Control Agent that encapsulates a control algorithm and communicates
via a message bus.
"""
from swp.core.interfaces import Agent, Controller, State
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional

class LocalControlAgent(Agent):
    """
    A Control Agent that operates at a local level (e.g., controlling one gate).

    This agent formalizes the concept of a controller in a Multi-Agent System.
    It wraps a specific control algorithm (a `Controller` implementation) and
    handles the communication (subscribing to sensor data, publishing actions)
    needed for it to operate. It can also subscribe to a command topic to
    receive high-level directives from a central dispatcher.
    """

    def __init__(self, agent_id: str, controller: Controller, message_bus: MessageBus,
                 observation_topic: str, action_topic: str, command_topic: Optional[str] = None):
        """
        Initializes the LocalControlAgent.

        Args:
            agent_id: The unique ID for this agent.
            controller: The control algorithm instance (e.g., PIDController).
            message_bus: The system's message bus for communication.
            observation_topic: The topic to listen to for state updates.
            action_topic: The topic to publish control actions to.
            command_topic: The topic to listen to for high-level commands.
        """
        super().__init__(agent_id)
        self.controller = controller
        self.bus = message_bus
        self.observation_topic = observation_topic
        self.action_topic = action_topic

        self.bus.subscribe(self.observation_topic, self.handle_observation)
        print(f"LocalControlAgent '{self.agent_id}' created. Subscribed to observation topic '{observation_topic}'.")

        if command_topic:
            self.bus.subscribe(command_topic, self.handle_command_message)
            print(f"LocalControlAgent '{self.agent_id}' also subscribed to command topic '{command_topic}'.")

    def handle_command_message(self, message: Message):
        """Callback to handle incoming high-level commands."""
        new_setpoint = message.get('new_setpoint')
        if new_setpoint is not None and hasattr(self.controller, 'set_setpoint'):
            print(f"[{self.agent_id}] Received new command: Set setpoint to {new_setpoint}")
            self.controller.set_setpoint(new_setpoint)

    def handle_observation(self, message: Message):
        """
        Callback function executed when a new observation message is received.
        """
        print(f"[{self.agent_id}] Received observation: {message}")

        # The message is the observation state needed by the controller
        observation_state: State = message

        # Compute the control action using the encapsulated controller
        control_signal = self.controller.compute_control_action(observation_state)

        # Publish the computed action to the action topic
        self.publish_action(control_signal)

    def publish_action(self, control_signal: any):
        """
        Publishes the control action to the message bus.
        """
        action_message: Message = {'control_signal': control_signal, 'agent_id': self.agent_id}
        print(f"[{self.agent_id}] Publishing action to '{self.action_topic}': {action_message}")
        self.bus.publish(self.action_topic, action_message)

    def run(self):
        """
        The main execution loop for the agent.

        In this event-driven design, the agent doesn't need a busy loop.
        Its logic is triggered by messages. The run method could be used
        for periodic health checks or other background tasks if needed.
        """
        print(f"LocalControlAgent '{self.agent_id}' is running (event-driven).")
        pass
