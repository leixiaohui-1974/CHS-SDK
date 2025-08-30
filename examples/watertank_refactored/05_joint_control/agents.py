# -*- coding: utf-8 -*-
"""
This module defines the custom agents for the joint control scenario.
To faithfully replicate the original script's logic, the reservoir itself
is modeled as an agent, and the original coordinator agent is wrapped to
make it compatible with the simulation harness.
"""
import sys
from pathlib import Path

# --- Path Setup ---
# Add the original example's directory to the path to import its custom agent.
original_example_path = Path(__file__).resolve().parent.parent.parent / 'watertank' / '05_joint_control'
sys.path.insert(0, str(original_example_path))

# Add base path for the original agent's imports
base_agent_path = Path(__file__).resolve().parent.parent.parent / 'watertank' / 'base'
sys.path.insert(0, str(base_agent_path))


from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from joint_control_agent import JointControlCoordinatorAgent as OriginalCoordinatorAgent

# --- Custom Agents for this Scenario ---

class ReservoirSimulationAgent(Agent):
    """
    An agent that simulates the physics of a reservoir.

    It subscribes to topics for inflow and outflow, calculates the
    change in water level based on a simple water balance equation,
    and publishes the new water level.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = config

        # Physical parameters
        self.water_level = config['initial_state']['water_level']
        self.surface_area = config['parameters']['surface_area']

        # Topics
        self.pump_inflow_topic = config['pump_inflow_topic']
        self.valve_outflow_topic = config['valve_outflow_topic']
        self.disturbance_outflow_topic = config['disturbance_outflow_topic']
        self.state_output_topic = config['state_output_topic']

        # Internal state for received data
        self.pump_inflow = 0.0
        self.valve_outflow = 0.0
        self.disturbance_outflow = 0.0

        # Subscriptions
        self.bus.subscribe(self.pump_inflow_topic, lambda msg: self.set_value('pump_inflow', msg))
        self.bus.subscribe(self.valve_outflow_topic, lambda msg: self.set_value('valve_outflow', msg))
        self.bus.subscribe(self.disturbance_outflow_topic, lambda msg: self.set_value('disturbance_outflow', msg))

    def set_value(self, key: str, message: Message):
        """Generic callback to update internal state from a message."""
        value = message.get("value", 0.0)
        if isinstance(value, (int, float)):
            setattr(self, key, value)

    def run(self, current_time: float, dt: float):
        # The total outflow is the sum of the controlled valve outflow and the
        # uncontrollable disturbance outflow.
        total_inflow = self.pump_inflow
        total_outflow = self.valve_outflow + self.disturbance_outflow

        delta_h = (total_inflow - total_outflow) * dt / self.surface_area
        self.water_level += delta_h

        if self.water_level < 0:
            self.water_level = 0

        # Publish the new state for the coordinator to read
        self.bus.publish(self.state_output_topic, Message(self.agent_id, {"value": self.water_level}))

        # Reset for next step to avoid using stale data if a message is missed
        self.pump_inflow = 0.0
        self.valve_outflow = 0.0
        self.disturbance_outflow = 0.0


class BusAwareCoordinatorAgent(Agent):
    """
    A wrapper that makes the original event-driven JointControlCoordinatorAgent
    compatible with the run-based simulation harness.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = config

        # Instantiate the original agent that contains the core logic.
        # The original agent subscribes to topics itself upon creation.
        self._logic_agent = OriginalCoordinatorAgent(
            agent_id=f"{agent_id}_internal",
            message_bus=self.bus,
            config=config['coordinator_config']
        )

        # The original agent is event-driven, its logic is in `handle_state_message`.
        # The message bus will trigger it directly when the ReservoirSimulationAgent
        # publishes a new state. So, this wrapper's run() method can be empty.
        print(f"[{self.agent_id}] wrapper created. Internal logic agent is event-driven.")

    def run(self, current_time: float, dt: float):
        pass
