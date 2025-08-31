import sys
import os
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder

def run_scenario(scenario_name, agent_ids, config_path):
    """
    Runs a single simulation scenario and saves the results.
    """
    print(f"--- Running Scenario: {scenario_name} ---")

    # Create a temporary agents.yml for the current scenario
    with open(os.path.join(config_path, 'agents.yml'), 'r') as f:
        all_agents_config = yaml.safe_load(f)

    scenario_agents_config = {
        'agents': [agent for agent in all_agents_config['agents'] if agent['id'] in agent_ids]
    }

    temp_agents_path = os.path.join(config_path, 'temp_agents.yml')
    with open(temp_agents_path, 'w') as f:
        yaml.dump(scenario_agents_config, f)

    # The SimulationLoader needs to be pointed to a directory where it can find
    # components.yml, topology.yml, config.yml, and the (temporary) agents.yml.
    # We rename our temp file to what the loader expects.
    original_agents_path = os.path.join(config_path, 'agents.yml')
    os.rename(original_agents_path, original_agents_path + '.bak')
    os.rename(temp_agents_path, original_agents_path)

    try:
        # Load and run the simulation
        loader = SimulationBuilder(scenario_path=config_path)
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
        # Clean up: restore original agents.yml and delete temp file
        os.rename(original_agents_path, temp_agents_path) # rename back to temp
        os.rename(original_agents_path + '.bak', original_agents_path) # restore original
        if os.path.exists(temp_agents_path):
             os.remove(temp_agents_path)


def plot_results(scenarios, config_path):
    """
    Plots the results from all scenarios for comparison.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), sharex=True)

    colors = plt.cm.viridis(np.linspace(0, 1, len(scenarios) * 2))
    line_styles = ['-', '--', ':']

    for i, scenario_name in enumerate(scenarios):
        filepath = os.path.join(config_path, f"results_{scenario_name}.csv")
        if not os.path.exists(filepath):
            print(f"Results file not found for scenario: {scenario_name}")
            continue

        df = pd.read_csv(filepath)

        # Plot water levels
        ax1.plot(df['time'], df['canal_1_water_level'], label=f'Canal 1 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2])
        ax1.plot(df['time'], df['canal_2_water_level'], label=f'Canal 2 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2+1])
        ax1.plot(df['time'], df['canal_3_water_level'], label=f'Canal 3 ({scenario_name})', linestyle='-.', color=colors[i*2])

        # Plot gate openings
        ax2.plot(df['time'], df['gate_1_opening'], label=f'Gate 1 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2])
        ax2.plot(df['time'], df['gate_2_opening'], label=f'Gate 2 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2+1])

    # Add setpoint lines
    ax1.axhline(y=5.0, color='gray', linestyle='--', label='Setpoint Canal 1 (5.0m)')
    ax1.axhline(y=4.5, color='black', linestyle='--', label='Setpoint Canal 2 (4.5m)')
    ax1.axhline(y=4.0, color='gray', linestyle=':', label='Setpoint Canal 3 (4.0m)')


    ax1.set_title('Canal Water Levels Comparison', fontsize=16)
    ax1.set_ylabel('Water Level (m)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    ax2.set_title('Gate Openings Comparison', fontsize=16)
    ax2.set_ylabel('Gate Opening (0-1)')
    ax2.set_xlabel('Time (s)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    plt.tight_layout()
    plot_path = os.path.join(config_path, 'pid_comparison_results.png')
    plt.savefig(plot_path)
    print(f"Comparison plot saved to {plot_path}")


def main():
    """Main function to run all scenarios and plot results."""
    config_path = os.path.dirname(__file__)

    scenarios = {
        "local_upstream": ["gate1_local_controller", "gate2_local_controller"],
        "distant_downstream": ["gate1_distant_controller", "gate2_distant_controller"],
        "mixed_control": ["gate1_mixed_controller", "gate2_mixed_controller"]
    }

    for name, agents in scenarios.items():
        run_scenario(name, agents, config_path)

    plot_results(list(scenarios.keys()), config_path)
    print("All scenarios executed and results plotted.")


if __name__ == "__main__":
    main()
