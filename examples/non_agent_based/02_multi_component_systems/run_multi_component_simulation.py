#!/usr/bin/env python3
"""
Example simulation script for Tutorial 2: A multi-component system.

This script demonstrates a more complex simulation with multiple, interconnected
components and two independent controllers.

The physical topology is:
Reservoir -> Gate 1 -> RiverChannel -> Gate 2

The control objectives are:
1. Control the Reservoir's water level by adjusting Gate 1.
2. Control the RiverChannel's volume by adjusting Gate 2.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def run_multi_component_simulation():
    """
    Sets up and runs the multi-component simulation.
    """
    print("--- Setting up Tutorial 2: Multi-Component Simulation ---")

    # 1. --- Component Setup ---

    # Reservoir
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'water_level': 15.0, 'volume': 15.0 * 1e6},
        parameters={'surface_area': 1e6, 'storage_curve': [[0, 0], [30e6, 30]]}
    )

    # Gate 1 (downstream of Reservoir)
    gate1 = Gate(
        name="gate_1",
        initial_state={'opening': 0.25},
        parameters={'discharge_coefficient': 0.8, 'width': 12}
    )

    # River Channel (downstream of Gate 1)
    channel = RiverChannel(
        name="channel_1",
        initial_state={'volume': 500000},
        parameters={'k': 0.0001} # Storage coefficient
    )

    # Gate 2 (downstream of River Channel)
    gate2 = Gate(
        name="gate_2",
        initial_state={'opening': 0.5},
        parameters={'discharge_coefficient': 0.7, 'width': 10}
    )

    # 2. --- Controller Setup ---

    # Controller 1: Reservoir Level Control (controls gate_1)
    # This is a direct-acting process: to raise the level, we need to close the gate (reduce opening).
    # A positive error (level is too low) should result in a negative action (closing the gate).
    # Therefore, the gains should be negative.
    controller1 = PIDController(
        Kp=-0.2, Ki=-0.01, Kd=-0.05,
        setpoint=18.0, # Target reservoir level
        min_output=0.0, max_output=1.0
    )

    # Controller 2: Channel Volume Control (controls gate_2)
    # This is a reverse-acting process: to lower the volume, we need to open the gate (increase opening).
    # A positive error (volume is too high) should result in a positive action (opening the gate).
    # Therefore, the gains should be negative.
    controller2 = PIDController(
        Kp=-1e-5, Ki=-1e-7, Kd=-1e-6,
        setpoint=4e5, # Target channel volume
        min_output=0.0, max_output=1.0
    )

    # 3. --- Simulation Harness Setup ---

    harness = SimulationHarness(config={'duration': 500, 'dt': 1.0})

    # Add all components
    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate1)
    harness.add_component("channel_1", channel)
    harness.add_component("gate_2", gate2)

    # Define the physical connections to establish the topology
    harness.add_connection("reservoir_1", "gate_1")
    harness.add_connection("gate_1", "channel_1")
    harness.add_connection("channel_1", "gate_2")

    # Add the controllers and wire them to the system
    harness.add_controller(
        controller_id="res_level_ctrl",
        controller=controller1,
        controlled_id="gate_1",
        observed_id="reservoir_1",
        observation_key="water_level"
    )
    harness.add_controller(
        controller_id="chan_vol_ctrl",
        controller=controller2,
        controlled_id="gate_2",
        observed_id="channel_1",
        observation_key="volume"
    )

    # Finalize the harness setup
    harness.build()

    # 4. --- Run Simulation ---
    print("\n--- Running Simulation ---")
    harness.run_simulation()
    print("\n--- Simulation Complete ---")
    
    # 5. --- Analyze Results ---
    print("\n--- Analyzing Results ---")
    
    # Extract data from simulation history
    times = [step['time'] for step in harness.history]
    reservoir_levels = [step['reservoir_1']['water_level'] for step in harness.history]
    channel_volumes = [step['channel_1']['volume'] for step in harness.history]
    gate1_openings = [step['gate_1']['opening'] for step in harness.history]
    gate2_openings = [step['gate_2']['opening'] for step in harness.history]
    
    # Calculate performance metrics for reservoir level control
    reservoir_setpoint = 18.0
    final_reservoir_level = reservoir_levels[-1]
    reservoir_steady_state_error = abs(final_reservoir_level - reservoir_setpoint)
    
    # Calculate performance metrics for channel volume control
    channel_setpoint = 4e5
    final_channel_volume = channel_volumes[-1]
    channel_steady_state_error = abs(final_channel_volume - channel_setpoint)
    
    # Calculate RMSE for both controllers
    import math
    reservoir_rmse = math.sqrt(sum((level - reservoir_setpoint)**2 for level in reservoir_levels) / len(reservoir_levels))
    channel_rmse = math.sqrt(sum((vol - channel_setpoint)**2 for vol in channel_volumes) / len(channel_volumes))
    
    print(f"\n=== Multi-Component PID Control Performance Analysis ===")
    print(f"\n--- Reservoir Level Control ---")
    print(f"Target water level (setpoint): {reservoir_setpoint:.2f} m")
    print(f"Initial water level: {reservoir_levels[0]:.2f} m")
    print(f"Final water level: {final_reservoir_level:.2f} m")
    print(f"Steady-state error: {reservoir_steady_state_error:.4f} m")
    print(f"RMSE: {reservoir_rmse:.4f} m")
    
    print(f"\n--- Channel Volume Control ---")
    print(f"Target volume (setpoint): {channel_setpoint:.0f} m³")
    print(f"Initial volume: {channel_volumes[0]:.0f} m³")
    print(f"Final volume: {final_channel_volume:.0f} m³")
    print(f"Steady-state error: {channel_steady_state_error:.0f} m³")
    print(f"RMSE: {channel_rmse:.0f} m³")
    
    # Create visualization
    try:
        import matplotlib.pyplot as plt
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot reservoir water level
        ax1.plot(times, reservoir_levels, 'b-', linewidth=2, label='Water Level')
        ax1.axhline(y=reservoir_setpoint, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Water Level (m)')
        ax1.set_title('Reservoir Water Level Control')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot channel volume
        ax2.plot(times, channel_volumes, 'g-', linewidth=2, label='Volume')
        ax2.axhline(y=channel_setpoint, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Volume (m³)')
        ax2.set_title('Channel Volume Control')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot gate 1 opening (controls reservoir level)
        ax3.plot(times, gate1_openings, 'orange', linewidth=2, label='Gate 1 Opening')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Opening (0-1)')
        ax3.set_title('Gate 1 Opening (Reservoir Control)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot gate 2 opening (controls channel volume)
        ax4.plot(times, gate2_openings, 'purple', linewidth=2, label='Gate 2 Opening')
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Opening (0-1)')
        ax4.set_title('Gate 2 Opening (Channel Control)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('02_multi_component_results.png', dpi=300, bbox_inches='tight')
        print(f"\nResults plot saved as '02_multi_component_results.png'")
        
    except ImportError:
        print("\nMatplotlib not available, skipping visualization")
    
    # Validate control performance
    print("\n=== Control Performance Validation ===")
    
    # Reservoir control validation
    if reservoir_steady_state_error < 0.5:
        print("✓ PASS: Reservoir steady-state error is acceptable (< 0.5 m)")
    else:
        print("✗ FAIL: Reservoir steady-state error is too large (>= 0.5 m)")
    
    # Channel control validation
    if channel_steady_state_error < 50000:  # 50,000 m³ tolerance
        print("✓ PASS: Channel volume steady-state error is acceptable (< 50,000 m³)")
    else:
        print("✗ FAIL: Channel volume steady-state error is too large (>= 50,000 m³)")
    
    # Overall system stability
    reservoir_variation = max(reservoir_levels[-10:]) - min(reservoir_levels[-10:])
    channel_variation = max(channel_volumes[-10:]) - min(channel_volumes[-10:])
    
    if reservoir_variation < 0.1:
        print("✓ PASS: Reservoir level is stable in final 10 steps")
    else:
        print("✗ FAIL: Reservoir level is still oscillating")
    
    if channel_variation < 10000:
        print("✓ PASS: Channel volume is stable in final 10 steps")
    else:
        print("✗ FAIL: Channel volume is still oscillating")

if __name__ == "__main__":
    run_multi_component_simulation()
