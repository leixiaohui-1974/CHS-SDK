"""
Control agent for a single valve, specializing the generic LocalControlAgent.
"""
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional

class ValveControlAgent(LocalControlAgent):
    """
    A control agent specifically for managing a single valve.

    This agent is a specialization of the LocalControlAgent. It is configured
    to listen to observations about a valve's state (e.g., from a
    ValvePerceptionAgent), use a provided controller to calculate a new
    valve opening percentage, and publish that as a command to the valve's
    action topic.
    """
    def __init__(self,
                 agent_id: str,
                 controller: Controller,
                 message_bus: MessageBus,
                 observation_topic: str,
                 observation_key: str,
                 action_topic: str,
                 dt: float,
                 target_component: Optional[str] = None,
                 command_topic: Optional[str] = None,
                 feedback_topic: Optional[str] = None):
        """
        Initializes the ValveControlAgent.

        Args:
            agent_id: The unique ID for this agent.
            controller: The control algorithm instance (e.g., PIDController).
            message_bus: The system's message bus for communication.
            observation_topic: The topic for valve state updates.
            observation_key: The specific key in the state to use (e.g., 'outflow').
            action_topic: The topic to publish valve control commands to.
            dt: The simulation time step.
            target_component: Optional identifier for the controlled component.
            command_topic: Optional topic for receiving high-level commands (e.g., new setpoint).
            feedback_topic: Optional topic for receiving state feedback from the valve.
        """
        data_sources = {'primary_data': observation_topic}
        control_targets = {'primary_action': action_topic}
        allocation_config = {}
        controller_config = {'type': controller.__class__.__name__ if controller else 'unknown'}

        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            dt=dt,
            target_component=target_component or action_topic or 'valve',
            control_type='valve_control',
            data_sources=data_sources,
            control_targets=control_targets,
            allocation_config=allocation_config,
            controller_config=controller_config,
            controller=controller,
            observation_topic=observation_topic,
            observation_key=observation_key,
            action_topic=action_topic,
            command_topic=command_topic,
            feedback_topic=feedback_topic
        )
        print(f"ValveControlAgent '{self.agent_id}' initialized. Will publish actions to '{action_topic}'.")
