import logging
from .base_control_agent import BaseControlAgent
from .pid_controller import PIDController
from core_lib.central_coordination.collaboration.message_bus import Message

class StructuredControlAgent(BaseControlAgent):
    """
    A structured, event-driven control agent that automatically determines its
    observation target based on a specified control mode.
    """

    def __init__(self, agent_id, message_bus, controlled_element_id: str, control_mode: str, controller_config: dict, dt: int, **kwargs):
        """
        Initializes the StructuredControlAgent.
        """
        super().__init__(agent_id, message_bus, dt)
        self.controlled_element_id = controlled_element_id
        self.control_mode = control_mode.lower()

        self.action_topic = self.controlled_element_id
        self.observation_topic, self.observation_key = self._determine_observation_info()

        if self.observation_topic:
            self._subscribed_topics.append(self.observation_topic)
            self.message_bus.subscribe(self.observation_topic, self.handle_observation)
        else:
            logging.error(f"Could not determine observation topic for agent {self.id} with mode {self.control_mode}")

        self.controller = PIDController(
            Kp=controller_config['Kp'],
            Ki=controller_config['Ki'],
            Kd=controller_config['Kd'],
            setpoint=controller_config['setpoint'],
            min_output=controller_config.get('min_output', 0.0),
            max_output=controller_config.get('max_output', 1.0)
        )

    def _determine_observation_info(self):
        """
        Determines the topic and key for observation based on the control mode and topology.
        """
        topology = self.message_bus.get_component_topology()

        if self.control_mode == 'lu': # Local Upstream Control
            target_id = topology.get(self.controlled_element_id, {}).get('upstream')
            if target_id:
                logging.info(f"Agent {self.agent_id} (LU mode) is observing upstream component: {target_id}")
                return target_id, 'water_level'
            else:
                logging.warning(f"Agent {self.agent_id} (LU mode) could not find an upstream component for {self.controlled_element_id}")

        elif self.control_mode == 'dd': # Distant Downstream Control
            target_id = topology.get(self.controlled_element_id, {}).get('downstream')
            if target_id:
                logging.info(f"Agent {self.agent_id} (DD mode) is observing downstream component: {target_id}")
                return target_id, 'water_level'
            else:
                logging.warning(f"Agent {self.agent_id} (DD mode) could not find a downstream component for {self.controlled_element_id}")

        elif self.control_mode == 'mix':
            logging.warning(f"Agent {self.agent_id}: 'mix' mode is not fully implemented. Defaulting to 'dd' behavior.")
            target_id = topology.get(self.controlled_element_id, {}).get('downstream')
            if target_id:
                return target_id, 'water_level'
        else:
            logging.error(f"Unknown control mode '{self.control_mode}' for agent {self.agent_id}")

        return None, None

    def handle_observation(self, message: Message):
        """
        Callback to handle incoming observation messages. This is the core logic loop.
        """
        process_variable = message.get(self.observation_key)
        if process_variable is not None:
            # 1. Format observation for PID controller
            observation_for_pid = {'process_variable': process_variable}

            # 2. Compute control action
            control_action = self.controller.compute_control_action(observation_for_pid, dt=self.dt)

            # 3. Publish the control action
            action_message = {'opening': control_action} # Assuming action is always 'opening'
            self.message_bus.publish(self.action_topic, action_message)
        else:
            logging.warning(f"Agent {self.agent_id} received message on topic {self.observation_topic} but key '{self.observation_key}' was missing.")

    def __repr__(self):
        return f"StructuredControlAgent(id={self.agent_id}, mode={self.control_mode}, controlled='{self.controlled_element_id}')"
