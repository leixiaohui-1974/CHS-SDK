"""
End-to-End Example: Branched Network Simulation with the new 1D Hydrodynamic Solver.
"""
import numpy as np
from swp.simulation_identification.physical_objects.st_venant_reach import StVenantReach
from swp.simulation_identification.hydro_nodes.gate_node import GateNode
from swp.core_engine.solver.network_solver import NetworkSolver

def run_hydrodynamic_network_example():
    """
    Sets up and runs a simple network simulation using the 1D hydrodynamic solver.
    This example models a simple network: Reach1 -> Gate -> Reach2
    """
    print("--- Setting up the 1D Hydrodynamic Network Example ---")

    # --- 1. Define Simulation Parameters ---
    sim_dt = 10.0  # Time step in seconds
    sim_theta = 0.8 # Implicit weighting factor
    num_steps = 20
    time = 0.0

    # --- 2. Define Reaches ---
    # Initial conditions: steady, uniform flow
    initial_depth = 5.0
    initial_flow = 150.0

    # Reach 1
    reach1_len = 1000
    reach1_pts = 11 # 10 segments
    reach1 = StVenantReach(
        name="reach1", length=reach1_len, num_points=reach1_pts,
        bottom_width=20, side_slope_z=2, manning_n=0.03, slope=0.001,
        initial_H=np.full(reach1_pts, initial_depth),
        initial_Q=np.full(reach1_pts, initial_flow)
    )

    # Reach 2
    reach2_len = 2000
    reach2_pts = 21 # 20 segments
    reach2 = StVenantReach(
        name="reach2", length=reach2_len, num_points=reach2_pts,
        bottom_width=20, side_slope_z=2, manning_n=0.03, slope=0.001,
        initial_H=np.full(reach2_pts, initial_depth),
        initial_Q=np.full(reach2_pts, initial_flow)
    )

    # --- 3. Define Nodes ---
    gate1 = GateNode(name="gate1", width=20, discharge_coeff=0.6)
    gate1.set_opening(0.5) # Partially closed gate

    # --- 4. Create and Configure the Solver ---
    solver = NetworkSolver(dt=sim_dt, theta=sim_theta)

    # Add components
    solver.add_component(reach1)
    solver.add_component(reach2)
    solver.add_component(gate1)

    # Link nodes to reaches
    gate1.link_to_reaches(up_obj=reach1, down_obj=reach2)
    # Use negative index to refer to the last point, as the solver now handles this.
    gate1.upstream_idx = -1
    gate1.downstream_idx = 0

    # --- 5. Set Boundary Conditions using the new method ---
    solver.add_boundary_condition(reach1, 'H', 0, lambda t: initial_depth)
    solver.add_boundary_condition(reach2, 'H', -1, lambda t: initial_depth)

    # --- 6. Run the Simulation ---
    print("\n--- Starting Hydrodynamic Simulation ---")
    for i in range(num_steps):
        current_time = i * solver.dt
        print(f"\n--- Time Step {i+1}/{num_steps} (t={current_time:.1f}s) ---")

        # Manually change a component state to see an effect
        if i == 5:
            print("\n!!! CLOSING GATE FURTHER !!!\n")
            gate1.set_opening(0.2)

        solver.step(current_time)

        # Print some state
        print(f"  Reach 1: H_start={reach1.H[0]:.3f}, H_end={reach1.H[-1]:.3f} | Q_end={reach1.Q[-1]:.3f}")
        print(f"  Reach 2: H_start={reach2.H[0]:.3f}, H_end={reach2.H[-1]:.3f} | Q_start={reach2.Q[0]:.3f}")

    print("\n--- Simulation Finished ---")


if __name__ == "__main__":
    run_hydrodynamic_network_example()
