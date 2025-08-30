"""
Control agent for a single gate, specializing the generic LocalControlAgent.
"""
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional

class GateControlAgent(LocalControlAgent):
    """
    A control agent specifically for managing a single gate.

    This agent is a specialization of the LocalControlAgent. It is configured
    to listen to observations about a gate's state (e.g., from a
    GatePerceptionAgent), use a provided controller (e.g., PID) to calculate
    a new gate opening, and publish that as a command to the gate's
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
                 command_topic: Optional[str] = None,
                 feedback_topic: Optional[str] = None):
        """
        Initializes the GateControlAgent.

        Args:
            agent_id: The unique ID for this agent.
            controller: The control algorithm instance (e.g., PIDController).
            message_bus: The system's message bus for communication.
            observation_topic: The topic for gate state updates.
            observation_key: The specific key in the state to use (e.g., 'outflow').
            action_topic: The topic to publish gate control commands to.
            dt: The simulation time step.
            command_topic: Optional topic for receiving high-level commands (e.g., new setpoint).
            feedback_topic: Optional topic for receiving state feedback from the gate.
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
        print(f"GateControlAgent '{self.agent_id}' initialized. Will publish actions to '{action_topic}'.")
