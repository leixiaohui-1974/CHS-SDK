#!/usr/bin/env python3
"""
Example simulation script for a simple pressurized pipe and valve system.

This script demonstrates the physical dynamics of a Pipe and Valve, showing how
flow and head loss are affected by valve opening changes.
"""

import sys
import os
import math
import time as pytime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.pipe import Pipe
from core_lib.physical_objects.valve import Valve

def run_pipe_valve_simulation():
    """
    Sets up and runs the pipe-valve simulation with a manual loop.
    """
    print("--- Setting up Pipe and Valve Simulation ---")

    # 1. --- Component Setup ---
    pipe_params = {
        'diameter': 0.5,
        'length': 1000,
        'friction_factor': 0.02
    }
    pipe = Pipe(
        name="pipe_1",
        initial_state={},
        parameters=pipe_params
    )

    valve_params = {
        'diameter': 0.5,
        'discharge_coefficient': 0.8
    }
    valve = Valve(
        name="valve_1",
        initial_state={'opening': 0.0},
        parameters=valve_params
    )

    # 2. --- Simulation Parameters ---
    duration = 600
    dt = 1.0
    upstream_head = 50.0  # Constant head from a large reservoir
    downstream_head = 20.0 # Constant head at the outlet

    # 3. --- Run Manual Simulation Loop ---
    print("\n--- Running Simulation ---")
    print(f"{'Time (s)':<10} | {'Valve Opening (%)':<20} | {'Pipe Outflow (m3/s)':<25} | {'Pipe Head Loss (m)':<20}")
    print("-" * 80)

    for i in range(int(duration / dt)):
        current_time = i * dt

        # Manually vary the valve opening over time
        valve_opening = 50 * (1 + math.sin(current_time / 100))
        valve.step({'control_signal': valve_opening}, dt)

        # The head at the pipe outlet is the downstream head plus the head loss from the valve.
        # This is a simplification; in a real system, these would be solved simultaneously.
        # For this example, we assume the valve's head loss is negligible compared to the pipe's.
        # So, the head at the pipe outlet is simply the downstream head.

        # The valve's outflow calculation requires upstream and downstream heads.
        # The upstream head for the valve is the source head minus the pipe's head loss.
        # This creates a circular dependency.

        # Let's simplify: calculate pipe flow first, assuming valve is just a downstream boundary.
        # Then, calculate valve flow based on pipe's output head. This isn't physically perfect
        # but demonstrates the component behaviors for an example.

        # In a real system, the flow would be the same through both components,
        # and the total head loss would be the sum of the losses in the pipe and valve.
        # To solve this requires an iterative solver. For this example, we'll make a
        # simplification: we calculate the flow as if the valve were the only component,
        # and then use that flow to determine the head loss in the pipe.

        # Calculate the potential flow through the valve given the total head difference
        valve_action = {'upstream_head': upstream_head, 'downstream_head': downstream_head}
        valve_state = valve.step(valve_action, dt)
        flow = valve_state['outflow']

        # Now, use this flow to calculate the head loss in the pipe
        pipe_action = {'outflow': flow}
        pipe_state = pipe.step(pipe_action, dt)

        if int(current_time) % 30 == 0:
            print(f"{current_time:<10.1f} | {valve_state['opening']:<20.2f} | {pipe_state['outflow']:<25.4f} | {pipe_state['head_loss']:<20.4f}")

        # A small delay to make the simulation not finish instantly
        pytime.sleep(0.01)

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_pipe_valve_simulation()
