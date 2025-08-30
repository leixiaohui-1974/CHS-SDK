from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class StepAgent(Agent):
    """
    An agent that sends a single action message at a specified time.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 action_topic: str,
                 action_time: float,
                 action_value: float):
        """
        Initializes the StepAgent.

        Args:
            agent_id: The unique ID for the agent.
            message_bus: The system's message bus.
            action_topic: The topic to publish the action message on.
            action_time: The simulation time at which to send the action.
            action_value: The value to send in the action message.
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.action_topic = action_topic
        self.action_time = action_time
        self.action_value = action_value
        self.action_sent = False

    def run(self, current_time: float):
        """
        Checks the current time and sends the action if the time is reached.
        """
        if not self.action_sent and current_time >= self.action_time:
            message: Message = {'control_signal': self.action_value}
            self.bus.publish(self.action_topic, message)
            self.action_sent = True
