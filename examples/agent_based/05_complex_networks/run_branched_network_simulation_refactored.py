#!/usr/bin/env python3
"""
Refactored Example: Complex Branched Network using SimulationBuilder.

This script demonstrates how to use SimulationBuilder to simplify the setup
of a complex, branched network topology.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent

def create_branched_network_system():
    """
    Creates a complex branched network system using SimulationBuilder.
    
    Returns:
        SimulationBuilder: Configured simulation builder
    """
    # Initialize builder with simulation configuration
    config = {'duration': 1000, 'dt': 1.0}
    builder = SimulationBuilder(config)
    
    print("Initializing physical components...")
    
    # Add reservoirs using builder methods
    builder.add_reservoir(
        component_id="res1",
        water_level=10.0,
        surface_area=1.5e6,
        volume=15e6
    )
    
    builder.add_reservoir(
        component_id="res2",
        water_level=20.0,
        surface_area=1.5e6,
        volume=30e6
    )
    
    # Add gates using builder methods
    builder.add_gate(
        component_id="g1",
        opening=0.1,
        max_flow_rate=100.0,
        control_topic="action.g1.opening"
    )
    
    builder.add_gate(
        component_id="g2",
        opening=0.1,
        max_flow_rate=150.0,
        control_topic="action.g2.opening"
    )
    
    builder.add_gate(
        component_id="g3",
        opening=0.5,
        max_flow_rate=200.0
    )
    
    # Add river channels manually (not in builder yet)
    trib_chan = RiverChannel(
        name="trib_chan",
        initial_state={'volume': 2e5, 'water_level': 2.0},
        parameters={'k': 0.0002}
    )
    
    main_chan = RiverChannel(
        name="main_chan",
        initial_state={'volume': 8e5, 'water_level': 8.0},
        parameters={'k': 0.0001}
    )
    
    builder.harness.add_component("trib_chan", trib_chan)
    builder.harness.add_component("main_chan", main_chan)
    
    print("Defining network connections...")
    
    # Define the complex network topology
    connections = [
        ("res1", "g1"),
        ("g1", "trib_chan"),
        ("res2", "g2"),
        ("trib_chan", "main_chan"),
        ("g2", "main_chan"),
        ("main_chan", "g3")
    ]
    
    builder.connect_components(connections)
    
    print("Setting up multi-agent control system...")
    
    # Add digital twin agents
    twin_agents = [
        DigitalTwinAgent(
            agent_id="twin_res1",
            simulated_object=builder.get_component("res1"),
            message_bus=builder.harness.message_bus,
            state_topic="state.res1.level"
        ),
        DigitalTwinAgent(
            agent_id="twin_g1",
            simulated_object=builder.get_component("g1"),
            message_bus=builder.harness.message_bus,
            state_topic="state.g1.opening"
        ),
        DigitalTwinAgent(
            agent_id="twin_res2",
            simulated_object=builder.get_component("res2"),
            message_bus=builder.harness.message_bus,
            state_topic="state.res2.level"
        ),
        DigitalTwinAgent(
            agent_id="twin_g2",
            simulated_object=builder.get_component("g2"),
            message_bus=builder.harness.message_bus,
            state_topic="state.g2.opening"
        )
    ]
    
    # Add PID controllers and local control agents
    pid1 = PIDController(
        Kp=-0.5, Ki=-0.05, Kd=-0.1,
        setpoint=12.0,
        min_output=0.0,
        max_output=1.0
    )
    
    pid2 = PIDController(
        Kp=-0.4, Ki=-0.04, Kd=-0.1,
        setpoint=18.0,
        min_output=0.0,
        max_output=1.0
    )
    
    lca1 = LocalControlAgent(
        agent_id="lca_g1",
        controller=pid1,
        message_bus=builder.harness.message_bus,
        observation_topic="state.res1.level",
        observation_key="water_level",
        action_topic="action.g1.opening",
        dt=config['dt'],
        command_topic="command.res1.setpoint"
    )
    
    lca2 = LocalControlAgent(
        agent_id="lca_g2",
        controller=pid2,
        message_bus=builder.harness.message_bus,
        observation_topic="state.res2.level",
        observation_key="water_level",
        action_topic="action.g2.opening",
        dt=config['dt'],
        command_topic="command.res2.setpoint"
    )
    
    # Add central dispatcher for monitoring
    dispatcher = CentralDispatcherAgent(
        agent_id="central_dispatcher",
        message_bus=builder.harness.message_bus,
        mode="rule",
        subscribed_topic="state.res1.level",
        observation_key="water_level",
        command_topic="command.res1.setpoint",
        dispatcher_params={
            "low_level": 8.0,
            "high_level": 12.0,
            "low_setpoint": 10.0,
            "high_setpoint": 8.0
        }
    )
    
    # Add all agents to the builder
    all_agents = twin_agents + [lca1, lca2, dispatcher]
    for agent in all_agents:
        builder.add_agent(agent)
    
    return builder

def run_branched_network_simulation():
    """
    Sets up and runs the branched network simulation.
    """
    print("\n--- Setting up Complex Networks Simulation (Refactored) ---")
    
    # Create the simulation system
    builder = create_branched_network_system()
    
    # Build and run the simulation
    print("\nBuilding simulation harness...")
    builder.build()
    
    print("Running simulation...")
    builder.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    # Print final results
    builder.print_final_states()
    
    # Get specific final values
    history = builder.get_history()
    if history:
        final_res1_level = history[-1]['res1']['water_level']
        final_res2_level = history[-1]['res2']['water_level']
        print(f"\nFinal reservoir 1 water level: {final_res1_level:.2f} m (Setpoint: 12.0 m)")
        print(f"Final reservoir 2 water level: {final_res2_level:.2f} m (Setpoint: 18.0 m)")

if __name__ == "__main__":
    run_branched_network_simulation()