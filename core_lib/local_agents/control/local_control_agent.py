"""
A Local Control Agent that encapsulates a control algorithm and communicates
via a message bus.
"""
from core_lib.core.interfaces import Agent, Controller, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
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
        # This is a more generic way to update a controller's setpoint
        if hasattr(self.controller, 'update_setpoint'):
            self.controller.update_setpoint(message)
        elif hasattr(self.controller, 'set_setpoint'):
            new_setpoint = message.get('new_setpoint')
            if new_setpoint is not None:
                self.controller.set_setpoint(new_setpoint)

    def handle_observation(self, message: Message):
        """
        Callback executed when a new observation message is received.
        """
        observation_for_controller = None
        # If observation_key is None, the controller wants the full state dictionary.
        if self.observation_key is None:
            observation_for_controller = message
        else:
            # Otherwise, extract the specific variable.
            process_variable = message.get(self.observation_key)
            if process_variable is None:
                print(f"[{self.agent_id}] Warning: Key '{self.observation_key}' not found in observation message: {message}")
                return
            # And wrap it in the expected format for simple controllers.
            observation_for_controller = {'process_variable': process_variable}

        if observation_for_controller is not None:
            # Compute the control action using the encapsulated controller
            control_signal = self.controller.compute_control_action(observation_for_controller, self.dt)
            # Publish the computed action to the action topic(s)
            self.publish_action(control_signal)

    def publish_action(self, control_signal: any):
        """
        Publishes the control action(s) to the message bus.

        This method supports two modes of operation:
        1. Single Action Mode: If the controller returns a single value, this method
           publishes it to the `action_topic` defined in the agent's constructor.
           The message is a dictionary: {'control_signal': value}.

        2. Multi-Action Mode: If the controller returns a dictionary, this method
           treats each key-value pair as `topic: signal`. It iterates through the
           dictionary and publishes each signal to its corresponding topic. This is
           useful for controllers that manage multiple actuators.
        """
        if isinstance(control_signal, dict):
            # Multi-Action Mode: Controller provided a dictionary of topic -> signal
            for topic, signal_value in control_signal.items():
                if topic is not None and signal_value is not None:
                    action_message: Message = {'control_signal': signal_value, 'agent_id': self.agent_id}
                    self.bus.publish(topic, action_message)
        else:
            # Single Action Mode: Publish a single control signal to the pre-configured topic
            if self.action_topic is not None:
                action_message: Message = {'control_signal': control_signal, 'agent_id': self.agent_id}
                self.bus.publish(self.action_topic, action_message)

    def run(self, current_time: float):
        """
        The main execution loop for the agent. For this event-driven agent,
        this method is a no-op as logic is triggered by message callbacks.

        Args:
            current_time: The current simulation time (ignored by this agent).
        """
        pass
