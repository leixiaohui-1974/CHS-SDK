import os
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path
import copy

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.mission.scenario_agent import ScenarioAgent
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate

def run_scenario(scenario_name, config, base_components, canal_params, config_path):
    """
    Runs a single simulation scenario with a specific canal model configuration.
    """
    print(f"--- Running Scenario: {scenario_name} ---")

    # Deepcopy base components to avoid state leaking between scenarios
    current_components = copy.deepcopy(base_components)

    canal_initial_state = {'water_level': 5.0, 'inflow': 25.0, 'outflow': 25.0} # Start in steady state
    canal = UnifiedCanal(name='canal', initial_state=canal_initial_state, parameters=canal_params)

    all_components = current_components + [canal]

    connections = [
        {'upstream': 'upstream_reservoir', 'downstream': 'gate_1'},
        {'upstream': 'gate_1', 'downstream': 'canal'},
        {'upstream': 'canal', 'downstream': 'downstream_reservoir'}
    ]

    # --- Correctly instantiate and configure the SimulationHarness ---
    harness = SimulationHarness(config=config['simulation'])

    # Use the message bus created by the harness
    bus = harness.message_bus

    # Load the scenario events script and create the agent
    with open(os.path.join(config_path, 'event_scenario.yml'), 'r') as f:
        event_config = yaml.safe_load(f)
    scenario_agent = ScenarioAgent(
        agent_id='scenario_agent',
        message_bus=bus,
        scenario_script=event_config['scenario_script']
    )

    # Add all simulation objects to the harness
    for component in all_components:
        harness.add_component(component.name, component)

    for conn in connections:
        harness.add_connection(conn['upstream'], conn['downstream'])

    harness.add_agent(scenario_agent)

    # Build the harness (e.g., for topological sort) and run the simulation
    harness.build()
    # We must use run_mas_simulation because we are using an agent
    harness.run_mas_simulation()

    history = harness.history
    if not history:
        print(f"Warning: No history recorded for scenario {scenario_name}")
        return

    # Correctly flatten the history data
    flat_data = []
    for time_step_data in history:
        row = {'time': time_step_data['time']}
        for component_id, component_state in time_step_data.items():
            if component_id != 'time':
                for key, value in component_state.items():
                    row[f"{component_id}_{key}"] = value
        flat_data.append(row)

    df = pd.DataFrame(flat_data)
    scenario_output_filename = f"results_{scenario_name}.csv"
    df.to_csv(os.path.join(os.path.dirname(__file__), scenario_output_filename), index=False)
    print(f"Results for {scenario_name} saved to {scenario_output_filename}")

def plot_results(scenarios, config_path):
    # This function remains unchanged
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
    colors = plt.cm.viridis(np.linspace(0, 1, len(scenarios)))

    for i, scenario_name in enumerate(scenarios):
        filepath = os.path.join(config_path, f"results_{scenario_name}.csv")
        if not os.path.exists(filepath):
            print(f"Results file not found for scenario: {scenario_name}")
            continue

        df = pd.read_csv(filepath)
        ax1.plot(df['time'], df['canal_water_level'], label=f'Canal Water Level ({scenario_name})', color=colors[i])
        if i == 0:
             ax2.plot(df['time'], df['gate_1_opening'], label='Gate 1 Opening', color='black')

    ax1.set_title('渠道模型的水位响应对比', fontsize=16)
    ax1.set_ylabel('水位 (m)')
    ax1.legend(loc='upper right')
    ax1.grid(True)
    ax2.set_title('闸门开度', fontsize=16)
    ax2.set_ylabel('开度 (0-1)')
    ax2.set_xlabel('时间 (s)')
    ax2.legend(loc='upper right')
    ax2.grid(True)
    plt.tight_layout()
    plot_path = os.path.join(config_path, 'model_comparison_results.png')
    plt.savefig(plot_path)
    print(f"比较图已保存至 {plot_path}")

def main():
    config_path = os.path.dirname(__file__)

    with open(os.path.join(config_path, 'config.yml'), 'r') as f:
        config = yaml.safe_load(f)

    # Manually define base components
    base_components = [
        Reservoir(name='upstream_reservoir',
                  initial_state={'water_level': 10.0},
                  parameters={'area': 10000.0, 'inflow': 50.0}),
        Gate(name='gate_1',
             initial_state={'opening': 0.5},
             parameters={'width': 5.0, 'discharge_coefficient': 0.8}),
        Reservoir(name='downstream_reservoir',
                  initial_state={'water_level': 4.0},
                  parameters={'area': 10000.0, 'inflow': 0.0})
    ]

    scenarios = {
        "integral": {'model_type': 'integral', 'surface_area': 10000},
        "integral_delay": {'model_type': 'integral_delay', 'gain': 0.001, 'delay': 300},
        "integral_delay_zero": {'model_type': 'integral_delay_zero', 'gain': 0.001, 'delay': 300, 'zero_time_constant': 50},
        "linear_reservoir": {'model_type': 'linear_reservoir', 'storage_constant': 1200, 'level_storage_ratio': 0.005}
    }

    for name, params in scenarios.items():
        run_scenario(name, config, base_components, params, config_path)

    plot_results(list(scenarios.keys()), config_path)
    print("所有场景执行完毕，并已绘制结果。")

if __name__ == "__main__":
    main()
