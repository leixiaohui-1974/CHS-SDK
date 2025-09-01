#!/usr/bin/env python3
"""
Example simulation script for Tutorial 1: A simple reservoir-gate system.

This script demonstrates the basic, non-agent-based simulation mode of the platform.
It sets up a single reservoir with a high water level and a PID controller that
opens a downstream gate to bring the water level down to a desired setpoint.
"""

import sys
import os

# Add the project root to the Python path
# This is necessary to run the script directly from the command line
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def run_getting_started_simulation():
    """
    Sets up and runs the reservoir-gate simulation.
    """
    print("--- Setting up Tutorial 1: Getting Started Simulation ---")

    # 1. --- Component Setup ---

    # Reservoir Model
    reservoir_params = {
        'surface_area': 1.5e6,  # m^2
        'storage_curve': [[0, 0], [30e6, 20]]  # [[volume_m3, level_m], ...]
    }
    reservoir_initial_state = {
        'volume': 21e6,  # m^3, equivalent to 14m * 1.5e6 m^2
        'water_level': 14.0  # m, initial level is above the setpoint
    }
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state=reservoir_initial_state,
        parameters=reservoir_params
    )

    # Gate Model
    gate_params = {
        'max_rate_of_change': 0.1,
        'discharge_coefficient': 0.6,
        'width': 10
    }
    gate_initial_state = {
        'opening': 0.5  # 50% open
    }
    gate = Gate(
        name="gate_1",
        initial_state=gate_initial_state,
        parameters=gate_params
    )

    # PID Controller
    # For a reverse-acting process (opening gate lowers level),
    # the controller gains must be negative.
    pid_controller = PIDController(
        Kp=-0.5,
        Ki=-0.01,
        Kd=-0.1,
        setpoint=12.0,      # Target water level in meters
        min_output=0.0,
        max_output=1.0      # Gate opening is a percentage
    )

    # 2. --- Simulation Harness Setup ---

    simulation_config = {
        'duration': 300,  # Simulate for 300 seconds
        'dt': 1.0         # Time step of 1 second
    }
    harness = SimulationHarness(config=simulation_config)

    # Add components to the harness
    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate)

    # Define the physical connection
    harness.add_connection("reservoir_1", "gate_1")

    # Add the controller and link it to the component it controls and observes
    harness.add_controller(
        controller_id="pid_controller_1",
        controller=pid_controller,
        controlled_id="gate_1",
        observed_id="reservoir_1",
        observation_key="water_level"
    )

    # Finalize the harness setup
    harness.build()

    # 3. --- Run Simulation ---
    print("\n--- Running Simulation ---")
    harness.run_simulation()
    print("\n--- Simulation Complete ---")
    
    # 4. --- Analyze Results ---
    print("\n--- Analyzing Results ---")
    
    # Extract data from simulation history
    times = [step['time'] for step in harness.history]
    water_levels = [step['reservoir_1']['water_level'] for step in harness.history]
    gate_openings = [step['gate_1']['opening'] for step in harness.history]
    
    # Calculate performance metrics
    setpoint = 12.0
    final_water_level = water_levels[-1]
    steady_state_error = abs(final_water_level - setpoint)
    
    # Calculate settling time (time to reach within 2% of setpoint)
    tolerance = 0.02 * setpoint
    settling_time = None
    for i, level in enumerate(water_levels):
        if abs(level - setpoint) <= tolerance:
            settling_time = times[i]
            break
    
    # Calculate overshoot
    max_level = max(water_levels)
    overshoot = max(0, max_level - setpoint)
    overshoot_percent = (overshoot / setpoint) * 100 if setpoint != 0 else 0
    
    print(f"\n=== PID Control Performance Analysis ===")
    print(f"Target water level (setpoint): {setpoint:.2f} m")
    print(f"Initial water level: {water_levels[0]:.2f} m")
    print(f"Final water level: {final_water_level:.2f} m")
    print(f"Steady-state error: {steady_state_error:.4f} m")
    print(f"Maximum overshoot: {overshoot:.4f} m ({overshoot_percent:.2f}%)")
    if settling_time is not None:
        print(f"Settling time (2% tolerance): {settling_time:.1f} s")
    else:
        print("System did not settle within simulation time")
    
    # Calculate RMSE
    import math
    rmse = math.sqrt(sum((level - setpoint)**2 for level in water_levels) / len(water_levels))
    print(f"Root Mean Square Error (RMSE): {rmse:.4f} m")
    
    # Create visualization
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot water level
        ax1.plot(times, water_levels, 'b-', linewidth=2, label='Water Level')
        ax1.axhline(y=setpoint, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Water Level (m)')
        ax1.set_title('PID Control of Reservoir Water Level')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot gate opening
        ax2.plot(times, gate_openings, 'g-', linewidth=2, label='Gate Opening')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Gate Opening (0-1)')
        ax2.set_title('PID Controller Output (Gate Opening)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('01_getting_started_results.png', dpi=300, bbox_inches='tight')
        print(f"\nResults plot saved as '01_getting_started_results.png'")
        
    except ImportError:
        print("\nMatplotlib not available, skipping visualization")
    
    # Validate control performance
    print("\n=== Control Performance Validation ===")
    if steady_state_error < 0.1:
        print("✓ PASS: Steady-state error is acceptable (< 0.1 m)")
    else:
        print("✗ FAIL: Steady-state error is too large (>= 0.1 m)")
    
    if overshoot_percent < 20:
        print("✓ PASS: Overshoot is acceptable (< 20%)")
    else:
        print("✗ FAIL: Overshoot is too large (>= 20%)")
    
    if settling_time is not None and settling_time < 50:
        print("✓ PASS: Settling time is acceptable (< 50 s)")
    else:
        print("✗ FAIL: Settling time is too long or system did not settle")

if __name__ == "__main__":
    run_getting_started_simulation()
