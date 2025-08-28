"""
Example: Verifying the ReservoirPerceptionAgent

This script tests that the AgentFactory correctly instantiates the
specialized `ReservoirPerceptionAgent` for a Reservoir model, instead of
the generic DigitalTwinAgent.
"""
import sys
import os

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swp.core_engine.agent_factory.factory import AgentFactory
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.local_agents.perception.reservoir_perception_agent import ReservoirPerceptionAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent

# --- Test Configuration ---
RESERVOIR_ID = 'res_1'
RESERVOIR_STATE_TOPIC = "state.reservoir.res1"

SYSTEM_CONFIG = {
    "components": [
        {
            "model": {
                "id": RESERVOIR_ID,
                "type": "Reservoir",
                "initial_state": {"volume": 10000},
                "params": {"area": 5000}
            },
            "perception_agent": {
                "agent_id": "pa_res_1",
                "state_topic": RESERVOIR_STATE_TOPIC
            }
        }
    ]
}

def run_test():
    """
    Runs the test scenario.
    """
    print("--- Starting ReservoirPerceptionAgent Factory Test ---")
    bus = MessageBus()
    factory = AgentFactory(message_bus=bus)

    # Create the system from the config
    agents, models = factory.create_system_from_config(SYSTEM_CONFIG)

    # --- Verification ---
    print("\n--- Verifying Agent Type ---")

    assert len(agents) == 1, "Expected exactly one agent to be created."
    created_agent = agents[0]

    print(f"Agent created is of type: {type(created_agent).__name__}")

    # The main assertion: Is the created agent the specialized one?
    assert isinstance(created_agent, ReservoirPerceptionAgent), \
        f"Agent should be ReservoirPerceptionAgent, but was {type(created_agent).__name__}."

    # As a sanity check, ensure it's not JUST the base class
    assert not type(created_agent) is DigitalTwinAgent, \
        "Agent should be a specialized subclass, not the base DigitalTwinAgent."

    print("Verification successful: AgentFactory correctly instantiated ReservoirPerceptionAgent.")
    print("\n--- ReservoirPerceptionAgent Factory Test Passed ---")

if __name__ == "__main__":
    run_test()
