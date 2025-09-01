#!/usr/bin/env python3
"""
Refactored Example: Hierarchical Control System using SimulationBuilder.

This script demonstrates how to use SimulationBuilder to simplify the setup
of a two-level hierarchical control system.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent

def create_hierarchical_control_system():
    """
    Creates a hierarchical control system using SimulationBuilder.
    
    Returns:
        SimulationBuilder: Configured simulation builder
    """
    # Initialize builder with simulation configuration
    config = {'duration': 500, 'dt': 1.0}
    builder = SimulationBuilder(config)
    
    # Communication topics
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"
    
    # Add physical components using builder methods
    builder.add_reservoir(
        component_id="reservoir_1",
        water_level=19.0,
        surface_area=1.5e6,
        volume=28.5e6
    )
    
    builder.add_gate(
        component_id="gate_1",
        opening=0.1,
        max_flow_rate=100.0,
        control_topic=GATE_ACTION_TOPIC
    )
    
    # Connect components
    builder.connect_components([("reservoir_1", "gate_1")])
    
    # Add digital twin agents
    reservoir_twin = DigitalTwinAgent(
        agent_id="twin_reservoir_1",
        simulated_object=builder.get_component("reservoir_1"),
        message_bus=builder.harness.message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )
    
    gate_twin = DigitalTwinAgent(
        agent_id="twin_gate_1",
        simulated_object=builder.get_component("gate_1"),
        message_bus=builder.harness.message_bus,
        state_topic=GATE_STATE_TOPIC
    )
    
    # Add PID controller and local control agent
    pid = PIDController(
        Kp=-0.8, Ki=-0.1, Kd=-0.2,
        setpoint=15.0,
        min_output=0.0,
        max_output=5.0
    )
    
    lca = LocalControlAgent(
        agent_id="lca_gate_1",
        controller=pid,
        message_bus=builder.harness.message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=config['dt'],
        command_topic=GATE_COMMAND_TOPIC,
        feedback_topic=GATE_STATE_TOPIC
    )
    
    # Add central dispatcher
    dispatcher = CentralDispatcherAgent(
        agent_id="dispatcher_1",
        message_bus=builder.harness.message_bus,
        mode="rule",
        subscribed_topic=RESERVOIR_STATE_TOPIC,
        observation_key="water_level",
        command_topic=GATE_COMMAND_TOPIC,
        dispatcher_params={
            "low_level": 12.0,
            "high_level": 18.0,
            "low_setpoint": 15.0,
            "high_setpoint": 12.0
        }
    )
    
    # Add all agents to the builder
    builder.add_agent(reservoir_twin)
    builder.add_agent(gate_twin)
    builder.add_agent(lca)
    builder.add_agent(dispatcher)
    
    return builder

def run_hierarchical_simulation():
    """
    Sets up and runs the hierarchical control simulation.
    """
    print("\n--- Setting up Hierarchical Control Simulation (Refactored) ---")
    
    # Create the simulation system
    builder = create_hierarchical_control_system()
    
    # Build and run the simulation
    builder.build()
    
    print("\n--- Running Hierarchical Simulation ---")
    builder.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    # Print final results
    builder.print_final_states()
    
    # Get specific final values
    history = builder.get_history()
    if history:
        final_level = history[-1]['reservoir_1']['water_level']
        final_opening = history[-1]['gate_1']['opening']
        print(f"\nFinal reservoir water level: {final_level:.2f} m")
        print(f"Final gate opening: {final_opening:.2f} m")

if __name__ == "__main__":
    run_hierarchical_simulation()