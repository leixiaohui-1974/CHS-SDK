"""
Example: Testing the ValveStationControlAgent

This script demonstrates the closed-loop control for a Valve Station.
1. A flow target is published.
2. The ValveStationControlAgent receives the target and the current state.
3. The agent calculates and sends new opening percentages to the valves.
4. The ValveStation model's flow rate changes.
5. The ValveStationPerceptionAgent publishes the new state.
6. The test verifies that the station's flow moves towards the target.
"""
import sys
import os
from typing import List, Dict, Any

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swp.core_engine.agent_factory.factory import AgentFactory
from swp.central_coordination.collaboration.message_bus import MessageBus

# --- Test Configuration ---
STATION_STATE_TOPIC = "state.valve_station.vs1"
STATION_GOAL_TOPIC = "goal.valve_station.vs1"
VALVE_1_ACTION_TOPIC = "action.valve.vs1_v1"

SYSTEM_CONFIG = {
    "components": [
        {
            "model": {
                "id": "vs_1",
                "type": "ValveStation",
                "initial_state": {},
                "params": {},
                "valves": [
                    {
                        "id": "vs1_v1",
                        "initial_state": {"opening": 50.0}, # Start at 50% open
                        "params": {
                            "diameter": 0.5, # meters
                            "discharge_coefficient": 0.8
                        },
                        "action_topic": VALVE_1_ACTION_TOPIC
                    }
                ]
            },
            "perception_agent": {
                "agent_id": "pa_vs_1",
                "state_topic": STATION_STATE_TOPIC
            },
            "control_agent": {
                "agent_id": "ca_vs_1",
                "type": "ValveStationControlAgent",
                "goal_topic": STATION_GOAL_TOPIC,
                "kp": 50.0 # A higher gain for faster convergence in the test
            }
        }
    ]
}

# --- Mock Subscriber ---
class StateLogger:
    def __init__(self):
        self.last_message: Dict[str, Any] = None
        self.history: List[Dict[str, Any]] = []

    def handle_message(self, message: Dict[str, Any]):
        print(f"StateLogger received message: {message}")
        self.last_message = message
        self.history.append(message)

# --- Test Runner ---
def run_test():
    print("--- Starting ValveStationControlAgent Test ---")
    bus = MessageBus()
    state_logger = StateLogger()
    bus.subscribe(STATION_STATE_TOPIC, state_logger.handle_message)

    factory = AgentFactory(message_bus=bus)
    agents, models = factory.create_system_from_config(SYSTEM_CONFIG)

    valve_station_model = models["vs_1"]
    perception_agent = next(a for a in agents if a.agent_id == "pa_vs_1")
    control_agent = next(a for a in agents if a.agent_id == "ca_vs_1")

    # --- SCENARIO: Achieve a target flow ---
    target_flow = 0.75 # m^3/s
    print(f"\n--- SCENARIO: Achieve a target flow of {target_flow} m^3/s ---")
    bus.publish(STATION_GOAL_TOPIC, {"target_total_flow": target_flow})

    # Run the simulation for a few steps to let the controller converge
    num_steps = 10
    # Action dict represents external conditions, e.g., upstream/downstream heads
    action = {'upstream_head': 10, 'downstream_head': 5}

    for i in range(num_steps):
        print(f"\n--- Step {i+1}/{num_steps} ---")
        # 1. Control agent runs its logic based on the last known state
        control_agent.run(current_time=i)
        # 2. The physical system reacts to the new valve opening
        valve_station_model.step(action=action, dt=1.0)
        # 3. Perception agent observes and publishes the new state
        perception_agent.run(current_time=i)
        # 4. The control agent's state handler is invoked by the publish, updating its internal state

    # --- Verification ---
    print("\n--- Verifying Results ---")
    final_flow = state_logger.last_message['total_outflow']
    print(f"Final flow after {num_steps} steps: {final_flow:.4f}")

    # Check that the controller got the flow reasonably close to the target
    assert abs(final_flow - target_flow) < 0.1, f"Controller failed to converge. Final flow: {final_flow}, Target: {target_flow}"

    print("SCENARIO PASSED: Controller successfully adjusted valve to meet flow target.")
    print("\n--- ValveStationControlAgent Test Passed ---")

if __name__ == "__main__":
    run_test()
