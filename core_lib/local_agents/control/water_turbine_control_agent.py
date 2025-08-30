"""
Control agent for a single water turbine, specializing the generic LocalControlAgent.
"""
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional

class WaterTurbineControlAgent(LocalControlAgent):
    """
    A control agent specifically for managing a single water turbine.

    This agent is a specialization of the LocalControlAgent. It is configured
    to listen to observations about a system's state (e.g., reservoir level),
    use a provided controller to calculate a new target outflow for the turbine,
    and publish that as a command to the turbine's action topic.
    """
    def __init__(self,
                 agent_id: str,
                 controller: Controller,
                 message_bus: MessageBus,
                 observation_topic: str,
                 observation_key: str,
                 action_topic: str,
                 dt: float,
                 command_topic: Optional[str] = None,
                 feedback_topic: Optional[str] = None):
        """
        Initializes the WaterTurbineControlAgent.

        Args:
            agent_id: The unique ID for this agent.
            controller: The control algorithm instance (e.g., PIDController).
            message_bus: The system's message bus for communication.
            observation_topic: The topic for system state updates (e.g., reservoir level).
            observation_key: The specific key in the state to use (e.g., 'water_level').
            action_topic: The topic to publish turbine control commands to.
            dt: The simulation time step.
            command_topic: Optional topic for receiving high-level commands (e.g., new setpoint).
            feedback_topic: Optional topic for receiving state feedback from the turbine.
        """
        super().__init__(
            agent_id=agent_id,
            controller=controller,
            message_bus=message_bus,
            observation_topic=observation_topic,
            observation_key=observation_key,
            action_topic=action_topic,
            dt=dt,
            command_topic=command_topic,
            feedback_topic=feedback_topic
        )
        print(f"WaterTurbineControlAgent '{self.agent_id}' initialized. Will publish actions to '{action_topic}'.")
