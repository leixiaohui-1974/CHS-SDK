"""
A Local Control Agent that encapsulates a control algorithm and communicates
via a message bus.
"""
from core_lib.core.interfaces import Agent, Controller, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional


def _resolve_logging_flag(value: Optional[bool]) -> bool:
    """Normalize optional truthy values to a boolean."""

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False

    if isinstance(value, (int, float)):
        return bool(value)

    return False

class LocalControlAgent(Agent):
    """
    A Control Agent that operates at a local level (e.g., controlling one gate).

    This agent wraps a control algorithm and handles the communication needed for
    it to operate within the MAS. It subscribes to sensor data, publishes actions,
    and can optionally be guided by high-level commands.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, dt: float,
                 target_component: str, control_type: str, data_sources: dict,
                 control_targets: dict, allocation_config: dict, controller_config: dict,
                 controller: Optional[Controller] = None, 
                 observation_topic: Optional[str] = None, observation_key: Optional[str] = None, 
                 action_topic: Optional[str] = None, command_topic: Optional[str] = None, 
                 feedback_topic: Optional[str] = None, **kwargs):
        """
        Initializes the LocalControlAgent.

        Args:
            agent_id: The unique ID for this agent.
            message_bus: The system's message bus for communication.
            dt: The simulation time step.
            target_component: The physical component this agent controls.
            control_type: The type of control (e.g., 'gate_control').
            data_sources: Dictionary of data source topics.
            control_targets: Dictionary of control target topics.
            allocation_config: Configuration for flow allocation.
            controller_config: Configuration for the controller.
            controller: The control algorithm instance (e.g., PIDController).
            observation_topic: The topic to listen to for state updates.
            observation_key: The specific key in the observation message to use as a process variable.
            action_topic: The topic to publish control actions to.
            command_topic: The topic for receiving high-level commands.
            feedback_topic: The topic for receiving state feedback from the controlled object.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.dt = dt
        self.target_component = target_component
        self.control_type = control_type
        self.data_sources = data_sources
        self.control_targets = control_targets
        self.allocation_config = allocation_config
        self.controller_config = controller_config
        
        # Set up topics from configuration
        primary_observation_topic = (
            data_sources.get('primary_data')
            or data_sources.get('primary_observation')
            or data_sources.get('observation_topic')
        )
        self.observation_topic = observation_topic or primary_observation_topic
        self.observation_key = observation_key or 'value'
        primary_action_topic = (
            control_targets.get('primary_target')
            or control_targets.get('action_topic')
            or control_targets.get('primary_action')
        )
        self.action_topic = action_topic or primary_action_topic or f'control.{target_component}.action'
        self.command_topic = command_topic
        self.feedback_topic = feedback_topic
        self.log_observations = _resolve_logging_flag(
            kwargs.get('log_observations', kwargs.get('verbose', kwargs.get('debug', False)))
        )
        
        # Initialize controller if provided, otherwise create from config
        if controller:
            self.controller = controller
        else:
            # Create controller from config (simplified for now)
            self.controller = None
            
        self.latest_feedback: State = {}

        self.bus.subscribe(self.observation_topic, self.handle_observation)
        print(f"LocalControlAgent '{self.agent_id}' created. Subscribed to observation topic '{self.observation_topic}'.")

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
            if self.log_observations:
                print(f"[{self.agent_id}] Observation: {observation_for_controller}, Control Signal: {control_signal}")
            # Publish the computed action to the action topic(s)
            self.publish_action(control_signal)

    def publish_action(self, control_signal: any):
        """
        Publishes the control action(s) to the message bus.

        This method supports two modes of operation:
        1. Single Action Mode: If the controller returns a single value, this method
           publishes it to the `action_topic` defined in the agent's constructor.
           The message is a dictionary: {'value': signal}.

        2. Multi-Action Mode: If the controller returns a dictionary, this method
           treats each key-value pair as `topic: signal`. It iterates through the
           dictionary and publishes each signal to its corresponding topic. This is
           useful for controllers that manage multiple actuators. The physical components
           (like the Reservoir) expect the key for the signal to be 'value'.
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
                action_message: Message = {
                    'control_signal': control_signal,
                    'agent_id': self.agent_id,
                }
                # 兼容期望特定键的物理组件，例如 Gate 需要 'opening'
                action_message.setdefault('value', control_signal)
                action_message.setdefault('opening', control_signal)
                self.bus.publish(self.action_topic, action_message)

    def run(self, current_time: float):
        """
        The main execution loop for the agent. For this event-driven agent,
        this method is a no-op as logic is triggered by message callbacks.

        Args:
            current_time: The current simulation time (ignored by this agent).
        """
        pass
