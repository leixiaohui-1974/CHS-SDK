from abc import abstractmethod
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class BaseControlAgent(Agent):
    """
    Abstract base class for all control agents.
    It follows an event-driven pattern where logic is triggered by messages.
    """

    def __init__(self, agent_id: str, message_bus: MessageBus, time_step: int):
        """
        Initializes the BaseControlAgent.

        Args:
            agent_id (str): The unique identifier for the agent.
            message_bus: The message bus instance for communication.
            dt (int): The simulation time step in seconds.
        """
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.time_step= dt
        self._subscribed_topics = []

    @abstractmethod
    def handle_observation(self, message: Message):
        """
        Abstract callback method to handle incoming observation messages.
        This is where the core control logic should be implemented.
        """
        pass

    def run(self, current_time: float):
        """
        The main execution loop for the agent. For this event-driven agent,
        this method is a no-op as logic is triggered by message callbacks.
        """
        pass

    def __del__(self):
        """
        Destructor to clean up subscriptions.
        """
        for topic in self._subscribed_topics:
            # We need to pass the method itself as the listener to unsubscribe
            self.message_bus.unsubscribe(topic, self.handle_observation)
