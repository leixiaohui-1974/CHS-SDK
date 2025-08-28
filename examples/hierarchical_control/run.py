import subprocess
import os
import sys

def main():
    """
    This script runs the hierarchical control example.
    It calls the main simulation runner and the visualization script
    located in the parent directory.
    """
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct paths to the generic runners and config files
    sim_runner_path = os.path.join(current_dir, '..', 'run_simulation.py')
    viz_runner_path = os.path.join(current_dir, '..', 'visualize_results.py')
    sim_config_path = os.path.join(current_dir, 'sim_config.json')

    # --- Step 1: Run the simulation ---
    print("--- Running Simulation ---")
    sim_command = [sys.executable, sim_runner_path, sim_config_path]

    try:
        subprocess.run(sim_command, check=True)
        print("\n--- Simulation Finished Successfully ---")
    except subprocess.CalledProcessError as e:
        print(f"\n--- Simulation Failed: {e} ---", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n--- Error: Could not find the runner script at {sim_runner_path} ---", file=sys.stderr)
        print("Please ensure you are running this from the correct directory.", file=sys.stderr)
        sys.exit(1)

    # --- Step 2: Generate visualizations ---
    print("\n--- Generating Visualization ---")
    output_dir = os.path.join(current_dir, 'output')
    viz_command = [sys.executable, viz_runner_path, output_dir]

    try:
        subprocess.run(viz_command, check=True)
        print("\n--- Visualization Finished Successfully ---")
        print(f"Results, including plots, are in the '{output_dir}' directory.")
    except subprocess.CalledProcessError as e:
        print(f"\n--- Visualization Failed: {e} ---", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
