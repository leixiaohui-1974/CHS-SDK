#!/usr/bin/env python3
"""
Example simulation script for Tutorial 4: A hierarchical control system.

This script demonstrates a two-level hierarchical control system where a high-level
supervisory agent manages the objectives of a low-level, local controller.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def setup_hierarchical_control_system(harness):
    """
    Initializes and connects all components for the hierarchical control simulation.
    """
    print("--- Initializing components for Hierarchical Control ---")

    message_bus = harness.message_bus
    simulation_dt = harness.dt

    # --- Communication Topics ---
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"

    # --- Physical Components ---
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 28.5e6, 'water_level': 19.0},
        parameters={'surface_area': 1.5e6, 'storage_curve': [[0, 0], [30e6, 20]]}
    )
    gate_params = {
        'max_rate_of_change': 0.5,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 5.0
    }
    # The Gate needs to listen for the 'control_signal' key from the LocalControlAgent.
    gate = Gate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC,
        action_key='control_signal'
    )

    # --- Agent Components ---
    reservoir_twin = DigitalTwinAgent(
        agent_id="twin_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )
    gate_twin = DigitalTwinAgent(
        agent_id="twin_gate_1",
        simulated_object=gate,
        message_bus=message_bus,
        state_topic=GATE_STATE_TOPIC
    )

    pid = PIDController(
        Kp=-0.8, Ki=-0.1, Kd=-0.2,
        setpoint=15.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )
    lca = LocalControlAgent(
        agent_id="lca_gate_1",
        controller=pid,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=simulation_dt,
        command_topic=GATE_COMMAND_TOPIC,
        feedback_topic=GATE_STATE_TOPIC
    )

    # --- Central Dispatcher with Corrected Message Key ---
    dispatcher_rules = {
        "profiles": {
            "flood_control": {
                "condition": lambda states: states.get('reservoir_level', {}).get('water_level', 0) > 18.0,
                "commands": {
                    "gate1_command": {'new_setpoint': 12.0}
                }
            },
            "normal_operation": {
                "condition": lambda states: True,
                "commands": {
                    "gate1_command": {'new_setpoint': 15.0}
                }
            }
        }
    }
    dispatcher = CentralDispatcher(
        agent_id="dispatcher_1",
        message_bus=message_bus,
        state_subscriptions={'reservoir_level': RESERVOIR_STATE_TOPIC},
        command_topics={'gate1_command': GATE_COMMAND_TOPIC},
        rules=dispatcher_rules
    )

    # --- Add all components to the harness ---
    harness.add_component(reservoir)
    harness.add_component(gate)
    harness.add_agent(reservoir_twin)
    harness.add_agent(gate_twin)
    harness.add_agent(lca)
    harness.add_agent(dispatcher)
    harness.add_connection("reservoir_1", "gate_1")


def run_hierarchical_simulation():
    """
    Sets up and runs the full hierarchical simulation.
    """
    print("\n--- Setting up Tutorial 4: Hierarchical Control Simulation ---")

    simulation_config = {'duration': 500, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)

    setup_hierarchical_control_system(harness)

    harness.build()

    print("\n--- Running Hierarchical Simulation ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    final_level = harness.history[-1]['reservoir_1']['water_level']
    final_opening = harness.history[-1]['gate_1']['opening']
    print(f"Final reservoir water level: {final_level:.2f} m")
    print(f"Final gate opening: {final_opening:.2f} m")


if __name__ == "__main__":
    run_hierarchical_simulation()
