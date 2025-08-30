import os
import sys
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import logging

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from docs.examples.canal_control.canal_models import LevelPoolCanal, IntegralCanal
from core_lib.physical_objects.integral_delay_canal import IntegralDelayCanal
from docs.examples.canal_control.canal_models import IntegralDelayZeroPointCanal
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.control.pid_controller import PIDController

def get_class(class_name):
    """Maps class names to class objects."""
    class_map = {
        "LevelPoolCanal": LevelPoolCanal,
        "IntegralCanal": IntegralCanal,
        "IntegralDelayCanal": IntegralDelayCanal,
        "IntegralDelayZeroPointCanal": IntegralDelayZeroPointCanal,
        "LocalControlAgent": LocalControlAgent,
        "Gate": Gate,
        "Reservoir": Reservoir,
        "PIDController": PIDController
    }
    return class_map[class_name]

def run_scenario(config_path):
    """
    Runs a single simulation scenario from a YAML configuration file.
    """
    scenario_name = os.path.splitext(os.path.basename(config_path))[0]
    print(f"--- Running Scenario: {scenario_name} ---")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    harness = SimulationHarness(config=config.get('simulation', {}))
    message_bus = MessageBus()

    # Manually load components
    component_instances = {}
    for comp_conf in config.get('components', []):
        CompClass = get_class(comp_conf['class'])
        instance = CompClass(name=comp_conf['name'], initial_state=comp_conf['initial_state'], parameters=comp_conf['parameters'])
        harness.add_component(instance)
        component_instances[comp_conf['name']] = instance

    # Manually load topology
    for conn in config.get('topology', []):
        harness.add_connection(conn['from'], conn['to'])

    # Manually load agents
    for agent_conf in config.get('agents', []):
        AgentClass = get_class(agent_conf['class'])
        pid_params = agent_conf['parameters']['pid']
        pid_controller = PIDController(
            Kp=pid_params['Kp'],
            Ki=pid_params['Ki'],
            Kd=pid_params['Kd'],
            setpoint=pid_params['setpoint'],
            min_output=pid_params['output_range'][0],
            max_output=pid_params['output_range'][1]
        )

        agent = AgentClass(
            agent_id=agent_conf['name'],
            message_bus=message_bus,
            controller=pid_controller,
            observation_topic=agent_conf['parameters']['observation_topic'],
            action_topic=agent_conf['parameters']['action_topic'],
            observation_key='water_level',
            dt=config.get('simulation', {}).get('time_step', 10)
        )
        harness.add_agent(agent)
        harness.subscribe_to_action(agent_conf['parameters']['action_topic'])

    harness.build()
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

    results_df = pd.DataFrame(flat_data)
    results_df['scenario'] = scenario_name

    results_path = os.path.join(os.path.dirname(config_path), f"results_{scenario_name}.csv")
    results_df.to_csv(results_path, index=False)
    print(f"Results for {scenario_name} saved to {results_path}")

    return results_df


def plot_comparison(all_results, output_dir):
    """
    Plots a comparison of the water levels from different scenarios.
    """
    plt.figure(figsize=(14, 8))

    for scenario_name, group in all_results.groupby('scenario'):
        plt.plot(group['time'], group['canal_1.water_level'], label=f"{scenario_name}")

    plt.title('Canal Model Comparison: Water Level Dynamics')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Water Level (m)')
    plt.legend()
    plt.grid(True)

    plot_path = os.path.join(output_dir, "model_comparison_results.png")
    plt.savefig(plot_path)
    print(f"Comparison plot saved to {plot_path}")
    plt.show()


def main():
    """
    Main function to run all scenarios and plot the comparison.
    """
    scenario_files = [
        "level_pool.yml",
        "integral.yml",
        "integral_delay.yml",
        "integral_delay_zero_point.yml"
    ]

    output_dir = os.path.dirname(__file__)
    all_results = []

    for scenario_file in scenario_files:
        config_path = os.path.join(output_dir, scenario_file)
        results = run_scenario(config_path)
        all_results.append(results)

    combined_results = pd.concat(all_results, ignore_index=True)
    plot_comparison(combined_results, output_dir)
    print("All scenarios executed and results plotted.")


if __name__ == "__main__":
    main()
