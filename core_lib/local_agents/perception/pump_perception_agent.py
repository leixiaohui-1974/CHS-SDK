"""
Perception agent for a single pump.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.pump import Pump
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional, Dict

class PumpPerceptionAgent(DigitalTwinAgent):
    """
    A perception agent for a single pump, providing fine-grained state data.

    This agent acts as the digital twin for a specific Pump instance. It reads
    the pump's state (e.g., status, outflow, power draw) and publishes it.
    This enables detailed monitoring and provides the necessary feedback for
    fine-grained control and diagnostics.
    """
    def __init__(self,
                 agent_id: str,
                 simulated_object: Pump,
                 message_bus: MessageBus,
                 state_topic: str,
                 smoothing_config: Optional[Dict[str, float]] = None):
        """
        Initializes the PumpPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            simulated_object: The Pump instance this agent is a twin of.
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
        print(f"PumpPerceptionAgent '{self.agent_id}' initialized for Pump '{simulated_object.name}'.")
