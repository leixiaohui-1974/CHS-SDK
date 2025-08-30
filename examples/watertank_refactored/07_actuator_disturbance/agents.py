# -*- coding: utf-8 -*-
"""
This module defines custom components and agents for the actuator disturbance scenario.
It uses inheritance to extend the functionality of core library classes to meet
the specific requirements of this scenario, namely using PhysicalIOAgent to
simulate a noisy actuator for a message-driven component.
"""
import random
from typing import Dict, Any

from core_lib.core.interfaces import Message
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent

# --- Custom Component (Subclass of a Physical Object) ---

class DisturbanceAwareReservoir(Reservoir):
    """
    A custom Reservoir subclass that is aware of an external outflow disturbance
    provided via a message bus topic.
    """
    def __init__(self, disturbance_outflow_topic: str, **kwargs):
        super().__init__(**kwargs)
        self.disturbance_outflow = 0.0
        if self.bus:
            self.bus.subscribe(disturbance_outflow_topic, self.handle_disturbance_message)
            print(f"[{self.name}] Subscribed to disturbance topic '{disturbance_outflow_topic}'.")

    def handle_disturbance_message(self, message: Message):
        """Callback to store the latest disturbance outflow value."""
        self.disturbance_outflow = message.get("value", 0.0)

    def step(self, action: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Overrides the base step method to include the disturbance outflow.
        """
        # The parent step method calculates total_inflow from physical_inflow
        # and data_inflow. The NoisyPhysicalIOAgent will set data_inflow.
        # It also calculates an outflow based on downstream demand, which is 0 here.

        # We will manually calculate the water balance here to include the disturbance.
        current_volume = self._state.get('volume', 0)
        surface_area = self._params.get('surface_area', 1e6)

        # The data_inflow (actual, noisy inflow) is set by the NoisyPhysicalIOAgent
        total_inflow = self.data_inflow
        total_outflow = self.disturbance_outflow

        delta_volume = (total_inflow - total_outflow) * dt
        new_volume = current_volume + delta_volume

        self._state['volume'] = new_volume
        self._state['water_level'] = new_volume / surface_area
        self._state['actual_inflow'] = total_inflow # For logging

        # Reset the data-driven inflow for the next step
        self.data_inflow = 0.0

        return self._state


# --- Custom Agent (Subclass of a Core Agent) ---

class NoisyPhysicalIOAgent(PhysicalIOAgent):
    """
    A custom PhysicalIOAgent subclass that adds noise and bias to actuator commands
    and also publishes the corrupted signal for logging purposes.
    """
    def __init__(self, noise_params: dict, **kwargs):
        super().__init__(**kwargs)
        self.bias = noise_params.get('bias', 1.0)
        self.std_dev = noise_params.get('std_dev', 0.0)
        # Topic for publishing the noisy signal for logging
        self.log_topic = noise_params.get('log_topic')
        print(f"NoisyPhysicalIOAgent '{self.agent_id}' initialized with actuator noise (bias={self.bias}, std_dev={self.std_dev}).")

    def _handle_action(self, message: Message, config: Dict[str, Any]):
        """
        Overrides the base _handle_action method to inject noise and bias.
        """
        obj = config['obj']
        target_attr = config['target_attr']
        control_key = config['control_key']

        commanded_signal = message.get(control_key)
        if commanded_signal is None:
            return

        # --- Noise Injection Logic ---
        noise = random.gauss(0, self.std_dev)
        actual_signal = (commanded_signal * self.bias) + noise
        if actual_signal < 0:
            actual_signal = 0
        # --- End of Noise Logic ---

        # Publish the actual, noisy signal for logging before applying it
        if self.log_topic:
            self.bus.publish(self.log_topic, Message(self.agent_id, {"value": actual_signal}))

        # Set the target attribute on the physical object with the corrupted signal
        setattr(obj, target_attr, actual_signal)
