"""
Digital Twin Agent for state synchronization and publication.
"""
from swp.core.interfaces import Agent, Simulatable, State
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

class DigitalTwinAgent(Agent):
    """
    A Perception Agent that acts as a digital twin for a physical object.

    Its primary responsibility is to maintain an internal simulation model and
    publish its state to the message bus, simulating a real-world sensor feed.
    It can also subscribe to topics to update its state from other sources if needed.
    """

    def __init__(self, agent_id: str, simulated_object: Simulatable, message_bus: MessageBus, state_topic: str):
        """
        Initializes the DigitalTwinAgent.

        Args:
            agent_id: The unique ID of this agent.
            simulated_object: The simulation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the object's state.
        """
        super().__init__(agent_id)
        self.model = simulated_object
        self.bus = message_bus
        self.state_topic = state_topic
        # Get the ID from the model, which could be 'reservoir_id', 'gate_id', etc.
        model_id = getattr(self.model, next((attr for attr in dir(self.model) if '_id' in attr), 'id'))
        print(f"DigitalTwinAgent '{self.agent_id}' created for model '{model_id}'. Will publish state to '{self.state_topic}'.")

    def publish_state(self):
        """
        Fetches the current state from the internal model and publishes it.
        """
        current_state = self.model.get_state()
        message: Message = current_state
        # print(f"[{self.agent_id}] Publishing state to '{self.state_topic}': {message}")
        self.bus.publish(self.state_topic, message)

    def run(self, current_time: float):
        """
        The main execution logic for the agent.

        In a simulation context, this method is called at each time step
        by the harness to make the agent publish its current state. This simulates
        a sensor broadcasting its reading periodically.

        Args:
            current_time: The current simulation time (ignored by this agent).
        """
        # print(f"DigitalTwinAgent '{self.agent_id}' run() called.")
        self.publish_state()
