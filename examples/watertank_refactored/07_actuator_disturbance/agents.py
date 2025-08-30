# -*- coding: utf-8 -*-
"""
This module defines a custom Reservoir component for the actuator disturbance scenario.
"""
from typing import Dict, Any

from core_lib.core.interfaces import Message
from core_lib.physical_objects.reservoir import Reservoir

class DisturbanceAwareReservoir(Reservoir):
    """
    A custom Reservoir subclass that is aware of an external outflow disturbance
    provided via a message bus topic. This is needed because the standard
    Reservoir cannot subscribe to a data-driven outflow.
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
        # The data_inflow (actual, noisy inflow) is set by the PhysicalIOAgent
        total_inflow = self.data_inflow
        total_outflow = self.disturbance_outflow

        current_volume = self._state.get('volume', 0)
        surface_area = self._params.get('surface_area', 1e6)

        delta_volume = (total_inflow - total_outflow) * dt
        new_volume = current_volume + delta_volume

        self._state['volume'] = new_volume
        self._state['water_level'] = new_volume / surface_area
        # For logging, we can add the actual inflow to the state
        self._state['actual_inflow'] = total_inflow

        # Reset the data-driven inflow for the next step, ready for the PIO agent
        self.data_inflow = 0.0

        return self._state
