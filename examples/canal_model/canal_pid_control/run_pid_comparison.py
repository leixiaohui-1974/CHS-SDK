import os
import sys
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# Add project root to Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder

def run_and_log_scenario(scenario_name, config_path, results_dir):
    """
    Runs a simulation scenario and logs the results to a CSV file.
    """
    print(f"--- Running Scenario: {scenario_name} ---")

    try:
        # Load and run the simulation
        loader = SimulationBuilder(scenario_path=config_path)
        harness = loader.load()
        harness.run()

        # Log results
        output_data = harness.get_logged_data()
        df = pd.DataFrame(output_data)

        # Ensure the results directory exists
        results_dir.mkdir(parents=True, exist_ok=True)

        output_file = results_dir / f"results_{scenario_name}.csv"
        df.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")

        return output_file

    except Exception as e:
        print(f"Error running scenario '{scenario_name}': {e}")
        return None

def plot_results(csv_files, plot_title, output_image_path):
    """
    Plots the water level from multiple CSV files on a single graph.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    for scenario_name, file_path in csv_files.items():
        if file_path:
            df = pd.read_csv(file_path)
            # Try different possible column names for the target reservoir water level
            water_level_col = None
            possible_cols = ['target_reservoir_water_level', 'downstream_reservoir_water_level', 'canal_2_water_level']
            for col in possible_cols:
                if col in df.columns:
                    water_level_col = col
                    break
            
            if water_level_col:
                ax.plot(df['time'], df[water_level_col], label=scenario_name, linewidth=2.5)
            else:
                print(f"Warning: No suitable water level column found for {scenario_name}. Available columns: {list(df.columns)}")

    ax.set_title(plot_title, fontsize=18, weight='bold')
    ax.set_xlabel("Time (seconds)", fontsize=14)
    ax.set_ylabel("Reservoir Water Level (meters)", fontsize=14)
    ax.legend(fontsize=12, loc='best')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.tick_params(axis='both', which='major', labelsize=12)

    fig.tight_layout()
    plt.savefig(output_image_path)
    print(f"Plot saved to {output_image_path}")

if __name__ == "__main__":
    # Base path for the scenarios
    base_path = Path(__file__).parent
    results_directory = base_path

    # Define scenarios to run
    scenarios = {
        "Local Upstream Control (User Defined)": "config_local_upstream_user_def.yml",
        "Distant Downstream Control (User Defined)": "config_distant_downstream_user_def.yml",
    }

    # Run scenarios and collect CSV file paths
    csv_results = {}
    for name, config_file in scenarios.items():
        # Note: The YAML files for these scenarios need to be created.
        # This script assumes they exist in the same directory.
        # For now, this will likely fail until the YAML files are set up.
        # This example is primarily to show the structure of a comparison script.

        # This part of the script is illustrative. To make it runnable,
        # you would need to create the corresponding YAML configuration files.
        # e.g., 'config_local_upstream_user_def.yml'

        print(f"\nSkipping '{name}' because YAML configurations are placeholders.")
        print("To run this, create the corresponding YAML files based on the scenario description.")

    # Example of what would happen if the files existed:
    # csv_results["Local Upstream Control"] = run_and_log_scenario(
    #     "local_upstream_user_def",
    #     base_path / "config_local_upstream_user_def.yml",
    #     results_directory
    # )

    # Since we are skipping the runs, we will use the pre-existing CSV files for plotting
    print("\n--- Using pre-existing CSV files for plotting ---")
    pre_existing_csv = {
        "Local Upstream Control": results_directory / "results_local_upstream_user_def.csv",
        "Distant Downstream Control": results_directory / "results_distant_downstream_user_def.csv",
    }

    # Check if pre-existing files are available
    valid_csv_files = {name: path for name, path in pre_existing_csv.items() if path.exists()}

    if not valid_csv_files:
        print("Could not find pre-existing CSV files. Plotting will be skipped.")
    else:
        # Plot the results
        plot_results(
            valid_csv_files,
            "PID Controller Performance: Water Level Stability",
            results_directory / "pid_comparison_results.png"
        )
