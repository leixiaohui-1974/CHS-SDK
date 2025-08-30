"""
A simple message bus for inter-agent communication.
"""
from typing import Callable, Dict, Any, List

# Type alias for a message
Message = Dict[str, Any]
# Type alias for a listener callback function
Listener = Callable[[Message], None]

class MessageBus:
    """
    A simple, centralized message bus for agent communication.

    This allows agents to publish messages to specific topics and subscribe
    to topics to receive relevant messages. It decouples agents from each other,
    as they only need to know about the message bus, not the specific recipients.

    This is a key component of the multi-agent collaboration mechanism.
    """

    def __init__(self):
        self._subscriptions: Dict[str, List[Listener]] = {}
        self._component_topology: Dict[str, Dict[str, str]] = {}
        print("MessageBus created.")

    def set_component_topology(self, topology: Dict[str, Dict[str, str]]):
        """
        Stores the component connection topology.

        Args:
            topology: A dictionary representing the connections, e.g.,
                      {'gate_1': {'downstream': 'canal_1'}, 'canal_1': {'upstream': 'gate_1'}}
        """
        self._component_topology = topology
        print("Component topology set on MessageBus.")

    def get_component_topology(self) -> Dict[str, Dict[str, str]]:
        """
        Retrieves the component connection topology.

        Returns:
            The topology dictionary.
        """
        return self._component_topology

    def subscribe(self, topic: str, listener: Listener):
        """
        Subscribes a listener function to a topic.

        Args:
            topic: The topic to subscribe to (e.g., 'sensor.reservoir_1.level').
            listener: The callback function to execute when a message is published.
        """
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        # Avoid adding the same listener multiple times
        if listener not in self._subscriptions[topic]:
            self._subscriptions[topic].append(listener)
            print(f"New subscription to topic '{topic}' for listener {listener}.")
        else:
            print(f"Listener {listener} already subscribed to topic '{topic}'.")

    def unsubscribe(self, topic: str, listener: Listener):
        """
        Unsubscribes a listener function from a topic.

        Args:
            topic: The topic to unsubscribe from.
            listener: The listener object to remove.
        """
        if topic in self._subscriptions and listener in self._subscriptions[topic]:
            self._subscriptions[topic].remove(listener)
            print(f"Unsubscribed listener {listener} from topic '{topic}'.")
            if not self._subscriptions[topic]:
                del self._subscriptions[topic]

    def publish(self, topic: str, message: Message):
        """
        Publishes a message to a topic, notifying all subscribers.

        Args:
            topic: The topic to publish the message to.
            message: The message payload dictionary.
        """
        if topic in self._subscriptions:
            # print(f"Publishing message to topic '{topic}': {message}")
            for listener in self._subscriptions[topic]:
                # In a real system, this might be asynchronous
                listener(message)
        # else:
        #     print(f"Publishing to topic '{topic}' with no subscribers.")
