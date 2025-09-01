#!/usr/bin/env python3
"""
Refactored hydropower plant simulation using SimulationBuilder.

This demonstrates how the SimulationBuilder class simplifies the setup
of a hydropower system with upstream reservoir, turbine, and downstream reservoir.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from core_lib.core_engine.testing.simulation_builder import create_hydropower_system

def run_hydropower_simulation_refactored():
    """
    Refactored hydropower simulation using SimulationBuilder.
    """
    print("--- Setting up Refactored Hydropower Plant Simulation ---")

    # 1. Create simulation using builder pattern
    simulation_config = {'end_time': 10, 'dt': 1.0}
    builder = create_hydropower_system(simulation_config)
    
    # 2. Build and run simulation
    builder.build()
    
    print("\n--- Running Refactored Simulation ---")
    num_steps = int(simulation_config['end_time'] / simulation_config['dt'])
    dt = simulation_config['dt']
    
    # Get components for direct access
    source_res = builder.get_component("source_res")
    downstream_res = builder.get_component("downstream_res")
    turbine = builder.get_component("turbine_1")
    
    for i in range(num_steps):
        current_time = i * dt
        print(f"\n--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")
        
        # Get head levels from reservoirs
        source_head = source_res.get_state()['water_level']
        downstream_head = downstream_res.get_state()['water_level']
        
        # Update the turbine with infinite inflow assumption
        turbine.set_inflow(float('inf'))
        
        # Step the turbine with head information
        turbine_action = {
            'upstream_head': source_head,
            'downstream_head': downstream_head
        }
        turbine_state = turbine.step(turbine_action, dt)
        turbine.set_state(turbine_state)
        
        # Update reservoirs based on turbine outflow
        outflow = turbine_state.get('outflow', 0)
        
        # Source reservoir loses water
        source_action = {'outflow': outflow}
        source_state = source_res.step(source_action, dt)
        source_res.set_state(source_state)
        
        # Downstream reservoir gains water
        downstream_res.set_inflow(outflow)
        downstream_action = {}
        downstream_state = downstream_res.step(downstream_action, dt)
        downstream_res.set_state(downstream_state)
        
        # Store history
        step_history = {
            'time': current_time,
            'source_res': source_state,
            'turbine_1': turbine_state,
            'downstream_res': downstream_state
        }
        builder.harness.history.append(step_history)
        
        # Print step results
        power_generated = turbine_state.get('power', 0)
        print(f"  Turbine Power: {power_generated:.2f} MW")
        print(f"  Turbine Outflow: {outflow:.2f} m^3/s")
        print(f"  Source Water Level: {source_state['water_level']:.2f} m")
        print(f"  Downstream Water Level: {downstream_state['water_level']:.2f} m")
    
    # Print final results
    print("\n--- Simulation Complete ---")
    builder.print_final_states()
    
    # Calculate total energy generated
    total_energy = sum(step['turbine_1']['power'] for step in builder.get_history()) * dt / 3600  # Convert to MWh
    print(f"\nTotal Energy Generated: {total_energy:.2f} MWh")
    
    final_turbine_state = turbine.get_state()
    print(f"Final Turbine Power: {final_turbine_state['power']:.2f} MW")
    print(f"Final Turbine Outflow: {final_turbine_state['outflow']:.2f} m^3/s")

if __name__ == "__main__":
    run_hydropower_simulation_refactored()