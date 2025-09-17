"""
Perception agent for a single valve.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.valve import Valve
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional, Dict

class ValvePerceptionAgent(DigitalTwinAgent):
    """
    A perception agent for a single valve, providing fine-grained state data.

    This agent acts as the digital twin for a specific Valve instance. It reads
    the valve's state (e.g., opening percentage, outflow) and publishes it,
    making it available for control or monitoring systems.
    """
    def __init__(self,
                 agent_id: str,
                 simulated_object: Valve,
                 message_bus: MessageBus,
                 state_topic: str,
                 smoothing_config: Optional[Dict[str, float]] = None):
        """
        Initializes the ValvePerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            simulated_object: The Valve instance this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the object's state.
            smoothing_config: Optional config for applying EMA smoothing.
        """
        super().__init__(
            agent_id=agent_id,
            simulated_object=simulated_object,
            message_bus=message_bus,
            state_topic=state_topic,
            smoothing_config=smoothing_config
        )
        print(f"ValvePerceptionAgent '{self.agent_id}' initialized for Valve '{simulated_object.name}'.")
