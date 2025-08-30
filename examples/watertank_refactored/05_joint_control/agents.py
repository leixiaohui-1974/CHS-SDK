# -*- coding: utf-8 -*-
"""
This module defines the custom agents for the joint control scenario.
The original coordinator agent is wrapped to make it compatible with the
simulation harness.
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
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from joint_control_agent import JointControlCoordinatorAgent as OriginalCoordinatorAgent

# --- Custom Agents for this Scenario ---

class BusAwareCoordinatorAgent(Agent):
    """
    A wrapper that makes the original event-driven JointControlCoordinatorAgent
    compatible with the run-based simulation harness.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self._config = kwargs

        # Instantiate the original agent that contains the core logic.
        # The original agent subscribes to topics itself upon creation.
        self._logic_agent = OriginalCoordinatorAgent(
            agent_id=f"{agent_id}_internal",
            message_bus=self.bus,
            config=kwargs['coordinator_config']
        )

        # The original agent is event-driven, its logic is in `handle_state_message`.
        # The message bus will trigger it directly when the new perception agent
        # publishes a new state. So, this wrapper's run() method can be empty.
        print(f"[{self.agent_id}] wrapper created. Internal logic agent is event-driven.")

    def run(self, current_time: float):
        pass
