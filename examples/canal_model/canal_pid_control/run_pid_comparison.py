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
from core_lib.io.yaml_loader import SimulationLoader
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def run_scenario(scenario_name, config, base_components, agent_configs):
    """
    Runs a single simulation scenario with a specific agent configuration.
    """
    print(f"--- Running Scenario: {scenario_name} ---")

    bus = MessageBus()

    # Deepcopy base components to avoid state leaking between scenarios
    components = copy.deepcopy(base_components)

    # Instantiate agents for the current scenario
    agents = []
    for agent_config in agent_configs:
        controller = PIDController(**agent_config['controller_config'])
        agent = LocalControlAgent(
            agent_id=agent_config['id'],
            message_bus=bus,
            controller=controller,
            observation_topic=agent_config['observation_topic'],
            action_topic=agent_config['action_topic'],
            observation_key=agent_config['observation_key'],
            dt=config['simulation']['dt']
        )
        agents.append(agent)

    # Instantiate the harness
    harness = SimulationHarness(config=config['simulation'])
    harness.message_bus = bus # Manually assign the bus

    # Add components to the harness
    for component in components:
        harness.add_component(component)

    # Add connections to the harness
    for connection in config['connections']:
        harness.add_connection(connection['upstream'], connection['downstream'])

    # Add agents to the harness
    for agent in agents:
        harness.add_agent(agent)

    # Build the harness after all elements are added
    harness.build()

    harness.run_mas_simulation()

    history = harness.history
    if not history:
        print(f"Warning: No history recorded for scenario {scenario_name}")
        return

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
        # Plot water levels for canal 1 and 2
        ax1.plot(df['time'], df['canal_1_water_level'], label=f'Canal 1 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2])
        ax1.plot(df['time'], df['canal_2_water_level'], label=f'Canal 2 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2+1])
        # Plot gate openings
        ax2.plot(df['time'], df['gate_1_opening'], label=f'Gate 1 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2])
        ax2.plot(df['time'], df['gate_2_opening'], label=f'Gate 2 ({scenario_name})', linestyle=line_styles[i], color=colors[i*2+1])

    # Add setpoint lines for canal 1 and 2
    ax1.axhline(y=5.0, color='gray', linestyle='--', label='Setpoint Canal 1 (5.0m)')
    ax1.axhline(y=4.5, color='black', linestyle='--', label='Setpoint Canal 2 (4.5m)')
    ax1.set_title('PID控制策略的水位对比', fontsize=16)
    ax1.set_ylabel('水位 (m)')
    ax1.legend(loc='upper right')
    ax1.grid(True)
    ax2.set_title('闸门开度对比', fontsize=16)
    ax2.set_ylabel('开度 (0-1)')
    ax2.set_xlabel('时间 (s)')
    ax2.legend(loc='upper right')
    ax2.grid(True)
    plt.tight_layout()
    plot_path = os.path.join(config_path, 'pid_comparison_results.png')
    plt.savefig(plot_path)
    print(f"比较图已保存至 {plot_path}")

def main():
    config_path = os.path.dirname(__file__)

    with open(os.path.join(config_path, 'config.yml'), 'r') as f:
        config = yaml.safe_load(f)
    with open(os.path.join(config_path, 'components.yml'), 'r') as f:
        components_config = yaml.safe_load(f)['components']
    with open(os.path.join(config_path, 'topology.yml'), 'r') as f:
        config['connections'] = yaml.safe_load(f)['connections']

    # Manually map class names to the actual classes
    from core_lib.physical_objects.reservoir import Reservoir
    from core_lib.physical_objects.gate import Gate
    from core_lib.physical_objects.unified_canal import UnifiedCanal
    CLASS_MAP = {
        "Reservoir": Reservoir,
        "Gate": Gate,
        "UnifiedCanal": UnifiedCanal,
    }

    # Manually instantiate components
    components = []
    for c_conf in components_config:
        CompClass = CLASS_MAP[c_conf['class']]
        # The constructor expects 'name' and unpacks other dicts.
        instance = CompClass(
            name=c_conf['id'],
            initial_state=c_conf.get('initial_state', {}),
            parameters=c_conf.get('parameters', {})
        )
        components.append(instance)

    # "Adjacent Downstream Control" is a more descriptive name for the classic "Upstream Control"
    # method, where a gate regulates the water level of the canal reach immediately downstream.
    # Scenarios implemented according to the user's specific definitions.
    # New Topology: reservoir -> gate_1 -> canal_1 -> gate_2 -> canal_2
    agent_scenarios = {
        # User's Definition of "Local Upstream Control":
        # - Gate 2 controls the water level of the canal IN FRONT of it (canal_1).
        # - Gate 1 has a fixed opening (no controller).
        "local_upstream_user_def": [
            {'id': 'gate2_local_upstream_controller', 'controller_config': {'Kp': 0.6, 'Ki': 0.07, 'Kd': 0.1, 'setpoint': 5.0, 'min_output': 0, 'max_output': 1}, 'observation_topic': 'canal_1', 'observation_key': 'water_level', 'action_topic': 'gate_2'}
        ],
        # User's Definition of "Remote Downstream Control":
        # - Gate 1 controls the water level of the canal AFTER it (canal_1).
        # - Gate 2 controls the water level of the canal AFTER it (canal_2).
        "distant_downstream_user_def": [
            {'id': 'gate1_distant_downstream_controller', 'controller_config': {'Kp': 0.5, 'Ki': 0.05, 'Kd': 0.1, 'setpoint': 5.0, 'min_output': 0, 'max_output': 1}, 'observation_topic': 'canal_1', 'observation_key': 'water_level', 'action_topic': 'gate_1'},
            {'id': 'gate2_distant_downstream_controller', 'controller_config': {'Kp': 0.5, 'Ki': 0.05, 'Kd': 0.1, 'setpoint': 4.5, 'min_output': 0, 'max_output': 1}, 'observation_topic': 'canal_2', 'observation_key': 'water_level', 'action_topic': 'gate_2'}
        ]
    }

    for name, agent_configs in agent_scenarios.items():
        run_scenario(name, config, components, agent_configs)

    plot_results(list(agent_scenarios.keys()), config_path)
    print("所有场景执行完毕，并已绘制结果。")

if __name__ == "__main__":
    main()
