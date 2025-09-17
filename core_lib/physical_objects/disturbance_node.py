"""
A component that represents a point of water withdrawal or external inflow.
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.core.event_bus import get_global_event_bus
from typing import Optional
import numpy as np

class DisturbanceNode(PhysicalObjectInterface):
    """
    A simple node that allows for the withdrawal (or addition) of water.

    This component is designed to be controlled by a disturbance agent via the
    message bus. It receives an inflow from an upstream component and passes a
    modified outflow downstream.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus=None, action_topic: Optional[str] = None,
                 action_key: str = 'outflow'):
        super().__init__(name, initial_state, parameters)
        self._state['outflow'] = initial_state.get('outflow', 0.0)
        self._state['passthrough_flow'] = 0.0
        self.bus = message_bus
        self.action_topic = action_topic
        self.action_key = action_key

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"DisturbanceNode '{self.name}' subscribed to action topic '{self.action_topic}'.")

    def handle_action_message(self, message: Dict[str, Any]):
        """Callback to handle incoming action messages from the bus."""
        if self.action_key in message:
            new_value = message.get(self.action_key)
            if new_value is not None:
                self._state['outflow'] = float(new_value)

    def step(self, action: any, time_step: float) -> State:
        """
        Updates the node's state. The primary control is via the message bus,
        but this can also handle direct actions if needed.
        """
        # Direct action can override message bus for testing/simplicity
        if isinstance(action, dict) and self.action_key in action:
            self._state['outflow'] = float(action[self.action_key])

        passthrough_flow = max(0, self._inflow - self._state['outflow'])
        self._state['passthrough_flow'] = passthrough_flow

        return self.get_state()

    @property
    def outflow(self):
        """The outflow passed to the next component in the network."""
        return self._state['passthrough_flow']

    def set_inflow(self, inflow: float):
        """Sets the inflow for the current time step. Called by the harness."""
        self._inflow = inflow
        self._state['inflow'] = inflow
