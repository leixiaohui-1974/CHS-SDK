import os
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationLoader

def run_scenario(scenario_name, config_path, components_file):
    """
    Runs a single simulation scenario and saves the results.

    NOTE: This file renaming approach is fragile and not ideal for production use.
    A better approach would be to modify the SimulationLoader to accept the
    components file path directly as an argument.
    """
    print(f"--- Running Scenario: {scenario_name} ---")

    # The SimulationLoader needs to be pointed to a directory where it can find
    # all the necessary .yml files. We will temporarily rename the components file
    # for the current scenario to 'components.yml'.
    original_components_path = os.path.join(config_path, 'components.yml')
    scenario_components_path = os.path.join(config_path, components_file)
    os.rename(scenario_components_path, original_components_path)

    try:
        # Load and run the simulation
        loader = SimulationLoader(scenario_path=config_path)
        harness = loader.load()
        harness.run_mas_simulation()

        # Process and save results
        history = harness.history
        if not history:
            print(f"Warning: No history recorded for scenario {scenario_name}")
            return

        flat_data = []
        for step_data in history:
            row = {'time': step_data['time']}
            for comp_id, state in step_data.items():
                if comp_id != 'time':
                    for key, value in state.items():
                        row[f"{comp_id}_{key}"] = value
            flat_data.append(row)

        df = pd.DataFrame(flat_data)
        scenario_output_filename = f"results_{scenario_name}.csv"
        df.to_csv(os.path.join(config_path, scenario_output_filename), index=False)
        print(f"Results for {scenario_name} saved to {scenario_output_filename}")

    finally:
        # Clean up: restore original components.yml name
        os.rename(original_components_path, scenario_components_path)

def plot_results(scenarios, config_path):
    """
    Plots the results from all scenarios for comparison.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), sharex=True)

    colors = plt.cm.viridis(np.linspace(0, 1, len(scenarios)))

    for i, scenario_name in enumerate(scenarios):
        filepath = os.path.join(config_path, f"results_{scenario_name}.csv")
        if not os.path.exists(filepath):
            print(f"Results file not found for scenario: {scenario_name}")
            continue

        df = pd.read_csv(filepath)

        # Plot water levels
        ax1.plot(df['time'], df['canal_water_level'], label=f'Canal Water Level ({scenario_name})', color=colors[i])

        # Plot gate openings
        ax2.plot(df['time'], df['gate_1_opening'], label=f'Gate 1 Opening ({scenario_name})', color=colors[i])


    ax1.set_title('Canal Water Level Comparison for Different Models', fontsize=16)
    ax1.set_ylabel('Water Level (m)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    ax2.set_title('Gate Opening', fontsize=16)
    ax2.set_ylabel('Gate Opening (0-1)')
    ax2.set_xlabel('Time (s)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    plt.tight_layout()
    plot_path = os.path.join(config_path, 'model_comparison_results.png')
    plt.savefig(plot_path)
    print(f"Comparison plot saved to {plot_path}")


def main():
    """Main function to run all scenarios and plot results."""
    config_path = os.path.dirname(__file__)

    scenarios = {
        "integral": "components_integral.yml",
        "integral_delay": "components_integral_delay.yml",
        "integral_delay_zero": "components_integral_delay_zero.yml",
        "linear_reservoir": "components_linear_reservoir.yml"
    }

    for name, components_file in scenarios.items():
        run_scenario(name, config_path, components_file)

    plot_results(list(scenarios.keys()), config_path)
    print("All scenarios executed and results plotted.")


if __name__ == "__main__":
    main()
