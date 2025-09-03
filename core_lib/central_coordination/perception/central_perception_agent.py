"""
Central Perception Agent for aggregating distributed state information.
"""
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import List, Dict, Any

class CentralPerceptionAgent(Agent):
    """
    The Central Perception Agent acts as the "sensory cortex" of the MAS.

    It subscribes to the state topics of multiple distributed perception agents
    and aggregates their individual states into a single, unified view of the
    entire network. This global state can then be used by central dispatchers
    or for high-level system monitoring.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 config=None,
                 **kwargs):
        # Handle different parameter formats
        if config is None:
            config = kwargs
        
        # Extract parameters from config
        data_collection = config.get('data_collection', None)
        subscribe_topics = config.get('subscribe_topics', None)
        data_fusion_config = config.get('data_fusion_config', None)
        centralized_twin_config = config.get('centralized_twin_config', None)
        global_evaluation_config = config.get('global_evaluation_config', None)
        global_prediction_config = config.get('global_prediction_config', None)
        publish_topics = config.get('publish_topics', None)
        subscribed_topics = config.get('subscribed_topics', None)
        global_state_topic = config.get('global_state_topic', None)
        """
        Initializes the CentralPerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            message_bus: The system's message bus for communication.
            data_collection: Data collection configuration
            subscribe_topics: List of topics to subscribe to
            data_fusion_config: Data fusion configuration
            centralized_twin_config: Centralized twin configuration
            global_evaluation_config: Global evaluation configuration
            global_prediction_config: Global prediction configuration
            publish_topics: List of topics to publish to
            subscribed_topics: Legacy parameter for backward compatibility
            global_state_topic: Legacy parameter for backward compatibility
        """
        super().__init__(agent_id)
        self.bus = message_bus
        
        # Handle legacy parameters for backward compatibility
        if subscribed_topics is not None:
            self.subscribed_topics = subscribed_topics
        else:
            # Convert subscribe_topics list to a dictionary format
            self.subscribed_topics = {}
            if subscribe_topics:
                for i, topic in enumerate(subscribe_topics):
                    component_id = f"component_{i}"
                    self.subscribed_topics[component_id] = topic
        
        if global_state_topic is not None:
            self.global_state_topic = global_state_topic
        else:
            # Use the first publish topic as global state topic
            if publish_topics and len(publish_topics) > 0:
                self.global_state_topic = publish_topics[0]
            else:
                self.global_state_topic = "agent.central_perception.system_state"
        
        # Store configuration parameters
        self.data_collection = data_collection or {}
        self.data_fusion_config = data_fusion_config or {}
        self.centralized_twin_config = centralized_twin_config or {}
        self.global_evaluation_config = global_evaluation_config or {}
        self.global_prediction_config = global_prediction_config or {}
        self.publish_topics = publish_topics or []

        # The unified, global state of the network
        self.global_state: Dict[str, State] = {comp_id: {} for comp_id in self.subscribed_topics.keys()}

        # Subscribe to each component's state topic
        for comp_id, topic in self.subscribed_topics.items():
            # Use a lambda with a default argument to capture the comp_id correctly
            self.bus.subscribe(topic, lambda msg, cid=comp_id: self.handle_state_message(cid, msg))
            print(f"'{self.agent_id}' subscribed to topic '{topic}' for component '{comp_id}'.")

    def handle_state_message(self, component_id: str, message: State):
        """
        Callback to update a part of the global state when a message is received.
        """
        print(f"'{self.agent_id}' received state update from '{component_id}': {message}")
        self.global_state[component_id] = message
        # In a real system, we might publish the global state on every update
        # or on a fixed interval. For simplicity, we'll make the run() method publish.

    def publish_global_state(self):
        """Publishes the entire aggregated state to the global topic."""
        print(f"'{self.agent_id}' publishing global state to '{self.global_state_topic}'.")
        self.bus.publish(self.global_state_topic, self.global_state)

    def run(self, current_time: float):
        """
        The main execution loop for the agent.

        This agent's primary role is reactive, but the run loop is used to
        periodically publish the complete, aggregated state.
        """
        self.publish_global_state()
