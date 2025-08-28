"""
Example: Testing the PumpStationControlAgent

This script demonstrates the full control loop for a Pump Station.
1. A goal is published (e.g., "turn on 2 pumps").
2. The PumpStationControlAgent receives the goal.
3. The Control Agent sends commands to individual pumps.
4. The PumpStation model state is updated.
5. The PumpStationPerceptionAgent observes and publishes the new state.
6. The test verifies the final state matches the initial goal.
"""
import sys
import os
import time
from typing import List, Dict, Any

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swp.core_engine.agent_factory.factory import AgentFactory
from swp.central_coordination.collaboration.message_bus import MessageBus

# --- Test Configuration ---
STATION_STATE_TOPIC = "state.pump_station.ps1"
STATION_GOAL_TOPIC = "goal.pump_station.ps1"
PUMP_1_ACTION_TOPIC = "action.pump.ps1_p1"
PUMP_2_ACTION_TOPIC = "action.pump.ps1_p2"

SYSTEM_CONFIG = {
    "components": [
        {
            "model": {
                "id": "ps_1",
                "type": "PumpStation",
                "initial_state": {},
                "params": {},
                "pumps": [
                    {
                        "id": "ps1_p1",
                        "initial_state": {"status": 0}, # Start off
                        "params": {"max_flow_rate": 10.0},
                        "action_topic": PUMP_1_ACTION_TOPIC
                    },
                    {
                        "id": "ps1_p2",
                        "initial_state": {"status": 0}, # Start off
                        "params": {"max_flow_rate": 10.0},
                        "action_topic": PUMP_2_ACTION_TOPIC
                    }
                ]
            },
            "perception_agent": {
                "agent_id": "pa_ps_1",
                "state_topic": STATION_STATE_TOPIC
            },
            "control_agent": {
                "agent_id": "ca_ps_1",
                "type": "PumpStationControlAgent",
                "goal_topic": STATION_GOAL_TOPIC
            }
        }
    ]
}

# --- Mock Subscriber ---
class StateLogger:
    def __init__(self):
        self.last_message: Dict[str, Any] = None

    def handle_message(self, message: Dict[str, Any]):
        print(f"StateLogger received message: {message}")
        self.last_message = message

# --- Test Runner ---
def run_test():
    print("--- Starting PumpStationControlAgent Test ---")
    bus = MessageBus()
    state_logger = StateLogger()
    bus.subscribe(STATION_STATE_TOPIC, state_logger.handle_message)

    factory = AgentFactory(message_bus=bus)
    agents, models = factory.create_system_from_config(SYSTEM_CONFIG)

    pump_station_model = models["ps_1"]
    perception_agent = next(a for a in agents if a.agent_id == "pa_ps_1")
    control_agent = next(a for a in agents if a.agent_id == "ca_ps_1")

    # --- SCENARIO 1: Turn on 1 pump ---
    print("\n--- SCENARIO 1: Goal = 1 active pump ---")
    # Publish the goal
    bus.publish(STATION_GOAL_TOPIC, {"target_active_pumps": 1})

    # Let the message propagate (in a real system, this is asynchronous)
    # The control agent's handle_goal_message and run_control_logic are triggered by the publish call.

    # Step the physical model
    pump_station_model.step(action={}, dt=1.0)

    # Run the perception agent to publish the new state
    perception_agent.run(current_time=1)

    # Verify
    time.sleep(0.1) # Allow a moment for async message handling
    assert state_logger.last_message is not None, "State logger should have received a message."
    assert state_logger.last_message['active_pumps'] == 1, "Should be 1 active pump."
    assert state_logger.last_message['total_outflow'] == 10.0, "Total outflow should be 10.0."
    print("SCENARIO 1 PASSED")

    # --- SCENARIO 2: Turn on 2 pumps ---
    print("\n--- SCENARIO 2: Goal = 2 active pumps ---")
    bus.publish(STATION_GOAL_TOPIC, {"target_active_pumps": 2})
    pump_station_model.step(action={}, dt=1.0)
    perception_agent.run(current_time=2)
    time.sleep(0.1)
    assert state_logger.last_message['active_pumps'] == 2, "Should be 2 active pumps."
    assert state_logger.last_message['total_outflow'] == 20.0, "Total outflow should be 20.0."
    print("SCENARIO 2 PASSED")

    # --- SCENARIO 3: Turn all pumps off ---
    print("\n--- SCENARIO 3: Goal = 0 active pumps ---")
    bus.publish(STATION_GOAL_TOPIC, {"target_active_pumps": 0})
    pump_station_model.step(action={}, dt=1.0)
    perception_agent.run(current_time=3)
    time.sleep(0.1)
    assert state_logger.last_message['active_pumps'] == 0, "Should be 0 active pumps."
    assert state_logger.last_message['total_outflow'] == 0.0, "Total outflow should be 0.0."
    print("SCENARIO 3 PASSED")

    print("\n--- PumpStationControlAgent Test Passed ---")

if __name__ == "__main__":
    run_test()
