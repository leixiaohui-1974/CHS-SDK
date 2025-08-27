"""
Verification Example for the 1D St. Venant Model.

This script verifies the correctness of the StVenantReach implementation
by comparing its steady-state results against the theoretical solution for
uniform flow, calculated using the Manning's equation.

The process is as follows:
1.  Calculate the theoretical "normal depth" for a given flow rate and
    channel geometry.
2.  Set up a simulation with a single channel reach. The upstream boundary
    is a constant inflow, and the downstream boundary is fixed at the
    calculated normal depth to encourage a steady state.
3.  Run the simulation for a long duration to allow it to settle.
4.  Compare the final simulated water depth profile with the theoretical
    normal depth and report the error.
5.  Plot the results for visual inspection.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

from swp.core_engine.solver.network_solver import NetworkSolver
from swp.simulation_identification.physical_objects.st_venant_reach import StVenantReach

# =============================================================================
# Configuration
# =============================================================================
VALIDATION_CONFIG = {
    # Simulation settings
    "duration": 500,  # s (long enough to reach steady state)
    "dt": 2.0,        # s
    "theta": 1.0,     # Use fully implicit for stability

    # Channel Geometry and Properties
    "length": 2000,   # m
    "num_points": 20,
    "bottom_width": 10.0, # m
    "side_slope_z": 2.0,  # z:1
    "manning_n": 0.025,
    "slope": 0.001,

    # Flow Conditions
    "flow_rate_Q": 50.0, # m^3/s
}

# =============================================================================
# Theoretical Calculation
# =============================================================================
def calculate_normal_depth(config):
    """
    Solves the Manning's equation to find the theoretical normal depth (y_n).
    """
    b = config["bottom_width"]
    z = config["side_slope_z"]
    n = config["manning_n"]
    S0 = config["slope"]
    Q = config["flow_rate_Q"]

    # Define the Manning's equation as a function to be solved for y (depth)
    # We want to find y such that: Q - (1/n) * A * R^(2/3) * S^(1/2) = 0
    def manning_equation(y):
        if y <= 0:
            return float('inf')
        area = (b + z * y) * y
        wetted_perimeter = b + 2 * y * np.sqrt(1 + z**2)
        hydraulic_radius = area / wetted_perimeter

        # Calculate flow based on y
        flow_calc = (1/n) * area * (hydraulic_radius**(2/3)) * (S0**0.5)
        return Q - flow_calc

    # Use a numerical solver to find the root of the equation
    # We start with an initial guess, e.g., 1.0 meter
    initial_guess = 1.0
    normal_depth, = fsolve(manning_equation, initial_guess)

    print(f"--- Theoretical Calculation ---")
    print(f"Calculated Normal Depth (y_n): {normal_depth:.4f} m")
    return normal_depth

# =============================================================================
# Simulation and Verification
# =============================================================================
def run_verification(config):
    """
    Sets up, runs, and verifies the St. Venant simulation.
    """
    # 1. Get the theoretical ground truth
    y_n = calculate_normal_depth(config)

    # 2. Set up the simulation
    print("\n--- Setting up Simulation ---")
    num_points = config["num_points"]
    Q = config["flow_rate_Q"]

    # Start the simulation with a flat water profile at the expected normal depth
    initial_H = np.full(num_points, y_n, dtype=float)
    initial_Q = np.full(num_points, Q, dtype=float)

    reach = StVenantReach(
        name="verification_reach", length=config["length"], num_points=num_points,
        bottom_width=config["bottom_width"], side_slope_z=config["side_slope_z"],
        manning_n=config["manning_n"], slope=config["slope"],
        initial_H=initial_H, initial_Q=initial_Q
    )

    solver = NetworkSolver(dt=config["dt"], theta=config["theta"])
    solver.add_component(reach)

    # Upstream BC: Constant flow rate
    solver.add_boundary_condition(
        component=reach, var='Q', point_idx=0,
        value_func=lambda t: Q
    )
    # Downstream BC: Fixed water level at normal depth
    solver.add_boundary_condition(
        component=reach, var='H', point_idx=-1,
        value_func=lambda t: y_n
    )

    # 3. Run the simulation
    print("\n--- Running Simulation ---")
    num_steps = int(config["duration"] / config["dt"])
    for i in range(num_steps):
        solver.step(i * config["dt"])

    print("Simulation finished.")

    # 4. Analyze and verify the results
    print("\n--- Verification Results ---")
    final_H = reach.H

    # We expect the water profile to be flat and equal to y_n
    mean_simulated_depth = np.mean(final_H)
    max_error = np.max(np.abs(final_H - y_n))

    print(f"Theoretical Normal Depth (y_n): {y_n:.4f} m")
    print(f"Mean Simulated Depth at End:    {mean_simulated_depth:.4f} m")
    print(f"Maximum Absolute Error:         {max_error:.4f} m")

    # Define a tolerance for verification success
    tolerance = 0.01 # 1 cm
    if max_error < tolerance:
        print(f"\nSUCCESS: The model is verified. Maximum error ({max_error:.4f}m) is within tolerance ({tolerance}m).")
    else:
        print(f"\nFAILURE: The model failed verification. Maximum error ({max_error:.4f}m) exceeds tolerance ({tolerance}m).")

    # 5. Plot results
    plot_results(reach, y_n, config)

def plot_results(reach, normal_depth, config):
    """Plots the final water surface profile against the theoretical normal depth."""
    x_coords = np.linspace(0, config["length"], config["num_points"])
    final_H = reach.H

    plt.figure(figsize=(12, 7))
    plt.plot(x_coords, final_H, 'b-o', label='Simulated Final Water Depth')
    plt.axhline(y=normal_depth, color='r', linestyle='--', label=f'Theoretical Normal Depth ({normal_depth:.3f}m)')

    plt.title('St. Venant Model Verification: Steady Uniform Flow')
    plt.xlabel('Distance along Channel (m)')
    plt.ylabel('Water Depth (m)')
    plt.legend()
    plt.grid(True)
    plt.ylim(bottom=normal_depth - 0.5, top=normal_depth + 0.5)

    output_filename = "verification_results.png"
    plt.savefig(output_filename)
    print(f"\nVerification plot saved to {output_filename}")


if __name__ == "__main__":
    run_verification(VALIDATION_CONFIG)
