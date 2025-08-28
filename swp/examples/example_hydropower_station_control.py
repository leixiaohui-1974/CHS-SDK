"""
Example: Testing the HydropowerStationControlAgent

This script demonstrates the complex control loop for a Hydropower Station,
involving coordination between turbines and gates to meet dual objectives.
"""
import sys
import os
from typing import List, Dict, Any

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swp.core_engine.agent_factory.factory import AgentFactory
from swp.central_coordination.collaboration.message_bus import MessageBus

# --- Test Configuration ---
STATION_STATE_TOPIC = "state.hydro_station.hs1"
STATION_GOAL_TOPIC = "goal.hydro_station.hs1"
TURBINE_1_ACTION_TOPIC = "action.turbine.hs1_t1"
GATE_1_ACTION_TOPIC = "action.gate.hs1_g1"

SYSTEM_CONFIG = {
    "components": [
        {
            "model": {
                "id": "hs_1",
                "type": "HydropowerStation",
                "initial_state": {},
                "params": {"turbine_efficiency": 0.90},
                "turbines": [
                    {
                        "id": "hs1_t1",
                        "initial_state": {"outflow": 0},
                        "params": {"efficiency": 0.90, "max_flow_rate": 100.0},
                        "action_topic": TURBINE_1_ACTION_TOPIC
                    }
                ],
                "gates": [
                    {
                        "id": "hs1_g1",
                        "initial_state": {"opening": 0.0},
                        "params": {
                            "width": 5.0,
                            "discharge_coefficient": 0.6,
                            "max_opening": 2.0,
                            "max_rate_of_change": 1.0  # Increase rate of change for faster test convergence
                        },
                        "action_topic": GATE_1_ACTION_TOPIC
                    }
                ]
            },
            "perception_agent": {
                "agent_id": "pa_hs_1",
                "state_topic": STATION_STATE_TOPIC
            },
            "control_agent": {
                "agent_id": "ca_hs_1",
                "type": "HydropowerStationControlAgent"
            }
        }
    ]
}

# --- Test Runner ---
def run_test():
    print("--- Starting HydropowerStationControlAgent Test ---")
    bus = MessageBus()
    factory = AgentFactory(message_bus=bus)

    # Manually set the goal topic for the control agent in the config
    SYSTEM_CONFIG['components'][0]['control_agent']['goal_topic'] = STATION_GOAL_TOPIC

    agents, models = factory.create_system_from_config(SYSTEM_CONFIG)

    station_model = models["hs_1"]
    perception_agent = next(a for a in agents if a.agent_id == "pa_hs_1")
    control_agent = next(a for a in agents if a.agent_id == "ca_hs_1")

    # --- SCENARIO: Generate power and meet a total outflow target ---
    # Goal: 5 MW of power, and a total outflow of 80 m^3/s
    target_power = 5_000_000 # 5 MW
    target_outflow = 80.0

    print(f"\n--- SCENARIO: Target Power={target_power/1e6:.1f}MW, Target Outflow={target_outflow}m^3/s ---")
    bus.publish(STATION_GOAL_TOPIC, {
        "target_power_generation": target_power,
        "target_total_outflow": target_outflow
    })

    # Simulate external conditions (e.g., from an upstream reservoir)
    upstream_head = 100
    downstream_head = 80
    head_action = {'upstream_head': upstream_head, 'downstream_head': downstream_head}

    # Manually publish initial head info so the controller can make its first decision
    bus.publish(STATION_STATE_TOPIC, {'upstream_head': upstream_head, 'downstream_head': downstream_head})

    # Run a few steps to show the system responding
    for i in range(5):
        print(f"\n--- Step {i+1}/5 ---")

        # 1. Control agent decides based on last known state
        control_agent.run(current_time=i)

        # 2. Physical system reacts
        # The station's inflow is a constraint. Assume it's sufficient for this test.
        station_model.set_inflow(200)
        station_model.step(action=head_action, dt=1.0)

        # 3. Perception agent observes and publishes the new state
        # In a real system, this state message would be an aggregate from multiple sensors.
        # Here, we enrich the model's state with the head info for the controller.
        current_state = station_model.get_state()
        current_state.update(head_action)
        bus.publish(STATION_STATE_TOPIC, current_state)

    # --- Verification ---
    print("\n--- Verifying Final State ---")
    final_state = station_model.get_state()
    print(f"Final State: {final_state}")

    final_power = final_state['total_power_generation']
    final_outflow = final_state['total_outflow']

    # Verify power is close to target
    power_error = abs(final_power - target_power) / target_power
    assert power_error < 0.1, f"Power target not met. Final: {final_power:.2f}, Target: {target_power:.2f}"
    print(f"Power target successfully met (Error: {power_error:.2%}).")

    # Verify total outflow is close to target
    outflow_error = abs(final_outflow - target_outflow) / target_outflow
    assert outflow_error < 0.1, f"Outflow target not met. Final: {final_outflow:.2f}, Target: {target_outflow:.2f}"
    print(f"Outflow target successfully met (Error: {outflow_error:.2%}).")

    print("\n--- HydropowerStationControlAgent Test Passed ---")

if __name__ == "__main__":
    run_test()
