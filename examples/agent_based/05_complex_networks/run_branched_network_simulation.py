#!/usr/bin/env python3
"""
Example simulation script for Tutorial 5: A complex, branched network.

This script demonstrates the graph-based simulation capabilities for modeling
complex, non-linear network topologies.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent

def run_branched_network_simulation():
    """
    Sets up and runs the branched network simulation.
    """
    print("\n--- Setting up Tutorial 5: Complex Networks Simulation ---")

    # 1. --- Simulation Harness and Message Bus Setup ---
    simulation_config = {'duration': 2400, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. --- Physical Components ---
    print("Initializing physical components...")
    res1 = Reservoir(
        name="res1",
        initial_state={'volume': 1.104e6, 'water_level': 9.2},
        parameters={
            'surface_area': 1.2e5,
            'storage_curve': [[0, 0], [1.2e6, 10.0]],
        }
    )
    res1.set_base_inflow(5.0)

    g1 = Gate(
        name="g1",
        initial_state={'opening': 0.12},
        parameters={
            'width': 9.5,
            'max_rate_of_change': 0.25,
            'discharge_coefficient': 0.62,
        },
        message_bus=message_bus,
        action_topic="action.g1.opening",
        action_key='control_signal'
    )

    trib_chan = RiverChannel(
        name="trib_chan",
        initial_state={'volume': 4.0e5, 'water_level': 3.2},
        parameters={'k': 0.00032}
    )

    res2 = Reservoir(
        name="res2",
        initial_state={'volume': 1.45e6, 'water_level': 14.5},
        parameters={
            'surface_area': 1.0e5,
            'storage_curve': [[0, 0], [1.6e6, 16.0]],
        }
    )
    res2.set_base_inflow(8.0)

    g2 = Gate(
        name="g2",
        initial_state={'opening': 0.12},
        parameters={
            'width': 11.5,
            'max_rate_of_change': 0.22,
            'discharge_coefficient': 0.6,
        },
        message_bus=message_bus,
        action_topic="action.g2.opening",
        action_key='control_signal'
    )

    main_chan = RiverChannel(
        name="main_chan",
        initial_state={'volume': 5.0e5, 'water_level': 6.0},
        parameters={'k': 0.00026}
    )

    g3 = Gate(
        name="g3",
        initial_state={'opening': 0.45},
        parameters={'width': 18.0, 'discharge_coefficient': 0.58}
    )

    physical_components = [("res1", res1), ("g1", g1), ("trib_chan", trib_chan), ("res2", res2), ("g2", g2), ("main_chan", main_chan), ("g3", g3)]
    for comp_id, comp in physical_components:
        harness.add_component(comp_id, comp)

    # 3. --- Network Topology Definition ---
    print("Defining network connections...")
    harness.add_connection("res1", "g1")
    harness.add_connection("g1", "trib_chan")
    harness.add_connection("res2", "g2")
    harness.add_connection("trib_chan", "main_chan")
    harness.add_connection("g2", "main_chan")
    harness.add_connection("main_chan", "g3")

    # 4. --- Multi-Agent System Setup ---
    print("Setting up multi-agent control system...")
    twin_agents = [
        DigitalTwinAgent(agent_id="twin_res1", simulated_object=res1, message_bus=message_bus, state_topic="state.res1.level"),
        DigitalTwinAgent(agent_id="twin_g1", simulated_object=g1, message_bus=message_bus, state_topic="state.g1.opening"),
        DigitalTwinAgent(agent_id="twin_res2", simulated_object=res2, message_bus=message_bus, state_topic="state.res2.level"),
        DigitalTwinAgent(agent_id="twin_g2", simulated_object=g2, message_bus=message_bus, state_topic="state.g2.opening"),
    ]

    pid1 = PIDController(Kp=-0.6, Ki=-0.07, Kd=-0.12, setpoint=8.0, min_output=0.0, max_output=1.0)
    pid2 = PIDController(Kp=-0.55, Ki=-0.06, Kd=-0.11, setpoint=12.8, min_output=0.0, max_output=1.0)

    lca1 = LocalControlAgent(
        agent_id="lca_g1",
        message_bus=message_bus,
        dt=simulation_config['dt'],
        target_component="g1",
        control_type="gate_control",
        data_sources={"primary_data": "state.res1.level"},
        control_targets={"primary_target": "action.g1.opening"},
        allocation_config={},
        controller_config={},
        controller=pid1,
        observation_topic="state.res1.level",
        observation_key="water_level",
        action_topic="action.g1.opening",
        command_topic="command.res1.setpoint"
    )
    lca2 = LocalControlAgent(
        agent_id="lca_g2",
        message_bus=message_bus,
        dt=simulation_config['dt'],
        target_component="g2",
        control_type="gate_control",
        data_sources={"primary_data": "state.res2.level"},
        control_targets={"primary_target": "action.g2.opening"},
        allocation_config={},
        controller_config={},
        controller=pid2,
        observation_topic="state.res2.level",
        observation_key="water_level",
        action_topic="action.g2.opening",
        command_topic="command.res2.setpoint"
    )

    # This dispatcher is for monitoring; its rules won't trigger in this scenario
    dispatcher = CentralDispatcherAgent(
        agent_id="central_dispatcher",
        message_bus=message_bus,
        mode="rule",
        subscribed_topic="state.res1.level",
        observation_key="water_level",
        command_topic="command.res1.setpoint",
        dispatcher_params={
            "low_level": 7.8,
            "high_level": 8.6,
            "low_setpoint": 8.1,
            "high_setpoint": 7.9
        }
    )

    all_agents = twin_agents + [lca1, lca2, dispatcher]
    for agent in all_agents:
        harness.add_agent(agent)

    # 5. --- Build and Run Simulation ---
    print("\nBuilding simulation harness...")
    harness.build()
    print("Running simulation...")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    final_res1_level = harness.history[-1]['res1']['water_level']
    final_res2_level = harness.history[-1]['res2']['water_level']
    print(f"Final reservoir 1 water level: {final_res1_level:.2f} m (Setpoint: 8.0 m)")
    print(f"Final reservoir 2 water level: {final_res2_level:.2f} m (Setpoint: 12.8 m)")

if __name__ == "__main__":
    run_branched_network_simulation()
