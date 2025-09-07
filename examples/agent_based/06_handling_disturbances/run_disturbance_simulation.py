#!/usr/bin/env python3
"""
Example simulation script for Tutorial 5: Handling Disturbances.

This script demonstrates the resilience of the hierarchical control system when
faced with an external disturbance from a RainfallAgent.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.disturbances.rainfall_agent import RainfallAgent

def setup_control_system(harness, inflow_topic=None):
    """
    Initializes the control system components. This is based on the hierarchical
    control example, modified to allow for a disturbance inflow topic.
    """
    print("--- Initializing components for Control System ---")

    message_bus = harness.message_bus
    simulation_dt = harness.dt

    # --- Communication Topics ---
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"

    # --- Physical Components ---
    # Reservoir is now configured to listen for disturbance inflows.
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 18e6, 'water_level': 12.0},
        parameters={'surface_area': 1.5e6, 'storage_curve': [[0, 0], [30e6, 20]]},
        message_bus=message_bus,
        inflow_topic=inflow_topic
    )
    gate_params = {
        'max_rate_of_change': 0.5,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 5.0
    }
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
    pid = PIDController(
        Kp=-0.8, Ki=-0.1, Kd=-0.2,
        setpoint=12.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )
    lca = UnifiedGateControlAgent(
        agent_id="lca_gate_1",
        controller=pid,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=simulation_dt,
        command_topic=GATE_COMMAND_TOPIC,
        target_component="gate_1",
        control_type="gate_control"
    )

    dispatcher_rules = {
        "profiles": {
            "flood_control": {
                "condition": lambda states: states.get('reservoir_level', {}).get('water_level', 0) > 13.0,
                "commands": {
                    "gate1_command": {'new_setpoint': 11.0}
                }
            },
            "normal_operation": {
                "condition": lambda states: True,
                "commands": {
                    "gate1_command": {'new_setpoint': 12.0}
                }
            }
        }
    }
    dispatcher = CentralDispatcherAgent(
        agent_id="dispatcher_1",
        message_bus=message_bus,
        mode="rule",
        subscribed_topic=RESERVOIR_STATE_TOPIC,
        observation_key="water_level",
        command_topic=GATE_COMMAND_TOPIC,
        dispatcher_params={
            "low_level": 10.0,
            "high_level": 13.0,
            "low_setpoint": 15.0,
            "high_setpoint": 12.0
        }
    )

    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate)
    harness.add_agent(reservoir_twin)
    harness.add_agent(lca)
    harness.add_agent(dispatcher)
    harness.add_connection("reservoir_1", "gate_1")

def run_disturbance_simulation():
    """
    Sets up and runs the full simulation with a rainfall disturbance.
    """
    print("\n--- Setting up Tutorial 5: Handling Disturbances Simulation ---")

    simulation_config = {'end_time': 8000, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)

    RAINFALL_TOPIC = "disturbance.rainfall.inflow"

    # Setup the control system, telling the reservoir to listen for rainfall.
    setup_control_system(harness, inflow_topic=RAINFALL_TOPIC)

    # Create and add the disturbance agent
    rainfall_agent = RainfallAgent(
        agent_id="rainfall_agent_1",
        message_bus=harness.message_bus,
        topic=RAINFALL_TOPIC,
        start_time=300,
        duration=200,
        inflow_rate=150
    )
    harness.add_agent(rainfall_agent)

    harness.build()

    print("\n--- Running Simulation with Disturbance ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    final_level = harness.history[-1]['reservoir_1']['water_level']
    max_level = max(h['reservoir_1']['water_level'] for h in harness.history)
    print(f"Final reservoir water level: {final_level:.2f} m")
    print(f"Maximum reservoir water level during simulation: {max_level:.2f} m")

if __name__ == "__main__":
    run_disturbance_simulation()
