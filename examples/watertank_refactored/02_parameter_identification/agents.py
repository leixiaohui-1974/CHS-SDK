# -*- coding: utf-8 -*-
"""
This module defines the message-bus-aware agents for the parameter identification scenario.
These agents act as wrappers around the original, script-based agents, adapting them
to the standard, message-driven architecture of the simulation harness.
"""
import sys
import os
from pathlib import Path

# --- Path Setup ---
# Add the original example's directory to the path to import its custom agents.
# This is a key part of the refactoring strategy, allowing us to reuse the
# original logic without placing it in the core library.
original_example_path = Path(__file__).resolve().parent.parent.parent / 'watertank' / '02_parameter_identification'
sys.path.insert(0, str(original_example_path))

# Also add the base agent path
base_agent_path = Path(__file__).resolve().parent.parent.parent / 'watertank' / 'base'
sys.path.insert(0, str(base_agent_path))


from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from reservoir_agent import ReservoirAgent as OriginalReservoirAgent
from twin_agent import TwinAgent as OriginalTwinAgent

# --- Wrapper Agents ---

class BusAwareReservoirAgent(Agent):
    """
    A wrapper that makes the original ReservoirAgent compatible with the message bus.

    It subscribes to an inflow topic, runs the original agent's logic,
    and publishes its state (water level) to an output topic.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = config

        # Instantiate the original agent that contains the core logic
        self._logic_agent = OriginalReservoirAgent(agent_id, config['reservoir_params'])

        # State for storing data from the bus
        self.current_inflow = 0.0

        # Subscribe to topics
        self.inflow_topic = config['inflow_topic']
        self.bus.subscribe(self.inflow_topic, self.handle_inflow)

        # Topic to publish results
        self.output_topic = config['output_topic']

    def handle_inflow(self, message: Message):
        """Callback to receive inflow data."""
        self.current_inflow = message.get("value", 0.0)

    def run(self, current_time: float, dt: float):
        """Main execution loop called by the harness."""
        # Prepare observation dict for the original agent
        obs = {"inflow": self.current_inflow, "dt": dt}
        self._logic_agent.step(obs)

        # Get the new state and publish it
        state = self._logic_agent.get_state()
        water_level = state['water_level']
        self.bus.publish(self.output_topic, Message(self.agent_id, {"value": water_level}))


class BusAwareTwinAgent(Agent):
    """
    A wrapper for the original TwinAgent.

    It subscribes to both inflow and the real reservoir's water level,
    runs the identification logic, and publishes its own state for logging.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = config

        # Instantiate the original agent
        self._logic_agent = OriginalTwinAgent(
            agent_id,
            config['twin_params'],
            config['identification_params']
        )

        # State for storing data from the bus
        self.current_inflow = 0.0
        self.real_water_level = None # Use None to track if we've received it this step

        # Subscribe to topics
        self.inflow_topic = config['inflow_topic']
        self.real_level_topic = config['real_level_topic']
        self.bus.subscribe(self.inflow_topic, self.handle_inflow)
        self.bus.subscribe(self.real_level_topic, self.handle_real_level)

        # Topics for publishing results
        self.twin_level_topic = config['twin_level_topic']
        self.estimated_coeff_topic = config['estimated_coeff_topic']

    def handle_inflow(self, message: Message):
        """Callback to receive inflow data."""
        self.current_inflow = message.get("value", 0.0)

    def handle_real_level(self, message: Message):
        """Callback to receive the real water level from the other agent."""
        self.real_water_level = message.get("value")

    def run(self, current_time: float, dt: float):
        """Main execution loop."""
        # Ensure we have received the real water level data for this step before running
        if self.real_water_level is None:
            # Data from the real reservoir hasn't arrived yet for this step.
            # This can happen due to agent execution order. Skip this run.
            # The harness will call us again.
            return

        # Prepare observation dict for the original agent
        obs = {
            "inflow": self.current_inflow,
            "dt": dt,
            "real_water_level": self.real_water_level
        }
        self._logic_agent.step(obs)

        # Get the new state and publish it for logging
        state = self._logic_agent.get_state()
        self.bus.publish(self.twin_level_topic, Message(self.agent_id, {"value": state['water_level']}))
        self.bus.publish(self.estimated_coeff_topic, Message(self.agent_id, {"value": state['estimated_coeff']}))

        # Reset real_water_level to None to ensure we wait for fresh data next step
        self.real_water_level = None
