#!/usr/bin/env python3
"""Refactored complex network example driven by SimulationBuilder."""

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent


def create_branched_network_system() -> SimulationBuilder:
    """Create the branched network scenario with shared parameters."""
    config = {'duration': 2400, 'end_time': 2400, 'dt': 1.0}
    builder = SimulationBuilder(config)

    print("Initializing physical components...")

    # Reservoirs with calibrated surface areas and inflows
    builder.add_reservoir(
        component_id="res1",
        water_level=9.2,
        surface_area=1.2e5,
        volume=1.104e6,
        storage_curve=[[0, 0], [1.2e6, 10.0]],
        inflow=5.0,
    )
    builder.add_reservoir(
        component_id="res2",
        water_level=14.5,
        surface_area=1.0e5,
        volume=1.45e6,
        storage_curve=[[0, 0], [1.6e6, 16.0]],
        inflow=8.0,
    )

    # Gates tied to message bus topics
    builder.add_gate(
        component_id="g1",
        opening=0.12,
        max_rate_of_change=0.25,
        control_topic="action.g1.opening",
        additional_parameters={'discharge_coefficient': 0.62, 'width': 9.5},
    )
    builder.add_gate(
        component_id="g2",
        opening=0.12,
        max_rate_of_change=0.22,
        control_topic="action.g2.opening",
        additional_parameters={'discharge_coefficient': 0.6, 'width': 11.5},
    )
    builder.add_gate(
        component_id="g3",
        opening=0.45,
        additional_parameters={'discharge_coefficient': 0.58, 'width': 16.0},
    )

    # Branched river segments
    builder.add_river_channel(
        component_id="trib_chan",
        volume=4.0e5,
        water_level=3.2,
        k=0.00032,
    )
    builder.add_river_channel(
        component_id="main_chan",
        volume=5.0e5,
        water_level=6.0,
        k=0.00026,
    )

    # Network topology
    builder.connect_components([
        ("res1", "g1"),
        ("g1", "trib_chan"),
        ("res2", "g2"),
        ("trib_chan", "main_chan"),
        ("g2", "main_chan"),
        ("main_chan", "g3"),
    ])

    print("Setting up multi-agent control system...")
    bus = builder.harness.message_bus

    twin_agents = [
        DigitalTwinAgent("twin_res1", builder.get_component("res1"), bus, "state.res1.level"),
        DigitalTwinAgent("twin_g1", builder.get_component("g1"), bus, "state.g1.opening"),
        DigitalTwinAgent("twin_res2", builder.get_component("res2"), bus, "state.res2.level"),
        DigitalTwinAgent("twin_g2", builder.get_component("g2"), bus, "state.g2.opening"),
    ]

    pid1 = PIDController(Kp=-0.6, Ki=-0.07, Kd=-0.12, setpoint=8.0, min_output=0.0, max_output=1.0)
    pid2 = PIDController(Kp=-0.55, Ki=-0.06, Kd=-0.11, setpoint=12.8, min_output=0.0, max_output=1.0)

    lca1 = LocalControlAgent(
        agent_id="lca_g1",
        message_bus=bus,
        dt=config['dt'],
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
        command_topic="command.res1.setpoint",
    )
    lca2 = LocalControlAgent(
        agent_id="lca_g2",
        message_bus=bus,
        dt=config['dt'],
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
        command_topic="command.res2.setpoint",
    )

    dispatcher = CentralDispatcherAgent(
        agent_id="central_dispatcher",
        message_bus=bus,
        mode="rule",
        subscribed_topic="state.res1.level",
        observation_key="water_level",
        command_topic="command.res1.setpoint",
        dispatcher_params={
            "low_level": 7.8,
            "high_level": 8.6,
            "low_setpoint": 8.1,
            "high_setpoint": 7.9,
        },
    )

    for agent in (*twin_agents, lca1, lca2, dispatcher):
        builder.add_agent(agent)

    return builder


def run_branched_network_simulation() -> None:
    """Build, execute, and summarize the branched network scenario."""
    print("\n--- Setting up Complex Networks Simulation (Refactored) ---")
    builder = create_branched_network_system()

    print("\nBuilding simulation harness...")
    builder.build()

    print("Running simulation...")
    builder.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    builder.print_final_states()

    history = builder.get_history()
    if history:
        final_res1_level = history[-1]['res1']['water_level']
        final_res2_level = history[-1]['res2']['water_level']
        print(f"\nFinal reservoir 1 water level: {final_res1_level:.2f} m (Setpoint: 8.0 m)")
        print(f"Final reservoir 2 water level: {final_res2_level:.2f} m (Setpoint: 12.8 m)")


if __name__ == "__main__":
    run_branched_network_simulation()
