"""
Perception agent for a river channel.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Optional, Dict

class RiverChannelPerceptionAgent(DigitalTwinAgent):
    """
    A perception agent specifically for a river channel, acting as its digital twin.

    This agent is responsible for reading the state of a RiverChannel simulation
    model, potentially enhancing it (e.g., through smoothing or filtering), and
    publishing it for other agents to consume. It is a specialization of the
    DigitalTwinAgent, tailored for RiverChannel objects.
    """
    def __init__(self,
                 agent_id: str,
                 simulated_object: RiverChannel,
                 message_bus: MessageBus,
                 state_topic: str,
                 smoothing_config: Optional[Dict[str, float]] = None):
        """
        Initializes the RiverChannelPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            simulated_object: The RiverChannel instance this agent is a twin of.
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
        print(f"RiverChannelPerceptionAgent '{self.agent_id}' initialized for RiverChannel '{simulated_object.name}'.")
