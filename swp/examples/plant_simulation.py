"""
Part 1: High-Fidelity Plant Simulation

This script simulates a canal system using the high-fidelity NetworkSolver.
It acts as the "real world" or "digital twin plant," generating sensor data
based on actuator inputs. This data will be saved to a CSV file for use
in a subsequent system identification task.

The system consists of:
- A main canal reach modeled with St. Venant equations.
- A controllable gate at the downstream end of the reach.
- A short dummy reach after the gate to enable correct node calculations.
- An upstream boundary condition providing a constant inflow.
- A downstream boundary condition representing a fixed water level.
"""

import numpy as np
import pandas as pd
from swp.simulation_identification.physical_objects.st_venant_reach import StVenantReach
from swp.simulation_identification.hydro_nodes.gate_node import GateNode
from swp.core_engine.solver.network_solver import NetworkSolver

def run_plant_simulation():
    """
    Sets up the components for the high-fidelity plant simulation.
    """
    print("--- Setting up the High-Fidelity Plant Simulation ---")

    # --- 1. Define Simulation Parameters ---
    sim_dt = 5.0
    sim_theta = 0.6
    num_steps = 100

    # --- 2. Define Reaches ---
    initial_depth = 4.0
    initial_flow = 100.0

    # Main upstream reach
    upstream_reach = StVenantReach(
        name="upstream_reach",
        length=5000, num_points=51,
        bottom_width=20, side_slope_z=2, manning_n=0.03, slope=0.001,
        initial_H=np.full(51, initial_depth),
        initial_Q=np.full(51, initial_flow)
    )

    # Short dummy reach downstream of the gate
    downstream_reach = StVenantReach(
        name="downstream_reach",
        length=100, num_points=2, # Minimal points needed
        bottom_width=20, side_slope_z=2, manning_n=0.03, slope=0.001,
        initial_H=np.full(2, initial_depth - 0.5), # Lower initial level
        initial_Q=np.full(2, initial_flow)
    )

    # --- 3. Define Node ---
    control_gate = GateNode(name="control_gate", width=20, discharge_coeff=0.7)
    control_gate.set_opening(0.8)

    # --- 4. Create and Configure the Solver ---
    solver = NetworkSolver(dt=sim_dt, theta=sim_theta)
    solver.add_component(upstream_reach)
    solver.add_component(downstream_reach)
    solver.add_component(control_gate)

    # Link the gate between the two reaches
    control_gate.link_to_reaches(up_obj=upstream_reach, down_obj=downstream_reach)
    control_gate.upstream_idx = -1
    control_gate.downstream_idx = 0

    # --- 5. Set Boundary Conditions ---
    # Upstream end of the whole system
    solver.add_boundary_condition(
        component=upstream_reach, var='Q', point_idx=0, value_func=lambda t: initial_flow
    )
    # Downstream end of the whole system
    solver.add_boundary_condition(
        component=downstream_reach, var='H', point_idx=-1, value_func=lambda t: initial_depth - 0.5
    )

    print("Physical network built successfully.")

    return {
        "solver": solver,
        "upstream_reach": upstream_reach,
        "downstream_reach": downstream_reach,
        "gate": control_gate,
        "num_steps": num_steps,
        "dt": sim_dt
    }

def execute_simulation_and_log_data(plant_setup):
    """
    Runs the simulation loop and logs data to a pandas DataFrame.
    """
    solver = plant_setup['solver']
    up_reach = plant_setup['upstream_reach']
    down_reach = plant_setup['downstream_reach']
    gate = plant_setup['gate']
    num_steps = plant_setup['num_steps']
    dt = plant_setup['dt']

    data_log = []

    print("\n--- Starting Simulation and Data Logging ---")
    for i in range(num_steps):
        current_time = i * dt

        if i == 20:
            print(f"\n!!! Time {current_time}s: Applying step input to gate. !!!\n")
            gate.set_opening(0.4)

        log_entry = {
            "timestamp": current_time,
            "gate_opening": gate.opening, # Fixed: Changed from get_opening()
            # Sensor 1: Water level just before the gate
            "upstream_water_level": up_reach.H[-1],
            # Sensor 2: Water level just after the gate
            "downstream_water_level": down_reach.H[0]
        }
        data_log.append(log_entry)

        solver.step(current_time)

        if i % 10 == 0:
            print(f"  Step {i}/{num_steps}: Gate Opening={gate.opening:.2f}, Upstream H={up_reach.H[-1]:.3f}m, Downstream H={down_reach.H[0]:.3f}m")

    print("\n--- Simulation Complete ---")
    return pd.DataFrame(data_log)

if __name__ == "__main__":
    plant_setup = run_plant_simulation()
    if plant_setup:
        results_df = execute_simulation_and_log_data(plant_setup)

        output_filename = "plant_data.csv"
        results_df.to_csv(output_filename, index=False)
        print(f"\n--- Plant simulation data saved to {output_filename} ---")
        print(results_df.head())
