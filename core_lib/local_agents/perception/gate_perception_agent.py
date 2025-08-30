"""
Perception agent for a single gate.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.gate import Gate
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional, Dict

class GatePerceptionAgent(DigitalTwinAgent):
    """
    A perception agent for a single gate, providing fine-grained state data.

    This agent acts as the digital twin for a specific Gate instance. It reads
    the gate's state (e.g., opening, outflow) and publishes it, making it
    available for control agents or monitoring systems. This provides a more
    granular view compared to a station-level perception agent.
    """
    def __init__(self,
                 agent_id: str,
                 simulated_object: Gate,
                 message_bus: MessageBus,
                 state_topic: str,
                 smoothing_config: Optional[Dict[str, float]] = None):
        """
        Initializes the GatePerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            simulated_object: The Gate instance this agent is a twin of.
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
        print(f"GatePerceptionAgent '{self.agent_id}' initialized for Gate '{simulated_object.name}'.")
