from typing import Optional
import logging
from .base_control_agent import BaseControlAgent
from .pid_controller import PIDController
from core_lib.central_coordination.collaboration.message_bus import Message

class StructuredControlAgent(BaseControlAgent):
    """
    A structured, event-driven control agent that can operate with a fixed or
    dynamic setpoint received from a message bus topic.
    """

    def __init__(self, agent_id, message_bus, controlled_element_id: str,
                 control_mode: str, controller_config: dict, time_step: int, **kwargs):
        """
        Initializes the StructuredControlAgent.

        Args:
            ...
            controller_config (dict): Can contain a `setpoint_topic` for dynamic updates.
            ...
        """
        super().__init__(agent_id, message_bus, time_step)
        self.controlled_element_id = controlled_element_id
        self.control_mode = control_mode.lower()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.time_step = time_step

        self.action_topic = f"actuator/{self.controlled_element_id}/opening"
        self.observation_topic, self.observation_key = self._determine_observation_info(
            kwargs.get('observation_topic'))

        # Standard observation subscription
        if self.observation_topic:
            self._subscribed_topics.append(self.observation_topic)
            self.message_bus.subscribe(self.observation_topic, self.handle_observation)
        else:
            self.logger.error(f"Could not determine observation topic for agent {self.agent_id} with mode {self.control_mode}")

        self.controller = PIDController(
            Kp=controller_config['Kp'],
            Ki=controller_config['Ki'],
            Kd=controller_config['Kd'],
            setpoint=controller_config.get('setpoint', 0.0), # Default setpoint
            min_output=controller_config.get('min_output', 0.0),
            max_output=controller_config.get('max_output', 1.0)
        )

        # Dynamic setpoint subscription
        self.setpoint_topic = kwargs.get('setpoint_topic')
        if self.setpoint_topic:
            self._subscribed_topics.append(self.setpoint_topic)
            self.message_bus.subscribe(self.setpoint_topic, self._handle_setpoint_update)
            self.logger.info(f"Agent {self.agent_id} subscribed to dynamic setpoint topic: {self.setpoint_topic}")

    def _determine_observation_info(self, explicit_topic: Optional[str] = None):
        """
        Determines the topic and key for observation.
        Uses an explicitly provided topic if available, otherwise infers from control mode.
        """
        if explicit_topic:
            self.logger.info(f"Agent {self.agent_id} using explicit observation topic: {explicit_topic}")
            # Assume the key is 'value' for generic sensor topics
            return explicit_topic, 'value'

        topology = self.message_bus.get_component_topology()
        if self.control_mode == 'lu': # Local Upstream Control
            target_id = topology.get(self.controlled_element_id, {}).get('upstream')
            if target_id:
                self.logger.info(f"Agent {self.agent_id} (LU mode) is observing upstream component: {target_id}")
                return f"sensor/{target_id}/water_level", 'value'
        elif self.control_mode == 'dd': # Distant Downstream Control
            target_id = topology.get(self.controlled_element_id, {}).get('downstream')
            if target_id:
                self.logger.info(f"Agent {self.agent_id} (DD mode) is observing downstream component: {target_id}")
                return f"sensor/{target_id}/water_level", 'value'

        self.logger.error(f"Unknown or unresolvable control mode '{self.control_mode}' for agent {self.agent_id}")
        return None, None

    def _handle_setpoint_update(self, message: Message):
        """
        Callback to handle incoming setpoint update messages.
        """
        new_setpoint = message.get('value')
        if new_setpoint is not None:
            self.controller.setpoint = new_setpoint
            self.logger.info(f"Agent {self.agent_id} updated setpoint to {new_setpoint} from topic {self.setpoint_topic}")
        else:
            self.logger.warning(f"Agent {self.agent_id} received message on topic {self.setpoint_topic} but key 'value' was missing.")

    def handle_observation(self, message: Message):
        """
        Callback to handle incoming observation messages. This is the core logic loop.
        """
        # The physical_io_agent sends a message where the key is the state_key.
        # e.g. {'water_level': 5.0, 'timestamp': ...}
        process_variable = None
        if self.observation_key:
            process_variable = message.get(self.observation_key)
        if process_variable is None:
            # The central_mpc_agent sends a message like {'value': 5.0}
            process_variable = message.get('value')

        if process_variable is not None:
            observation_for_pid = {'process_variable': process_variable}
            control_action = self.controller.compute_control_action(observation_for_pid, time_step=self.time_step)
            payload = {'value': control_action}
            self.message_bus.publish(self.action_topic, payload)
        else:
            self.logger.warning(f"Agent {self.agent_id} received message on topic {self.observation_topic} but could not find key '{self.observation_key}' or 'value'.")

    def __del__(self):
        """
        Destructor to clean up subscriptions.
        """
        super().__del__() # Call parent destructor
        if self.setpoint_topic:
            self.message_bus.unsubscribe(self.setpoint_topic, self._handle_setpoint_update)

    def __repr__(self):
        return f"StructuredControlAgent(id={self.agent_id}, mode={self.control_mode}, controlled='{self.controlled_element_id}')"
