"""
Example: Testing the CentralPerceptionAgent

This script demonstrates how the CentralPerceptionAgent aggregates state
information from multiple distributed agents into a unified global view.
"""
import sys
import os
from typing import List, Dict, Any

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swp.core_engine.agent_factory.factory import AgentFactory
from swp.central_coordination.collaboration.message_bus import MessageBus

# --- Test Configuration ---
PUMP_STATION_ID = 'ps_1'
VALVE_STATION_ID = 'vs_1'
PUMP_STATE_TOPIC = "state.pump_station.ps1"
VALVE_STATE_TOPIC = "state.valve_station.vs1"
GLOBAL_STATE_TOPIC = "state.network.global"

SYSTEM_CONFIG = {
    "components": [
        {
            "model": {
                "id": PUMP_STATION_ID,
                "type": "PumpStation",
                "initial_state": {'total_outflow': 50.0, 'active_pumps': 2, 'total_power_draw_kw': 100.0},
                "params": {},
                "pumps": [] # No need to define pumps for this test
            },
            "perception_agent": {
                "agent_id": "pa_ps_1",
                "state_topic": PUMP_STATE_TOPIC
            }
        },
        {
            "model": {
                "id": VALVE_STATION_ID,
                "type": "ValveStation",
                "initial_state": {'total_outflow': 50.0, 'valve_count': 1},
                "params": {},
                "valves": [] # No need to define valves for this test
            },
            "perception_agent": {
                "agent_id": "pa_vs_1",
                "state_topic": VALVE_STATE_TOPIC
            }
        }
    ],
    "central_agents": [
        {
            "agent_id": "central_perception",
            "type": "CentralPerceptionAgent",
            "subscribed_topics": {
                PUMP_STATION_ID: PUMP_STATE_TOPIC,
                VALVE_STATION_ID: VALVE_STATE_TOPIC
            },
            "global_state_topic": GLOBAL_STATE_TOPIC
        }
    ]
}

# --- Mock Subscriber ---
class GlobalStateLogger:
    def __init__(self):
        self.last_global_state: Dict[str, Any] = None

    def handle_message(self, message: Dict[str, Any]):
        print(f"GlobalStateLogger received message: {message}")
        self.last_global_state = message

# --- Test Runner ---
def run_test():
    print("--- Starting CentralPerceptionAgent Test ---")
    bus = MessageBus()
    global_state_logger = GlobalStateLogger()
    bus.subscribe(GLOBAL_STATE_TOPIC, global_state_logger.handle_message)

    factory = AgentFactory(message_bus=bus)
    agents, models = factory.create_system_from_config(SYSTEM_CONFIG)

    pump_perception_agent = next(a for a in agents if a.agent_id == "pa_ps_1")
    valve_perception_agent = next(a for a in agents if a.agent_id == "pa_vs_1")
    central_perception_agent = next(a for a in agents if a.agent_id == "central_perception")

    # --- SCENARIO: Verify state aggregation ---
    print("\n--- SCENARIO: Distributed agents publish state, central agent aggregates ---")

    # 1. Local agents publish their state
    pump_perception_agent.run(current_time=1)
    valve_perception_agent.run(current_time=1)

    # 2. Central agent runs to publish the aggregated state
    central_perception_agent.run(current_time=1)

    # 3. Verification
    print("\n--- Verifying Results ---")
    final_global_state = global_state_logger.last_global_state
    assert final_global_state is not None, "Global state logger should have received a message."

    # Check if the global state contains keys for both components
    assert PUMP_STATION_ID in final_global_state, "Global state should contain the pump station's ID."
    assert VALVE_STATION_ID in final_global_state, "Global state should contain the valve station's ID."

    # Check if the states within the global state match the original states
    pump_model = models[PUMP_STATION_ID]
    valve_model = models[VALVE_STATION_ID]

    assert final_global_state[PUMP_STATION_ID] == pump_model.get_state(), "Pump station state is incorrect."
    assert final_global_state[VALVE_STATION_ID] == valve_model.get_state(), "Valve station state is incorrect."

    print("Verification successful: Central agent correctly aggregated states from all components.")
    print("\n--- CentralPerceptionAgent Test Passed ---")

if __name__ == "__main__":
    run_test()
