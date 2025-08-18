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

    This agent wraps a control algorithm and handles the communication needed for
    it to operate within the MAS. It subscribes to sensor data, publishes actions,
    and can optionally be guided by high-level commands.
    """

    def __init__(self, agent_id: str, controller: Controller, message_bus: MessageBus,
                 observation_topic: str, observation_key: str, action_topic: str,
                 dt: float, command_topic: Optional[str] = None, feedback_topic: Optional[str] = None):
        """
        Initializes the LocalControlAgent.

        Args:
            agent_id: The unique ID for this agent.
            controller: The control algorithm instance (e.g., PIDController).
            message_bus: The system's message bus for communication.
            observation_topic: The topic to listen to for state updates.
            observation_key: The specific key in the observation message to use as a process variable.
            action_topic: The topic to publish control actions to.
            dt: The simulation time step, required for the controller.
            command_topic: The topic for receiving high-level commands.
            feedback_topic: The topic for receiving state feedback from the controlled object.
        """
        super().__init__(agent_id)
        self.controller = controller
        self.bus = message_bus
        self.observation_topic = observation_topic
        self.observation_key = observation_key
        self.action_topic = action_topic
        self.dt = dt
        self.latest_feedback: State = {}

        self.bus.subscribe(self.observation_topic, self.handle_observation)
        print(f"LocalControlAgent '{self.agent_id}' created. Subscribed to observation topic '{observation_topic}'.")

        if command_topic:
            self.bus.subscribe(command_topic, self.handle_command_message)
            print(f"LocalControlAgent '{self.agent_id}' also subscribed to command topic '{command_topic}'.")

        if feedback_topic:
            self.bus.subscribe(feedback_topic, self.handle_feedback_message)
            print(f"LocalControlAgent '{self.agent_id}' also subscribed to feedback topic '{feedback_topic}'.")

    def handle_feedback_message(self, message: Message):
        """Callback to handle incoming state feedback from the controlled object."""
        self.latest_feedback = message
        # print(f"[{self.agent_id}] Received feedback: {self.latest_feedback}")

    def handle_command_message(self, message: Message):
        """Callback to handle incoming high-level commands."""
        new_setpoint = message.get('new_setpoint')
        if new_setpoint is not None and hasattr(self.controller, 'set_setpoint'):
            # print(f"[{self.agent_id}] Received new command: Set setpoint to {new_setpoint}")
            self.controller.set_setpoint(new_setpoint)

    def handle_observation(self, message: Message):
        """
        Callback executed when a new observation message is received.
        """
        # print(f"[{self.agent_id}] Received observation: {message}")

        # Extract the specific process variable from the observation message
        process_variable = message.get(self.observation_key)

        if process_variable is None:
            print(f"[{self.agent_id}] Warning: Key '{self.observation_key}' not found in observation message: {message}")
            return

        # Create a simplified state for the controller
        observation_state: State = {'process_variable': process_variable}

        # Compute the control action using the encapsulated controller
        control_signal = self.controller.compute_control_action(observation_state, self.dt)

        # Publish the computed action to the action topic
        self.publish_action(control_signal)

    def publish_action(self, control_signal: any):
        """
        Publishes the control action to the message bus.
        """
        action_message: Message = {'control_signal': control_signal, 'agent_id': self.agent_id}
        # print(f"[{self.agent_id}] Publishing action to '{self.action_topic}': {action_message}")
        self.bus.publish(self.action_topic, action_message)

    def run(self):
        """
        The main execution loop for the agent. For this event-driven agent,
        this method is a no-op as logic is triggered by message callbacks.
        """
        pass
