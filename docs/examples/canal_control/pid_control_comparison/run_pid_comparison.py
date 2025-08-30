import os
import pandas as pd
import matplotlib.pyplot as plt
import logging
import sys

# Add the project root to the Python path
# This is necessary to ensure that the core_lib modules can be found
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationLoader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - root - %(levelname)s - %(message)s')

def run_scenario(config_path: str, scenario_name: str):
    """Loads and runs a specific scenario from YAML configuration files."""
    logging.info(f"--- Running Scenario: {scenario_name} ---")

    scenario_specific_path = os.path.join(config_path, scenario_name)

    loader = SimulationLoader(scenario_specific_path)

    # The load() method returns a fully configured and built harness
    harness = loader.load()

    # Run the simulation
    harness.run_mas_simulation()

    # Process and return results
    history = harness.history
    flat_data = []
    for step_data in history:
        row = {'time': step_data['time']}
        for comp_id, state in step_data.items():
            if comp_id != 'time':
                for key, value in state.items():
                    row[f"{comp_id}.{key}"] = value
        flat_data.append(row)

    return pd.DataFrame(flat_data)

def plot_results(results_dict, output_dir):
    """Plots the results from all scenarios for comparison."""
    plt.style.use('seaborn-v0_8-whitegrid')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 14), sharex=True)

    line_styles = ['-', '--', ':']
    colors = {
        'local_upstream': 'blue',
        'distant_downstream': 'green',
        'mixed_control': 'red'
    }

    # Plot Water Levels
    for i, (scenario_name, df) in enumerate(results_dict.items()):
        if df.empty:
            logging.warning(f"DataFrame for scenario '{scenario_name}' is empty. Skipping plot.")
            continue

        color = colors.get(scenario_name, 'black')

        for canal_num in [1, 2, 3]:
            col_name = f'canal_{canal_num}.water_level'
            if col_name in df.columns:
                ax1.plot(df['time'], df[col_name], label=f'Canal {canal_num} ({scenario_name})', linestyle=line_styles[i], color=color, alpha=0.8)
            else:
                logging.warning(f"Column '{col_name}' not found for scenario '{scenario_name}'.")

    ax1.axhline(y=5.0, color='grey', linestyle='--', label='Setpoint Canal 1 (Upstream)')
    ax1.axhline(y=4.5, color='grey', linestyle='-.', label='Setpoint Canal 2 (Upstream/Downstream)')
    ax1.axhline(y=4.0, color='grey', linestyle=':', label='Setpoint Canal 3 (Downstream)')

    ax1.set_title('Canal Water Level Comparison Across Scenarios', fontsize=16)
    ax1.set_ylabel('Water Level (m)')
    ax1.legend(loc='upper right')
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Plot Gate Openings
    gate_colors = ['darkorange', 'purple']
    for i, (scenario_name, df) in enumerate(results_dict.items()):
        if df.empty:
            continue

        scenario_color = colors.get(scenario_name, 'black')

        if 'gate_1.opening' in df.columns:
            ax2.plot(df['time'], df['gate_1.opening'], label=f'Gate 1 ({scenario_name})', linestyle=line_styles[i], color=gate_colors[0])
        if 'gate_2.opening' in df.columns:
            ax2.plot(df['time'], df['gate_2.opening'], label=f'Gate 2 ({scenario_name})', linestyle=line_styles[i], color=gate_colors[1])

    ax2.set_title('Gate Opening Comparison Across Scenarios', fontsize=16)
    ax2.set_ylabel('Gate Opening (0-1)')
    ax2.set_xlabel('Time (s)')
    ax2.legend(loc='upper right')
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'pid_comparison_results.png')
    plt.savefig(plot_path)
    logging.info(f"Comparison plot saved to {plot_path}")

def main():
    """Main function to run all scenarios and plot results."""
    base_config_path = os.path.dirname(__file__)

    scenarios = ["local_upstream", "distant_downstream", "mixed_control"]
    results = {}

    for name in scenarios:
        df = run_scenario(base_config_path, name)
        results[name] = df

        output_csv_path = os.path.join(base_config_path, f"results_{name}.csv")
        df.to_csv(output_csv_path, index=False)
        logging.info(f"Results for {name} saved to {output_csv_path}")

    plot_results(results, base_config_path)
    logging.info("All scenarios executed and results plotted.")

if __name__ == "__main__":
    main()
